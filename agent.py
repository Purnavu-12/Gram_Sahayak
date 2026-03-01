from dotenv import load_dotenv
import json
import logging
import sqlite3
from typing import Optional

from livekit import agents, rtc
from livekit.agents import AgentServer, AgentSession, Agent, room_io
from livekit.agents.llm import function_tool
from livekit.plugins import (
    google,
    noise_cancellation,
)
from google.genai import types
from ddgs import DDGS

import scheme_lookup

load_dotenv()

log = logging.getLogger("gram-agent")

# ── Ensure FTS index is ready at startup ─────────────────────────────────────
scheme_lookup.ensure_fts()


# ── Per-conversation temporary memory (in-memory SQLite) ─────────────────────

class ConversationMemory:
    """In-memory SQLite store that lives for a single conversation.
    Automatically garbage-collected when the Assistant instance is destroyed."""

    def __init__(self):
        self._conn = sqlite3.connect(":memory:")
        self._conn.row_factory = sqlite3.Row
        self._conn.executescript("""
            CREATE TABLE user_profile (
                key   TEXT PRIMARY KEY,
                value TEXT NOT NULL
            );
            CREATE TABLE search_history (
                id        INTEGER PRIMARY KEY AUTOINCREMENT,
                query     TEXT NOT NULL,
                filters   TEXT,          -- JSON of {state, category, level}
                results   TEXT NOT NULL,  -- JSON array of schemes returned
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE shortlisted (
                slug       TEXT PRIMARY KEY,
                scheme_json TEXT NOT NULL
            );
        """)

    # ── user profile ──────────────────────────────────────────────────────
    def save_detail(self, key: str, value: str):
        self._conn.execute(
            "INSERT OR REPLACE INTO user_profile (key, value) VALUES (?, ?)",
            (key.lower().strip(), value.strip()),
        )
        self._conn.commit()

    def get_detail(self, key: str) -> Optional[str]:
        row = self._conn.execute(
            "SELECT value FROM user_profile WHERE key = ?", (key.lower().strip(),)
        ).fetchone()
        return row["value"] if row else None

    def get_all_details(self) -> dict:
        rows = self._conn.execute("SELECT key, value FROM user_profile").fetchall()
        return {r["key"]: r["value"] for r in rows}

    # ── search history ────────────────────────────────────────────────────
    def save_search(self, query: str, filters: dict, results: list):
        self._conn.execute(
            "INSERT INTO search_history (query, filters, results) VALUES (?, ?, ?)",
            (query, json.dumps(filters), json.dumps(results, ensure_ascii=False)),
        )
        self._conn.commit()

    def get_last_search(self) -> Optional[dict]:
        row = self._conn.execute(
            "SELECT query, filters, results FROM search_history ORDER BY id DESC LIMIT 1"
        ).fetchone()
        if not row:
            return None
        return {
            "query": row["query"],
            "filters": json.loads(row["filters"]),
            "results": json.loads(row["results"]),
        }

    def get_search_count(self) -> int:
        return self._conn.execute("SELECT COUNT(*) FROM search_history").fetchone()[0]

    # ── shortlist ─────────────────────────────────────────────────────────
    def shortlist_scheme(self, slug: str, scheme_json: dict):
        self._conn.execute(
            "INSERT OR REPLACE INTO shortlisted (slug, scheme_json) VALUES (?, ?)",
            (slug, json.dumps(scheme_json, ensure_ascii=False)),
        )
        self._conn.commit()

    def get_shortlisted(self) -> list[dict]:
        rows = self._conn.execute("SELECT scheme_json FROM shortlisted").fetchall()
        return [json.loads(r["scheme_json"]) for r in rows]

    def clear_shortlist(self):
        self._conn.execute("DELETE FROM shortlisted")
        self._conn.commit()

    def close(self):
        self._conn.close()


# ── System instructions ──────────────────────────────────────────────────────

SYSTEM_INSTRUCTIONS = """\
You are a helpful Indian government schemes assistant. Your job is to help
citizens find government schemes they are eligible for.
Be slow while talking and ask follow-up questions to clarify their needs before recommending schemes.


RESPONSE STYLE:
- Be concise and direct. Start speaking immediately — do NOT pause or hesitate.
- Keep initial responses short (1-2 sentences), then elaborate if the user asks.
- When presenting schemes, give the name and one-line summary first, then ask
  if they want more details rather than dumping everything at once.
- Speak at a natural pace. Be warm but efficient.

Ask follow-up questions to clarify the user's needs before recommending schemes.
Choose the right scheme for the user based on their specific eligibility criteria.
If asked about a specific scheme, provide accurate details including who it's for,
what benefits it offers, and how to apply.

IMPORTANT RULES:
1. When a user describes a problem or need (money, health, education, housing,
   marriage, farming, business, etc.), use your tools to search the schemes
   database for relevant government schemes.
2. ALWAYS call the `search_schemes` tool to look up schemes — never invent or
   guess scheme names.
3. If the search returns multiple schemes, present the top 3-5 briefly, then
   ask clarifying questions to narrow down:
   - Which state do they live in?
   - Their specific situation (age, gender, caste, employment status, etc.)
   - What type of help they need (cash, loan, training, subsidy, etc.)
4. When the user asks about a SPECIFIC scheme by name (e.g. 'tell me about
   PM-KISAN', 'what are the benefits of PMAY?'), call `get_scheme_details`
   to get full details — benefits, eligibility, documents, how to apply.
   This gives much richer info than the basic search results.
5. Use `web_search` if you need the latest news, updates, or any info not
   available in the database (e.g. application deadlines, recent changes).
6. Once you narrow it down to the best match, give full details: scheme name,
   description, ministry, and the URL where they can apply.
7. Respond in the same language the user speaks in.
8. Be empathetic and supportive — many users may be in difficult situations.
9. If no schemes match, say so honestly and suggest they check myscheme.gov.in
   directly or contact the helpline.

CONVERSATION MEMORY — you have persistent per-conversation memory tools:
- Call `save_user_detail` to store info the user shares (state, gender, age,
  occupation, caste, need, etc.) so you never re-ask.
- Call `recall_conversation` only when you're unsure if the user already told
  you something — do NOT call it on every turn.
- When the user gives new info (e.g. their state), call `refine_search`
  to re-run the last search with the new filter instead of starting over.
- Use `shortlist_scheme` to save the final recommended scheme(s).
"""


class Assistant(Agent):
    def __init__(self) -> None:
        super().__init__(instructions=SYSTEM_INSTRUCTIONS)
        self._mem = ConversationMemory()

    # ── Memory / context tools ────────────────────────────────────────────

    @function_tool(description=(
        "Save a piece of information the user shared about themselves. "
        "Call this EVERY TIME the user reveals personal details like their state, "
        "age, gender, caste, occupation, income, marital status, need, etc. "
        "This ensures you never ask the same question twice."
    ))
    async def save_user_detail(self, key: str, value: str) -> str:
        """Store a user detail in conversation memory.

        Args:
            key: The kind of info, e.g. 'state', 'gender', 'age', 'caste', 'occupation', 'need', 'marital_status'.
            value: The value the user provided, e.g. 'Gujarat', 'Male', '25', 'OBC'.
        """
        self._mem.save_detail(key, value)
        log.info("Saved user detail: %s = %s", key, value)
        return json.dumps({"saved": True, "key": key, "value": value})

    @function_tool(description=(
        "Recall everything the user has told you so far in this conversation — "
        "their profile details, previous searches, and shortlisted schemes. "
        "Call this BEFORE asking the user a question to avoid repeating questions "
        "they already answered."
    ))
    async def recall_conversation(self) -> str:
        """Return full conversation context: user profile, last search, shortlist."""
        profile = self._mem.get_all_details()
        last_search = self._mem.get_last_search()
        shortlisted = self._mem.get_shortlisted()
        search_count = self._mem.get_search_count()

        context = {
            "user_profile": profile if profile else "No details collected yet.",
            "total_searches_done": search_count,
            "last_search": {
                "query": last_search["query"],
                "filters": last_search["filters"],
                "num_results": len(last_search["results"]),
                "scheme_names": [s["name"] for s in last_search["results"]],
            } if last_search else "No searches done yet.",
            "shortlisted_schemes": [s["name"] for s in shortlisted] if shortlisted else "None yet.",
        }
        log.info("Recalled conversation context: %d profile entries, %d searches",
                 len(profile), search_count)
        return json.dumps(context, ensure_ascii=False)

    # ── Search tools ─────────────────────────────────────────────────────

    @function_tool(description=(
        "Search the Indian government schemes database. Use this whenever the "
        "user asks about government help, subsidies, scholarships, loans, or any "
        "financial/social assistance. Pass relevant keywords extracted from the "
        "user's query. Results are saved to conversation memory automatically."
    ))
    async def search_schemes(
        self,
        query: str,
        state: str = "",
        category: str = "",
        level: str = "",
    ) -> str:
        """Search government schemes by keywords.

        Args:
            query: Search keywords (e.g. 'marriage financial assistance', 'farmer loan', 'student scholarship').
            state: Optional state filter (e.g. 'Gujarat', 'Tamil Nadu', 'All' for central).
            category: Optional category filter (e.g. 'Education & Learning', 'Health & Wellness').
            level: Optional level filter — 'Central' or 'State'.
        """
        log.info("Tool call: search_schemes(query=%r, state=%r, category=%r, level=%r)",
                 query, state, category, level)

        results = scheme_lookup.search_schemes(
            query=query,
            state=state or None,
            category=category or None,
            level=level or None,
            limit=10,
        )

        if not results:
            self._mem.save_search(query, {"state": state, "category": category, "level": level}, [])
            return json.dumps({
                "found": 0,
                "message": "No schemes found matching the query. Try different keywords."
            })

        schemes_out = []
        for r in results:
            schemes_out.append({
                "name": r["scheme_name"],
                "short_title": r["short_title"],
                "description": r["description"],
                "ministry": r["ministry"],
                "level": r["level"],
                "categories": r["categories"],
                "tags": r["tags"],
                "states": r["states"],
                "apply_url": r["url"],
            })

        # Persist to conversation memory
        self._mem.save_search(
            query,
            {"state": state, "category": category, "level": level},
            schemes_out,
        )

        return json.dumps({"found": len(schemes_out), "schemes": schemes_out}, ensure_ascii=False)

    @function_tool(description=(
        "Re-run the LAST search with additional or updated filters. Use this "
        "when the user provides new info (like their state) after an initial "
        "search. Any filter left empty keeps the value from the previous search."
    ))
    async def refine_search(
        self,
        state: str = "",
        category: str = "",
        level: str = "",
    ) -> str:
        """Refine the previous search with new filters.

        Args:
            state: State filter to apply or update.
            category: Category filter to apply or update.
            level: 'Central' or 'State' filter to apply or update.
        """
        last = self._mem.get_last_search()
        if not last:
            return json.dumps({"error": "No previous search to refine. Use search_schemes first."})

        prev_filters = last["filters"]
        new_state = state or prev_filters.get("state", "")
        new_category = category or prev_filters.get("category", "")
        new_level = level or prev_filters.get("level", "")

        log.info("Refining last search %r with state=%r, category=%r, level=%r",
                 last["query"], new_state, new_category, new_level)

        return await self.search_schemes(
            query=last["query"],
            state=new_state,
            category=new_category,
            level=new_level,
        )

    @function_tool(description=(
        "Save a scheme to the shortlist when you have narrowed down to the best "
        "match(es) for the user. Pass the exact scheme name from search results."
    ))
    async def shortlist_scheme(self, scheme_name: str) -> str:
        """Add a scheme to the conversation shortlist.

        Args:
            scheme_name: The exact scheme name from search results to shortlist.
        """
        last = self._mem.get_last_search()
        if not last:
            return json.dumps({"error": "No search results to pick from."})

        for s in last["results"]:
            if s["name"].lower() == scheme_name.lower():
                slug = s.get("apply_url", "").rstrip("/").split("/")[-1]
                self._mem.shortlist_scheme(slug, s)
                log.info("Shortlisted scheme: %s", scheme_name)
                return json.dumps({"shortlisted": True, "scheme": s})

        return json.dumps({"error": f"Scheme '{scheme_name}' not found in last search results."})

    # ── Web search & scheme details ───────────────────────────────────────

    @function_tool(description=(
        "Search the web using DuckDuckGo for up-to-date information. Use this "
        "when you need the latest news, application deadlines, recent policy "
        "changes, or any info not in the local schemes database."
    ))
    async def web_search(self, query: str) -> str:
        """Search the web for current information.

        Args:
            query: The search query (e.g. 'PM-KISAN latest installment 2026', 'PMAY application deadline').
        """
        log.info("Tool call: web_search(query=%r)", query)
        try:
            with DDGS() as ddgs:
                results = list(ddgs.text(query, max_results=5))
            if not results:
                return json.dumps({"found": 0, "message": "No web results found."})
            return json.dumps({"found": len(results), "results": results}, ensure_ascii=False)
        except Exception as e:
            log.error("Web search failed: %s", e)
            return json.dumps({"error": f"Web search failed: {e}"})

    @function_tool(description=(
        "Get FULL details about a specific government scheme — including benefits, "
        "eligibility, documents required, how to apply, and more. Use this when the "
        "user asks for in-depth information about a SPECIFIC scheme (e.g. 'tell me "
        "about PM-KISAN', 'what are PMAY benefits?'). Pass the scheme name or slug. "
        "This searches the web for comprehensive, up-to-date scheme information."
    ))
    async def get_scheme_details(self, scheme_name: str) -> str:
        """Fetch full details for a specific scheme via web search.

        Args:
            scheme_name: The scheme name or slug (e.g. 'PM-KISAN', 'Pradhan Mantri Awas Yojana', 'pmay-u').
        """
        log.info("Tool call: get_scheme_details(scheme_name=%r)", scheme_name)
        try:
            # Search for the scheme on myscheme.gov.in and general web
            queries = [
                f"{scheme_name} scheme benefits eligibility myscheme.gov.in",
                f"{scheme_name} scheme how to apply documents required India",
            ]
            all_results = []
            with DDGS() as ddgs:
                for q in queries:
                    results = list(ddgs.text(q, max_results=5))
                    all_results.extend(results)

            if not all_results:
                return json.dumps({
                    "error": f"Could not find details for '{scheme_name}'. "
                             "Try searching with search_schemes first."
                })

            # Deduplicate by URL
            seen_urls = set()
            unique = []
            for r in all_results:
                url = r.get("href", "")
                if url not in seen_urls:
                    seen_urls.add(url)
                    unique.append(r)

            return json.dumps({
                "scheme": scheme_name,
                "web_results": unique[:8],
                "tip": "Summarize the key details: benefits, eligibility, documents, application process."
            }, ensure_ascii=False)
        except Exception as e:
            log.error("Scheme detail search failed: %s", e)
            return json.dumps({"error": f"Search failed: {e}"})

    # ── Info tools ────────────────────────────────────────────────────────

    @function_tool(description=(
        "Get the list of all scheme categories available in the database. "
        "Use this when you need to show the user what types of schemes exist."
    ))
    async def list_categories(self) -> str:
        """Return all available scheme categories."""
        cats = scheme_lookup.get_all_categories()
        return json.dumps({"categories": cats})

    @function_tool(description=(
        "Get database statistics: total schemes, central vs state counts. "
        "Use when the user asks how many schemes are available."
    ))
    async def get_stats(self) -> str:
        """Return database statistics."""
        stats = scheme_lookup.get_db_stats()
        return json.dumps(stats)


server = AgentServer()


@server.rtc_session(agent_name="my-agent")
async def my_agent(ctx: agents.JobContext):
    session = AgentSession(
        llm=google.beta.realtime.RealtimeModel(
            voice="Charon",
            enable_affective_dialog=True,
            realtime_input_config=types.RealtimeInputConfig(
                automatic_activity_detection=types.AutomaticActivityDetection(
                    end_of_speech_sensitivity=types.EndSensitivity.END_SENSITIVITY_HIGH,
                    silence_duration_ms=300,
                    prefix_padding_ms=100,
                ),
            ),
        )
    )

    await session.start(
        room=ctx.room,
        agent=Assistant(),
        room_options=room_io.RoomOptions(
            audio_input=room_io.AudioInputOptions(
                noise_cancellation=lambda params: noise_cancellation.BVCTelephony() if params.participant.kind == rtc.ParticipantKind.PARTICIPANT_KIND_SIP else noise_cancellation.BVC(),
            ),
        ),
    )

    await session.generate_reply(
        instructions=(
            "Greet the user warmly and tell them you can help find Indian government "
            "schemes they may be eligible for. Ask how you can help them today. "
            "Respond in the language the user speaks in."
        )
    )


if __name__ == "__main__":
    agents.cli.run_app(server)