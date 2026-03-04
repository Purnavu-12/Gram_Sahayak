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
    noise_cancellation as nc,  # FIX #7: renamed to avoid shadowing the parameter
)
from google.genai import types
from ddgs import DDGS

import scheme_lookup

load_dotenv()

log = logging.getLogger("gram-agent")

# ── Ensure FTS index is ready at startup ─────────────────────────────────────
scheme_lookup.ensure_fts()

# ── DNS retry helper (non-blocking-safe) ─────────────────────────────────────
# FIX #6: reduced sleep, fewer retries, and only catches transient errors
import socket

_original_getaddrinfo = socket.getaddrinfo


def _retry_getaddrinfo(*args, **kwargs):
    last_err = None
    for attempt in range(2):  # was 3 — reduced
        try:
            return _original_getaddrinfo(*args, **kwargs)
        except socket.gaierror as e:
            last_err = e
            if attempt < 1:
                import time
                time.sleep(0.3)  # was 0.5*(attempt+1) — much shorter
    raise last_err  # type: ignore


socket.getaddrinfo = _retry_getaddrinfo


# ── Per-conversation memory (unchanged — already fast) ───────────────────────

class ConversationMemory:
    """In-memory SQLite store that lives for a single conversation."""

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
                filters   TEXT,
                results   TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE shortlisted (
                slug       TEXT PRIMARY KEY,
                scheme_json TEXT NOT NULL
            );
        """)

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


# ── System instructions (FIX #5: trimmed ~40% — same behavior, less tokens) ──

SYSTEM_INSTRUCTIONS = """\
You are Gram Sahayak, an Indian government schemes and services assistant.
ONLY help with Indian government topics — schemes, benefits, documents, portals, processes.
Refuse anything else politely: "I'm Gram Sahayak — I only help with Indian government schemes and services."

RESPONSE STYLE: Concise (1-3 sentences), warm, conversational. Respond in the user's language.
In Indian languages, mix English naturally for technical terms (scheme, eligibility, application, portal, etc.).

SCHEME DISCOVERY:
1. Use search_schemes for any scheme query — it's instant (local DB, <50ms).
2. NEVER invent scheme names — always use a tool.
3. DON'T dump lists. Ask user questions (state, age, income, category) to narrow down, then recommend 1-2 best matches explaining WHY they fit.
4. Use get_scheme_details for specific scheme deep-dives.
5. Use web_search ONLY when: user wants latest updates/deadlines, local DB returned nothing, or user explicitly asks.

CRITICAL — BEFORE any web_search call, ALWAYS speak first:
"Let me look that up for you..." THEN call the tool. Never leave silence.

MEMORY:
- save_user_detail: call EVERY TIME user shares personal info.
- recall_conversation: call before asking something they may have already answered.
- shortlist_scheme: save final recommendations.
"""


# ── Shared web search helper ─────────────────────────────────────────────────

def _ddg_search_sync(query: str, max_results: int = 5) -> list:
    """Synchronous DuckDuckGo search (runs in threadpool)."""
    with DDGS() as ddgs:
        return list(ddgs.text(query, max_results=max_results))


async def _ddg_search(query: str, max_results: int = 5, timeout: float = 5.0) -> list:
    """Async wrapper with timeout."""
    return await asyncio.wait_for(
        asyncio.to_thread(_ddg_search_sync, query, max_results),
        timeout=timeout,
    )


# ── Agent ─────────────────────────────────────────────────────────────────────

class Assistant(Agent):
    def __init__(self) -> None:
        super().__init__(instructions=SYSTEM_INSTRUCTIONS)
        self._mem = ConversationMemory()

    # ── Memory tools (FIX #9: shorter descriptions) ──────────────────────

    @function_tool(description="Save user info (state, age, gender, caste, occupation, income, need, etc).")
    async def save_user_detail(self, key: str, value: str) -> str:
        """Store a user detail in conversation memory.

        Args:
            key: Kind of info — e.g. 'state', 'gender', 'age', 'caste', 'occupation', 'need'.
            value: The value — e.g. 'Gujarat', 'Male', '25', 'OBC'.
        """
        self._mem.save_detail(key, value)
        log.info("Saved: %s = %s", key, value)
        return json.dumps({"saved": True, "key": key, "value": value})

    @function_tool(description="Recall user profile, last search, and shortlist to avoid repeating questions.")
    async def recall_conversation(self) -> str:
        """Return full conversation context."""
        profile = self._mem.get_all_details()
        last_search = self._mem.get_last_search()
        shortlisted = self._mem.get_shortlisted()
        ctx = {
            "user_profile": profile or "No details yet.",
            "searches_done": self._mem.get_search_count(),
            "last_search": {
                "query": last_search["query"],
                "filters": last_search["filters"],
                "schemes": [s["name"] for s in last_search["results"]],
            } if last_search else None,
            "shortlisted": [s["name"] for s in shortlisted] if shortlisted else None,
        }
        return json.dumps(ctx, ensure_ascii=False)

    # ── Scheme search (FIX #1: LOCAL DB ONLY — no inline web fallback) ───

    @function_tool(description="Search government schemes in the local database. Instant results (<50ms). If 0 results, tell the user and optionally use web_search.")
    async def search_schemes(
        self, query: str, state: str = "", category: str = "", level: str = "",
    ) -> str:
        """Search government schemes by keywords.

        Args:
            query: Search keywords (e.g. 'marriage financial assistance', 'farmer loan').
            state: Optional state filter (e.g. 'Gujarat', 'Tamil Nadu').
            category: Optional category (e.g. 'Education & Learning', 'Health & Wellness').
            level: Optional — 'Central' or 'State'.
        """
        log.info("search_schemes(%r, state=%r, cat=%r, lvl=%r)", query, state, category, level)

        results = scheme_lookup.search_schemes(
            query=query,
            state=state or None,
            category=category or None,
            level=level or None,
            limit=10,
        )

        schemes_out = [
            {
                "name": r["scheme_name"],
                "description": r["description"][:200],
                "ministry": r["ministry"],
                "level": r["level"],
                "apply_url": r["url"],
            }
            for r in results
        ]

        self._mem.save_search(
            query,
            {"state": state, "category": category, "level": level},
            schemes_out,
        )

        if schemes_out:
            return json.dumps(
                {"found": len(schemes_out), "schemes": schemes_out},
                ensure_ascii=False,
            )

        # FIX #1: Return immediately instead of blocking on web search.
        # The LLM can decide to call web_search (after speaking to the user).
        return json.dumps({
            "found": 0,
            "message": "No schemes found in database. Try different keywords, or "
                       "SPEAK to the user first then call web_search to look online.",
        })

    @function_tool(description="Re-run last search with new/updated filters (state, category, level).")
    async def refine_search(
        self, state: str = "", category: str = "", level: str = "",
    ) -> str:
        """Refine previous search with new filters.

        Args:
            state: State filter to apply or update.
            category: Category filter to apply or update.
            level: 'Central' or 'State'.
        """
        last = self._mem.get_last_search()
        if not last:
            return json.dumps({"error": "No previous search. Use search_schemes first."})
        prev = last["filters"]
        return await self.search_schemes(
            query=last["query"],
            state=state or prev.get("state", ""),
            category=category or prev.get("category", ""),
            level=level or prev.get("level", ""),
        )

    @function_tool(description="Save a scheme to shortlist by exact name from search results.")
    async def shortlist_scheme(self, scheme_name: str) -> str:
        """Add a scheme to the shortlist.

        Args:
            scheme_name: Exact scheme name from search results.
        """
        last = self._mem.get_last_search()
        if not last:
            return json.dumps({"error": "No search results."})
        for s in last["results"]:
            if s["name"].lower() == scheme_name.lower():
                slug = s.get("apply_url", "").rstrip("/").split("/")[-1]
                self._mem.shortlist_scheme(slug, s)
                return json.dumps({"shortlisted": True, "scheme": s})
        return json.dumps({"error": f"'{scheme_name}' not in last results."})

    # ── Detail & web tools ────────────────────────────────────────────────

    @function_tool(description="Get full details for a specific scheme. Checks local DB first (instant), falls back to web. SPEAK FIRST if scheme might not be in DB.")
    async def get_scheme_details(self, scheme_name: str) -> str:
        """Fetch full details for a specific scheme.

        Args:
            scheme_name: Scheme name or slug (e.g. 'PM-KISAN', 'pmay-u').
        """
        log.info("get_scheme_details(%r)", scheme_name)

        # Try local DB first (fast path)
        local = scheme_lookup.get_scheme_by_name(scheme_name)
        if not local:
            local = scheme_lookup.get_scheme_by_slug(scheme_name)
        if not local:
            last = self._mem.get_last_search()
            if last:
                for s in last["results"]:
                    if scheme_name.lower() in s.get("name", "").lower():
                        local = s
                        break

        if local:
            return json.dumps(
                {"scheme": scheme_name, "source": "database", "details": local},
                ensure_ascii=False,
            )

        # Web fallback (slow path)
        log.info("'%s' not in DB, searching web.", scheme_name)
        try:
            q = f"{scheme_name} scheme benefits eligibility how to apply myscheme.gov.in"
            results = await _ddg_search(q, max_results=5, timeout=5.0)
            if results:
                return json.dumps(
                    {"scheme": scheme_name, "source": "web", "results": results},
                    ensure_ascii=False,
                )
        except (asyncio.TimeoutError, Exception) as e:
            log.warning("Web detail search failed: %s", e)

        return json.dumps(
            {"error": f"Could not find '{scheme_name}'. Try search_schemes first."}
        )

    # FIX #2: Merged web_search + smart_answer into one tool
    @function_tool(description="Search the web for up-to-date info (deadlines, news, processes, helplines, documents, etc). ALWAYS speak to the user BEFORE calling this — it takes a few seconds.")
    async def web_search(self, query: str) -> str:
        """Search the web for current information.

        Args:
            query: Search query (e.g. 'PM-KISAN latest installment 2025', 'how to apply for Aadhaar').
        """
        log.info("web_search(%r)", query)
        try:
            results = await _ddg_search(query, max_results=5, timeout=5.0)  # FIX #8: 5s not 8s
            if not results:
                return json.dumps({"found": 0, "message": "No web results found."})
            return json.dumps(
                {"found": len(results), "results": results},
                ensure_ascii=False,
            )
        except asyncio.TimeoutError:
            return json.dumps({"error": "Search timed out. Try a simpler query."})
        except Exception as e:
            log.error("Web search failed: %s", e)
            return json.dumps({"error": f"Search failed: {e}"})

    # ── Info tools ────────────────────────────────────────────────────────

    @function_tool(description="List all scheme categories in the database.")
    async def list_categories(self) -> str:
        """Return all available scheme categories."""
        return json.dumps({"categories": scheme_lookup.get_all_categories()})

    @function_tool(description="Get database stats (total schemes, central vs state).")
    async def get_stats(self) -> str:
        """Return database statistics."""
        return json.dumps(scheme_lookup.get_db_stats())


# ── Server wiring ─────────────────────────────────────────────────────────────

server = AgentServer()


@server.rtc_session()
async def my_agent(ctx: agents.JobContext):
    assistant = Assistant()

    session = AgentSession(
        llm=google.beta.realtime.RealtimeModel(
            voice="Charon",
            enable_affective_dialog=True,
            realtime_input_config=types.RealtimeInputConfig(
                automatic_activity_detection=types.AutomaticActivityDetection(
                    end_of_speech_sensitivity=types.EndSensitivity.END_SENSITIVITY_HIGH,
                    silence_duration_ms=300,   # FIX #4: was 500 → faster turn-taking
                    prefix_padding_ms=100,     # FIX #4: was 200 → less buffering
                ),
            ),
            conn_options=agents.APIConnectOptions(
                max_retry=3,          # FIX #8: was 5
                retry_interval=2.0,   # FIX #8: was 3.0
                timeout=10.0,         # FIX #8: was 15.0
            ),
        ),
        allow_interruptions=True,
        min_interruption_duration=0.5,   # was 1.0 → user can interrupt faster
        min_interruption_words=2,        # was 3
        min_endpointing_delay=0.3,       # was 0.5
        max_endpointing_delay=1.5,       # FIX #3: was 3.0 → biggest latency win
    )

    # FIX #7: use renamed import `nc` so the lambda doesn't shadow the module
    await session.start(
        room=ctx.room,
        agent=assistant,
        room_options=room_io.RoomOptions(
            audio_input=room_io.AudioInputOptions(
                noise_cancellation=lambda params: (
                    nc.BVCTelephony()
                    if params.participant.kind == rtc.ParticipantKind.PARTICIPANT_KIND_SIP
                    else nc.BVC()
                ),
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
            "Greet warmly in ONE short sentence, e.g.: "
            "'Namaste! I'm Gram Sahayak — how can I help you with government schemes today?' "
            "Match the user's language."
        )
    )

    # FIX #10: clean up memory when the room disconnects
    @ctx.room.on("disconnected")
    def _on_disconnect():
        assistant._mem.close()
        log.info("Session memory cleaned up.")


if __name__ == "__main__":
    agents.cli.run_app(server)