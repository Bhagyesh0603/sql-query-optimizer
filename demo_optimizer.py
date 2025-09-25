#!/usr/bin/env python3
"""
Demo script showing SQL Query Optimizer in action
"""
from optimizer.candidate_generator import predict_cost
from ml_optimizer.feature_extraction import extract_features

def demo_optimization():
    """Demonstrate SQL query optimization"""
    print("🚀 SQL QUERY OPTIMIZER DEMO")
    print("=" * 50)
    
    # Demo query based on your actual schema
    query = """
    SELECT e.emp_id, e.first_name, e.last_name, 
           d.dept_name, p.proj_name, p.budget
    FROM employees e
    JOIN departments d ON e.dept_id = d.dept_id
    JOIN projects p ON d.dept_id = p.dept_id
    WHERE e.hire_date >= '2018-01-01' 
    AND p.budget > 150000
    ORDER BY p.budget DESC
    """
    
    print("Original Query:")
    print(query.strip())
    print("\n" + "=" * 50)
    
    # Show original query analysis
    print("📊 ORIGINAL QUERY ANALYSIS:")
    features = extract_features(query)
    print(f"  • Tables involved: {features['num_tables']}")
    print(f"  • JOIN operations: {features['num_joins']}")
    print(f"  • WHERE conditions: {features['num_conditions']}")
    print(f"  • Query complexity: {features['query_complexity']:.1f}")
    print(f"  • Has ORDER BY: {'Yes' if features['has_order_by'] else 'No'}")
    print(f"  • Has BETWEEN: {'Yes' if features['has_between'] else 'No'}")
    
    print("\n🔄 GENERATING OPTIMIZED CANDIDATES...")
    
    # Get optimization results
    try:
        results = predict_cost(query, max_permutations=5)
        
        print(f"\n✅ Generated {len(results)} optimization candidates:")
        print("=" * 50)
        
        for i, (strategy, opt_query, cost) in enumerate(results):
            print(f"\n{i+1}. Strategy: {strategy}")
            print(f"   Predicted Cost: {cost:.2f}")
            print(f"   Query Preview: {opt_query[:100]}...")
            
        # Show best result
        if results:
            best_strategy, best_query, best_cost = results[0]
            original_cost = results[0][2] if results[0][0] == 'original' else cost
            
            print("\n🏆 OPTIMIZATION RESULT:")
            print("=" * 50)
            print(f"Best Strategy: {best_strategy}")
            print(f"Estimated Cost: {best_cost:.2f}")
            
            if len(results) > 1:
                improvement = ((results[-1][2] - best_cost) / results[-1][2] * 100) if results[-1][2] > 0 else 0
                print(f"Potential Improvement: {improvement:.1f}%")
            
            print(f"\nOptimized Query:")
            print(best_query)
            
    except Exception as e:
        print(f"❌ Optimization failed: {e}")

if __name__ == "__main__":
    demo_optimization()
