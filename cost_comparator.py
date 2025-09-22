#!/usr/bin/env python3
"""
Improved cost comparison system for SQL optimizer
"""
import time
from typing import Dict, List, Tuple, Optional
from explain_runner import run_explain
from cost_model import get_query_cost, load_cost_model
from ml_optimizer.feature_extraction import extract_features
import pandas as pd
import numpy as np

class CostComparator:
    """Handles cost comparison between query candidates with proper error handling"""
    
    def __init__(self):
        self.model, self.trained_features = load_cost_model()
        self.use_ml = self.model is not None
        
    def get_explain_cost(self, query: str) -> Optional[float]:
        """Get cost from EXPLAIN plan"""
        try:
            explain_result = run_explain(query)
            if explain_result and "Plan" in explain_result:
                plan = explain_result["Plan"]
                return float(plan.get("Total Cost", 0))
        except Exception as e:
            print(f"⚠️ EXPLAIN failed: {e}")
        return None
    
    def get_explain_runtime(self, query: str) -> Optional[float]:
        """Get actual runtime from EXPLAIN ANALYZE"""
        try:
            explain_result = run_explain(query)
            if explain_result and "Execution Time" in explain_result:
                return float(explain_result["Execution Time"])
            elif explain_result and "Plan" in explain_result:
                plan = explain_result["Plan"]
                actual_time = plan.get("Actual Total Time")
                if actual_time:
                    return float(actual_time)
        except Exception as e:
            print(f"⚠️ EXPLAIN ANALYZE failed: {e}")
        return None
    
    def get_ml_prediction(self, query: str) -> Optional[float]:
        """Get ML model prediction"""
        if not self.use_ml:
            return None
            
        try:
            features = extract_features(query, None)
            
            if self.trained_features:
                # Use specific feature order
                feature_vector = [features.get(f, 0) for f in self.trained_features]
                X = pd.DataFrame([feature_vector], columns=self.trained_features)
            else:
                # Use all features
                X = pd.DataFrame([features])
            
            prediction = self.model.predict(X)[0]
            return float(prediction) if not np.isnan(prediction) else None
            
        except Exception as e:
            print(f"⚠️ ML prediction failed: {e}")
            return None
    
    def get_heuristic_cost(self, query: str) -> float:
        """Get heuristic cost (always works as fallback)"""
        return get_query_cost(query)
    
    def get_comprehensive_cost(self, query: str) -> Dict[str, float]:
        """Get all available cost estimates for a query"""
        costs = {}
        
        # Get EXPLAIN cost (DB estimate)
        explain_cost = self.get_explain_cost(query)
        if explain_cost is not None:
            costs['db_estimate'] = explain_cost
        
        # Get EXPLAIN runtime (actual execution)
        runtime = self.get_explain_runtime(query)
        if runtime is not None:
            costs['actual_runtime'] = runtime
        
        # Get ML prediction
        ml_cost = self.get_ml_prediction(query)
        if ml_cost is not None:
            costs['ml_prediction'] = ml_cost
        
        # Always get heuristic (fallback)
        costs['heuristic'] = self.get_heuristic_cost(query)
        
        return costs
    
    def get_best_cost_estimate(self, query: str) -> float:
        """Get the best available cost estimate"""
        costs = self.get_comprehensive_cost(query)
        
        # Priority: actual runtime > DB estimate > ML prediction > heuristic
        if 'actual_runtime' in costs:
            return costs['actual_runtime']
        elif 'db_estimate' in costs:
            return costs['db_estimate']
        elif 'ml_prediction' in costs:
            return costs['ml_prediction']
        else:
            return costs['heuristic']
    
    def compare_queries(self, original: str, candidates: List[str]) -> List[Tuple[str, Dict[str, float]]]:
        """Compare original query with candidates, return sorted by best cost"""
        all_queries = [("original", original)] + [(f"candidate_{i+1}", q) for i, q in enumerate(candidates)]
        results = []
        
        print("\n🔍 COMPREHENSIVE COST ANALYSIS")
        print("=" * 60)
        
        for name, query in all_queries:
            costs = self.get_comprehensive_cost(query)
            best_cost = self.get_best_cost_estimate(query)
            costs['best_estimate'] = best_cost
            
            results.append((name, query, costs))
            
            print(f"\n{name.upper()}:")
            if 'actual_runtime' in costs:
                print(f"  ✅ Actual Runtime: {costs['actual_runtime']:.3f} ms")
            if 'db_estimate' in costs:
                print(f"  📊 DB Estimate: {costs['db_estimate']:.2f}")
            if 'ml_prediction' in costs:
                print(f"  🤖 ML Prediction: {costs['ml_prediction']:.2f}")
            print(f"  📋 Heuristic: {costs['heuristic']:.2f}")
            print(f"  🎯 Best Estimate: {costs['best_estimate']:.2f}")
        
        # Sort by best estimate
        results.sort(key=lambda x: x[2]['best_estimate'])
        
        print("\n🏆 RANKING (Best to Worst):")
        print("=" * 60)
        
        for i, (name, query, costs) in enumerate(results, 1):
            improvement = ""
            if i > 1:  # Compare to best (first result)
                best_cost = results[0][2]['best_estimate']
                current_cost = costs['best_estimate']
                if current_cost > best_cost:
                    pct_worse = ((current_cost - best_cost) / best_cost) * 100
                    improvement = f" (+{pct_worse:.1f}% worse)"
                elif current_cost < best_cost:
                    pct_better = ((best_cost - current_cost) / best_cost) * 100
                    improvement = f" (-{pct_better:.1f}% better)"
            
            print(f"{i}. {name}: {costs['best_estimate']:.2f}{improvement}")
        
        return results


def test_cost_comparator():
    """Test the cost comparator with sample queries"""
    comparator = CostComparator()
    
    # Test with a simple query
    original_query = """
    SELECT e.emp_id, e.first_name, e.last_name, d.dept_name
    FROM employees e
    JOIN departments d ON e.dept_id = d.dept_id
    WHERE e.salary > 50000
    """
    
    # Generate some simple candidates (without complex reordering for now)
    candidates = [
        # Add index hint
        """
        SELECT /*+ USE_INDEX(e, idx_emp_dept) */ e.emp_id, e.first_name, e.last_name, d.dept_name
        FROM employees e
        JOIN departments d ON e.dept_id = d.dept_id
        WHERE e.salary > 50000
        """,
        
        # Different join syntax
        """
        SELECT e.emp_id, e.first_name, e.last_name, d.dept_name
        FROM employees e, departments d
        WHERE e.dept_id = d.dept_id AND e.salary > 50000
        """
    ]
    
    results = comparator.compare_queries(original_query, candidates)
    
    return results


if __name__ == "__main__":
    test_cost_comparator()