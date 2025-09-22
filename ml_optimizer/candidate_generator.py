import sqlparse
import itertools
import random


# -----------------------------------------
# Helper: Extract tables, joins, and where
# -----------------------------------------
def extract_structure(query: str):
    """
    Parse SQL query using sqlparse and extract FROM, JOIN, and WHERE components.
    Returns:
        {
            "from": str,
            "joins": list[str],
            "where": str
        }
    """
    parsed = sqlparse.parse(query)
    if not parsed:
        return {"from": None, "joins": [], "where": None}

    stmt = parsed[0]
    tokens = [t for t in stmt.tokens if not t.is_whitespace]

    from_clause, joins, where_clause = None, [], None
    mode = None
    for tok in tokens:
        tval = tok.value.upper()
        if tval.startswith("FROM"):
            from_clause = tok.value
            mode = "FROM"
        elif "JOIN" in tval:
            joins.append(tok.value)
            mode = "JOIN"
        elif tval.startswith("WHERE"):
            where_clause = tok.value
            mode = "WHERE"

    return {"from": from_clause, "joins": joins, "where": where_clause}


# -----------------------------------------
# Candidate Generation Strategies
# -----------------------------------------
def original_query(query: str):
    return [("original", query)]


def join_permutations(query: str, limit: int = 20, deterministic: bool = False):
    """
    Generate join order permutations.
    - If join count <= 4 → try all permutations.
    - If join count > 4 → sample up to `limit` permutations.
    """
    struct = extract_structure(query)
    joins = struct["joins"]

    if not joins:
        return []

    candidates = []
    n = len(joins)
    if n <= 4:
        # all permutations (small factorials)
        perms = itertools.permutations(joins)
    else:
        # sample permutations
        joins_list = list(joins)
        if deterministic:
            random.seed(42)
        perms = (random.sample(joins_list, n) for _ in range(limit))

    for perm in itertools.islice(perms, limit):
        q = "SELECT * "  # placeholder SELECT
        if struct["from"]:
            q += struct["from"] + " "
        q += " ".join(perm)
        if struct["where"]:
            q += " " + struct["where"]
        candidates.append(("join_perm", q.strip()))

    return candidates


def reverse_joins(query: str):
    struct = extract_structure(query)
    joins = struct["joins"]

    if not joins:
        return []

    q = "SELECT * "
    if struct["from"]:
        q += struct["from"] + " "
    q += " ".join(reversed(joins))
    if struct["where"]:
        q += " " + struct["where"]
    return [("reverse_joins", q.strip())]


def predicate_pushdown(query: str):
    struct = extract_structure(query)
    if not struct["where"]:
        return []

    q = query.replace("FROM", "FROM (SELECT * FROM", 1)
    q = q.replace(struct["where"], f"){struct['where']}", 1)
    return [("predicate_pushdown", q.strip())]


def exists_rewrite(query: str):
    if "JOIN" not in query.upper():
        return []

    q = query.replace("JOIN", "WHERE EXISTS (SELECT 1 FROM")
    if not q.strip().endswith(")"):
        q += ")"
    return [("exists_rewrite", q.strip())]


# -----------------------------------------
# Main API
# -----------------------------------------
def generate_candidates(query: str, limit: int = 10, deterministic: bool = False):
    """
    Generate candidate rewrites for a query.
    Args:
        query (str) : SQL query
        limit (int) : Max number of candidates (approx, after sampling)
        deterministic (bool): Fix random seed for reproducibility
    Returns:
        list of (strategy_name, candidate_sql)
    """
    candidates = []

    # Always include original
    candidates.extend(original_query(query))

    # Join permutations
    candidates.extend(join_permutations(query, limit=limit, deterministic=deterministic))

    # Reverse joins
    candidates.extend(reverse_joins(query))

    # Predicate pushdown
    candidates.extend(predicate_pushdown(query))

    # EXISTS rewrite
    candidates.extend(exists_rewrite(query))

    # Deduplicate
    seen = set()
    unique = []
    for strategy, cand in candidates:
        if cand not in seen:
            unique.append((strategy, cand))
            seen.add(cand)

    # Shuffle (unless deterministic)
    if not deterministic:
        random.shuffle(unique)

    # Always keep original as first
    unique = sorted(unique, key=lambda x: 0 if x[0] == "original" else 1)

    return unique[:limit]


# -----------------------------------------
# Standalone test
# -----------------------------------------
if __name__ == "__main__":
    q = """
    SELECT e.name, d.dept_name
    FROM employees e
    JOIN departments d ON e.dept_id = d.id
    JOIN locations l ON d.loc_id = l.id
    WHERE e.salary > 50000;
    """

    print("Input Query:")
    print(q)

    cands = generate_candidates(q, limit=10, deterministic=True)
    for strat, cand in cands:
        print("\n---", strat, "---")
        print(cand)
