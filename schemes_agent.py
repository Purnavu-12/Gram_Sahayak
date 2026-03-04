"""
MyScheme.gov.in Schemes Database Sync Agent
============================================
Usage:
    python schemes_agent.py              # Run once (sync if API available)
    python schemes_agent.py --daemon     # Run continuously every hour
    python schemes_agent.py --stats      # Show database statistics
    python schemes_agent.py --test-api   # Test API connectivity
"""

import sqlite3
import requests
import json
import time
import logging
import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path
import os
from dotenv import load_dotenv

load_dotenv()

DB_PATH = Path(__file__).parent / os.getenv("DB_PATH", "schemes.db")
API_BASE = "https://api.myscheme.gov.in/search/v6/schemes"
API_KEY = os.getenv("MYSCHEME_API_KEY", "")
PAGE_SIZE = 100
SYNC_INTERVAL_SECONDS = int(os.getenv("SYNC_INTERVAL_HOURS", "1")) * 3600
REQUEST_TIMEOUT = 30
RETRY_ATTEMPTS = 3
RETRY_DELAY = 5

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger("schemes_agent")


def _build_headers() -> dict:
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "application/json",
        "Origin": "https://www.myscheme.gov.in",
        "Referer": "https://www.myscheme.gov.in/",
    }
    if API_KEY:
        headers["x-api-key"] = API_KEY
        log.info("Using API key: %s...%s", API_KEY[:4], API_KEY[-4:])
    else:
        log.info("No MYSCHEME_API_KEY set — trying without API key")
    return headers


HEADERS = _build_headers()

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS schemes (
    id                  TEXT PRIMARY KEY,
    slug                TEXT UNIQUE NOT NULL,
    scheme_name         TEXT NOT NULL,
    scheme_short_title  TEXT,
    brief_description   TEXT,
    nodal_ministry_name TEXT,
    level               TEXT,
    scheme_for          TEXT,
    scheme_close_date   TEXT,
    priority            INTEGER,
    beneficiary_states  TEXT,
    scheme_categories   TEXT,
    tags                TEXT,
    url                 TEXT,
    first_seen_at       TEXT NOT NULL,
    last_seen_at        TEXT NOT NULL,
    updated_at          TEXT NOT NULL
);
"""

CREATE_SYNC_LOG_SQL = """
CREATE TABLE IF NOT EXISTS sync_log (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    started_at      TEXT NOT NULL,
    finished_at     TEXT,
    total_from_api  INTEGER,
    added           INTEGER DEFAULT 0,
    updated         INTEGER DEFAULT 0,
    removed         INTEGER DEFAULT 0,
    status          TEXT DEFAULT 'running'
);
"""

CREATE_INDEX_SQL = [
    "CREATE INDEX IF NOT EXISTS idx_schemes_slug ON schemes(slug);",
    "CREATE INDEX IF NOT EXISTS idx_schemes_level ON schemes(level);",
    "CREATE INDEX IF NOT EXISTS idx_schemes_ministry ON schemes(nodal_ministry_name);",
    "CREATE INDEX IF NOT EXISTS idx_schemes_last_seen ON schemes(last_seen_at);",
]


def init_db(db_path: Path = DB_PATH) -> sqlite3.Connection:
    conn = sqlite3.connect(str(db_path))
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA foreign_keys=ON;")
    conn.execute(CREATE_TABLE_SQL)
    conn.execute(CREATE_SYNC_LOG_SQL)
    for idx_sql in CREATE_INDEX_SQL:
        conn.execute(idx_sql)
    conn.commit()
    return conn


def _get_existing_count() -> int:
    """Check how many schemes are already in the database."""
    if not DB_PATH.exists():
        return 0
    try:
        conn = sqlite3.connect(str(DB_PATH))
        count = conn.execute("SELECT COUNT(*) FROM schemes").fetchone()[0]
        conn.close()
        return count
    except Exception:
        return 0


API_ENDPOINTS = [
    {"url": "https://api.myscheme.gov.in/search/v6/schemes", "needs_key": True, "name": "v6 with key"},
    {"url": "https://api.myscheme.gov.in/search/v6/schemes", "needs_key": False, "name": "v6 without key"},
    {"url": "https://api.myscheme.gov.in/search/v5/schemes", "needs_key": False, "name": "v5 without key"},
    {"url": "https://api.myscheme.gov.in/search/schemes", "needs_key": False, "name": "base without key"},
]


def _test_endpoint(endpoint: dict) -> bool:
    headers = HEADERS.copy()
    if not endpoint["needs_key"]:
        headers.pop("x-api-key", None)
    try:
        resp = requests.get(
            endpoint["url"],
            headers=headers,
            params={"lang": "en", "q": "", "size": 1, "from": 0},
            timeout=15,
        )
        if resp.status_code == 200:
            data = resp.json()
            if data.get("status") == "Success" and data.get("data", {}).get("hits", {}).get("items"):
                return True
        return False
    except Exception:
        return False


def _find_working_endpoint() -> dict | None:
    """Find the first working API endpoint. Returns None if none work."""
    for ep in API_ENDPOINTS:
        if ep["needs_key"] and not API_KEY:
            continue
        log.info("Testing endpoint: %s ...", ep["name"])
        if _test_endpoint(ep):
            log.info("Using endpoint: %s", ep["name"])
            return ep
    return None


_active_endpoint: dict | None = None
_active_headers: dict | None = None


def _get_active_endpoint() -> tuple[str, dict] | None:
    """Return (url, headers) for the working endpoint, or None."""
    global _active_endpoint, _active_headers
    if _active_endpoint is None:
        _active_endpoint = _find_working_endpoint()
        if _active_endpoint is None:
            return None
        _active_headers = HEADERS.copy()
        if not _active_endpoint["needs_key"]:
            _active_headers.pop("x-api-key", None)
    return _active_endpoint["url"], _active_headers


def fetch_page(from_offset: int, size: int = PAGE_SIZE) -> dict:
    result = _get_active_endpoint()
    if result is None:
        raise RuntimeError("No working API endpoint")
    url, headers = result

    params = {"lang": "en", "q": "", "size": size, "from": from_offset}
    last_err = None
    for attempt in range(1, RETRY_ATTEMPTS + 1):
        try:
            resp = requests.get(url, headers=headers, params=params, timeout=REQUEST_TIMEOUT)
            resp.raise_for_status()
            data = resp.json()
            if data.get("status") == "Success":
                return data["data"]
            raise ValueError(f"API returned non-success: {data}")
        except Exception as e:
            last_err = e
            log.warning("Attempt %d/%d offset %d: %s", attempt, RETRY_ATTEMPTS, from_offset, e)
            if attempt < RETRY_ATTEMPTS:
                time.sleep(RETRY_DELAY)
    raise RuntimeError(f"Failed at offset {from_offset}: {last_err}")


def fetch_all_schemes() -> list[dict]:
    first_page = fetch_page(0)
    total = first_page["hits"]["page"]["total"]
    items = first_page["hits"]["items"]
    log.info("Total schemes from API: %d", total)

    offset = PAGE_SIZE
    while offset < total:
        page_data = fetch_page(offset)
        page_items = page_data["hits"]["items"]
        if not page_items:
            break
        items.extend(page_items)
        log.info("  Fetched %d / %d ...", len(items), total)
        offset += PAGE_SIZE
        time.sleep(0.3)

    log.info("Got %d schemes total.", len(items))
    return items


def parse_scheme(raw: dict) -> dict:
    f = raw.get("fields", {})
    return {
        "id": raw.get("id", ""),
        "slug": f.get("slug", ""),
        "scheme_name": f.get("schemeName", ""),
        "scheme_short_title": f.get("schemeShortTitle", ""),
        "brief_description": f.get("briefDescription", ""),
        "nodal_ministry_name": f.get("nodalMinistryName", ""),
        "level": f.get("level", ""),
        "scheme_for": f.get("schemeFor", ""),
        "scheme_close_date": f.get("schemeCloseDate"),
        "priority": f.get("priority"),
        "beneficiary_states": json.dumps(f.get("beneficiaryState", []), ensure_ascii=False),
        "scheme_categories": json.dumps(f.get("schemeCategory", []), ensure_ascii=False),
        "tags": json.dumps(f.get("tags", []), ensure_ascii=False),
        "url": f"https://www.myscheme.gov.in/schemes/{f.get('slug', '')}",
    }


def sync(conn: sqlite3.Connection) -> dict:
    now = datetime.now(timezone.utc).isoformat()
    cur = conn.cursor()
    cur.execute("INSERT INTO sync_log (started_at, status) VALUES (?, 'running')", (now,))
    sync_id = cur.lastrowid
    conn.commit()

    try:
        all_raw = fetch_all_schemes()
        all_schemes = [parse_scheme(s) for s in all_raw]
        api_slugs = {s["slug"] for s in all_schemes}

        added = updated = 0
        for s in all_schemes:
            existing = cur.execute("SELECT slug FROM schemes WHERE slug = ?", (s["slug"],)).fetchone()
            if existing:
                cur.execute(
                    """UPDATE schemes SET
                        id=?, scheme_name=?, scheme_short_title=?,
                        brief_description=?, nodal_ministry_name=?,
                        level=?, scheme_for=?, scheme_close_date=?,
                        priority=?, beneficiary_states=?,
                        scheme_categories=?, tags=?, url=?,
                        last_seen_at=?, updated_at=?
                    WHERE slug=?""",
                    (s["id"], s["scheme_name"], s["scheme_short_title"],
                     s["brief_description"], s["nodal_ministry_name"],
                     s["level"], s["scheme_for"], s["scheme_close_date"],
                     s["priority"], s["beneficiary_states"],
                     s["scheme_categories"], s["tags"], s["url"],
                     now, now, s["slug"]),
                )
                updated += 1
            else:
                cur.execute(
                    """INSERT INTO schemes (
                        id, slug, scheme_name, scheme_short_title,
                        brief_description, nodal_ministry_name, level,
                        scheme_for, scheme_close_date, priority,
                        beneficiary_states, scheme_categories, tags, url,
                        first_seen_at, last_seen_at, updated_at
                    ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                    (s["id"], s["slug"], s["scheme_name"], s["scheme_short_title"],
                     s["brief_description"], s["nodal_ministry_name"], s["level"],
                     s["scheme_for"], s["scheme_close_date"], s["priority"],
                     s["beneficiary_states"], s["scheme_categories"], s["tags"],
                     s["url"], now, now, now),
                )
                added += 1

        db_slugs = {r[0] for r in cur.execute("SELECT slug FROM schemes").fetchall()}
        removed_slugs = db_slugs - api_slugs
        removed = len(removed_slugs)
        if removed_slugs:
            ph = ",".join("?" for _ in removed_slugs)
            cur.execute(f"DELETE FROM schemes WHERE slug IN ({ph})", list(removed_slugs))

        finished = datetime.now(timezone.utc).isoformat()
        cur.execute(
            """UPDATE sync_log SET finished_at=?, total_from_api=?,
               added=?, updated=?, removed=?, status='success' WHERE id=?""",
            (finished, len(all_schemes), added, updated, removed, sync_id),
        )
        conn.commit()
        return {"total_from_api": len(all_schemes), "added": added,
                "updated": updated, "removed": removed,
                "total_in_db": cur.execute("SELECT COUNT(*) FROM schemes").fetchone()[0]}

    except Exception as exc:
        finished = datetime.now(timezone.utc).isoformat()
        cur.execute("UPDATE sync_log SET finished_at=?, status='error' WHERE id=?",
                     (finished, sync_id))
        conn.commit()
        raise


def run_once():
    """Sync if API is available. If not, report status of existing DB."""
    existing_count = _get_existing_count()

    # Check if API is reachable before doing anything
    endpoint = _find_working_endpoint()

    if endpoint is None:
        # API is not available
        log.warning("=" * 60)
        log.warning("API is unavailable (all endpoints failed).")
        if existing_count > 0:
            log.warning("Your database already has %d schemes — the agent works fine.", existing_count)
            log.warning("To update schemes, set MYSCHEME_API_KEY in .env")
        else:
            log.error("No existing database and no API access.")
            log.error("Set MYSCHEME_API_KEY in your .env file and try again.")
        log.warning("=" * 60)
        return  # Don't crash — just return

    # API is available — run sync
    global _active_endpoint, _active_headers
    _active_endpoint = endpoint
    _active_headers = HEADERS.copy()
    if not endpoint["needs_key"]:
        _active_headers.pop("x-api-key", None)

    conn = init_db()
    try:
        log.info("=" * 60)
        log.info("Starting sync ...")
        summary = sync(conn)
        log.info(
            "Sync complete!  API: %d | Added: %d | Updated: %d | Removed: %d | DB total: %d",
            summary["total_from_api"], summary["added"], summary["updated"],
            summary["removed"], summary["total_in_db"],
        )
        log.info("=" * 60)
    except Exception:
        log.exception("Sync failed!")
        if existing_count > 0:
            log.warning("Existing database with %d schemes is still usable.", existing_count)
    finally:
        conn.close()


def run_daemon():
    log.info("Daemon mode – syncing every %d seconds", SYNC_INTERVAL_SECONDS)
    while True:
        try:
            run_once()
        except KeyboardInterrupt:
            log.info("Interrupted. Exiting.")
            sys.exit(0)
        except Exception:
            log.exception("Sync cycle failed! Will retry.")

        log.info("Next sync in %d seconds ...", SYNC_INTERVAL_SECONDS)
        try:
            time.sleep(SYNC_INTERVAL_SECONDS)
        except KeyboardInterrupt:
            log.info("Interrupted. Exiting.")
            sys.exit(0)


def test_api():
    print("\n" + "=" * 50)
    print("  MyScheme API Connectivity Test")
    print("=" * 50)
    print(f"\n  API Key: {'set (' + API_KEY[:4] + '...' + API_KEY[-4:] + ')' if API_KEY else 'NOT SET'}")

    for ep in API_ENDPOINTS:
        if ep["needs_key"] and not API_KEY:
            print(f"\n  [{ep['name']}] SKIPPED (no API key)")
            continue
        print(f"\n  [{ep['name']}]")
        headers = HEADERS.copy()
        if not ep["needs_key"]:
            headers.pop("x-api-key", None)
        try:
            resp = requests.get(
                ep["url"], headers=headers,
                params={"lang": "en", "q": "", "size": 2, "from": 0},
                timeout=15,
            )
            print(f"    Status: {resp.status_code}")
            if resp.status_code == 200:
                data = resp.json()
                if data.get("status") == "Success":
                    total = data.get("data", {}).get("hits", {}).get("page", {}).get("total", 0)
                    print(f"    Schemes available: {total}")
                    print("    RESULT: WORKING")
                else:
                    print("    RESULT: API ERROR")
            else:
                print(f"    RESULT: HTTP {resp.status_code}")
        except Exception as e:
            print(f"    RESULT: ERROR - {e}")

    existing = _get_existing_count()
    print(f"\n  Local Database:")
    if existing > 0:
        print(f"    Schemes: {existing}")
        print(f"    Size: {DB_PATH.stat().st_size / 1024:.1f} KB")
        print("    STATUS: Agent can work with existing data")
    else:
        print("    STATUS: Empty or missing — need API to populate")
    print("=" * 50)


def show_stats():
    if not DB_PATH.exists():
        print("Database not found. Run sync first.")
        return
    conn = sqlite3.connect(str(DB_PATH))
    cur = conn.cursor()
    total = cur.execute("SELECT COUNT(*) FROM schemes").fetchone()[0]
    central = cur.execute("SELECT COUNT(*) FROM schemes WHERE level='Central'").fetchone()[0]
    state = cur.execute("SELECT COUNT(*) FROM schemes WHERE level='State'").fetchone()[0]
    print(f"\n  Total: {total} | Central: {central} | State: {state}")
    print(f"  File: {DB_PATH} ({DB_PATH.stat().st_size / 1024:.1f} KB)")
    conn.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="MyScheme.gov.in Sync Agent")
    parser.add_argument("--daemon", action="store_true")
    parser.add_argument("--stats", action="store_true")
    parser.add_argument("--test-api", action="store_true")
    args = parser.parse_args()

    if args.test_api:
        test_api()
    elif args.stats:
        show_stats()
    elif args.daemon:
        run_daemon()
    else:
        run_once()