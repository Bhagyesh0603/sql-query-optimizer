# join_optimizer.py
import re
from db import get_connection
from typing import List, Tuple, Dict

def _get_alias_map(query: str) -> Dict[str,str]:
    """
    Return mapping alias -> table and table -> alias for FROM and JOINs.
    """
    alias_map = {}
    table_map = {}

    # FROM table
    m = re.search(r"FROM\s+(\w+)(?:\s+(\w+))?", query, re.IGNORECASE)
    if m:
        table, alias = m.group(1).lower(), (m.group(2) or m.group(1)).lower()
        alias_map[alias] = table
        table_map[table] = alias

    # JOINs
    for jt, ja in re.findall(r"JOIN\s+(\w+)(?:\s+(\w+))?", query, re.IGNORECASE):
        table = jt.lower()
        alias = (ja or jt).lower()
        alias_map[alias] = table
        table_map[table] = alias

    return alias_map, table_map

def _get_join_conditions(query: str):
    """
    Returns a mapping table_alias -> ON condition string (original).
    """
    join_conds = {}
    # Pattern matches: JOIN <table> <alias?> ON <condition> (stops before next JOIN/WHERE/; )
    for jt, ja, cond in re.findall(r"JOIN\s+(\w+)(?:\s+(\w+))?\s+ON\s+([^;]+?)(?=(?:\s+JOIN|\s+WHERE|;|$))",
                                   query, re.IGNORECASE | re.DOTALL):
        alias = (ja or jt).lower()
        join_conds[alias] = cond.strip()
    return join_conds

def estimate_table_rows(conn, table_name: str) -> int:
    """
    Try to read reltuples from pg_class (fast estimate). Falls back to 1000.
    """
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT reltuples::bigint
            FROM pg_class
            WHERE relname = %s
        """, (table_name,))
        row = cur.fetchone()
        cur.close()
        if row and row[0] is not None:
            return int(row[0])
    except Exception:
        pass
    # fallback
    return 1000

def optimize_join_order(query: str, max_steps: int = 100) -> List[str]:
    """
    Greedy heuristic to produce a good join order (list of table aliases).
    Returns list of table aliases in chosen order (alias strings).
    """
    conn = None
    try:
        conn = get_connection()
    except Exception:
        conn = None  # will use simple heuristic if no DB

    alias_map, table_map = _get_alias_map(query)
    if not alias_map:
        return []

    # get join conditions and adjacency
    join_conds = _get_join_conditions(query)

    # candidates = list of aliases
    aliases = list(alias_map.keys())

    # estimate sizes
    size_by_alias = {}
    for a in aliases:
        table = alias_map[a]
        est = None
        if conn:
            try:
                est = estimate_table_rows(conn, table)
            except Exception:
                est = None
        size_by_alias[a] = est or 1000

    # Try to find seed: alias used by WHERE (most selective)
    where_match = re.search(r"WHERE\s+(.+)", query, re.IGNORECASE | re.DOTALL)
    preferred_alias = None
    if where_match:
        where_block = where_match.group(1)
        # pick alias referenced most in where_block
        counts = {a: where_block.lower().count(f"{a}.") for a in aliases}
        preferred_alias = max(counts, key=lambda k: counts[k]) if any(counts.values()) else None

    # seed choice: prefer preferred_alias if exists, else smallest table
    if preferred_alias and counts[preferred_alias] > 0:
        order = [preferred_alias]
    else:
        order = [min(aliases, key=lambda a: size_by_alias.get(a, 1e9))]

    remaining = [a for a in aliases if a not in order]

    # Greedily add a next table that has a join condition with current set and minimal size
    steps = 0
    while remaining and steps < max_steps:
        steps += 1
        candidates = []
        for r in remaining:
            # check if r has ON condition referencing any alias in order by looking for order alias in its ON clause or vice versa
            cond = join_conds.get(r, "")
            connected = any((f"{a}." in cond or f"{alias_map[a]}." in cond) for a in order)
            if connected:
                candidates.append((r, size_by_alias.get(r, 1000)))
        if not candidates:
            # if none connected, pick smallest remaining
            next_alias = min(remaining, key=lambda a: size_by_alias.get(a, 1000))
        else:
            # pick smallest candidate
            next_alias = min(candidates, key=lambda x: x[1])[0]
        order.append(next_alias)
        remaining.remove(next_alias)

    # if remaining still left (rare), append them
    order.extend([a for a in remaining if a not in order])

    if conn:
        try:
            conn.close()
        except:
            pass

    return order

def reorder_query_by_alias_order(query: str, alias_order: List[str]) -> str:
    """
    Rebuild FROM + JOIN clauses according to alias_order (uses original ON conditions).
    Returns the rebuilt query string; if we can't rebuild, return original query.
    """
    alias_map, table_map = _get_alias_map(query)
    join_conds = _get_join_conditions(query)

    if not alias_order or not alias_map:
        return query

    # Build FROM clause using first alias
    first_alias = alias_order[0]
    first_table = alias_map[first_alias]
    from_clause = f"FROM {first_table} {first_alias}"

    join_parts = []
    for alias in alias_order[1:]:
        table = alias_map.get(alias)
        on = join_conds.get(alias)
        if not table or not on:
            # if we can't find ON for alias, bail out and return original
            return query
        join_parts.append(f"JOIN {table} {alias} ON {on}")

    # replace the original FROM...JOIN block with new block
    # naive approach: replace from first FROM up to WHERE or end
    prefix = re.split(r"\bWHERE\b", query, flags=re.IGNORECASE)[0]
    rest = query[len(prefix):]  # remainder (WHERE ... or '')
    new_from_block = from_clause + "\n" + "\n".join(join_parts) + "\n"
    new_query = re.sub(r"FROM\s+(.+?)(?=(\bWHERE\b|$))", new_from_block, query, flags=re.IGNORECASE | re.DOTALL)
    return new_query
