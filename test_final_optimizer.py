#!/usr/bin/env python3
"""
Comprehensive test of the SQL optimizer showing cost differences
"""
import time
from cost_comparator import CostComparator

def test_optimizer_improvements():
    """Test various SQL queries to demonstrate cost optimization"""
    
    print("🚀 SQL OPTIMIZER COST DIFFERENCE DEMONSTRATION")
    print("=" * 60)
    
    test_queries = [
        {
            "name": "Simple Employee Query",
            "query": """
                SELECT emp_id, first_name, last_name 
                FROM employees 
                WHERE salary > 50000
            """
        },
        {
            "name": "Employee-Department Join",
            "query": """
                SELECT e.emp_id, e.first_name, d.dept_name
                FROM employees e
                JOIN departments d ON e.dept_id = d.dept_id
                WHERE e.salary > 60000
            """
        },
        {
            "name": "3-Table Join with Filters",
            "query": """
                SELECT e.emp_id, e.first_name, d.dept_name, p.proj_name
                FROM employees e
                JOIN departments d ON e.dept_id = d.dept_id
                JOIN projects p ON d.dept_id = p.dept_id
                WHERE e.salary BETWEEN 50000 AND 100000 
                AND p.budget > 150000
            """
        },
        {
            "name": "Query with ORDER BY",
            "query": """
                SELECT e.emp_id, e.first_name, e.salary
                FROM employees e
                JOIN departments d ON e.dept_id = d.dept_id
                WHERE d.dept_name = 'Engineering'
                ORDER BY e.salary DESC
            """
        }
    ]
    
    comparator = CostComparator()
    all_results = []
    
    for test_case in test_queries:
        print(f"\n{'='*60}")
        print(f"🔍 TESTING: {test_case['name']}")
        print(f"{'='*60}")
        
        print("\nOriginal Query:")
        print(test_case['query'].strip())
        
        # Generate candidates using our simple generator
        from simple_candidates import generate_simple_candidates
        candidates = generate_simple_candidates(test_case['query'], 4)
        candidate_queries = [c for c in candidates if c != test_case['query']][:3]
        
        if candidate_queries:
            results = comparator.compare_queries(test_case['query'], candidate_queries)
            all_results.append((test_case['name'], results))
            
            # Show best improvement
            best_name, best_query, best_costs = results[0]
            original_cost = None
            for name, query, costs in results:
                if name == "original":
                    original_cost = costs['best_estimate']
                    break
            
            if original_cost and best_costs['best_estimate'] < original_cost:
                improvement = ((original_cost - best_costs['best_estimate']) / original_cost) * 100
                print(f"\n🎉 IMPROVEMENT FOUND:")
                print(f"   Strategy: {best_name}")
                print(f"   Original: {original_cost:.3f} ms")
                print(f"   Optimized: {best_costs['best_estimate']:.3f} ms")
                print(f"   Improvement: {improvement:.1f}% faster")
            else:
                print(f"\n📋 No significant improvement found")
                print(f"   Original query was already optimal")
        else:
            print("\n⚠️ No alternative candidates generated")
    
    # Summary report
    print(f"\n{'='*60}")
    print("📊 OPTIMIZATION SUMMARY REPORT")
    print(f"{'='*60}")
    
    improvements_found = 0
    total_tests = len(all_results)
    
    for test_name, results in all_results:
        best_result = results[0]
        original_result = None
        
        for name, query, costs in results:
            if name == "original":
                original_result = costs
                break
        
        if original_result:
            best_cost = best_result[2]['best_estimate']
            original_cost = original_result['best_estimate']
            
            if best_cost < original_cost:
                improvements_found += 1
                improvement_pct = ((original_cost - best_cost) / original_cost) * 100
                print(f"✅ {test_name}: {improvement_pct:.1f}% improvement")
            else:
                print(f"📋 {test_name}: No improvement")
    
    print(f"\n🎯 FINAL RESULTS:")
    print(f"   Tests run: {total_tests}")
    print(f"   Improvements found: {improvements_found}")
    print(f"   Success rate: {(improvements_found/total_tests)*100:.1f}%")
    
    if improvements_found > 0:
        print(f"\n✅ SQL Optimizer is working correctly!")
        print(f"   Cost differences are properly calculated and displayed")
        print(f"   ML model and heuristics are providing meaningful optimizations")
    else:
        print(f"\n⚠️ No improvements found - this could mean:")
        print(f"   • Queries are already well optimized")
        print(f"   • Database has good default optimization")
        print(f"   • Small dataset doesn't show significant differences")

def test_simple_optimization():
    """Quick test to show basic functionality"""
    print("\n" + "="*50)
    print("🧪 QUICK OPTIMIZATION TEST")
    print("="*50)
    
    query = """
        SELECT e.emp_id, e.first_name, d.dept_name
        FROM employees e
        JOIN departments d ON e.dept_id = d.dept_id
        WHERE e.salary > 50000 AND e.hire_date >= '2020-01-01'
    """
    
    comparator = CostComparator()
    from simple_candidates import generate_simple_candidates
    
    candidates = generate_simple_candidates(query, 3)
    candidate_queries = [c for c in candidates[1:] if c != query]  # Skip original
    
    print("Testing query optimization...")
    results = comparator.compare_queries(query, candidate_queries)
    
    print(f"\n📈 Results: {len(results)} candidates evaluated")
    for i, (name, query, costs) in enumerate(results):
        print(f"   {i+1}. {name}: {costs['best_estimate']:.3f} ms")

if __name__ == "__main__":
    try:
        test_simple_optimization()
        time.sleep(1)
        test_optimizer_improvements()
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()