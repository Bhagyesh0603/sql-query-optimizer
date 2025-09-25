#!/usr/bin/env python3

import sys
from main import optimize_query

def test_complex_queries():
    """Test queries that should generate multiple optimization candidates"""
    
    test_queries = [
        # Query 1: Multiple table query with potential for join reordering
        """
        SELECT e.emp_id, e.first_name, e.last_name, e.salary, d.dept_name
        FROM employees e, departments d, projects p
        WHERE e.dept_id = d.dept_id 
        AND d.dept_id = p.dept_id
        AND e.salary > 70000
        AND p.budget > 100000
        ORDER BY e.salary DESC
        """,
        
        # Query 2: Subquery that could be converted to JOIN
        """
        SELECT emp_id, first_name, salary
        FROM employees 
        WHERE dept_id IN (
            SELECT dept_id FROM departments WHERE dept_name = 'Engineering'
        )
        AND salary > 80000
        """,
        
        # Query 3: Query with functions that could benefit from optimization
        """
        SELECT * FROM employees 
        WHERE UPPER(first_name) LIKE '%JOHN%' 
        AND LOWER(last_name) LIKE '%smith%'
        AND hire_date >= '2020-01-01'
        ORDER BY salary DESC
        """,
        
        # Query 4: Aggregation query without LIMIT
        """
        SELECT dept_id, COUNT(*) as emp_count, AVG(salary) as avg_salary
        FROM employees
        WHERE salary > 50000
        GROUP BY dept_id
        HAVING COUNT(*) > 5
        ORDER BY avg_salary DESC
        """
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n{'='*60}")
        print(f"TESTING QUERY {i}")
        print(f"{'='*60}")
        print(f"Query: {query.strip()}")
        print()
        
        try:
            result = optimize_query(query.strip())
            print("✅ Query optimization completed")
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_complex_queries()