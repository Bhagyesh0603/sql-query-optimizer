import re
import itertools
from join_optimizer import optimize_join_order, reorder_query_by_alias_order
from simple_candidates import generate_simple_candidates


SCHEMA_COLUMNS = {
    "employees": ["emp_id", "first_name", "last_name", "dept_id", "hire_date", "salary"],
    "departments": ["dept_id", "dept_name"],
    "salaries": ["emp_id", "amount", "from_date", "to_date"],
    "projects": ["proj_id", "proj_name", "dept_id", "budget"],
    "visits": ["visit_id", "emp_id", "patient_id", "visit_date"],
    "appointments": ["appointment_id", "visit_id", "doctor_id", "appointment_date"],
    "patients": ["patient_id", "name", "dob"],
    "doctors": ["doctor_id", "name", "specialty"]
}

TABLE_ALIASES = {
    "employees": "e",
    "departments": "d",
    "salaries": "s",
    "projects": "p",
    "visits": "v",
    "appointments": "a",
    "patients": "pt",
    "doctors": "doc"
}


def rewrite_single_query(query):
    rewritten = query

    # 1️⃣ Replace SELECT *
    select_star = re.search(r"SELECT\s+\*\s+FROM\s+(\w+)(?:\s+(\w+))?", rewritten, re.IGNORECASE)
    if select_star:
        table = select_star.group(1).lower()
        existing_alias = select_star.group(2)
        alias = existing_alias or TABLE_ALIASES.get(table, table)
        if table in SCHEMA_COLUMNS:
            columns = [f"{alias}.{c}" for c in SCHEMA_COLUMNS[table]]
            col_list = ", ".join(columns)
            rewritten = re.sub(r"SELECT\s+\*\s+FROM\s+" + table + (rf"\s+{existing_alias}" if existing_alias else ""),
                               f"SELECT {col_list} FROM {table} {alias}",
                               rewritten, flags=re.IGNORECASE)

    # 2️⃣ YEAR() → BETWEEN
    year_matches = re.findall(r"YEAR\((\w+\.\w+)\)\s*=\s*(\d{4})", rewritten, re.IGNORECASE)
    for col, year in year_matches:
        between_clause = f"{col} BETWEEN '{year}-01-01' AND '{year}-12-31'"
        rewritten = re.sub(rf"YEAR\({col}\)\s*=\s*{year}", between_clause, rewritten, flags=re.IGNORECASE)

    # 3️⃣ Prefix ambiguous columns
    for table, alias in TABLE_ALIASES.items():
        for col in SCHEMA_COLUMNS.get(table, []):
            rewritten = re.sub(rf"(?<!\.)\b{col}\b", f"{alias}.{col}", rewritten)

    # 4️⃣ Subquery rewrite (IN → JOIN)
    rewritten = re.sub(
        r"(\w+)\.(\w+)\s+IN\s*\(\s*SELECT\s+(\w+)\s+FROM\s+(\w+)\s+(\w+)?\s*WHERE\s+([^)]+)\)",
        lambda m: f"EXISTS (SELECT 1 FROM {m.group(4)} {m.group(5) or TABLE_ALIASES.get(m.group(4), m.group(4))} "
                  f"WHERE {m.group(1)}.{m.group(2)} = {m.group(5) or TABLE_ALIASES.get(m.group(4), m.group(4))}.{m.group(3)} "
                  f"AND {m.group(6)})",
        rewritten, flags=re.IGNORECASE
    )

    return rewritten


# near top of rewriter.py

# rewriter.py
import re
from itertools import permutations

def generate_join_candidates(query: str, max_permutations=10):
    """
    Generate candidate optimizations for a query using simple, reliable methods.
    Returns a list of SQL strings with different optimization strategies.
    """
    return generate_simple_candidates(query, max_permutations)


if __name__ == "__main__":
    test_query = """
    SELECT *
    FROM employees e
    JOIN departments d ON e.dept_id = d.dept_id
    JOIN projects p ON d.dept_id = p.dept_id
    JOIN salaries s ON e.emp_id = s.emp_id
    WHERE YEAR(e.hire_date) = 2018
      AND e.dept_id IN (SELECT dept_id FROM projects WHERE budget > 10000);
    """
    candidates = generate_join_candidates(test_query)
    print("=== GENERATED CANDIDATES ===")
    for q in candidates:
        print(q)
        print("-" * 60)
