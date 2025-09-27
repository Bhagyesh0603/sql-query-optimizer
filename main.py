import argparse
import pandas as pd
import time
from tabulate import tabulate
from rules import apply_rules
from rewriter import generate_join_candidates
from cost_model import get_query_cost
from explain_runner import run_explain
from query_logger import create_query_logs_table as init_db, log_query
import joblib
from ml_optimizer.feature_extraction import extract_features
from ml_optimizer.train_model import train_model_function  # optional
from cost_comparator import CostComparator  # Import our new cost comparator
from query_explainer import QueryExplainer  # Import query difference explainer

def count_joins(query):
    return query.lower().count(' join')

# Initialize query logs DB
init_db()

# Load ML predictor (optional)
try:
    model_data = joblib.load("cost_predictor.joblib")
    cost_model = model_data["model"]
    trained_features = model_data["features"]  # feature names order
    print("✅ ML cost predictor loaded.")
except:
    cost_model = None
    trained_features = []
    print("⚠️ ML cost predictor not found. Predictions will be skipped.")


def main():
    parser = argparse.ArgumentParser(description="SQL Query Optimizer CLI")
    parser.add_argument("--query", type=str, required=True, help="SQL query to optimize")
    args = parser.parse_args()

    original_query = args.query
    print("\n=== ORIGINAL QUERY ===")
    print(original_query)

    # 1️⃣ Apply rules
    suggestions = apply_rules(original_query)
    print("\n--- SUGGESTIONS ---")
    if suggestions:
        for s in suggestions:
            print(" •", s)
    else:
        print("No obvious anti-patterns detected.")

    # 2️⃣ Generate join-order candidates & compare costs with improved system
    print("\n--- GENERATING CANDIDATES AND COMPARING COSTS ---")
    start_time = time.time()
    candidates = generate_join_candidates(original_query)
    end_time = time.time()
    candidate_runtime = end_time - start_time
    
    # Use our improved cost comparator
    comparator = CostComparator()
    candidate_queries = [c for c in candidates if c != original_query]  # Remove duplicates
    
    if candidate_queries:
        results = comparator.compare_queries(original_query, candidate_queries[:5])  # Limit for performance
        
        # Extract best result
        best_name, best_query, best_costs = results[0]
        best_cost = best_costs['best_estimate']
        
        # Get original cost for comparison
        original_cost = None
        for name, query, costs in results:
            if name == "original":
                original_cost = costs['best_estimate']
                break
        
        if original_cost and best_cost < original_cost:
            improvement_pct = ((original_cost - best_cost) / original_cost) * 100
            print(f"\n✅ OPTIMIZATION SUCCESSFUL!")
            print(f"   Best strategy: {best_name}")
            print(f"   Original cost: {original_cost:.2f}")
            print(f"   Optimized cost: {best_cost:.2f}")
            print(f"   Improvement: {improvement_pct:.1f}% better")
        else:
            print(f"\n⚠️ No significant improvement found")
            print(f"   Original cost: {original_cost:.2f}")
            print(f"   Best alternative: {best_cost:.2f}")
            best_query = original_query  # Keep original if no improvement
    else:
        print("   No alternative candidates generated")
        best_query = original_query
        best_cost = comparator.get_best_cost_estimate(original_query)

    print("\n--- BEST OPTIMIZED QUERY ---")
    print(best_query)
    print(f"\nCandidate evaluation runtime: {candidate_runtime:.3f} seconds")

    # 🔍 QUERY DIFFERENCE EXPLANATION
    if best_query != original_query:
        print("\n" + "="*60)
        print("🔍 DETAILED OPTIMIZATION EXPLANATION")
        print("="*60)
        
        explainer = QueryExplainer()
        performance_info = ""
        if original_cost and best_cost < original_cost:
            improvement_pct = ((original_cost - best_cost) / original_cost) * 100
            performance_info = f"{improvement_pct:.1f}% performance improvement"
        
        explanation = explainer.explain_differences(
            original_query, 
            best_query, 
            best_name if 'best_name' in locals() else "optimization",
            performance_info
        )
        
        # Format and display the explanation with proper line breaks
        print()  # Add spacing
        for line in explanation.split('\n'):
            if line.strip():  # Only print non-empty lines
                print(line)
            elif explanation.split('\n').index(line) > 0:  # Add spacing between sections
                print()
        
        print("\n" + "="*60)
        print("--- QUERY DIFF (LINE BY LINE) ---")
        diff_output = explainer.show_side_by_side_diff(original_query, best_query)
        print(diff_output)
        print("="*60)

    # 3️⃣ EXPLAIN JSON for best query
    explain_json = run_explain(best_query)

    # 4️⃣ Final summary
    print("\n--- OPTIMIZATION SUMMARY ---")
    original_features = extract_features(original_query)
    best_features = extract_features(best_query)
    
    print(f"Original query complexity: {original_features['query_complexity']:.1f}")
    print(f"Optimized query complexity: {best_features['query_complexity']:.1f}")
    print(f"Tables involved: {original_features['num_tables']}")
    print(f"JOIN operations: {original_features['num_joins']}")
    print(f"WHERE conditions: {original_features['num_conditions']}")

    # 5️⃣ EXPLAIN summary
    print("\n--- EXECUTION PLAN (BEST QUERY) ---")
    if explain_json:
        plan = explain_json.get("Plan", {})
        print(tabulate([
            ["Node Type", plan.get("Node Type")],
            ["Total Cost", plan.get("Total Cost")],
            ["Rows", plan.get("Plan Rows")],
            ["Execution Time", f"{explain_json.get('Execution Time', 'N/A')} ms"]
        ], tablefmt="grid"))
    else:
        print("EXPLAIN failed.")

    # 6️⃣ Log the query results
    explain_orig = run_explain(original_query)
    original_cost = comparator.get_best_cost_estimate(original_query)
    
    # Extract features for logging
    original_features = extract_features(original_query)
    
    log_query(
        original_query, best_query,
        original_cost, best_cost, candidate_runtime,
        features=original_features,  # Pass features dict
        explain_original=explain_orig, 
        explain_rewritten=explain_json
    )


if __name__ == "__main__":
    main()
