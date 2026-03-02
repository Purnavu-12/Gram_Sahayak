"""
LiveKit Token Server + Scheme Search API
Generates JWT tokens and serves scheme search endpoints.
In production, also serves the built React frontend from dist/.
Run alongside the LiveKit agent: python token_server.py
"""

import os
import json
import uuid
import logging
import mimetypes
from http.server import HTTPServer, BaseHTTPRequestHandler
from socketserver import ThreadingMixIn
from urllib.parse import urlparse, parse_qs
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from dotenv import load_dotenv
from livekit.api import AccessToken, VideoGrants

import scheme_lookup

load_dotenv()

log = logging.getLogger("token_server")

LIVEKIT_API_KEY = os.getenv("LIVEKIT_API_KEY", "")
LIVEKIT_API_SECRET = os.getenv("LIVEKIT_API_SECRET", "")
LIVEKIT_URL = os.getenv("LIVEKIT_URL", "")
PORT = int(os.getenv("PORT", os.getenv("TOKEN_SERVER_PORT", "8081")))

# Serve frontend static files from dist/ if it exists (production mode)
DIST_DIR = Path(__file__).parent / "dist"
SERVE_STATIC = DIST_DIR.is_dir()

# Thread pool for DDGS web searches (keeps the HTTP server responsive)
_executor = ThreadPoolExecutor(max_workers=4)


def _ddgs_search(query: str, max_results: int = 5) -> list[dict]:
    """Run a DuckDuckGo web search (blocking). Returns simplified results."""
    try:
        from duckduckgo_search import DDGS
        with DDGS() as ddgs:
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
        log.warning("DDGS search failed: %s", e)
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
        elif SERVE_STATIC:
            self._serve_static(path)
        else:
            self._json_response(404, {"error": "Not found"})

    def _json_response(self, status: int, data: dict | list):
        """Send a JSON response with CORS headers."""
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
        })

    # ── Scheme search ────────────────────────────────────────────────
    def _handle_search(self, parsed):
        params = parse_qs(parsed.query)
        q = params.get("q", [""])[0]
        state_filter = params.get("state", [""])[0]
        cat_filter = params.get("category", [""])[0]
        level_filter = params.get("level", [""])[0]
        limit = min(int(params.get("limit", ["50"])[0]), 200)

        # 1. Search local DB (FTS)
        results = scheme_lookup.search_schemes_full(
            q, state=state_filter or None, category=cat_filter or None,
            level=level_filter or None, limit=limit,
        )

        # 2. If few DB results AND a query was given, supplement with DDGS
        web_results = []
        if q and len(results) < 3:
            try:
                web_results = _ddgs_search(q, max_results=5)
            except Exception:
                pass

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
        stats = scheme_lookup.get_db_stats()
        self._json_response(200, stats)

    def _handle_categories(self, _parsed=None):
        cats = scheme_lookup.get_all_categories()
        self._json_response(200, {"categories": cats})

    def _handle_states(self, _parsed=None):
        states = scheme_lookup.get_all_states()
        self._json_response(200, {"states": states})

    def _handle_scheme(self, parsed):
        """Get a single scheme by slug: /api/scheme?slug=xxx"""
        params = parse_qs(parsed.query)
        slug = params.get("slug", [""])[0]
        if not slug:
            return self._json_response(400, {"error": "slug parameter required"})
        result = scheme_lookup.get_scheme_by_slug(slug)
        if result:
            # get_scheme_by_slug uses _format_scheme (agent-style), remap to full
            # Use the full formatter via a direct query
            conn = scheme_lookup._get_conn()
            row = conn.execute("SELECT * FROM schemes WHERE slug = ?", (slug,)).fetchone()
            if row:
                full = scheme_lookup._format_scheme_full(row)
                return self._json_response(200, full)
        self._json_response(404, {"error": "Scheme not found"})

    def log_message(self, format, *args):
        print(f"[TokenServer] {args[0]}")

    def _serve_static(self, path: str):
        """Serve files from dist/ — fallback to index.html for SPA routing."""
        # Map / to /index.html
        file_path = DIST_DIR / (path.lstrip("/") or "index.html")

        # Security: prevent path traversal
        try:
            file_path = file_path.resolve()
            if not str(file_path).startswith(str(DIST_DIR.resolve())):
                return self._json_response(403, {"error": "Forbidden"})
        except Exception:
            return self._json_response(400, {"error": "Bad request"})

        # If file doesn't exist, serve index.html (SPA client-side routing)
        if not file_path.is_file():
            file_path = DIST_DIR / "index.html"

        if not file_path.is_file():
            return self._json_response(404, {"error": "Not found"})

        mime_type, _ = mimetypes.guess_type(str(file_path))
        if mime_type is None:
            mime_type = "application/octet-stream"

        self.send_response(200)
        self.send_header("Content-Type", mime_type)
        self._set_cors_headers()
        # Cache static assets (they have content hashes in filenames)
        if "/assets/" in path:
            self.send_header("Cache-Control", "public, max-age=31536000, immutable")
        self.end_headers()
        self.wfile.write(file_path.read_bytes())


class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    """Handle each request in a new thread."""
    daemon_threads = True


def main():
    if not LIVEKIT_API_KEY or not LIVEKIT_API_SECRET:
        print("WARNING: LIVEKIT_API_KEY or LIVEKIT_API_SECRET not set in .env")
        print("Token generation will fail until credentials are configured.")

    # Build FTS index on startup so first search is fast
    print("Building FTS index...")
    scheme_lookup.ensure_fts()
    stats = scheme_lookup.get_db_stats()
    print(f"Database ready: {stats['total']} schemes ({stats['central']} central, {stats['state']} state)")

    server = ThreadedHTTPServer(("0.0.0.0", PORT), TokenHandler)
    print(f"\nToken + Search API running on http://0.0.0.0:{PORT}")
    if SERVE_STATIC:
        print(f"  Serving frontend from: {DIST_DIR}")
    else:
        print("  Static file serving: OFF (no dist/ folder — use Vite dev server)")
    print(f"  Health:     http://localhost:{PORT}/api/health")
    print(f"  Token:      http://localhost:{PORT}/api/token?room=gram-sahayak&name=user")
    print(f"  Search:     http://localhost:{PORT}/api/search?q=education")
    print(f"  Featured:   http://localhost:{PORT}/api/featured")
    print(f"  Stats:      http://localhost:{PORT}/api/stats")
    print(f"  Categories: http://localhost:{PORT}/api/categories")
    print(f"  States:     http://localhost:{PORT}/api/states")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down token server...")
        server.server_close()


if __name__ == "__main__":
    main()
