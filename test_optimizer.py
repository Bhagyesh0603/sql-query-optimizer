#!/usr/bin/env python3
"""
Test script for SQL Query Optimizer with proper schema queries
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ml_optimizer.feature_extraction import extract_features
from cost_model import get_query_cost, load_cost_model
from optimizer.candidate_generator import generate_candidates

def test_feature_extraction():
    """Test feature extraction with sample queries"""
    print("=" * 60)
    print("TESTING FEATURE EXTRACTION")
    print("=" * 60)
    
    test_queries = [
        # Simple query
        "SELECT * FROM employees WHERE salary > 50000",
        
        # 2-table join
        """SELECT e.emp_id, e.first_name, e.last_name, d.dept_name
           FROM employees e
           JOIN departments d ON e.dept_id = d.dept_id
           WHERE e.salary > 60000""",
        
        # 3-table join with complex conditions
        """SELECT e.emp_id, e.first_name, d.dept_name, p.proj_name, p.budget
           FROM employees e
           JOIN departments d ON e.dept_id = d.dept_id
           JOIN projects p ON d.dept_id = p.dept_id
           WHERE e.salary BETWEEN 50000 AND 100000
           AND p.budget > 150000""",
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n--- Test Query {i} ---")
        print(query.strip())
        try:
            features = extract_features(query)
            print("\nExtracted Features:")
            for key, value in sorted(features.items()):
                print(f"  {key}: {value}")
            print(f"  Total features: {len(features)}")
        except Exception as e:
            print(f"❌ Feature extraction failed: {e}")

def test_candidate_generation():
    """Test candidate generation"""
    print("\n" + "=" * 60)
    print("TESTING CANDIDATE GENERATION")
    print("=" * 60)
    
    test_query = """
    SELECT e.emp_id, e.first_name, e.last_name, d.dept_name, p.proj_name
    FROM employees e
    JOIN departments d ON e.dept_id = d.dept_id
    JOIN projects p ON d.dept_id = p.dept_id
    WHERE e.salary > 70000 AND p.budget > 200000
    """
    
    print("Original Query:")
    print(test_query.strip())
    
    try:
        candidates = generate_candidates(test_query.strip(), limit=6, deterministic=True)
        
        print(f"\nGenerated {len(candidates)} candidates:")
        for i, (strategy, candidate_query) in enumerate(candidates):
            print(f"\n{i+1}. Strategy: {strategy}")
            print(f"   Query: {candidate_query[:100]}{'...' if len(candidate_query) > 100 else ''}")
    except Exception as e:
        print(f"❌ Candidate generation failed: {e}")

def test_cost_prediction():
    """Test cost prediction pipeline"""
    print("\n" + "=" * 60)
    print("TESTING COST PREDICTION")
    print("=" * 60)
    
    test_query = """
    SELECT e.emp_id, e.first_name, e.last_name, d.dept_name
    FROM employees e
    JOIN departments d ON e.dept_id = d.dept_id
    WHERE e.salary > 60000
    """
    
    print("Test Query:")
    print(test_query.strip())
    
    try:
        # Test individual cost prediction
        cost = get_query_cost(test_query)
        print(f"\nHeuristic cost: {cost}")
        
        # Test feature extraction
        features = extract_features(test_query)
        print(f"Features extracted: {len(features)}")
        print(f"Sample features: {dict(list(features.items())[:5])}")
        
        print("✅ Cost prediction components working")
        
    except Exception as e:
        print(f"❌ Cost prediction failed: {e}")

def main():
    """Run all tests"""
    print("🚀 STARTING SQL OPTIMIZER TESTS")
    print("=" * 60)
    
    try:
        test_feature_extraction()
        test_candidate_generation() 
        test_cost_prediction()
        
        print("\n" + "=" * 60)
        print("✅ ALL TESTS COMPLETED")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Test suite failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
