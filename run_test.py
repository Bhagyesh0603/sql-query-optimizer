#!/usr/bin/env python3
"""
Simple test runner for the SQL Optimizer
"""

import subprocess
import sys

# Test queries based on your schema
TEST_QUERIES = [
    # Simple employee query
    "SELECT emp_id, first_name, last_name FROM employees WHERE salary > 50000",
    
    # Employee-Department join
    """SELECT e.emp_id, e.first_name, e.last_name, d.dept_name
       FROM employees e
       JOIN departments d ON e.dept_id = d.dept_id
       WHERE e.salary > 60000""",
    
    # Three-table join
    """SELECT e.emp_id, e.first_name, d.dept_name, p.proj_name
       FROM employees e
       JOIN departments d ON e.dept_id = d.dept_id
       JOIN projects p ON d.dept_id = p.dept_id
       WHERE e.hire_date >= '2018-01-01' AND p.budget > 150000""",
    
    # Complex four-table join
    """SELECT e.emp_id, e.first_name, d.dept_name, p.proj_name, s.amount
       FROM employees e
       JOIN departments d ON e.dept_id = d.dept_id
       JOIN projects p ON d.dept_id = p.dept_id
       JOIN salaries s ON e.emp_id = s.emp_id
       WHERE s.from_date <= '2020-01-01' AND p.budget > 100000"""
]

def run_optimizer_test(query, test_num):
    """Run optimizer CLI with a test query"""
    print(f"\n{'='*80}")
    print(f"TEST {test_num}: RUNNING OPTIMIZER")
    print(f"{'='*80}")
    print("Query:")
    print(query)
    print(f"{'='*80}")
    
    try:
        # Run the optimizer CLI
        cmd = [sys.executable, "optimizer_cli.py", "--query", query, "--verbose"]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        print("STDOUT:")
        print(result.stdout)
        
        if result.stderr:
            print("STDERR:")
            print(result.stderr)
            
        print(f"Exit code: {result.returncode}")
        
    except subprocess.TimeoutExpired:
        print("❌ Test timed out (30 seconds)")
    except Exception as e:
        print(f"❌ Test failed: {e}")

def main():
    print("🚀 STARTING SQL OPTIMIZER CLI TESTS")
    
    # Run feature extraction test first
    print("\n" + "="*80)
    print("RUNNING FEATURE EXTRACTION TEST")
    print("="*80)
    try:
        subprocess.run([sys.executable, "test_optimizer.py"], check=True, timeout=60)
        print("✅ Feature extraction test completed")
    except Exception as e:
        print(f"❌ Feature extraction test failed: {e}")
    
    # Run CLI tests with actual queries
    for i, query in enumerate(TEST_QUERIES, 1):
        run_optimizer_test(query.strip(), i)
    
    print(f"\n{'='*80}")
    print("🏁 ALL TESTS COMPLETED")
    print(f"{'='*80}")

if __name__ == "__main__":
    main()
