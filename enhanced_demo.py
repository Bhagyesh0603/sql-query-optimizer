#!/usr/bin/env python3
"""
Enhanced SQL Query Optimizer - Demonstration of New Features

This script demonstrates the advanced features added to the SQL Query Optimizer:
- Enhanced rule-based optimization with priority levels
- Smart index recommendations
- Advanced ML with ensemble models
- Query pattern detection
- Complexity analysis
"""

import sys
import argparse
from typing import Dict, List
import time

# Import all the new modules
from enhanced_rules import apply_enhanced_rules, format_suggestions
from index_recommender import IndexRecommender
from pattern_detector import QueryPatternDetector, QueryComplexityAnalyzer
from advanced_ml import AdvancedMLOptimizer

def demonstrate_enhancements():
    """Demonstrate all the new enhancement features"""
    
    # Test queries of varying complexity
    test_queries = [
        # Simple query
        "SELECT * FROM employees WHERE salary > 50000",
        
        # Complex query with multiple issues
        """
        SELECT DISTINCT e.*, d.department_name, 
               UPPER(e.first_name) as upper_name,
               (SELECT COUNT(*) FROM projects p WHERE p.employee_id = e.emp_id) as project_count
        FROM employees e 
        JOIN departments d ON e.dept_id = d.id
        WHERE UPPER(e.first_name) LIKE '%JOHN%' 
        AND e.salary > (SELECT AVG(salary) FROM employees WHERE dept_id = e.dept_id)
        ORDER BY e.salary DESC
        """,
        
        # Query with potential N+1 pattern
        """
        SELECT emp_id, first_name, last_name 
        FROM employees 
        WHERE dept_id IN (
            SELECT id FROM departments WHERE budget > 100000
        )
        """,
        
        # Query with potential cartesian product
        "SELECT * FROM employees e, departments d, projects p WHERE e.salary > 50000"
    ]
    
    print("🚀 SQL Query Optimizer - Advanced Features Demonstration")
    print("=" * 70)
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n{'='*20} TEST QUERY {i} {'='*20}")
        print("Query:", query.strip()[:100] + "..." if len(query.strip()) > 100 else query.strip())
        print()
        
        # 1. Enhanced Rule-Based Analysis
        print("🔧 ENHANCED RULE-BASED ANALYSIS:")
        print("-" * 40)
        enhanced_suggestions = apply_enhanced_rules(query)
        if enhanced_suggestions:
            print(format_suggestions(enhanced_suggestions))
        else:
            print("✅ No rule-based suggestions")
        
        # 2. Index Recommendations
        print("\n📊 INDEX RECOMMENDATIONS:")
        print("-" * 30)
        try:
            index_recommender = IndexRecommender()
            index_report = index_recommender.generate_report(query)
            print(index_report)
        except Exception as e:
            print(f"Index analysis error: {e}")
        
        # 3. Pattern Detection
        print("\n🔍 PATTERN DETECTION:")
        print("-" * 20)
        try:
            pattern_detector = QueryPatternDetector()
            pattern_report = pattern_detector.generate_pattern_report(query)
            print(pattern_report)
        except Exception as e:
            print(f"Pattern detection error: {e}")
        
        # 4. Complexity Analysis
        print("\n📈 COMPLEXITY ANALYSIS:")
        print("-" * 25)
        try:
            complexity_metrics = QueryComplexityAnalyzer.calculate_complexity_score(query)
            
            print(f"Complexity Level: {complexity_metrics['complexity_level']}")
            print(f"Overall Score: {complexity_metrics['overall_score']}/100")
            print(f"Query Length: {complexity_metrics['basic_metrics']['length']} characters")
            print(f"Number of JOINs: {complexity_metrics['structural_complexity']['num_joins']}")
            print(f"Number of Subqueries: {complexity_metrics['structural_complexity']['num_subqueries']}")
            print(f"Max Nesting Depth: {complexity_metrics['structural_complexity']['max_nesting_depth']}")
            
            if complexity_metrics['operation_complexity']['has_aggregates']:
                print("⚡ Contains aggregate functions")
            if complexity_metrics['operation_complexity']['has_window_functions']:
                print("🪟 Contains window functions")
            if complexity_metrics['operation_complexity']['has_cte']:
                print("🔗 Uses Common Table Expressions")
                
        except Exception as e:
            print(f"Complexity analysis error: {e}")
        
        print("\n" + "="*70)

def interactive_analysis():
    """Interactive query analysis mode"""
    print("\n🎯 INTERACTIVE QUERY ANALYZER")
    print("Enter your SQL query (type 'quit' to exit):")
    
    # Initialize analyzers
    try:
        index_recommender = IndexRecommender()
        pattern_detector = QueryPatternDetector()
        print("✅ All analyzers initialized successfully")
    except Exception as e:
        print(f"⚠️ Some analyzers failed to initialize: {e}")
        return
    
    while True:
        print("\n" + "-"*50)
        query = input("SQL> ").strip()
        
        if query.lower() in ['quit', 'exit', 'q']:
            print("👋 Goodbye!")
            break
            
        if not query:
            continue
            
        print(f"\n🔍 Analyzing query: {query[:50]}...")
        start_time = time.time()
        
        # Enhanced rules analysis
        print("\n📋 OPTIMIZATION SUGGESTIONS:")
        suggestions = apply_enhanced_rules(query)
        if suggestions:
            for suggestion in suggestions:
                priority_emoji = {"CRITICAL": "🚨", "HIGH": "⚠️", "MEDIUM": "📋", "LOW": "💡"}
                emoji = priority_emoji.get(suggestion['priority'], "📋")
                print(f"{emoji} [{suggestion['priority']}] {suggestion['suggestion']}")
        else:
            print("✅ No immediate suggestions")
        
        # Quick pattern check
        print("\n🔍 PATTERN ANALYSIS:")
        patterns = pattern_detector.analyze_query(query)
        if patterns:
            for pattern in patterns[:3]:  # Show top 3
                print(f"⚠️ {pattern.description} (confidence: {pattern.confidence:.1%})")
        else:
            print("✅ No problematic patterns detected")
        
        # Quick complexity check
        print("\n📊 COMPLEXITY:")
        complexity = QueryComplexityAnalyzer.calculate_complexity_score(query)
        print(f"Level: {complexity['complexity_level']} (Score: {complexity['overall_score']}/100)")
        
        analysis_time = time.time() - start_time
        print(f"\n⏱️ Analysis completed in {analysis_time:.3f} seconds")

def main():
    """Main function with command-line interface"""
    parser = argparse.ArgumentParser(description="Enhanced SQL Query Optimizer")
    parser.add_argument('--demo', action='store_true', help='Run demonstration of all features')
    parser.add_argument('--interactive', action='store_true', help='Start interactive analysis mode')
    parser.add_argument('--query', type=str, help='Analyze a specific query')
    
    args = parser.parse_args()
    
    if args.demo:
        demonstrate_enhancements()
    elif args.interactive:
        interactive_analysis()
    elif args.query:
        # Analyze single query
        print(f"🔍 Analyzing query: {args.query}")
        
        # Enhanced rules
        suggestions = apply_enhanced_rules(args.query)
        if suggestions:
            print("\n📋 SUGGESTIONS:")
            print(format_suggestions(suggestions))
        
        # Patterns
        detector = QueryPatternDetector()
        patterns = detector.analyze_query(args.query)
        if patterns:
            print("\n🔍 PATTERNS:")
            for pattern in patterns:
                print(f"⚠️ {pattern.description}")
        
        # Complexity
        complexity = QueryComplexityAnalyzer.calculate_complexity_score(args.query)
        print(f"\n📊 COMPLEXITY: {complexity['complexity_level']} ({complexity['overall_score']}/100)")
        
    else:
        print("Enhanced SQL Query Optimizer")
        print("Usage:")
        print("  python enhanced_demo.py --demo              # Run feature demonstration")
        print("  python enhanced_demo.py --interactive       # Interactive analysis mode")
        print("  python enhanced_demo.py --query 'SELECT...' # Analyze specific query")

if __name__ == "__main__":
    main()