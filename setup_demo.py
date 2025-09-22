#!/usr/bin/env python3
"""
SQL Query Optimizer - Setup and Demo Script

This script helps you get started with the SQL Query Optimizer by:
1. Setting up the database with sample data
2. Training the ML model
3. Running example optimizations
4. Demonstrating key features

Usage: python setup_demo.py
"""

import sys
import os
import time
from typing import List, Dict

def check_dependencies():
    """Check if all required dependencies are installed"""
    print("🔍 Checking dependencies...")
    
    required_packages = [
        'psycopg2',
        'pandas', 
        'numpy',
        'sklearn',
        'sqlparse',
        'tabulate',
        'joblib'
    ]
    
    missing = []
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
            print(f"  ✅ {package}")
        except ImportError:
            print(f"  ❌ {package}")
            missing.append(package)
    
    if missing:
        print(f"\n⚠️ Missing packages: {', '.join(missing)}")
        print("Please install with: pip install -r requirements.txt")
        return False
    
    print("✅ All dependencies found!")
    return True

def setup_database():
    """Set up database connection and sample data"""
    print("\n🗄️ Setting up database...")
    
    try:
        from db import get_connection, test_connection
        
        # Test connection
        print("  Testing database connection...")
        test_connection()
        print("  ✅ Database connection successful")
        
        # Check if we have sample data
        conn = get_connection()
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM employees")
            employee_count = cur.fetchone()[0]
            
            if employee_count > 0:
                print(f"  ✅ Found {employee_count} employees in database")
            else:
                print("  ⚠️ No sample data found")
                print("  💡 Consider running: python dummy_data.py")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Database setup failed: {e}")
        print("  💡 Make sure PostgreSQL is running and update db.py configuration")
        return False

def initialize_ml_model():
    """Initialize or train the ML model"""
    print("\n🤖 Setting up ML model...")
    
    try:
        import joblib
        from ml_optimizer.train_model import train_model_function
        
        # Check if model exists
        if os.path.exists('cost_predictor.joblib'):
            model_data = joblib.load('cost_predictor.joblib')
            print("  ✅ Found existing ML model")
            print(f"     Features: {len(model_data.get('features', []))}")
            print(f"     Model type: {type(model_data.get('model', 'Unknown')).__name__}")
        else:
            print("  📚 Training new ML model...")
            train_model_function()
            print("  ✅ ML model trained and saved")
        
        return True
        
    except Exception as e:
        print(f"  ⚠️ ML model setup issue: {e}")
        print("  💡 Model will use fallback cost estimation")
        return False

def run_example_optimizations():
    """Run example queries to demonstrate the optimizer"""
    print("\n🚀 Running example optimizations...")
    
    example_queries = [
        {
            "name": "Simple SELECT with WHERE",
            "query": "SELECT * FROM employees WHERE salary > 50000",
            "description": "Basic optimization showing SELECT * and index recommendations"
        },
        {
            "name": "Query with ORDER BY",
            "query": "SELECT first_name, last_name, salary FROM employees WHERE salary > 60000 ORDER BY salary DESC",
            "description": "Demonstrates ORDER BY analysis and potential LIMIT suggestion"
        },
        {
            "name": "Complex query with potential issues",
            "query": "SELECT DISTINCT first_name FROM employees WHERE UPPER(first_name) LIKE '%JOHN%'",
            "description": "Shows function in WHERE clause and DISTINCT analysis"
        }
    ]
    
    try:
        from main import main as run_optimizer
        import sys
        
        for i, example in enumerate(example_queries, 1):
            print(f"\n--- Example {i}: {example['name']} ---")
            print(f"Description: {example['description']}")
            print(f"Query: {example['query']}")
            print()
            
            # Temporarily modify sys.argv to run optimizer
            original_argv = sys.argv.copy()
            sys.argv = ['main.py', '--query', example['query']]
            
            try:
                run_optimizer()
            except SystemExit:
                pass  # Expected from argparse
            except Exception as e:
                print(f"  ⚠️ Error running optimizer: {e}")
            finally:
                sys.argv = original_argv
            
            print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"  ❌ Failed to run examples: {e}")
        return False

def demonstrate_enhanced_features():
    """Demonstrate enhanced features"""
    print("\n✨ Demonstrating enhanced features...")
    
    try:
        from enhanced_rules import apply_enhanced_rules, format_suggestions
        from pattern_detector import QueryPatternDetector, QueryComplexityAnalyzer
        
        test_query = "SELECT * FROM employees WHERE UPPER(first_name) LIKE '%JOHN%' ORDER BY salary"
        
        print(f"Test query: {test_query}")
        print()
        
        # Enhanced rules
        print("🔧 Enhanced Rules Analysis:")
        suggestions = apply_enhanced_rules(test_query)
        if suggestions:
            print(format_suggestions(suggestions)[:500] + "..." if len(format_suggestions(suggestions)) > 500 else format_suggestions(suggestions))
        
        # Pattern detection
        print("\n🔍 Pattern Detection:")
        detector = QueryPatternDetector()
        patterns = detector.analyze_query(test_query)
        if patterns:
            for pattern in patterns[:2]:  # Show first 2 patterns
                print(f"  ⚠️ {pattern.description}")
        else:
            print("  ✅ No problematic patterns detected")
        
        # Complexity analysis
        print("\n📊 Complexity Analysis:")
        complexity = QueryComplexityAnalyzer.calculate_complexity_score(test_query)
        print(f"  Level: {complexity['complexity_level']}")
        print(f"  Score: {complexity['overall_score']}/100")
        
        return True
        
    except Exception as e:
        print(f"  ⚠️ Enhanced features demo failed: {e}")
        return False

def print_next_steps():
    """Print next steps for the user"""
    print("\n🎯 Next Steps:")
    print("=" * 50)
    print()
    print("1. 🔧 Basic Usage:")
    print("   python main.py --query \"SELECT * FROM employees WHERE salary > 50000\"")
    print()
    print("2. 🚀 Enhanced Analysis:")
    print("   python enhanced_demo.py --interactive")
    print("   python enhanced_demo.py --demo")
    print()
    print("3. 📊 Benchmarking:")
    print("   python benchmark_runner.py")
    print()
    print("4. 🤖 ML Model Training:")
    print("   python -c \"from ml_optimizer.train_model import train_model_function; train_model_function()\"")
    print()
    print("5. 📚 Documentation:")
    print("   - README.md: Complete feature overview")
    print("   - ENHANCEMENTS.md: Advanced features guide")
    print("   - examples/: Sample queries and use cases")
    print()
    print("🎉 Your SQL Query Optimizer is ready to use!")

def main():
    """Main setup function"""
    print("🚀 SQL Query Optimizer - Setup & Demo")
    print("=" * 50)
    
    success_count = 0
    total_steps = 5
    
    # Step 1: Check dependencies
    if check_dependencies():
        success_count += 1
    
    # Step 2: Setup database
    if setup_database():
        success_count += 1
    
    # Step 3: Initialize ML model
    if initialize_ml_model():
        success_count += 1
    
    # Step 4: Run examples
    if run_example_optimizations():
        success_count += 1
    
    # Step 5: Demonstrate enhanced features
    if demonstrate_enhanced_features():
        success_count += 1
    
    # Summary
    print(f"\n📈 Setup Summary: {success_count}/{total_steps} steps completed")
    
    if success_count >= 4:
        print("✅ Setup successful! System is ready for use.")
        print_next_steps()
    elif success_count >= 2:
        print("⚠️ Partial setup completed. Some features may be limited.")
        print("💡 Check error messages above and resolve issues.")
    else:
        print("❌ Setup failed. Please resolve the issues above.")
        print("💡 Common solutions:")
        print("   - Install dependencies: pip install -r requirements.txt")
        print("   - Check database configuration in db.py")
        print("   - Ensure PostgreSQL is running")

if __name__ == "__main__":
    main()