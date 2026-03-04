"""
scheme_lookup.py – Query interface for the schemes SQLite database.
"""

import sqlite3
import json
import logging
import re
from pathlib import Path
from typing import Optional

log = logging.getLogger("scheme_lookup")

DB_PATH = Path(__file__).parent / "schemes.db"

_conn: Optional[sqlite3.Connection] = None


def _get_conn() -> sqlite3.Connection:
    global _conn
    if _conn is None:
        if not DB_PATH.exists():
            raise FileNotFoundError(
                f"Database not found at {DB_PATH}. "
                "Make sure schemes.db is in the same directory as scheme_lookup.py."
            )
        _conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
        _conn.row_factory = sqlite3.Row
        _conn.execute("PRAGMA journal_mode=WAL;")
        _conn.execute("PRAGMA cache_size=-8000;")
        _conn.execute("PRAGMA mmap_size=67108864;")
        _conn.execute("PRAGMA synchronous=NORMAL;")
        _conn.execute("PRAGMA temp_store=MEMORY;")
    return _conn


# ── FTS special character sanitization ───────────────────────────────────────

_FTS5_SPECIAL = re.compile(r'["\'\(\)\*\+\-\:\^\~\{\}\[\]\\/<>!@#$%&=]')


def _sanitize_fts_query(text: str) -> str:
    """Remove FTS5 special characters and normalize whitespace."""
    cleaned = _FTS5_SPECIAL.sub(" ", text)
    # Collapse multiple spaces and strip
    return " ".join(cleaned.split())


# ── FTS setup ────────────────────────────────────────────────────────────────

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
    """Create FTS virtual table and triggers, rebuild only if needed."""
    conn = _get_conn()
    cur = conn.cursor()
    cur.execute(CREATE_FTS_SQL)
    for trigger_sql in FTS_TRIGGERS:
        try:
            cur.execute(trigger_sql)
        except sqlite3.OperationalError:
            pass

    fts_count = cur.execute(f"SELECT COUNT(*) FROM {_FTS_TABLE}").fetchone()[0]
    src_count = cur.execute("SELECT COUNT(*) FROM schemes").fetchone()[0]

    if fts_count != src_count:
        log.info("FTS out of sync (fts=%d, source=%d). Rebuilding...", fts_count, src_count)
        cur.execute(f"INSERT INTO {_FTS_TABLE}({_FTS_TABLE}) VALUES('rebuild');")
        fts_count = src_count
    else:
        log.info("FTS index in sync — skipping rebuild.")

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


def validate() -> dict:
    """Run diagnostic checks. Call after ensure_fts()."""
    result = {"ok": False, "errors": []}
    try:
        conn = _get_conn()
        cur = conn.cursor()

        # 1. Check schemes table exists and has rows
        try:
            count = cur.execute("SELECT COUNT(*) FROM schemes").fetchone()[0]
            result["schemes_count"] = count
            if count == 0:
                result["errors"].append("schemes table is EMPTY")
        except sqlite3.OperationalError as e:
            result["errors"].append(f"schemes table missing: {e}")
            return result

        # 2. Check required columns exist
        cols = {r[1] for r in cur.execute("PRAGMA table_info(schemes)").fetchall()}
        required = {"slug", "scheme_name", "brief_description", "nodal_ministry_name",
                     "scheme_categories", "tags", "level", "beneficiary_states"}
        missing = required - cols
        if missing:
            result["errors"].append(f"Missing columns in schemes table: {missing}")
        result["columns"] = sorted(cols)

        # 3. Check FTS index has rows
        try:
            fts_count = cur.execute(f"SELECT COUNT(*) FROM {_FTS_TABLE}").fetchone()[0]
            result["fts_count"] = fts_count
            if fts_count == 0:
                result["errors"].append("FTS index is EMPTY — search will return nothing")
        except sqlite3.OperationalError as e:
            result["errors"].append(f"FTS table missing: {e}")
            result["fts_count"] = 0

        # 4. Run a test FTS search
        try:
            test_rows = cur.execute(
                f"SELECT COUNT(*) FROM {_FTS_TABLE} WHERE {_FTS_TABLE} MATCH 'scheme'",
            ).fetchone()[0]
            result["test_search_results"] = test_rows
            if test_rows == 0:
                # Try broader test
                test_rows2 = cur.execute(
                    f"SELECT COUNT(*) FROM {_FTS_TABLE} WHERE {_FTS_TABLE} MATCH '*'",
                ).fetchone()[0]
                result["test_wildcard_results"] = test_rows2
        except Exception as e:
            result["errors"].append(f"Test FTS search failed: {e}")
            result["test_search_results"] = 0

        # 5. Check a sample row can be formatted
        try:
            sample = cur.execute("SELECT * FROM schemes LIMIT 1").fetchone()
            if sample:
                _format_scheme(sample)  # Will throw if column access fails
                result["sample_scheme"] = sample["scheme_name"]
        except Exception as e:
            result["errors"].append(f"Sample row formatting failed: {e}")

        result["ok"] = len(result["errors"]) == 0

    except Exception as e:
        result["errors"].append(f"Validation crashed: {e}")

    if result["errors"]:
        log.error("Validation errors: %s", result["errors"])
    return result


# ── Search helpers ───────────────────────────────────────────────────────────

def _format_scheme(row: sqlite3.Row) -> dict:
    keys = row.keys() if hasattr(row, "keys") else []
    return {
        "scheme_name": row["scheme_name"],
        "short_title": row["scheme_short_title"] if "scheme_short_title" in keys else "",
        "description": row["brief_description"] or "",
        "ministry": row["nodal_ministry_name"] or "",
        "level": row["level"] or "",
        "categories": json.loads(row["scheme_categories"]) if row["scheme_categories"] else [],
        "tags": json.loads(row["tags"]) if row["tags"] else [],
        "states": json.loads(row["beneficiary_states"]) if row["beneficiary_states"] else [],
        "url": row["url"] if "url" in keys else "",
    }


def _build_fts_query(tokens: list[str], operator: str = "OR") -> str:
    """Build a safe FTS5 query from sanitized tokens.

    Uses bare token* syntax (no quotes) since input is already sanitized.
    Filters out FTS5 reserved words to prevent syntax errors.
    """
    fts5_reserved = {"AND", "OR", "NOT", "NEAR"}
    safe_tokens = [t for t in tokens if t.upper() not in fts5_reserved and len(t) > 0]
    if not safe_tokens:
        # All tokens were reserved words — try using them as quoted tokens
        safe_tokens = [f'"{t}"' for t in tokens if len(t) > 0]
    return f" {operator} ".join(f"{t}*" for t in safe_tokens)


def search_schemes(
    query: str,
    state: Optional[str] = None,
    category: Optional[str] = None,
    level: Optional[str] = None,
    limit: int = 10,
) -> list[dict]:
    """FTS search with AND-first strategy, OR fallback, then LIKE fallback."""
    conn = _get_conn()
    cur = conn.cursor()

    clean = _sanitize_fts_query(query)
    tokens = clean.split()
    if not tokens:
        log.warning("search_schemes: empty query after sanitization (original: %r)", query)
        return []

    log.info("search_schemes: sanitized %r -> tokens=%r", query, tokens)

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
        sql += " ORDER BY fts.rank LIMIT ?"
        params.append(limit)

        log.debug("FTS query: %s | params: %s", fts_query, params)
        return cur.execute(sql, params).fetchall()

    try:
        # Strategy 1: AND (most precise)
        if len(tokens) > 1:
            and_q = _build_fts_query(tokens, "AND")
            if and_q:
                log.info("Trying AND query: %s", and_q)
                rows = _run_fts(and_q)
                if rows:
                    log.info("AND query returned %d results", len(rows))
                    return [_format_scheme(r) for r in rows]

        # Strategy 2: OR (broader)
        or_q = _build_fts_query(tokens, "OR")
        if or_q:
            log.info("Trying OR query: %s", or_q)
            rows = _run_fts(or_q)
            if rows:
                log.info("OR query returned %d results", len(rows))
                return [_format_scheme(r) for r in rows]

        log.info("FTS returned 0 results for '%s'", query)

    except Exception as e:
        log.warning("FTS search failed for '%s': %s. Falling back to LIKE.", query, e)
        rows = _fallback_search(cur, clean, state, category, level, limit)
        return [_format_scheme(r) for r in rows]

    # Strategy 3: LIKE fallback (slowest but most forgiving)
    log.info("Trying LIKE fallback for '%s'", query)
    rows = _fallback_search(cur, clean, state, category, level, limit)
    log.info("LIKE fallback returned %d results", len(rows))
    return [_format_scheme(r) for r in rows]


def _fallback_search(
    cur: sqlite3.Cursor,
    query: str,
    state: Optional[str],
    category: Optional[str],
    level: Optional[str],
    limit: int,
) -> list:
    """LIKE-based fallback when FTS fails or returns nothing."""
    clauses = []
    params: list = []
    for token in query.strip().split():
        if len(token) < 2:  # Skip single-char tokens
            continue
        clauses.append(
            "(scheme_name LIKE ? OR brief_description LIKE ? OR tags LIKE ? "
            "OR scheme_categories LIKE ? OR nodal_ministry_name LIKE ?)"
        )
        like = f"%{token}%"
        params.extend([like, like, like, like, like])

    where = " OR ".join(clauses) if clauses else "1=1"

    if state:
        where = f"({where}) AND beneficiary_states LIKE ?"
        params.append(f"%{state}%")
    if category:
        where = f"({where}) AND scheme_categories LIKE ?"
        params.append(f"%{category}%")
    if level:
        where = f"({where}) AND level = ?"
        params.append(level)

    sql = f"SELECT * FROM schemes WHERE {where} LIMIT ?"
    params.append(limit)
    return cur.execute(sql, params).fetchall()


def get_scheme_by_slug(slug: str) -> Optional[dict]:
    conn = _get_conn()
    row = conn.execute("SELECT * FROM schemes WHERE slug = ?", (slug,)).fetchone()
    return _format_scheme(row) if row else None


def get_scheme_by_name(name: str) -> Optional[dict]:
    conn = _get_conn()
    # Exact match (indexed)
    row = conn.execute(
        "SELECT * FROM schemes WHERE scheme_name = ? COLLATE NOCASE", (name,)
    ).fetchone()
    if row:
        return _format_scheme(row)

    # FTS-based partial match
    clean = _sanitize_fts_query(name)
    if clean:
        try:
            fts_q = _build_fts_query(clean.split(), "AND")
            if fts_q:
                row = conn.execute(
                    f"""SELECT s.* FROM {_FTS_TABLE} fts
                        JOIN schemes s ON s.rowid = fts.rowid
                        WHERE {_FTS_TABLE} MATCH ?
                        ORDER BY fts.rank LIMIT 1""",
                    (fts_q,),
                ).fetchone()
                if row:
                    return _format_scheme(row)
        except Exception as e:
            log.debug("FTS name lookup failed for '%s': %s", name, e)

    # LIKE fallback
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

def _has_column(conn: sqlite3.Connection, table: str, column: str) -> bool:
    cur = conn.execute(f"PRAGMA table_info({table})")
    return any(r[1] == column for r in cur.fetchall())


def _format_scheme_full(row: sqlite3.Row) -> dict:
    keys = row.keys() if hasattr(row, "keys") else []
    cats = json.loads(row["scheme_categories"]) if row["scheme_categories"] else []
    states = json.loads(row["beneficiary_states"]) if row["beneficiary_states"] else []
    tags = json.loads(row["tags"]) if row["tags"] else []
    return {
        "id": row["slug"],
        "name": row["scheme_name"],
        "shortTitle": (row["scheme_short_title"] or "") if "scheme_short_title" in keys else "",
        "description": row["brief_description"] or "",
        "ministry": row["nodal_ministry_name"] or "",
        "level": row["level"] or "",
        "category": cats[0] if cats else "General",
        "categories": cats,
        "tags": tags,
        "states": states,
        "state": ", ".join(states) if states else "All India",
        "url": (row["url"] or "https://www.myscheme.gov.in") if "url" in keys else "https://www.myscheme.gov.in",
        "schemeFor": (row["scheme_for"] or "") if "scheme_for" in keys else "",
        "source": "db",
    }


def get_featured_schemes(limit: int = 6) -> list[dict]:
    conn = _get_conn()
    if _has_column(conn, "schemes", "priority"):
        rows = conn.execute(
            "SELECT * FROM schemes WHERE priority IS NOT NULL "
            "ORDER BY priority DESC, scheme_name ASC LIMIT ?",
            (limit,),
        ).fetchall()
    else:
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
    conn = _get_conn()
    cur = conn.cursor()

    tokens = query.strip().split() if query else []
    has_priority = _has_column(conn, "schemes", "priority")
    order_col = "priority DESC," if has_priority else ""

    if not tokens:
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
        if len(clean_tokens) > 1:
            and_q = _build_fts_query(clean_tokens, "AND")
            if and_q:
                rows = _run_fts_full(and_q)
                if rows:
                    return [_format_scheme_full(r) for r in rows]

        or_q = _build_fts_query(clean_tokens, "OR")
        if or_q:
            rows = _run_fts_full(or_q)
            if rows:
                return [_format_scheme_full(r) for r in rows]
    except Exception as e:
        log.warning("FTS search_full failed: %s. Using LIKE.", e)
        rows = _fallback_search(cur, clean, state, category, level, limit)
        return [_format_scheme_full(r) for r in rows]

    rows = _fallback_search(cur, clean, state, category, level, limit)
    return [_format_scheme_full(r) for r in rows]