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
    noise_cancellation as nc,
)
from google.genai import types

import scheme_lookup

load_dotenv()

log = logging.getLogger("gram-agent")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(name)s %(levelname)s: %(message)s",
)

scheme_lookup.ensure_fts()

# ── DNS retry ────────────────────────────────────────────────────────────────
import socket
_original_getaddrinfo = socket.getaddrinfo

def _retry_getaddrinfo(*args, **kwargs):
    last_err = None
    for attempt in range(2):
        try:
            return _original_getaddrinfo(*args, **kwargs)
        except socket.gaierror as e:
            last_err = e
            if attempt < 1:
                import time; time.sleep(0.3)
    raise last_err

socket.getaddrinfo = _retry_getaddrinfo


# ── Web search — robust import with fallback ─────────────────────────────────
# FIX: Try both package names, and verify it actually works at import time

_DDGS_CLASS = None
_WEB_SEARCH_AVAILABLE = False

def _init_web_search():
    """Try to import and test DuckDuckGo search at startup."""
    global _DDGS_CLASS, _WEB_SEARCH_AVAILABLE

    # Try the newer package first, then the older one
    for module_name in ("duckduckgo_search", "ddgs"):
        try:
            mod = __import__(module_name, fromlist=["DDGS"])
            _DDGS_CLASS = mod.DDGS
            log.info("Web search: using '%s' package", module_name)

            # Actually test it works (catches import-but-broken scenarios)
            with _DDGS_CLASS() as ddgs:
                test = list(ddgs.text("test", max_results=1))
                if test:
                    _WEB_SEARCH_AVAILABLE = True
                    log.info("✅ Web search working (test query returned %d results)", len(test))
                    return
                else:
                    log.warning("Web search imported from '%s' but test returned 0 results", module_name)
        except ImportError:
            log.info("Package '%s' not installed, trying next...", module_name)
        except Exception as e:
            log.warning("Package '%s' import/test failed: %s", module_name, e)

    log.error(
        "❌ Web search NOT available. Install one of:\n"
        "   pip install duckduckgo-search\n"
        "   pip install ddgs"
    )

# Run at import time so we know immediately
try:
    _init_web_search()
except Exception as e:
    log.error("Web search init failed: %s", e)


def _ddg_sync(query: str, max_results: int = 5) -> list:
    """Synchronous DuckDuckGo search with error handling."""
    if not _WEB_SEARCH_AVAILABLE or _DDGS_CLASS is None:
        log.warning("Web search called but not available")
        return []

    try:
        with _DDGS_CLASS() as ddgs:
            results = list(ddgs.text(query, max_results=max_results))
            log.info("DDGS returned %d results for '%s'", len(results), query)
            return results
    except Exception as e:
        log.error("DDGS search error for '%s': %s", query, e)
        return []


async def _ddg(query: str, max_results: int = 5, timeout: float = 5.0) -> list:
    """Async wrapper with timeout."""
    try:
        return await asyncio.wait_for(
            asyncio.to_thread(_ddg_sync, query, max_results),
            timeout=timeout,
        )
    except asyncio.TimeoutError:
        log.warning("Web search timed out for '%s'", query)
        return []
    except Exception as e:
        log.error("Web search async error: %s", e)
        return []


# ── Conversation Memory ─────────────────────────────────────────────────────

class ConversationMemory:
    def __init__(self):
        self._conn = sqlite3.connect(":memory:")
        self._conn.row_factory = sqlite3.Row
        self._conn.executescript("""
            CREATE TABLE user_profile (key TEXT PRIMARY KEY, value TEXT NOT NULL);
            CREATE TABLE search_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                query TEXT NOT NULL, filters TEXT, results TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE shortlisted (slug TEXT PRIMARY KEY, scheme_json TEXT NOT NULL);
        """)

    def save_detail(self, key: str, value: str):
        self._conn.execute(
            "INSERT OR REPLACE INTO user_profile VALUES (?, ?)",
            (key.lower().strip(), value.strip()),
        )
        self._conn.commit()

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
        return {"query": row["query"], "filters": json.loads(row["filters"]),
                "results": json.loads(row["results"])}

    def get_search_count(self) -> int:
        return self._conn.execute("SELECT COUNT(*) FROM search_history").fetchone()[0]

    def shortlist_scheme(self, slug: str, scheme_json: dict):
        self._conn.execute(
            "INSERT OR REPLACE INTO shortlisted VALUES (?, ?)",
            (slug, json.dumps(scheme_json, ensure_ascii=False)),
        )
        self._conn.commit()

    def get_shortlisted(self) -> list[dict]:
        rows = self._conn.execute("SELECT scheme_json FROM shortlisted").fetchall()
        return [json.loads(r["scheme_json"]) for r in rows]

    def close(self):
        self._conn.close()


# ── System prompt ────────────────────────────────────────────────────────────

SYSTEM_INSTRUCTIONS = """\
You are Gram Sahayak, an Indian government schemes and services assistant.
ONLY help with Indian government topics — schemes, benefits, documents, portals, processes.
Refuse anything else: "I'm Gram Sahayak — I only help with Indian government schemes and services."

STYLE: Concise (1-3 sentences), warm, conversational. Match the user's language.
In Indian languages, mix English naturally (scheme, eligibility, application, portal, etc.).

SCHEME DISCOVERY:
1. Use search_schemes for any scheme query — it's instant (local DB).
2. NEVER invent scheme names — always use a tool.
3. Don't dump lists. Ask questions (state, age, income, category) to narrow down,
   then recommend 1-2 best matches with WHY they fit.
4. Use get_scheme_details for deep-dives on a specific scheme.
5. Use web_search ONLY when: local DB returned nothing, user wants latest updates,
   or user explicitly asks. ALWAYS speak BEFORE calling web_search.

MEMORY: Call save_user_detail when user shares personal info.
Call recall_conversation before asking something they may have answered.
"""


# ── Agent ────────────────────────────────────────────────────────────────────

class Assistant(Agent):
    def __init__(self):
        super().__init__(instructions=SYSTEM_INSTRUCTIONS)
        self._mem = ConversationMemory()

    @function_tool(description="Save user info (state, age, gender, caste, occupation, income, need).")
    async def save_user_detail(self, key: str, value: str) -> str:
        """Args:
            key: Info type like state, gender, age, caste, occupation.
            value: The value like Gujarat, Male, 25.
        """
        try:
            self._mem.save_detail(key, value)
            log.info("Saved: %s = %s", key, value)
            return json.dumps({"saved": True, "key": key, "value": value})
        except Exception as e:
            log.error("save_user_detail error: %s", e)
            return json.dumps({"error": str(e)})

    @function_tool(description="Recall user profile and search history.")
    async def recall_conversation(self) -> str:
        """Return conversation context."""
        try:
            profile = self._mem.get_all_details()
            last = self._mem.get_last_search()
            short = self._mem.get_shortlisted()
            return json.dumps({
                "profile": profile or "None yet.",
                "searches": self._mem.get_search_count(),
                "last_search": {"query": last["query"],
                                "schemes": [s["name"] for s in last["results"]]}
                if last else None,
                "shortlisted": [s["name"] for s in short] if short else None,
            }, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"error": str(e)})

    @function_tool(description="Search government schemes in local database. Instant results.")
    async def search_schemes(
        self, query: str, state: str = "", category: str = "", level: str = "",
    ) -> str:
        """Args:
            query: Keywords like farmer loan, student scholarship.
            state: Optional state like Gujarat.
            category: Optional category like Education.
            level: Optional Central or State.
        """
        log.info("TOOL: search_schemes(%r, state=%r, cat=%r, lvl=%r)",
                 query, state, category, level)
        try:
            results = scheme_lookup.search_schemes(
                query=query, state=state or None,
                category=category or None, level=level or None, limit=10,
            )
            out = [{"name": r["scheme_name"], "description": r["description"][:200],
                     "ministry": r["ministry"], "level": r["level"],
                     "apply_url": r.get("url", "")} for r in results]

            self._mem.save_search(query,
                                  {"state": state, "category": category, "level": level}, out)
            log.info("search_schemes: %d results for '%s'", len(out), query)

            if out:
                return json.dumps({"found": len(out), "schemes": out}, ensure_ascii=False)
            return json.dumps({"found": 0,
                               "message": "No results. Try broader keywords or call web_search."})
        except Exception as e:
            log.error("search_schemes FAILED: %s", e, exc_info=True)
            return json.dumps({"error": str(e)})

    @function_tool(description="Get full details for a specific scheme. Checks DB first, then web.")
    async def get_scheme_details(self, scheme_name: str) -> str:
        """Args:
            scheme_name: Scheme name or slug like PM-KISAN.
        """
        log.info("TOOL: get_scheme_details(%r)", scheme_name)
        try:
            local = scheme_lookup.get_scheme_by_name(scheme_name)
            if not local:
                local = scheme_lookup.get_scheme_by_slug(scheme_name)
            if not local:
                last = self._mem.get_last_search()
                if last:
                    for s in last["results"]:
                        if scheme_name.lower() in s.get("name", "").lower():
                            local = s; break
            if local:
                return json.dumps({"source": "database", "details": local}, ensure_ascii=False)

            # Web fallback
            if _WEB_SEARCH_AVAILABLE:
                results = await _ddg(
                    f"{scheme_name} scheme eligibility benefits site:myscheme.gov.in",
                    max_results=5, timeout=5.0,
                )
                if results:
                    return json.dumps({"source": "web", "results": results}, ensure_ascii=False)

            return json.dumps({"error": f"'{scheme_name}' not found. Try search_schemes first."})
        except Exception as e:
            log.error("get_scheme_details FAILED: %s", e, exc_info=True)
            return json.dumps({"error": str(e)})

    @function_tool(description="Search the web for latest info. ALWAYS speak before calling this.")
    async def web_search(self, query: str) -> str:
        """Args:
            query: Search query like PM-KISAN latest installment.
        """
        log.info("TOOL: web_search(%r)", query)

        if not _WEB_SEARCH_AVAILABLE:
            log.warning("web_search called but DDGS not available")
            return json.dumps({
                "error": "Web search is currently unavailable. "
                         "I can only search the local database.",
                "suggestion": "Try search_schemes with different keywords.",
            })

        results = await _ddg(query, max_results=5, timeout=5.0)
        if results:
            return json.dumps({"found": len(results), "results": results}, ensure_ascii=False)
        return json.dumps({
            "found": 0,
            "message": "No web results. DuckDuckGo may be rate-limiting. "
                       "Try again in a moment or rephrase the query.",
        })

    @function_tool(description="Re-run last search with new filters.")
    async def refine_search(self, state: str = "", category: str = "", level: str = "") -> str:
        """Args:
            state: State filter. category: Category filter. level: Central or State.
        """
        try:
            last = self._mem.get_last_search()
            if not last:
                return json.dumps({"error": "No previous search."})
            prev = last["filters"]
            return await self.search_schemes(
                query=last["query"],
                state=state or prev.get("state", ""),
                category=category or prev.get("category", ""),
                level=level or prev.get("level", ""),
            )
        except Exception as e:
            return json.dumps({"error": str(e)})


# ── Server ───────────────────────────────────────────────────────────────────

server = AgentServer()


@server.rtc_session()
async def my_agent(ctx: agents.JobContext):
    assistant = Assistant()

    realtime_model = google.beta.realtime.RealtimeModel(
        model="gemini-2.5-flash-native-audio-latest",
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

    session = AgentSession(
        llm=realtime_model,
        allow_interruptions=True,
        min_interruption_duration=0.5,
        min_interruption_words=2,
        min_endpointing_delay=0.3,
        max_endpointing_delay=1.5,
    )

    try:
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
                    track_publish_options=rtc.TrackPublishOptions(dtx=True, red=True),
                ),
            ),
        )
        log.info("✅ Session started with gemini-2.5-flash-native-audio-latest")
    except Exception as e:
        log.error("❌ Session start failed: %s", e, exc_info=True)
        if "1008" in str(e):
            log.info("Retrying without affective dialog...")
            try:
                realtime_model = google.beta.realtime.RealtimeModel(
                    model="gemini-2.5-flash-native-audio-latest",
                    voice="Charon",
                    enable_affective_dialog=False,
                )
                session = AgentSession(
                    llm=realtime_model,
                    allow_interruptions=True,
                    min_interruption_duration=0.5,
                    min_interruption_words=2,
                    min_endpointing_delay=0.3,
                    max_endpointing_delay=1.5,
                )
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
                            track_publish_options=rtc.TrackPublishOptions(dtx=True, red=True),
                        ),
                    ),
                )
                log.info("✅ Session started (affective dialog OFF)")
            except Exception as e2:
                log.error("❌ Fallback failed: %s", e2, exc_info=True)
                assistant._mem.close()
                return
        else:
            assistant._mem.close()
            return

    await session.generate_reply(
        instructions=(
            "Greet warmly in ONE short sentence, e.g.: "
            "'Namaste! I'm Gram Sahayak — how can I help you today?' "
            "Match the user's language."
        )
    )

    @ctx.room.on("disconnected")
    def _cleanup():
        assistant._mem.close()
        log.info("Session memory cleaned up.")


if __name__ == "__main__":
    agents.cli.run_app(server)