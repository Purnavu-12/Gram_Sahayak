"""
scheme_lookup.py – Query interface for the schemes SQLite database.
Used by the voice agent to search for relevant government schemes.
"""

import sqlite3
import json
import logging
import re
from pathlib import Path
from typing import Optional

log = logging.getLogger("scheme_lookup")

DB_PATH = Path(__file__).parent / "schemes.db"

# ── Persistent connection (reused across calls) ─────────────────────────────
# NOTE: This module is read-heavy. The single connection with WAL mode is safe
# for concurrent reads from asyncio.to_thread(). Writes only happen during
# ensure_fts() at startup (single-threaded).

_conn: Optional[sqlite3.Connection] = None


def _get_conn() -> sqlite3.Connection:
    global _conn
    if _conn is None:
        _conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
        _conn.row_factory = sqlite3.Row
        _conn.execute("PRAGMA journal_mode=WAL;")
        _conn.execute("PRAGMA cache_size=-8000;")       # 8 MB page cache
        _conn.execute("PRAGMA mmap_size=67108864;")      # 64 MB memory-mapped I/O
        _conn.execute("PRAGMA synchronous=NORMAL;")
        _conn.execute("PRAGMA temp_store=MEMORY;")
    return _conn


# ── FTS special character sanitization ───────────────────────────────────────
# FIX #3: FTS5 treats these as syntax. Strip them to prevent query parse errors.

_FTS5_SPECIAL = re.compile(r'["\'\(\)\*\+\-\:\^\~\{\}\[\]\\]')


def _sanitize_fts_query(text: str) -> str:
    """Remove FTS5 special characters from user input."""
    return _FTS5_SPECIAL.sub(" ", text).strip()


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
    """Create FTS virtual table and sync triggers if they don't exist.
    Only rebuilds if the FTS index is empty or out of sync."""
    conn = _get_conn()
    cur = conn.cursor()

    cur.execute(CREATE_FTS_SQL)

    for trigger_sql in FTS_TRIGGERS:
        try:
            cur.execute(trigger_sql)
        except sqlite3.OperationalError:
            pass  # trigger already exists

    # FIX #1: Only rebuild if FTS is empty or row count doesn't match source
    fts_count = cur.execute(f"SELECT COUNT(*) FROM {_FTS_TABLE}").fetchone()[0]
    src_count = cur.execute("SELECT COUNT(*) FROM schemes").fetchone()[0]

    if fts_count != src_count:
        log.info("FTS out of sync (fts=%d, source=%d). Rebuilding...", fts_count, src_count)
        cur.execute(f"INSERT INTO {_FTS_TABLE}({_FTS_TABLE}) VALUES('rebuild');")
        fts_count = src_count
    else:
        log.info("FTS index already in sync — skipping rebuild.")

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
    log.info("FTS index ready – %d rows indexed.", fts_count)


# ── Search helpers ───────────────────────────────────────────────────────────

def _format_scheme(row: sqlite3.Row) -> dict:
    """Convert a DB row into a clean dict for presentation."""
    # FIX #5: Safely access columns that may not exist in all query shapes
    keys = row.keys() if hasattr(row, "keys") else []
    return {
        "scheme_name": row["scheme_name"],
        "short_title": row["scheme_short_title"] if "scheme_short_title" in keys else "",
        "description": row["brief_description"],
        "ministry": row["nodal_ministry_name"],
        "level": row["level"],
        "categories": json.loads(row["scheme_categories"]) if row["scheme_categories"] else [],
        "tags": json.loads(row["tags"]) if row["tags"] else [],
        "states": json.loads(row["beneficiary_states"]) if row["beneficiary_states"] else [],
        "url": row["url"] if "url" in keys else "",
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

    FIX #2: Tries AND first (precise), then falls back to OR (broad).
    """
    conn = _get_conn()
    cur = conn.cursor()

    # FIX #3: Sanitize user input before building FTS query
    clean = _sanitize_fts_query(query)
    tokens = clean.split()
    if not tokens:
        return []

    def _run_fts(fts_query: str) -> list:
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

        sql += " ORDER BY fts.rank LIMIT ?"  # FTS5 rank: more negative = better
        params.append(limit)
        return cur.execute(sql, params).fetchall()

    try:
        # FIX #2: Try AND first — "farmer AND loan" is more precise than "farmer OR loan"
        if len(tokens) > 1:
            and_query = " AND ".join(f'"{t}"*' for t in tokens)
            rows = _run_fts(and_query)
            if rows:
                return [_format_scheme(r) for r in rows]

        # Fallback to OR for broader matching
        or_query = " OR ".join(f'"{t}"*' for t in tokens)
        rows = _run_fts(or_query)

    except Exception as e:
        log.warning("FTS search failed for query '%s': %s. Falling back to LIKE.", query, e)
        rows = _fallback_search(cur, clean, state, category, level, limit)

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
    params: list = []
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
    """Return a single scheme by exact or partial name match."""
    conn = _get_conn()
    # Try exact match first (indexed, fast)
    row = conn.execute(
        "SELECT * FROM schemes WHERE scheme_name = ? COLLATE NOCASE", (name,)
    ).fetchone()
    if row:
        return _format_scheme(row)

    # FIX #8: Use FTS for partial name matching instead of full-table LIKE scan
    clean = _sanitize_fts_query(name)
    if clean:
        try:
            fts_q = " AND ".join(f'"{t}"*' for t in clean.split())
            row = conn.execute(
                f"""SELECT s.* FROM {_FTS_TABLE} fts
                    JOIN schemes s ON s.rowid = fts.rowid
                    WHERE {_FTS_TABLE} MATCH ?
                    ORDER BY fts.rank LIMIT 1""",
                (fts_q,),
            ).fetchone()
            if row:
                return _format_scheme(row)
        except Exception:
            pass

    # Final fallback: LIKE (but with LIMIT 1, it's bounded)
    row = conn.execute(
        "SELECT * FROM schemes WHERE scheme_name LIKE ? COLLATE NOCASE LIMIT 1",
        (f"%{name}%",),
    ).fetchone()
    return _format_scheme(row) if row else None


# ── Cached static lookups ────────────────────────────────────────────────────

_categories_cache: Optional[list[str]] = None
_states_cache: Optional[list[str]] = None
_stats_cache: Optional[dict] = None


def get_all_categories() -> list[str]:
    """Return all unique categories across schemes (cached after first call)."""
    global _categories_cache
    if _categories_cache is not None:
        return _categories_cache
    conn = _get_conn()
    rows = conn.execute("SELECT DISTINCT scheme_categories FROM schemes").fetchall()
    categories: set[str] = set()
    for r in rows:
        for cat in json.loads(r[0] or "[]"):
            categories.add(cat)
    _categories_cache = sorted(categories)
    return _categories_cache


def get_all_states() -> list[str]:
    """Return all unique beneficiary states (cached after first call)."""
    global _states_cache
    if _states_cache is not None:
        return _states_cache
    conn = _get_conn()
    rows = conn.execute("SELECT DISTINCT beneficiary_states FROM schemes").fetchall()
    states: set[str] = set()
    for r in rows:
        for s in json.loads(r[0] or "[]"):
            states.add(s)
    _states_cache = sorted(states)
    return _states_cache


def get_db_stats() -> dict:
    """Quick stats about the database (cached after first call)."""
    global _stats_cache
    if _stats_cache is not None:
        return _stats_cache
    conn = _get_conn()
    cur = conn.cursor()
    total = cur.execute("SELECT COUNT(*) FROM schemes").fetchone()[0]
    central = cur.execute("SELECT COUNT(*) FROM schemes WHERE level='Central'").fetchone()[0]
    state_count = cur.execute("SELECT COUNT(*) FROM schemes WHERE level='State'").fetchone()[0]
    _stats_cache = {"total": total, "central": central, "state": state_count}
    return _stats_cache


# ── Full-detail formatter (for frontend API) ─────────────────────────────────

def _format_scheme_full(row: sqlite3.Row) -> dict:
    """Convert a DB row into a rich dict for the frontend API."""
    keys = row.keys() if hasattr(row, "keys") else []
    cats = json.loads(row["scheme_categories"]) if row["scheme_categories"] else []
    states = json.loads(row["beneficiary_states"]) if row["beneficiary_states"] else []
    tags = json.loads(row["tags"]) if row["tags"] else []
    return {
        "id": row["slug"],
        "name": row["scheme_name"],
        "shortTitle": row["scheme_short_title"] or "" if "scheme_short_title" in keys else "",
        "description": row["brief_description"] or "",
        "ministry": row["nodal_ministry_name"] or "",
        "level": row["level"] or "",
        "category": cats[0] if cats else "General",
        "categories": cats,
        "tags": tags,
        "states": states,
        "state": ", ".join(states) if states else "All India",
        "url": row["url"] or "https://www.myscheme.gov.in" if "url" in keys else "https://www.myscheme.gov.in",
        "schemeFor": row["scheme_for"] or "" if "scheme_for" in keys else "",
        "source": "db",
    }


def _has_column(conn: sqlite3.Connection, table: str, column: str) -> bool:
    """Check if a column exists in a table."""
    cur = conn.execute(f"PRAGMA table_info({table})")
    return any(r[1] == column for r in cur.fetchall())


def get_featured_schemes(limit: int = 6) -> list[dict]:
    """Return top schemes for the featured section.
    FIX #10: Gracefully handles missing 'priority' column."""
    conn = _get_conn()
    if _has_column(conn, "schemes", "priority"):
        rows = conn.execute(
            "SELECT * FROM schemes WHERE priority IS NOT NULL "
            "ORDER BY priority DESC, scheme_name ASC LIMIT ?",
            (limit,),
        ).fetchall()
    else:
        # No priority column — return first N by name
        rows = conn.execute(
            "SELECT * FROM schemes ORDER BY scheme_name ASC LIMIT ?",
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
    """Like search_schemes but returns the full frontend-shaped dict."""
    conn = _get_conn()
    cur = conn.cursor()

    tokens = query.strip().split() if query else []
    has_priority = _has_column(conn, "schemes", "priority")
    order_col = "priority DESC," if has_priority else ""

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
        sql += f" ORDER BY {order_col} scheme_name ASC LIMIT ?"
        params.append(limit)
        rows = cur.execute(sql, params).fetchall()
        return [_format_scheme_full(r) for r in rows]

    # FIX #3: Sanitize tokens
    clean = _sanitize_fts_query(query)
    clean_tokens = clean.split()
    if not clean_tokens:
        return []

    def _run_fts_full(fts_query: str) -> list:
        sql = f"""
            SELECT s.*, fts.rank
            FROM {_FTS_TABLE} fts
            JOIN schemes s ON s.rowid = fts.rowid
            WHERE {_FTS_TABLE} MATCH ?
        """
        p: list = [fts_query]
        if state:
            sql += " AND s.beneficiary_states LIKE ?"
            p.append(f"%{state}%")
        if category:
            sql += " AND s.scheme_categories LIKE ?"
            p.append(f"%{category}%")
        if level:
            sql += " AND s.level = ?"
            p.append(level)
        sql += " ORDER BY fts.rank LIMIT ?"
        p.append(limit)
        return cur.execute(sql, p).fetchall()

    try:
        # AND first, then OR
        if len(clean_tokens) > 1:
            and_q = " AND ".join(f'"{t}"*' for t in clean_tokens)
            rows = _run_fts_full(and_q)
            if rows:
                return [_format_scheme_full(r) for r in rows]

        or_q = " OR ".join(f'"{t}"*' for t in clean_tokens)
        rows = _run_fts_full(or_q)
    except Exception as e:
        log.warning("FTS search failed: %s. Falling back to LIKE.", e)
        rows = _fallback_search(cur, clean, state, category, level, limit)

    return [_format_scheme_full(r) for r in rows]