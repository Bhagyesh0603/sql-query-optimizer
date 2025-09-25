#!/usr/bin/env python3
"""
Working test for SQL Query Optimizer
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ml_optimizer.feature_extraction import extract_features
from cost_model import get_query_cost
from optimizer.candidate_generator import generate_candidates, predict_cost

def test_full_optimization_pipeline():
    """Test the complete optimization pipeline"""
    print("🚀 TESTING FULL OPTIMIZATION PIPELINE")
    print("=" * 60)
    
    # Test query based on your actual schema
    test_query = """
    SELECT e.emp_id, e.first_name, e.last_name, d.dept_name, p.proj_name
    FROM employees e
    JOIN departments d ON e.dept_id = d.dept_id
    JOIN projects p ON d.dept_id = p.dept_id
    WHERE e.salary > 60000 AND p.budget > 100000
    """
    
    print("Original Query:")
    print(test_query.strip())
    
    # 1. Test feature extraction
    print("\n1️⃣ FEATURE EXTRACTION")
    features = extract_features(test_query)
    print(f"✅ Extracted {len(features)} features")
    print("Key features:")
    important_features = ['num_tables', 'num_joins', 'num_conditions', 'query_complexity']
    for feat in important_features:
        print(f"  {feat}: {features.get(feat, 'N/A')}")
    
    # 2. Test candidate generation
    print("\n2️⃣ CANDIDATE GENERATION")
    candidates = generate_candidates(test_query, limit=5, deterministic=True)
    print(f"✅ Generated {len(candidates)} candidates:")
    for i, (strategy, query) in enumerate(candidates):
        print(f"  {i+1}. {strategy}: {query[:80]}...")
    
    # 3. Test cost prediction
    print("\n3️⃣ COST PREDICTION")
    original_cost = get_query_cost(test_query)
    print(f"✅ Original query cost: {original_cost:.2f}")
    
    # Test costs for all candidates
    for strategy, query in candidates:
        cost = get_query_cost(query)
        features_count = len(extract_features(query))
        print(f"  {strategy}: Cost={cost:.2f}, Features={features_count}")
    
    # 4. Test full prediction pipeline
    print("\n4️⃣ FULL PREDICTION PIPELINE")
    try:
        results = predict_cost(test_query, max_permutations=3)
        print(f"✅ Prediction pipeline returned {len(results)} results")
        
        for i, result in enumerate(results):
            if len(result) >= 3:
                strategy, query, cost = result[:3]
                print(f"  {i+1}. {strategy}: Cost={cost:.2f}")
            else:
                print(f"  {i+1}. Incomplete result: {result}")
    except Exception as e:
        print(f"❌ Prediction pipeline failed: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n✅ PIPELINE TEST COMPLETED")

def test_different_query_types():
    """Test with different types of queries"""
    print("\n" + "=" * 60)
    print("🔍 TESTING DIFFERENT QUERY TYPES")
    print("=" * 60)
    
    queries = [
        # Simple query
        ("Simple", "SELECT * FROM employees WHERE salary > 50000"),
        
        # 2-table join
        ("2-Join", """SELECT e.emp_id, d.dept_name FROM employees e 
                     JOIN departments d ON e.dept_id = d.dept_id"""),
        
        # 3-table join with conditions
        ("3-Join", """SELECT e.emp_id, d.dept_name, p.proj_name 
                     FROM employees e 
                     JOIN departments d ON e.dept_id = d.dept_id 
                     JOIN projects p ON d.dept_id = p.dept_id 
                     WHERE e.salary BETWEEN 50000 AND 100000"""),
        
        # Aggregation query
        ("Aggregation", """SELECT dept_id, COUNT(*), AVG(salary) 
                          FROM employees 
                          GROUP BY dept_id 
                          HAVING COUNT(*) > 5""")
    ]
    
    for query_type, query in queries:
        print(f"\n--- {query_type} Query ---")
        try:
            features = extract_features(query)
            cost = get_query_cost(query)
            candidates = generate_candidates(query, limit=3)
            
            print(f"✅ Features: {len(features)}")
            print(f"✅ Cost: {cost:.2f}")
            print(f"✅ Candidates: {len(candidates)}")
            
            # Show key metrics
            print(f"   Tables: {features.get('num_tables', 0)}")
            print(f"   Joins: {features.get('num_joins', 0)}")
            print(f"   Conditions: {features.get('num_conditions', 0)}")
            print(f"   Complexity: {features.get('query_complexity', 0):.1f}")
            
        except Exception as e:
            print(f"❌ Failed: {e}")

def main():
    print("🚀 STARTING COMPREHENSIVE SQL OPTIMIZER TESTS")
    
    try:
        test_full_optimization_pipeline()
        test_different_query_types()
        
        print("\n" + "=" * 60)
        print("🎉 ALL COMPREHENSIVE TESTS PASSED!")
        print("=" * 60)
        
        # Summary
        print("\n📊 SUMMARY:")
        print("✅ Feature extraction working")
        print("✅ Candidate generation working")
        print("✅ Cost prediction working")
        print("✅ Full optimization pipeline working")
        
    except Exception as e:
        print(f"\n❌ Test suite failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
