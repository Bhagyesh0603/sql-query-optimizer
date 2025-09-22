import re
import sqlparse
from typing import Dict, Any

def count_joins(query: str) -> int:
    """Count JOIN occurrences in the SQL query."""
    return len(re.findall(r'\b(?:INNER\s+|LEFT\s+|RIGHT\s+|FULL\s+)?JOIN\b', query, re.IGNORECASE))

def count_subqueries(query: str) -> int:
    """Count subqueries in the SQL query."""
    # Count SELECT statements - 1 (for main query)
    return max(0, len(re.findall(r'\bSELECT\b', query, re.IGNORECASE)) - 1)

def count_aggregations(query: str) -> int:
    """Count aggregation functions."""
    agg_functions = ['COUNT', 'SUM', 'AVG', 'MIN', 'MAX', 'GROUP_CONCAT']
    count = 0
    for func in agg_functions:
        # Fixed: Use proper string concatenation instead of f-string with raw string
        pattern = r'\b' + func + r'\s*\('
        count += len(re.findall(pattern, query, re.IGNORECASE))
    return count

def count_conditions(query: str) -> int:
    """Count WHERE conditions."""
    where_match = re.search(r'WHERE\s+(.+?)(?:\s+GROUP|\s+ORDER|\s+LIMIT|\s*$)', query, re.IGNORECASE | re.DOTALL)
    if not where_match:
        return 0
    
    where_clause = where_match.group(1)
    # Count AND/OR operators + 1
    and_count = len(re.findall(r'\bAND\b', where_clause, re.IGNORECASE))
    or_count = len(re.findall(r'\bOR\b', where_clause, re.IGNORECASE))
    return and_count + or_count + 1

def extract_table_count(query: str) -> int:
    """Extract number of distinct tables involved."""
    tables = set()
    
    # FROM clause
    from_match = re.search(r'FROM\s+(\w+)', query, re.IGNORECASE)
    if from_match:
        tables.add(from_match.group(1).lower())
    
    # JOIN clauses
    join_matches = re.findall(r'JOIN\s+(\w+)', query, re.IGNORECASE)
    for table in join_matches:
        tables.add(table.lower())
    
    return len(tables)

def extract_selectivity_features(query: str) -> Dict[str, int]:
    """Extract query selectivity indicators."""
    features = {}
    
    # Range queries
    features['has_between'] = 1 if re.search(r'\bBETWEEN\b', query, re.IGNORECASE) else 0
    features['has_like'] = 1 if re.search(r'\bLIKE\b', query, re.IGNORECASE) else 0
    features['has_in'] = 1 if re.search(r'\bIN\s*\(', query, re.IGNORECASE) else 0
    
    # Comparison operators
    features['comparison_ops'] = len(re.findall(r'[<>=!]+', query))
    
    # DISTINCT
    features['has_distinct'] = 1 if re.search(r'\bDISTINCT\b', query, re.IGNORECASE) else 0
    
    # ORDER BY and GROUP BY
    features['has_order_by'] = 1 if re.search(r'\bORDER\s+BY\b', query, re.IGNORECASE) else 0
    features['has_group_by'] = 1 if re.search(r'\bGROUP\s+BY\b', query, re.IGNORECASE) else 0
    
    # LIMIT
    features['has_limit'] = 1 if re.search(r'\bLIMIT\b', query, re.IGNORECASE) else 0
    
    return features

def estimate_query_complexity(query: str) -> float:
    """Estimate overall query complexity score."""
    num_joins = count_joins(query)
    num_subqueries = count_subqueries(query)
    num_conditions = count_conditions(query)
    num_aggregations = count_aggregations(query)
    
    # Weighted complexity score
    complexity = (
        num_joins * 2.0 +           # JOINs are expensive
        num_subqueries * 3.0 +      # Subqueries are very expensive
        num_conditions * 0.5 +      # Conditions add some cost
        num_aggregations * 1.5      # Aggregations are moderately expensive
    )
    
    return complexity

def extract_features(query: str, explain_json=None) -> Dict[str, Any]:
    """
    Extract comprehensive features for ML model.
    Returns consistent feature set for training and prediction.
    """
    features = {}
    
    # Basic structural features
    features['num_tables'] = extract_table_count(query)
    features['num_joins'] = count_joins(query)
    features['num_subqueries'] = count_subqueries(query)
    features['num_conditions'] = count_conditions(query)
    features['num_aggregations'] = count_aggregations(query)
    features['query_length'] = len(query)
    features['query_complexity'] = estimate_query_complexity(query)
    
    # Selectivity features
    selectivity_features = extract_selectivity_features(query)
    features.update(selectivity_features)
    
    # Parse-based features
    try:
        parsed = sqlparse.parse(query)[0]
        tokens = [t for t in parsed.flatten() if not t.is_whitespace]
        features['num_tokens'] = len(tokens)
        features['num_keywords'] = len([t for t in tokens if t.ttype in sqlparse.tokens.Keyword])
    except:
        features['num_tokens'] = 0
        features['num_keywords'] = 0
    
    # EXPLAIN-based features (if available)
    if explain_json and isinstance(explain_json, dict) and "Plan" in explain_json:
        plan = explain_json["Plan"]
        features['plan_rows'] = plan.get("Plan Rows", 0)
        features['plan_width'] = plan.get("Plan Width", 0)
        features['startup_cost'] = plan.get("Startup Cost", 0.0)
        features['total_cost'] = plan.get("Total Cost", 0.0)
        features['plan_type'] = hash(plan.get("Node Type", "")) % 1000  # Hash node type
    else:
        # Default values when EXPLAIN not available
        features['plan_rows'] = 0
        features['plan_width'] = 0
        features['startup_cost'] = 0.0
        features['total_cost'] = 0.0
        features['plan_type'] = 0
    
    # Derived features
    features['joins_per_table'] = features['num_joins'] / max(1, features['num_tables'])
    features['conditions_per_join'] = features['num_conditions'] / max(1, features['num_joins']) if features['num_joins'] > 0 else 0
    
    return features

if __name__ == "__main__":
    test_queries = [
        "SELECT * FROM employees",
        "SELECT e.*, d.dept_name FROM employees e JOIN departments d ON e.dept_id = d.dept_id WHERE e.salary > 50000",
        """SELECT e.emp_id, d.dept_name, COUNT(*) as emp_count 
           FROM employees e 
           JOIN departments d ON e.dept_id = d.dept_id 
           WHERE e.hire_date BETWEEN '2020-01-01' AND '2023-01-01' 
           GROUP BY e.emp_id, d.dept_name 
           ORDER BY emp_count DESC"""
    ]
    
    for i, query in enumerate(test_queries):
        print(f"\n=== Query {i+1} Features ===")
        features = extract_features(query)
        for key, value in features.items():
            print(f"{key}: {value}")
