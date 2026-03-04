"""
LiveKit Token Server + Scheme Search API
Run alongside the agent: python token_server.py
"""

import os
import json
import uuid
import logging
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

from dotenv import load_dotenv
from livekit.api import AccessToken, VideoGrants

import scheme_lookup

load_dotenv()

log = logging.getLogger("token_server")
logging.basicConfig(level=logging.INFO)

LIVEKIT_API_KEY = os.getenv("LIVEKIT_API_KEY", "")
LIVEKIT_API_SECRET = os.getenv("LIVEKIT_API_SECRET", "")
LIVEKIT_URL = os.getenv("LIVEKIT_URL", "")
PORT = int(os.getenv("TOKEN_SERVER_PORT", "8081"))


# ── Web search — same robust import as agent ────────────────────────────────

_DDGS_CLASS = None
_WEB_SEARCH_AVAILABLE = False

for _mod_name in ("duckduckgo_search", "ddgs"):
    try:
        _mod = __import__(_mod_name, fromlist=["DDGS"])
        _DDGS_CLASS = _mod.DDGS
        # Quick test
        with _DDGS_CLASS() as _ddgs:
            _test = list(_ddgs.text("test", max_results=1))
        _WEB_SEARCH_AVAILABLE = True
        log.info("Web search: using '%s' (%s)", _mod_name,
                 "working" if _test else "imported but test returned 0")
        break
    except ImportError:
        continue
    except Exception as e:
        log.warning("'%s' failed: %s", _mod_name, e)

if not _WEB_SEARCH_AVAILABLE:
    log.warning(
        "Web search NOT available. Install: pip install duckduckgo-search\n"
        "Scheme search will only use local database."
    )


def _ddgs_search(query: str, max_results: int = 5) -> list[dict]:
    """Run a DuckDuckGo web search. Returns simplified results."""
    if not _WEB_SEARCH_AVAILABLE or _DDGS_CLASS is None:
        return []
    try:
        with _DDGS_CLASS() as ddgs:
            raw = list(ddgs.text(f"{query} Indian government scheme", max_results=max_results))
        return [
            {
                "id": f"web-{i}",
                "name": r.get("title", ""),
                "description": r.get("body", ""),
                "url": r.get("href", ""),
                "category": "Web Result",
                "state": "",
                "states": [],
                "categories": [],
                "tags": [],
                "ministry": "",
                "level": "",
                "shortTitle": "",
                "schemeFor": "",
                "source": "web",
            }
            for i, r in enumerate(raw)
        ]
    except Exception as e:
        log.warning("DDGS search failed for '%s': %s", query, e)
        return []


class TokenHandler(BaseHTTPRequestHandler):
    def _set_cors_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def do_OPTIONS(self):
        self.send_response(200)
        self._set_cors_headers()
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/")

        routes = {
            "/api/token": self._handle_token,
            "/api/health": self._handle_health,
            "/api/search": self._handle_search,
            "/api/featured": self._handle_featured,
            "/api/stats": self._handle_stats,
            "/api/categories": self._handle_categories,
            "/api/states": self._handle_states,
            "/api/scheme": self._handle_scheme,
        }

        handler = routes.get(path)
        if handler:
            handler(parsed)
        else:
            self._json_response(404, {"error": "Not found"})

    def _json_response(self, status: int, data: dict | list):
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self._set_cors_headers()
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode("utf-8"))

    def _handle_token(self, parsed):
        if not LIVEKIT_API_KEY or not LIVEKIT_API_SECRET:
            return self._json_response(500, {"error": "LiveKit credentials not configured"})

        params = parse_qs(parsed.query)
        room_name = params.get("room", ["gram-sahayak"])[0]
        participant_name = params.get("name", [f"user-{uuid.uuid4().hex[:8]}"])[0]

        token = (
            AccessToken(LIVEKIT_API_KEY, LIVEKIT_API_SECRET)
            .with_identity(participant_name)
            .with_name(participant_name)
            .with_grants(
                VideoGrants(
                    room_join=True,
                    room=room_name,
                    can_publish=True,
                    can_subscribe=True,
                )
            )
        )

        self._json_response(200, {
            "token": token.to_jwt(),
            "url": LIVEKIT_URL,
            "room": room_name,
            "participant": participant_name,
        })

    def _handle_health(self, _parsed=None):
        self._json_response(200, {
            "status": "ok",
            "livekit_configured": bool(LIVEKIT_API_KEY and LIVEKIT_API_SECRET),
            "livekit_url": LIVEKIT_URL,
            "web_search_available": _WEB_SEARCH_AVAILABLE,
            "db_stats": scheme_lookup.get_db_stats(),
        })

    def _handle_search(self, parsed):
        params = parse_qs(parsed.query)
        q = params.get("q", [""])[0]
        state_filter = params.get("state", [""])[0]
        cat_filter = params.get("category", [""])[0]
        level_filter = params.get("level", [""])[0]
        limit = min(int(params.get("limit", ["50"])[0]), 200)

        results = scheme_lookup.search_schemes_full(
            q, state=state_filter or None, category=cat_filter or None,
            level=level_filter or None, limit=limit,
        )

        web_results = []
        if q and len(results) < 3:
            web_results = _ddgs_search(q, max_results=5)

        self._json_response(200, {
            "results": results,
            "webResults": web_results,
            "total": len(results),
            "query": q,
        })

    def _handle_featured(self, parsed):
        params = parse_qs(parsed.query)
        limit = min(int(params.get("limit", ["6"])[0]), 20)
        results = scheme_lookup.get_featured_schemes(limit)
        self._json_response(200, {"results": results})

    def _handle_stats(self, _parsed=None):
        self._json_response(200, scheme_lookup.get_db_stats())

    def _handle_categories(self, _parsed=None):
        self._json_response(200, {"categories": scheme_lookup.get_all_categories()})

    def _handle_states(self, _parsed=None):
        self._json_response(200, {"states": scheme_lookup.get_all_states()})

    def _handle_scheme(self, parsed):
        params = parse_qs(parsed.query)
        slug = params.get("slug", [""])[0]
        if not slug:
            return self._json_response(400, {"error": "slug parameter required"})
        conn = scheme_lookup._get_conn()
        row = conn.execute("SELECT * FROM schemes WHERE slug = ?", (slug,)).fetchone()
        if row:
            return self._json_response(200, scheme_lookup._format_scheme_full(row))
        self._json_response(404, {"error": "Scheme not found"})

    def log_message(self, format, *args):
        log.info("[%s] %s", self.client_address[0], args[0] if args else format)


def main():
    if not LIVEKIT_API_KEY or not LIVEKIT_API_SECRET:
        print("⚠️  LIVEKIT_API_KEY or LIVEKIT_API_SECRET not set")

    print("Building FTS index...")
    scheme_lookup.ensure_fts()
    stats = scheme_lookup.get_db_stats()
    print(f"✅ Database: {stats['total']} schemes ({stats['central']} central, {stats['state']} state)")
    print(f"{'✅' if _WEB_SEARCH_AVAILABLE else '❌'} Web search: {'available' if _WEB_SEARCH_AVAILABLE else 'NOT available'}")

    http = HTTPServer(("0.0.0.0", PORT), TokenHandler)
    print(f"\n🚀 Server running on http://localhost:{PORT}")
    print(f"   Health:     /api/health")
    print(f"   Token:      /api/token?room=gram-sahayak&name=user")
    print(f"   Search:     /api/search?q=education")
    print(f"   Featured:   /api/featured")
    print(f"   Scheme:     /api/scheme?slug=pm-kisan")

    try:
        http.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down...")
        http.server_close()


if __name__ == "__main__":
    main()