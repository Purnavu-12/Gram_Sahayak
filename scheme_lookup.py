"""
scheme_lookup.py – Query interface for the schemes SQLite database.
Used by the voice agent to search for relevant government schemes.
"""

import sqlite3
import json
import logging
from pathlib import Path
from typing import Optional

log = logging.getLogger("scheme_lookup")

DB_PATH = Path(__file__).parent / "schemes.db"

# ── FTS (Full-Text Search) setup ─────────────────────────────────────────────

_FTS_TABLE = "schemes_fts"

CREATE_FTS_SQL = f"""
CREATE VIRTUAL TABLE IF NOT EXISTS {_FTS_TABLE}
USING fts5(
    slug,
    scheme_name,
    brief_description,
    nodal_ministry_name,
    scheme_categories,
    tags,
    level,
    beneficiary_states,
    content='schemes',
    content_rowid='rowid'
);
"""

# Triggers to keep FTS in sync when the main table changes
FTS_TRIGGERS = [
    f"""CREATE TRIGGER IF NOT EXISTS schemes_ai AFTER INSERT ON schemes BEGIN
        INSERT INTO {_FTS_TABLE}(rowid, slug, scheme_name, brief_description,
            nodal_ministry_name, scheme_categories, tags, level, beneficiary_states)
        VALUES (new.rowid, new.slug, new.scheme_name, new.brief_description,
            new.nodal_ministry_name, new.scheme_categories, new.tags, new.level,
            new.beneficiary_states);
    END;""",
    f"""CREATE TRIGGER IF NOT EXISTS schemes_ad AFTER DELETE ON schemes BEGIN
        INSERT INTO {_FTS_TABLE}({_FTS_TABLE}, rowid, slug, scheme_name,
            brief_description, nodal_ministry_name, scheme_categories, tags,
            level, beneficiary_states)
        VALUES ('delete', old.rowid, old.slug, old.scheme_name, old.brief_description,
            old.nodal_ministry_name, old.scheme_categories, old.tags, old.level,
            old.beneficiary_states);
    END;""",
    f"""CREATE TRIGGER IF NOT EXISTS schemes_au AFTER UPDATE ON schemes BEGIN
        INSERT INTO {_FTS_TABLE}({_FTS_TABLE}, rowid, slug, scheme_name,
            brief_description, nodal_ministry_name, scheme_categories, tags,
            level, beneficiary_states)
        VALUES ('delete', old.rowid, old.slug, old.scheme_name, old.brief_description,
            old.nodal_ministry_name, old.scheme_categories, old.tags, old.level,
            old.beneficiary_states);
        INSERT INTO {_FTS_TABLE}(rowid, slug, scheme_name, brief_description,
            nodal_ministry_name, scheme_categories, tags, level, beneficiary_states)
        VALUES (new.rowid, new.slug, new.scheme_name, new.brief_description,
            new.nodal_ministry_name, new.scheme_categories, new.tags, new.level,
            new.beneficiary_states);
    END;""",
]


def _get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    return conn


def ensure_fts():
    """Create FTS virtual table and sync triggers if they don't exist, then
    do an initial rebuild so existing rows are indexed."""
    conn = _get_conn()
    cur = conn.cursor()
    cur.execute(CREATE_FTS_SQL)
    for trigger_sql in FTS_TRIGGERS:
        try:
            cur.execute(trigger_sql)
        except sqlite3.OperationalError:
            pass  # trigger already exists
    # Rebuild FTS index from current data
    cur.execute(f"INSERT INTO {_FTS_TABLE}({_FTS_TABLE}) VALUES('rebuild');")
    conn.commit()
    count = cur.execute(f"SELECT COUNT(*) FROM {_FTS_TABLE}").fetchone()[0]
    log.info("FTS index ready – %d rows indexed.", count)
    conn.close()


# ── Search helpers ───────────────────────────────────────────────────────────

def _format_scheme(row: sqlite3.Row) -> dict:
    """Convert a DB row into a clean dict for presentation."""
    return {
        "scheme_name": row["scheme_name"],
        "short_title": row["scheme_short_title"],
        "description": row["brief_description"],
        "ministry": row["nodal_ministry_name"],
        "level": row["level"],
        "categories": json.loads(row["scheme_categories"]) if row["scheme_categories"] else [],
        "tags": json.loads(row["tags"]) if row["tags"] else [],
        "states": json.loads(row["beneficiary_states"]) if row["beneficiary_states"] else [],
        "url": row["url"],
    }


def search_schemes(
    query: str,
    state: Optional[str] = None,
    category: Optional[str] = None,
    level: Optional[str] = None,
    limit: int = 10,
) -> list[dict]:
    """
    Full-text search across scheme name, description, tags, etc.
    Optionally filter by state, category, or level.
    Returns a list of scheme dicts ordered by relevance.
    """
    conn = _get_conn()
    cur = conn.cursor()

    # Build FTS query – add wildcards for partial matching
    tokens = query.strip().split()
    if not tokens:
        return []

    # FTS5 query: each token gets a * suffix for prefix matching, combined with OR
    fts_query = " OR ".join(f'"{t}"*' for t in tokens if t)

    sql = f"""
        SELECT s.*, fts.rank
        FROM {_FTS_TABLE} fts
        JOIN schemes s ON s.rowid = fts.rowid
        WHERE {_FTS_TABLE} MATCH ?
    """
    params: list = [fts_query]

    if state:
        sql += " AND s.beneficiary_states LIKE ?"
        params.append(f"%{state}%")
    if category:
        sql += " AND s.scheme_categories LIKE ?"
        params.append(f"%{category}%")
    if level:
        sql += " AND s.level = ?"
        params.append(level)

    sql += " ORDER BY fts.rank LIMIT ?"
    params.append(limit)

    try:
        rows = cur.execute(sql, params).fetchall()
    except Exception as e:
        log.warning("FTS search failed for query '%s': %s. Falling back to LIKE.", query, e)
        rows = _fallback_search(cur, query, state, category, level, limit)

    conn.close()
    return [_format_scheme(r) for r in rows]


def _fallback_search(
    cur: sqlite3.Cursor,
    query: str,
    state: Optional[str],
    category: Optional[str],
    level: Optional[str],
    limit: int,
) -> list:
    """LIKE-based fallback when FTS fails."""
    clauses = []
    params = []
    for token in query.strip().split():
        clauses.append(
            "(scheme_name LIKE ? OR brief_description LIKE ? OR tags LIKE ? OR scheme_categories LIKE ?)"
        )
        like = f"%{token}%"
        params.extend([like, like, like, like])

    where = " AND ".join(clauses) if clauses else "1=1"

    if state:
        where += " AND beneficiary_states LIKE ?"
        params.append(f"%{state}%")
    if category:
        where += " AND scheme_categories LIKE ?"
        params.append(f"%{category}%")
    if level:
        where += " AND level = ?"
        params.append(level)

    sql = f"SELECT * FROM schemes WHERE {where} LIMIT ?"
    params.append(limit)
    return cur.execute(sql, params).fetchall()


def get_scheme_by_slug(slug: str) -> Optional[dict]:
    """Return a single scheme by its slug."""
    conn = _get_conn()
    cur = conn.cursor()
    row = cur.execute("SELECT * FROM schemes WHERE slug = ?", (slug,)).fetchone()
    conn.close()
    return _format_scheme(row) if row else None


def get_all_categories() -> list[str]:
    """Return all unique categories across schemes."""
    conn = _get_conn()
    rows = conn.execute("SELECT DISTINCT scheme_categories FROM schemes").fetchall()
    conn.close()
    categories = set()
    for r in rows:
        for cat in json.loads(r[0] or "[]"):
            categories.add(cat)
    return sorted(categories)


def get_all_states() -> list[str]:
    """Return all unique beneficiary states."""
    conn = _get_conn()
    rows = conn.execute("SELECT DISTINCT beneficiary_states FROM schemes").fetchall()
    conn.close()
    states = set()
    for r in rows:
        for s in json.loads(r[0] or "[]"):
            states.add(s)
    return sorted(states)


def get_db_stats() -> dict:
    """Quick stats about the database."""
    conn = _get_conn()
    cur = conn.cursor()
    total = cur.execute("SELECT COUNT(*) FROM schemes").fetchone()[0]
    central = cur.execute("SELECT COUNT(*) FROM schemes WHERE level='Central'").fetchone()[0]
    state = cur.execute("SELECT COUNT(*) FROM schemes WHERE level='State'").fetchone()[0]
    conn.close()
    return {"total": total, "central": central, "state": state}
