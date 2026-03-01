"""
MyScheme.gov.in Schemes Database Sync Agent
============================================
Scrapes all government schemes from myscheme.gov.in API and stores them
in a local SQLite database. Runs every hour, adding new schemes, updating
existing ones, and removing discontinued ones.

Usage:
    python schemes_agent.py              # Run once (initial sync)
    python schemes_agent.py --daemon     # Run continuously every hour
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

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
DB_PATH = Path(__file__).parent / "schemes.db"
API_BASE = "https://api.myscheme.gov.in/search/v6/schemes"
API_KEY = "tYTy5eEhlu9rFjyxuCr7ra7ACp4dv1RH8gWuHTDc"
PAGE_SIZE = 100                # max items per API call
SYNC_INTERVAL_SECONDS = 3600   # 1 hour
REQUEST_TIMEOUT = 30           # seconds per HTTP request
RETRY_ATTEMPTS = 3
RETRY_DELAY = 5                # seconds between retries

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "application/json",
    "x-api-key": API_KEY,
    "Origin": "https://www.myscheme.gov.in",
    "Referer": "https://www.myscheme.gov.in/",
}

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger("schemes_agent")

# ---------------------------------------------------------------------------
# Database setup
# ---------------------------------------------------------------------------

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS schemes (
    id                  TEXT PRIMARY KEY,       -- elastic id from API
    slug                TEXT UNIQUE NOT NULL,   -- URL-friendly identifier
    scheme_name         TEXT NOT NULL,
    scheme_short_title  TEXT,
    brief_description   TEXT,
    nodal_ministry_name TEXT,
    level               TEXT,                   -- Central / State
    scheme_for          TEXT,                   -- Individual / Organization etc.
    scheme_close_date   TEXT,
    priority            INTEGER,
    beneficiary_states  TEXT,                   -- JSON array
    scheme_categories   TEXT,                   -- JSON array
    tags                TEXT,                   -- JSON array
    url                 TEXT,                   -- full URL on myscheme.gov.in
    first_seen_at       TEXT NOT NULL,          -- ISO timestamp
    last_seen_at        TEXT NOT NULL,          -- ISO timestamp (updated each sync)
    updated_at          TEXT NOT NULL           -- ISO timestamp
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
    status          TEXT DEFAULT 'running'      -- running / success / error
);
"""

CREATE_INDEX_SQL = [
    "CREATE INDEX IF NOT EXISTS idx_schemes_slug ON schemes(slug);",
    "CREATE INDEX IF NOT EXISTS idx_schemes_level ON schemes(level);",
    "CREATE INDEX IF NOT EXISTS idx_schemes_ministry ON schemes(nodal_ministry_name);",
    "CREATE INDEX IF NOT EXISTS idx_schemes_last_seen ON schemes(last_seen_at);",
]


def init_db(db_path: Path = DB_PATH) -> sqlite3.Connection:
    """Create/open the SQLite database and ensure tables exist."""
    conn = sqlite3.connect(str(db_path))
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA foreign_keys=ON;")
    conn.execute(CREATE_TABLE_SQL)
    conn.execute(CREATE_SYNC_LOG_SQL)
    for idx_sql in CREATE_INDEX_SQL:
        conn.execute(idx_sql)
    conn.commit()
    return conn


# ---------------------------------------------------------------------------
# API helpers
# ---------------------------------------------------------------------------

def fetch_page(from_offset: int, size: int = PAGE_SIZE) -> dict:
    """Fetch a single page of schemes from the API with retry logic."""
    params = {"lang": "en", "q": "", "size": size, "from": from_offset}
    last_err = None
    for attempt in range(1, RETRY_ATTEMPTS + 1):
        try:
            resp = requests.get(
                API_BASE, headers=HEADERS, params=params, timeout=REQUEST_TIMEOUT
            )
            resp.raise_for_status()
            data = resp.json()
            if data.get("status") == "Success":
                return data["data"]
            else:
                raise ValueError(f"API returned non-success: {data}")
        except Exception as e:
            last_err = e
            log.warning("Attempt %d/%d failed for offset %d: %s", attempt, RETRY_ATTEMPTS, from_offset, e)
            if attempt < RETRY_ATTEMPTS:
                time.sleep(RETRY_DELAY)
    raise RuntimeError(f"Failed to fetch page at offset {from_offset} after {RETRY_ATTEMPTS} attempts: {last_err}")


def fetch_all_schemes() -> list[dict]:
    """Fetch every scheme from the API using pagination."""
    # First call to determine total
    first_page = fetch_page(0)
    total = first_page["hits"]["page"]["total"]
    items = first_page["hits"]["items"]
    log.info("Total schemes reported by API: %d", total)

    offset = PAGE_SIZE
    while offset < total:
        page_data = fetch_page(offset)
        page_items = page_data["hits"]["items"]
        if not page_items:
            break
        items.extend(page_items)
        fetched_so_far = len(items)
        log.info("  Fetched %d / %d schemes ...", fetched_so_far, total)
        offset += PAGE_SIZE
        # Be polite – small delay between pages
        time.sleep(0.3)

    log.info("Finished fetching. Got %d schemes total.", len(items))
    return items


# ---------------------------------------------------------------------------
# Sync logic
# ---------------------------------------------------------------------------

def parse_scheme(raw: dict) -> dict:
    """Convert an API item into a flat dict for DB insertion."""
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
    """
    Run a full sync:
      1. Fetch all schemes from the API.
      2. Upsert each scheme (insert new, update existing).
      3. Delete schemes no longer present on the website.
    Returns a summary dict.
    """
    now = datetime.now(timezone.utc).isoformat()
    cur = conn.cursor()

    # Create sync log entry
    cur.execute(
        "INSERT INTO sync_log (started_at, status) VALUES (?, 'running')",
        (now,),
    )
    sync_id = cur.lastrowid
    conn.commit()

    try:
        # ---- Step 1: Fetch all schemes ----
        all_raw = fetch_all_schemes()
        all_schemes = [parse_scheme(s) for s in all_raw]
        api_slugs = {s["slug"] for s in all_schemes}

        # ---- Step 2: Upsert ----
        added = 0
        updated = 0
        for s in all_schemes:
            existing = cur.execute(
                "SELECT slug FROM schemes WHERE slug = ?", (s["slug"],)
            ).fetchone()

            if existing:
                # Update existing scheme
                cur.execute(
                    """UPDATE schemes SET
                        id = ?, scheme_name = ?, scheme_short_title = ?,
                        brief_description = ?, nodal_ministry_name = ?,
                        level = ?, scheme_for = ?, scheme_close_date = ?,
                        priority = ?, beneficiary_states = ?,
                        scheme_categories = ?, tags = ?, url = ?,
                        last_seen_at = ?, updated_at = ?
                    WHERE slug = ?""",
                    (
                        s["id"], s["scheme_name"], s["scheme_short_title"],
                        s["brief_description"], s["nodal_ministry_name"],
                        s["level"], s["scheme_for"], s["scheme_close_date"],
                        s["priority"], s["beneficiary_states"],
                        s["scheme_categories"], s["tags"], s["url"],
                        now, now, s["slug"],
                    ),
                )
                updated += 1
            else:
                # Insert new scheme
                cur.execute(
                    """INSERT INTO schemes (
                        id, slug, scheme_name, scheme_short_title,
                        brief_description, nodal_ministry_name, level,
                        scheme_for, scheme_close_date, priority,
                        beneficiary_states, scheme_categories, tags, url,
                        first_seen_at, last_seen_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        s["id"], s["slug"], s["scheme_name"], s["scheme_short_title"],
                        s["brief_description"], s["nodal_ministry_name"], s["level"],
                        s["scheme_for"], s["scheme_close_date"], s["priority"],
                        s["beneficiary_states"], s["scheme_categories"], s["tags"],
                        s["url"], now, now, now,
                    ),
                )
                added += 1

        # ---- Step 3: Remove schemes no longer on the website ----
        db_slugs_rows = cur.execute("SELECT slug FROM schemes").fetchall()
        db_slugs = {row[0] for row in db_slugs_rows}
        removed_slugs = db_slugs - api_slugs
        removed = len(removed_slugs)
        if removed_slugs:
            placeholders = ",".join("?" for _ in removed_slugs)
            cur.execute(
                f"DELETE FROM schemes WHERE slug IN ({placeholders})",
                list(removed_slugs),
            )
            log.info("Removed %d discontinued schemes: %s", removed,
                     ", ".join(sorted(removed_slugs)[:10]) + ("..." if removed > 10 else ""))

        # ---- Update sync log ----
        finished = datetime.now(timezone.utc).isoformat()
        cur.execute(
            """UPDATE sync_log SET
                finished_at = ?, total_from_api = ?, added = ?,
                updated = ?, removed = ?, status = 'success'
            WHERE id = ?""",
            (finished, len(all_schemes), added, updated, removed, sync_id),
        )
        conn.commit()

        summary = {
            "total_from_api": len(all_schemes),
            "added": added,
            "updated": updated,
            "removed": removed,
            "total_in_db": cur.execute("SELECT COUNT(*) FROM schemes").fetchone()[0],
        }
        return summary

    except Exception as exc:
        finished = datetime.now(timezone.utc).isoformat()
        cur.execute(
            "UPDATE sync_log SET finished_at = ?, status = 'error' WHERE id = ?",
            (finished, sync_id),
        )
        conn.commit()
        raise exc


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def run_once():
    """Execute a single sync cycle."""
    conn = init_db()
    try:
        log.info("=" * 60)
        log.info("Starting sync ...")
        summary = sync(conn)
        log.info(
            "Sync complete!  API: %d | Added: %d | Updated: %d | Removed: %d | DB total: %d",
            summary["total_from_api"],
            summary["added"],
            summary["updated"],
            summary["removed"],
            summary["total_in_db"],
        )
        log.info("=" * 60)
    finally:
        conn.close()


def run_daemon():
    """Run the sync in a loop every SYNC_INTERVAL_SECONDS."""
    log.info("Daemon mode – syncing every %d seconds (%d minutes)",
             SYNC_INTERVAL_SECONDS, SYNC_INTERVAL_SECONDS // 60)
    while True:
        try:
            run_once()
        except KeyboardInterrupt:
            log.info("Interrupted by user. Exiting.")
            sys.exit(0)
        except Exception:
            log.exception("Sync failed! Will retry at next interval.")

        log.info("Next sync in %d seconds ...", SYNC_INTERVAL_SECONDS)
        try:
            time.sleep(SYNC_INTERVAL_SECONDS)
        except KeyboardInterrupt:
            log.info("Interrupted by user. Exiting.")
            sys.exit(0)


def show_stats():
    """Print quick DB stats."""
    if not DB_PATH.exists():
        print("Database does not exist yet. Run a sync first.")
        return
    conn = sqlite3.connect(str(DB_PATH))
    cur = conn.cursor()
    total = cur.execute("SELECT COUNT(*) FROM schemes").fetchone()[0]
    central = cur.execute("SELECT COUNT(*) FROM schemes WHERE level='Central'").fetchone()[0]
    state = cur.execute("SELECT COUNT(*) FROM schemes WHERE level='State'").fetchone()[0]
    ministries = cur.execute("SELECT COUNT(DISTINCT nodal_ministry_name) FROM schemes").fetchone()[0]

    print(f"\n{'='*50}")
    print(f"  Schemes Database Stats")
    print(f"{'='*50}")
    print(f"  Total schemes    : {total}")
    print(f"  Central schemes  : {central}")
    print(f"  State/UT schemes : {state}")
    print(f"  Ministries       : {ministries}")
    print(f"  Database file    : {DB_PATH}")
    print(f"  Database size    : {DB_PATH.stat().st_size / 1024:.1f} KB")

    # Last sync
    row = cur.execute(
        "SELECT started_at, total_from_api, added, updated, removed, status "
        "FROM sync_log ORDER BY id DESC LIMIT 1"
    ).fetchone()
    if row:
        print(f"\n  Last sync        : {row[0]}")
        print(f"  Status           : {row[5]}")
        print(f"  From API         : {row[1]}")
        print(f"  Added / Updated  : {row[2]} / {row[3]}")
        print(f"  Removed          : {row[4]}")

    # Top 5 categories
    print(f"\n  Top categories:")
    rows = cur.execute("""
        SELECT scheme_categories, COUNT(*) as cnt FROM schemes
        GROUP BY scheme_categories ORDER BY cnt DESC LIMIT 5
    """).fetchall()
    for r in rows:
        cats = json.loads(r[0]) if r[0] else []
        print(f"    {', '.join(cats):50s} ({r[1]})")

    print(f"{'='*50}\n")
    conn.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="MyScheme.gov.in Schemes Database Sync Agent"
    )
    parser.add_argument(
        "--daemon", action="store_true",
        help="Run continuously, syncing every hour"
    )
    parser.add_argument(
        "--stats", action="store_true",
        help="Show database statistics and exit"
    )
    args = parser.parse_args()

    if args.stats:
        show_stats()
    elif args.daemon:
        run_daemon()
    else:
        run_once()
