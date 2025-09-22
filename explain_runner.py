from db import run_sql

def run_explain(query):
    """
    Run EXPLAIN (ANALYZE, FORMAT JSON) on a query and return parsed JSON.
    """
    explain_query = f"EXPLAIN (ANALYZE, FORMAT JSON) {query}"
    try:
        result = run_sql(explain_query)
        if result:
            # PostgreSQL returns JSON in first row, first column
            return result[0]['QUERY PLAN'][0]
        return None
    except Exception as e:
        print("❌ EXPLAIN failed:", e)
        return None

# Test block
if __name__ == "__main__":
    test_query = """
    SELECT e.first_name, e.last_name, d.dept_name
    FROM employees e
    JOIN departments d ON e.dept_id = d.dept_id
    WHERE e.salary > 50000;
    """
    explain_json = run_explain(test_query)
    if explain_json:
        print("✅ EXPLAIN JSON obtained!")
        # Print a summary
        print("Plan type:", explain_json.get("Plan", {}).get("Node Type"))
        print("Total cost:", explain_json.get("Plan", {}).get("Total Cost"))
    else:
        print("❌ No EXPLAIN output.")
