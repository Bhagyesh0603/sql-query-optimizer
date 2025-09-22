#!/usr/bin/env python3
"""
Simple and reliable candidate generator for SQL optimization
Focuses on working candidates rather than complex reordering that breaks SQL
"""
import re
from typing import List, Tuple

def generate_simple_candidates(query: str, limit: int = 5) -> List[str]:
    """Generate simple, working SQL candidates without breaking syntax"""
    candidates = [query]  # Always include original
    query_lower = query.lower().strip()
    
    # 1. Add index hints for common patterns
    if "join" in query_lower:
        # Nested loop hint
        nl_query = query.replace("SELECT", "SELECT /*+ USE_NL */", 1)
        if nl_query != query:
            candidates.append(nl_query)
        
        # Hash join hint  
        hash_query = query.replace("SELECT", "SELECT /*+ USE_HASH */", 1)
        if hash_query != query:
            candidates.append(hash_query)
    
    # 2. Convert explicit JOINs to WHERE-based joins (if simple enough)
    if query_lower.count("join") <= 2:  # Only for simple joins
        where_based = convert_to_where_joins(query)
        if where_based and where_based != query:
            candidates.append(where_based)
    
    # 3. Reorder WHERE conditions (move selective ones first)
    reordered_where = reorder_where_conditions(query)
    if reordered_where and reordered_where != query:
        candidates.append(reordered_where)
    
    # 4. Add LIMIT if not exists and has ORDER BY
    if "order by" in query_lower and "limit" not in query_lower:
        limited_query = query.rstrip('; \t\n') + " LIMIT 1000"
        candidates.append(limited_query)
    
    # Remove duplicates while preserving order
    seen = set()
    unique_candidates = []
    for cand in candidates:
        normalized = ' '.join(cand.split())  # Normalize whitespace
        if normalized not in seen:
            seen.add(normalized)
            unique_candidates.append(cand)
    
    return unique_candidates[:limit]

def convert_to_where_joins(query: str) -> str:
    """Convert simple JOIN syntax to WHERE-based joins"""
    try:
        # Only handle simple cases to avoid breaking complex queries
        if query.lower().count("join") > 2:
            return query
            
        # Extract components
        select_match = re.search(r'SELECT\s+(.+?)\s+FROM', query, re.IGNORECASE | re.DOTALL)
        if not select_match:
            return query
            
        # Simple pattern: FROM t1 alias1 JOIN t2 alias2 ON condition
        pattern = r'FROM\s+(\w+)\s+(\w+)\s+JOIN\s+(\w+)\s+(\w+)\s+ON\s+([^;]+?)(?:\s+WHERE\s+([^;]+?))?(?:\s+ORDER|\s+GROUP|\s*$)'
        match = re.search(pattern, query, re.IGNORECASE | re.DOTALL)
        
        if match:
            table1, alias1, table2, alias2, join_condition, where_condition = match.groups()
            
            select_clause = select_match.group(1)
            
            # Build WHERE-based query
            new_query = f"SELECT {select_clause}\nFROM {table1} {alias1}, {table2} {alias2}\nWHERE {join_condition}"
            
            if where_condition:
                new_query += f" AND {where_condition.strip()}"
            
            # Add any ORDER BY or GROUP BY from original
            order_match = re.search(r'ORDER\s+BY\s+[^;]+', query, re.IGNORECASE)
            if order_match:
                new_query += f"\n{order_match.group()}"
            
            group_match = re.search(r'GROUP\s+BY\s+[^;]+', query, re.IGNORECASE)
            if group_match:
                new_query += f"\n{group_match.group()}"
            
            return new_query
            
    except Exception:
        pass
        
    return query

def reorder_where_conditions(query: str) -> str:
    """Reorder WHERE conditions to put more selective ones first"""
    try:
        where_match = re.search(r'WHERE\s+(.+?)(?=\s+ORDER|\s+GROUP|\s*$)', query, re.IGNORECASE | re.DOTALL)
        if not where_match:
            return query
            
        where_clause = where_match.group(1).strip()
        
        # Split on AND (simple case)
        if ' and ' in where_clause.lower():
            conditions = [c.strip() for c in re.split(r'\s+and\s+', where_clause, flags=re.IGNORECASE)]
            
            # Sort conditions by selectivity (heuristic)
            def selectivity_score(condition):
                condition_lower = condition.lower()
                # Equality is most selective
                if '=' in condition_lower and 'like' not in condition_lower:
                    return 1
                # Range conditions
                elif any(op in condition_lower for op in ['between', '>', '<']):
                    return 2
                # IN conditions
                elif ' in (' in condition_lower:
                    return 3
                # LIKE conditions
                elif 'like' in condition_lower:
                    return 4
                # Everything else
                else:
                    return 5
            
            # Sort conditions (most selective first)
            sorted_conditions = sorted(conditions, key=selectivity_score)
            
            if sorted_conditions != conditions:
                new_where = ' AND '.join(sorted_conditions)
                return query.replace(where_clause, new_where)
                
    except Exception:
        pass
        
    return query

def test_candidate_generator():
    """Test the candidate generator"""
    test_queries = [
        """SELECT e.emp_id, e.first_name, d.dept_name
           FROM employees e
           JOIN departments d ON e.dept_id = d.dept_id
           WHERE e.salary > 50000 AND e.hire_date >= '2020-01-01'""",
           
        """SELECT e.emp_id, p.proj_name
           FROM employees e
           JOIN projects p ON e.dept_id = p.dept_id
           WHERE p.budget > 100000
           ORDER BY e.salary DESC"""
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n=== TEST QUERY {i} ===")
        print("Original:")
        print(query)
        
        candidates = generate_simple_candidates(query)
        print(f"\nGenerated {len(candidates)} candidates:")
        
        for j, candidate in enumerate(candidates):
            print(f"\nCandidate {j + 1}:")
            print(candidate)

if __name__ == "__main__":
    test_candidate_generator()