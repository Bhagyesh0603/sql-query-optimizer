# cost_model.py
import os
import joblib
import numpy as np
from explain_runner import run_explain

# -------------------------------
# Load ML cost model
# -------------------------------

def load_cost_model(model_path: str = "cost_predictor.joblib"):
    """
    Loads a trained ML model for query cost prediction.
    Returns: (model, trained_features)
    """
    if not os.path.exists(model_path):
        print("⚠️ ML model file not found, using EXPLAIN fallback.")
        return None, []

    try:
        md = joblib.load(model_path)
        if isinstance(md, dict):
            model = md.get("model")
            features = md.get("features", [])
            print(f"✅ ML model loaded with {len(features)} features")
        else:
            model = md
            features = []
            print("✅ ML model loaded (legacy format)")
        return model, features
    except Exception as e:
        print(f"⚠️ Failed to load ML model: {e}")
        return None, []

# -------------------------------
# Query cost estimation
# -------------------------------

def get_query_cost(query: str) -> float:
    """
    Returns the estimated cost of a SQL query using EXPLAIN or heuristics.
    """
    # Try EXPLAIN first
    explain_json = run_explain(query)
    
    if explain_json and isinstance(explain_json, dict):
        try:
            plan = explain_json.get("Plan", {})
            total_cost = plan.get("Total Cost")
            if total_cost is not None and not np.isnan(total_cost):
                return float(total_cost)
        except Exception as e:
            print(f"⚠️ Failed to parse EXPLAIN JSON: {e}")

    # Fallback to enhanced heuristic
    return calculate_heuristic_cost(query)

def calculate_heuristic_cost(query: str) -> float:
    """Enhanced heuristic cost calculation."""
    query_lower = query.lower()
    
    # Table scan costs (estimated rows * scan cost)
    table_costs = {
        "employees": 500 * 1.0,      # 500 rows
        "departments": 10 * 1.0,     # 10 rows  
        "salaries": 1000 * 1.0,      # 1000 rows
        "projects": 50 * 1.0,        # 50 rows
        "patients": 200 * 1.0,       # 200 rows
        "doctors": 50 * 1.0,         # 50 rows
        "visits": 1000 * 1.0,        # 1000 rows
        "appointments": 1000 * 1.0   # 1000 rows
    }
    
    base_cost = 0.0
    
    # Add table scan costs
    for table, cost in table_costs.items():
        if table in query_lower:
            base_cost += cost
    
    # JOIN costs (exponential with number of joins)
    num_joins = query_lower.count("join")
    if num_joins > 0:
        base_cost *= (1.5 ** num_joins)  # Each join increases cost by 50%
    
    # WHERE clause selectivity
    if "where" in query_lower:
        # Selective filters reduce cost
        if any(op in query_lower for op in ["=", "between", "in ("]):
            base_cost *= 0.3  # Very selective
        elif any(op in query_lower for op in [">", "<", ">=", "<="]):
            base_cost *= 0.6  # Moderately selective
        else:
            base_cost *= 0.8  # Less selective
    
    # Aggregation costs
    agg_functions = ["count(", "sum(", "avg(", "min(", "max("]
    for func in agg_functions:
        if func in query_lower:
            base_cost *= 1.2
    
    # GROUP BY cost
    if "group by" in query_lower:
        base_cost *= 1.5
    
    # ORDER BY cost  
    if "order by" in query_lower:
        base_cost *= 1.3
    
    # Subquery penalty
    subquery_count = query_lower.count("select") - 1
    if subquery_count > 0:
        base_cost *= (2.0 ** subquery_count)
    
    # Add some variance based on query complexity
    complexity_bonus = len(query) / 100.0
    base_cost += complexity_bonus
    
    return max(1.0, base_cost)  # Minimum cost of 1

# -------------------------------
# Optional: test CLI
# -------------------------------
if __name__ == "__main__":
    test_query = """
    SELECT e.emp_id, e.first_name, e.last_name, e.dept_id, e.hire_date, e.salary
    FROM employees e
    JOIN departments d ON e.dept_id = d.dept_id
    WHERE e.hire_date BETWEEN '2018-01-01' AND '2018-12-31';
    """

    ml_model, features = load_cost_model()
    cost = get_query_cost(test_query)

    print("Query cost:", cost)
