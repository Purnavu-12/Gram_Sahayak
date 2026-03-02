"""
scheme_lookup.py – Query interface for the schemes SQLite database.
Used by the voice agent to search for relevant government schemes.
"""

import sqlite3
import json
import logging
from functools import lru_cache
from pathlib import Path
from typing import Optional

log = logging.getLogger("scheme_lookup")

DB_PATH = Path(__file__).parent / "schemes.db"

# ── Persistent connection (reused across calls) ─────────────────────────────

_conn: Optional[sqlite3.Connection] = None


def _get_conn() -> sqlite3.Connection:
    global _conn
    if _conn is None:
        _conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
        _conn.row_factory = sqlite3.Row
        _conn.execute("PRAGMA journal_mode=WAL;")
        _conn.execute("PRAGMA cache_size=-8000;")       # 8 MB page cache
        _conn.execute("PRAGMA mmap_size=67108864;")      # 64 MB memory-mapped I/O
        _conn.execute("PRAGMA synchronous=NORMAL;")      # faster reads
        _conn.execute("PRAGMA temp_store=MEMORY;")       # temp tables in RAM
    return _conn


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
    # Add indexes for common filter columns
    for idx_sql in [
        "CREATE INDEX IF NOT EXISTS idx_schemes_level ON schemes(level);",
        "CREATE INDEX IF NOT EXISTS idx_schemes_slug ON schemes(slug);",
        "CREATE INDEX IF NOT EXISTS idx_schemes_name ON schemes(scheme_name);",
    ]:
        try:
            cur.execute(idx_sql)
        except sqlite3.OperationalError:
            pass
    conn.commit()
    count = cur.execute(f"SELECT COUNT(*) FROM {_FTS_TABLE}").fetchone()[0]
    log.info("FTS index ready – %d rows indexed.", count)


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
    row = conn.execute("SELECT * FROM schemes WHERE slug = ?", (slug,)).fetchone()
    return _format_scheme(row) if row else None


def get_scheme_by_name(name: str) -> Optional[dict]:
    """Return a single scheme by exact or fuzzy name match."""
    conn = _get_conn()
    # Try exact match first
    row = conn.execute(
        "SELECT * FROM schemes WHERE scheme_name = ? COLLATE NOCASE", (name,)
    ).fetchone()
    if row:
        return _format_scheme(row)
    # Try LIKE match
    row = conn.execute(
        "SELECT * FROM schemes WHERE scheme_name LIKE ? COLLATE NOCASE LIMIT 1",
        (f"%{name}%",)
    ).fetchone()
    return _format_scheme(row) if row else None


# ── Cached static lookups ────────────────────────────────────────────────────

_categories_cache: Optional[list[str]] = None
_states_cache: Optional[list[str]] = None
_stats_cache: Optional[dict] = None


def get_all_categories() -> list[str]:
    """Return all unique categories across schemes (cached)."""
    global _categories_cache
    if _categories_cache is not None:
        return _categories_cache
    conn = _get_conn()
    rows = conn.execute("SELECT DISTINCT scheme_categories FROM schemes").fetchall()
    categories = set()
    for r in rows:
        for cat in json.loads(r[0] or "[]"):
            categories.add(cat)
    _categories_cache = sorted(categories)
    return _categories_cache


def get_all_states() -> list[str]:
    """Return all unique beneficiary states (cached)."""
    global _states_cache
    if _states_cache is not None:
        return _states_cache
    conn = _get_conn()
    rows = conn.execute("SELECT DISTINCT beneficiary_states FROM schemes").fetchall()
    states = set()
    for r in rows:
        for s in json.loads(r[0] or "[]"):
            states.add(s)
    _states_cache = sorted(states)
    return _states_cache


def get_db_stats() -> dict:
    """Quick stats about the database (cached)."""
    global _stats_cache
    if _stats_cache is not None:
        return _stats_cache
    conn = _get_conn()
    cur = conn.cursor()
    total = cur.execute("SELECT COUNT(*) FROM schemes").fetchone()[0]
    central = cur.execute("SELECT COUNT(*) FROM schemes WHERE level='Central'").fetchone()[0]
    state = cur.execute("SELECT COUNT(*) FROM schemes WHERE level='State'").fetchone()[0]
    _stats_cache = {"total": total, "central": central, "state": state}
    return _stats_cache


# ── Full-detail formatter (for frontend API) ─────────────────────────────────

def _format_scheme_full(row: sqlite3.Row) -> dict:
    """Convert a DB row into a rich dict for the frontend API."""
    cats = json.loads(row["scheme_categories"]) if row["scheme_categories"] else []
    states = json.loads(row["beneficiary_states"]) if row["beneficiary_states"] else []
    tags = json.loads(row["tags"]) if row["tags"] else []
    return {
        "id": row["slug"],
        "name": row["scheme_name"],
        "shortTitle": row["scheme_short_title"] or "",
        "description": row["brief_description"] or "",
        "ministry": row["nodal_ministry_name"] or "",
        "level": row["level"] or "",
        "category": cats[0] if cats else "General",
        "categories": cats,
        "tags": tags,
        "states": states,
        "state": ", ".join(states) if states else "All India",
        "url": row["url"] or "https://www.myscheme.gov.in",
        "schemeFor": row["scheme_for"] or "",
        "source": "db",
    }


def get_featured_schemes(limit: int = 6) -> list[dict]:
    """Return top schemes by priority for the featured section."""
    conn = _get_conn()
    rows = conn.execute(
        "SELECT * FROM schemes WHERE priority IS NOT NULL ORDER BY priority DESC, scheme_name ASC LIMIT ?",
        (limit,),
    ).fetchall()
    return [_format_scheme_full(r) for r in rows]


def search_schemes_full(
    query: str,
    state: Optional[str] = None,
    category: Optional[str] = None,
    level: Optional[str] = None,
    limit: int = 20,
) -> list[dict]:
    """
    Like search_schemes but returns the full frontend-shaped dict.
    """
    conn = _get_conn()
    cur = conn.cursor()

    tokens = query.strip().split() if query else []
    if not tokens:
        # No query text — just apply filters or return popular
        sql = "SELECT * FROM schemes WHERE 1=1"
        params: list = []
        if state:
            sql += " AND beneficiary_states LIKE ?"
            params.append(f"%{state}%")
        if category:
            sql += " AND scheme_categories LIKE ?"
            params.append(f"%{category}%")
        if level:
            sql += " AND level = ?"
            params.append(level)
        sql += " ORDER BY priority DESC LIMIT ?"
        params.append(limit)
        rows = cur.execute(sql, params).fetchall()
        return [_format_scheme_full(r) for r in rows]

    fts_query = " OR ".join(f'"{t}"*' for t in tokens if t)
    sql = f"""
        SELECT s.*, fts.rank
        FROM {_FTS_TABLE} fts
        JOIN schemes s ON s.rowid = fts.rowid
        WHERE {_FTS_TABLE} MATCH ?
    """
    params = [fts_query]
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
        log.warning("FTS search failed: %s. Falling back to LIKE.", e)
        rows = _fallback_search(cur, query, state, category, level, limit)

    return [_format_scheme_full(r) for r in rows]
