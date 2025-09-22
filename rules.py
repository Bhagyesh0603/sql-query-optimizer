import re

def apply_rules(query: str):
    suggestions = []
    q = query.lower()

    # 1. SELECT * → specify columns
    if "select *" in q:
        suggestions.append("Avoid SELECT *; specify only required columns.")

    # 2. Missing WHERE clause
    if " where " not in q:
        suggestions.append("No WHERE clause found; full table scan may occur.")

    # 3. Too many JOINs
    join_count = q.count(" join ")
    if join_count > 5:
        suggestions.append(f"Query has {join_count} joins; consider optimizing join order or reducing joins if possible.")

    # 4. Filter pushdown
    if "where" in q and "join" in q:
        suggestions.append("Check if WHERE filters can be pushed before JOINs for efficiency.")

    # 5. OR conditions
    if " or " in q:
        suggestions.append("Consider splitting OR conditions into UNION queries or using IN for better performance.")

    # 6. DISTINCT usage
    if " distinct " in q:
        suggestions.append("Verify if DISTINCT is necessary; it can be costly on large datasets.")

    # 7. Subquery detection
    if "select" in q and " in (" in q:
        suggestions.append("Subquery detected with IN; consider JOIN instead of subquery for performance.")

    # 8. LIKE without wildcard prefix
    if re.search(r"like '%", q) and not re.search(r"like '%.*%'", q):
        suggestions.append("LIKE with leading wildcard (e.g., '%abc') prevents index usage. Try removing prefix if possible.")

    # 9. ORDER BY without LIMIT
    if "order by" in q and "limit" not in q:
        suggestions.append("ORDER BY without LIMIT may sort entire dataset; consider adding LIMIT.")

    return suggestions
