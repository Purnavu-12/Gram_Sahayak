from dotenv import load_dotenv
import asyncio
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

# ── DNS retry helper ─────────────────────────────────────────────────────────
import socket
_original_getaddrinfo = socket.getaddrinfo

def _retry_getaddrinfo(*args, **kwargs):
    """Retry DNS resolution up to 3 times to handle transient failures."""
    last_err = None
    for attempt in range(3):
        try:
            return _original_getaddrinfo(*args, **kwargs)
        except socket.gaierror as e:
            last_err = e
            import time
            time.sleep(0.5 * (attempt + 1))
    raise last_err  # type: ignore

socket.getaddrinfo = _retry_getaddrinfo

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
You are Gram Sahayak, an Indian government schemes and services assistant.
You ONLY help with topics related to the Indian government — schemes,
policies, benefits, government documents, portals, and official processes.

STRICT SCOPE — CRITICAL:
- You MUST REFUSE any question that is NOT about Indian government schemes,
  government services, government documents, or government processes.
- If a user asks about entertainment, sports, coding, recipes, personal
  advice, math homework, science trivia, or anything unrelated to
  government, politely say:
  "I'm Gram Sahayak — I only help with Indian government schemes and
  services. Please ask me about government benefits, documents, or
  official processes!"
- ALLOWED topics: government schemes, Aadhaar, PAN, ration card, voter ID,
  passport, driving license, certificates, RTI, pensions, tax, government
  portals, helplines, rural welfare, agricultural subsidies, government
  housing, education scholarships, healthcare schemes, government jobs.
- NOT ALLOWED: anything outside government scope.

Be warm, empathetic, and supportive — many users may be in difficult
situations or unfamiliar with technology.

RESPONSE STYLE:
- Be concise and direct. Start speaking immediately.
- Keep answers short (1-3 sentences) and conversational, then go deeper
  only when the user asks.
- Speak at a natural, unhurried pace. Sound like a helpful friend, not a
  robot reading a list.

SCHEME DISCOVERY — DO NOT JUST LIST SCHEMES:
1. When a user describes a need, call `search_schemes`. This automatically
   fetches from the database AND pre-fetches detailed web info in parallel,
   so follow-up detail requests are instant.
2. NEVER invent scheme names — always use a tool.
3. **DO NOT dump a list of 3-5 schemes and ask "which one do you want?"**
   Instead, use the results internally and ASK THE USER QUESTIONS to figure
   out which scheme fits them best:
   - "Are you looking for this for yourself or a family member?"
   - "What state are you from?"
   - "Are you currently employed or looking for work?"
   - "How old are you?" / "What is your approximate family income?"
   - "Do you belong to SC/ST/OBC or General category?"
   Build a picture of the user, THEN recommend the 1-2 best-matching
   schemes with a short explanation of WHY it fits them.
4. Only if multiple schemes genuinely fit equally, briefly mention 2-3
   and explain the difference, then recommend which one to explore first.
5. If the search returns NO database results but includes web_details,
   use those web findings to help the user.
6. When the user asks for details on a specific scheme, call
   `get_scheme_details` — it checks DB first and enriches from the web
   in parallel, so you'll have comprehensive info instantly.

**HANDLING SLOW OPERATIONS — CRITICAL:**
Before calling `web_search`, `smart_answer`, or any tool that may take
a few seconds, FIRST say something brief like:
- "Let me look that up for you..."
- "One moment, checking that..."
- "Searching for the latest info..."
This prevents awkward silence.

GOVERNMENT SERVICES (within scope):
- Aadhaar, PAN, ration card, voter ID, passport, driving license,
  certificates — use `smart_answer` for step-by-step guidance.
- Government portals, helplines, RTI, complaints, pension, tax — use
  `smart_answer`.
- Agricultural subsidies, rural welfare — use `smart_answer`.

CONVERSATION MEMORY:
- Call `save_user_detail` EVERY TIME the user shares personal info.
- Call `recall_conversation` before asking something they may have
  already told you.
- Use `refine_search` to re-run last search with new filters.
- Use `shortlist_scheme` to save the final recommendation.

LANGUAGE RULES — CRITICAL:
- Always respond in the same language the user speaks in.
- When speaking in an Indian language (Hindi, Tamil, Telugu, Kannada,
  Malayalam, Bengali, Marathi, Gujarati, etc.), speak NATURALLY like a
  real Indian person does — mix in common English words freely.
  For example in Hindi: "Aapka application process bahut simple hai" 
  not "Aapki aavedan prakriya bahut saral hai".
  In Tamil: "Ungaloda eligibility check pannalaam" not pure literary Tamil.
- Use the everyday spoken form with English words for technical/government
  terms (scheme, application, eligibility, documents, online, portal,
  download, form, etc.) — don't translate these into formal/pure language.
- Sound like a knowledgeable friend chatting, not a textbook.
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

        # ── Run DB search AND web pre-fetch in parallel ──────────────────
        async def _db_search():
            return scheme_lookup.search_schemes(
                query=query,
                state=state or None,
                category=category or None,
                level=level or None,
                limit=10,
            )

        async def _web_prefetch():
            """Pre-fetch detailed web info so follow-up detail requests are instant."""
            try:
                web_query = f"Indian government scheme {query} eligibility benefits how to apply"
                if state:
                    web_query += f" {state}"
                return await asyncio.to_thread(self._sync_web_search, web_query, 5)
            except Exception as e:
                log.warning("Web prefetch failed: %s", e)
                return []

        results, web_details = await asyncio.gather(_db_search(), _web_prefetch())

        if not results:
            log.info("No DB results for '%s', using web fallback.", query)
            self._mem.save_search(query, {"state": state, "category": category, "level": level}, [])
            if web_details:
                return json.dumps({
                    "found": 0,
                    "db_results": 0,
                    "web_fallback": True,
                    "message": "No exact matches in our database, but I found relevant info from the web.",
                    "web_results": web_details,
                }, ensure_ascii=False)
            return json.dumps({
                "found": 0,
                "message": "No schemes found. Try different keywords or ask me to search the web."
            })

        schemes_out = []
        for r in results:
            schemes_out.append({
                "name": r["scheme_name"],
                "description": r["description"][:200],
                "ministry": r["ministry"],
                "level": r["level"],
                "apply_url": r["url"],
            })

        self._mem.save_search(
            query,
            {"state": state, "category": category, "level": level},
            schemes_out,
        )

        payload = {"found": len(schemes_out), "schemes": schemes_out}
        # Attach pre-fetched web details so the model has rich info immediately
        if web_details:
            payload["web_details"] = web_details[:4]

        return json.dumps(payload, ensure_ascii=False)

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
        "changes, or any info not in the local schemes database. "
        "IMPORTANT: Before calling this tool, always tell the user you are "
        "searching the web so they know to wait."
    ))
    async def web_search(self, query: str) -> str:
        """Search the web for current information.

        Args:
            query: The search query (e.g. 'PM-KISAN latest installment 2026', 'PMAY application deadline').
        """
        log.info("Tool call: web_search(query=%r)", query)
        try:
            results = await asyncio.to_thread(self._sync_web_search, query, 5)
            if not results:
                return json.dumps({"found": 0, "message": "No web results found."})
            return json.dumps({"found": len(results), "results": results}, ensure_ascii=False)
        except Exception as e:
            log.error("Web search failed: %s", e)
            return json.dumps({"error": f"Web search failed: {e}"})

    @staticmethod
    def _sync_web_search(query: str, max_results: int = 5) -> list:
        """Synchronous DuckDuckGo search (called from threadpool)."""
        with DDGS() as ddgs:
            return list(ddgs.text(query, max_results=max_results))

    @function_tool(description=(
        "Get FULL details about a specific government scheme — including benefits, "
        "eligibility, documents required, how to apply, and more. Use this when the "
        "user asks for in-depth information about a SPECIFIC scheme (e.g. 'tell me "
        "about PM-KISAN', 'what are PMAY benefits?'). Pass the scheme name or slug."
    ))
    async def get_scheme_details(self, scheme_name: str) -> str:
        """Fetch full details for a specific scheme. Runs DB + web in parallel for speed.

        Args:
            scheme_name: The scheme name or slug (e.g. 'PM-KISAN', 'Pradhan Mantri Awas Yojana', 'pmay-u').
        """
        log.info("Tool call: get_scheme_details(scheme_name=%r)", scheme_name)

        # ── Run local DB lookup AND web search in PARALLEL ───────────────
        async def _local_lookup():
            local = scheme_lookup.get_scheme_by_name(scheme_name)
            if not local:
                local = scheme_lookup.get_scheme_by_slug(scheme_name)
            if not local:
                # Check search history
                last = self._mem.get_last_search()
                if last:
                    for s in last["results"]:
                        if scheme_name.lower() in s.get("name", "").lower():
                            return s
            return local

        async def _web_detail():
            try:
                q1 = f"{scheme_name} scheme benefits eligibility how to apply myscheme.gov.in"
                q2 = f"{scheme_name} scheme documents required application process India"
                r1, r2 = await asyncio.gather(
                    asyncio.to_thread(self._sync_web_search, q1, 4),
                    asyncio.to_thread(self._sync_web_search, q2, 4),
                )
                all_results = (r1 or []) + (r2 or [])
                seen: set[str] = set()
                unique = []
                for r in all_results:
                    url = r.get("href", "")
                    if url not in seen:
                        seen.add(url)
                        unique.append(r)
                return unique[:6]
            except Exception as e:
                log.warning("Web detail search failed: %s", e)
                return []

        local, web_results = await asyncio.gather(_local_lookup(), _web_detail())

        if local:
            result = {
                "scheme": scheme_name,
                "source": "local_database",
                "details": local,
            }
            if web_results:
                result["web_enrichment"] = web_results
                result["tip"] = ("Use web_enrichment for additional details like latest updates, "
                                 "step-by-step application process, and documents required.")
            return json.dumps(result, ensure_ascii=False)

        if web_results:
            return json.dumps({
                "scheme": scheme_name,
                "source": "web_search",
                "web_results": web_results,
                "tip": "Summarize: benefits, eligibility, documents, how to apply."
            }, ensure_ascii=False)

        return json.dumps({
            "error": f"Could not find details for '{scheme_name}'. "
                     "Try searching with search_schemes first."
        })

    # ── General knowledge tool ─────────────────────────────────────────────

    @function_tool(description=(
        "Answer ANY general question that is NOT specifically about searching "
        "for a government scheme. Use this for: how to get Aadhaar/PAN/ration "
        "card/passport, government processes, helpline numbers, RTI, tax filing, "
        "crop prices, weather, agricultural advice, rural welfare, or ANY topic "
        "the user asks about that you don't have direct knowledge of. "
        "This searches the web and returns relevant information. "
        "IMPORTANT: Before calling this tool, always tell the user you are "
        "searching for the answer so they know to wait."
    ))
    async def smart_answer(self, question: str) -> str:
        """Search the web to answer a general question.

        Args:
            question: The user's question in natural language (e.g. 'how to apply for Aadhaar card', 'PM helpline number', 'wheat MSP price 2026').
        """
        log.info("Tool call: smart_answer(question=%r)", question)
        try:
            # Build a focused search query
            search_query = f"{question} India government official"
            results = await asyncio.to_thread(self._sync_web_search, search_query, 6)

            if not results:
                # Try a broader search
                results = await asyncio.to_thread(self._sync_web_search, question, 5)

            if not results:
                return json.dumps({
                    "found": 0,
                    "message": "I couldn't find information on that. You may want to "
                               "check the official government website or call the helpline."
                })

            return json.dumps({
                "found": len(results),
                "results": results,
                "instruction": "Summarize the most relevant information from these results "
                               "in a clear, helpful way. Give step-by-step guidance if applicable."
            }, ensure_ascii=False)
        except Exception as e:
            log.error("smart_answer failed: %s", e)
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


@server.rtc_session()
async def my_agent(ctx: agents.JobContext):
    session = AgentSession(
        llm=google.beta.realtime.RealtimeModel(
            voice="Charon",
            enable_affective_dialog=True,
            realtime_input_config=types.RealtimeInputConfig(
                automatic_activity_detection=types.AutomaticActivityDetection(
                    end_of_speech_sensitivity=types.EndSensitivity.END_SENSITIVITY_HIGH,
                    silence_duration_ms=500,
                    prefix_padding_ms=200,
                ),
            ),
            conn_options=agents.APIConnectOptions(
                max_retry=5,
                retry_interval=3.0,
                timeout=15.0,
            ),
        ),
        allow_interruptions=True,
        min_interruption_duration=1.0,
        min_interruption_words=3,
        min_endpointing_delay=0.5,
        max_endpointing_delay=3.0,
    )

    await session.start(
        room=ctx.room,
        agent=Assistant(),
        room_options=room_io.RoomOptions(
            audio_input=room_io.AudioInputOptions(
                noise_cancellation=lambda params: noise_cancellation.BVCTelephony() if params.participant.kind == rtc.ParticipantKind.PARTICIPANT_KIND_SIP else noise_cancellation.BVC(),
            ),
            audio_output=room_io.AudioOutputOptions(
                sample_rate=24000,
                num_channels=1,
                track_publish_options=rtc.TrackPublishOptions(
                    dtx=True,
                    red=True,
                ),
            ),
        ),
    )

    await session.generate_reply(
        instructions=(
            "Say a short, warm greeting in one smooth sentence, for example: "
            "'Namaste! I'm Gram Sahayak, here to help you find government schemes "
            "and services — how can I help you today?' Keep it to ONE sentence "
            "with no pauses. Respond in the language the user speaks in."
        )
    )


if __name__ == "__main__":
    agents.cli.run_app(server)