import re
import sqlparse
from typing import List, Dict, Any

def apply_enhanced_rules(query: str) -> List[Dict[str, Any]]:
    """
    Enhanced rule-based optimizer with more sophisticated analysis
    Returns structured suggestions with priority levels and specific improvements
    """
    suggestions = []
    q = query.lower().strip()
    
    # Parse SQL for better analysis
    try:
        parsed = sqlparse.parse(query)[0]
        tokens = list(parsed.flatten())
    except:
        tokens = []

    # CRITICAL ISSUES (High Priority)
    
    # 1. SELECT * detection with specific column suggestions
    if "select *" in q:
        suggestions.append({
            "rule": "avoid_select_star",
            "priority": "HIGH",
            "issue": "SELECT * retrieves all columns",
            "suggestion": "Specify only required columns to reduce I/O and network traffic",
            "example": "SELECT id, name, email FROM users WHERE...",
            "impact": "Can improve performance by 20-50% for wide tables"
        })

    # 2. Missing indexes detection
    where_patterns = re.findall(r'where\s+(\w+)\s*[><=!]', q)
    join_patterns = re.findall(r'join\s+\w+\s+\w+\s+on\s+(\w+\.)?(\w+)\s*=', q)
    
    if where_patterns or join_patterns:
        columns = set(where_patterns + [col for _, col in join_patterns])
        suggestions.append({
            "rule": "index_recommendation",
            "priority": "HIGH",
            "issue": f"Potential missing indexes on columns: {', '.join(columns)}",
            "suggestion": f"Consider creating indexes: CREATE INDEX idx_column ON table(column)",
            "columns": list(columns),
            "impact": "Can improve query performance by 10-1000x"
        })

    # 3. N+1 query pattern detection
    if "select" in q and " in (" in q and "select" in q[q.find(" in ("):]:
        suggestions.append({
            "rule": "n_plus_one_query",
            "priority": "CRITICAL",
            "issue": "Potential N+1 query pattern detected",
            "suggestion": "Replace subquery with JOIN for better performance",
            "example": "SELECT ... FROM table1 t1 JOIN table2 t2 ON t1.id = t2.foreign_id",
            "impact": "Can reduce query count from N+1 to 1"
        })

    # MEDIUM PRIORITY OPTIMIZATIONS

    # 4. JOIN order optimization
    join_count = q.count(" join ")
    if join_count > 2:
        suggestions.append({
            "rule": "join_order",
            "priority": "MEDIUM",
            "issue": f"Query has {join_count} joins",
            "suggestion": "Ensure smallest tables are joined first, add appropriate WHERE filters early",
            "join_count": join_count,
            "impact": "Can improve performance by 10-30%"
        })

    # 5. LIMIT without ORDER BY
    if "limit" in q and "order by" not in q:
        suggestions.append({
            "rule": "limit_without_order",
            "priority": "MEDIUM",
            "issue": "LIMIT without ORDER BY returns unpredictable results",
            "suggestion": "Add ORDER BY clause to ensure consistent results",
            "example": "... ORDER BY id LIMIT 10",
            "impact": "Ensures deterministic query results"
        })

    # 6. Inefficient LIKE patterns
    like_patterns = re.findall(r"like\s+'([^']+)'", q)
    for pattern in like_patterns:
        if pattern.startswith('%'):
            suggestions.append({
                "rule": "inefficient_like",
                "priority": "MEDIUM",
                "issue": f"LIKE pattern '{pattern}' prevents index usage",
                "suggestion": "Consider full-text search or restructuring the query",
                "pattern": pattern,
                "impact": "May cause full table scan"
            })

    # LOW PRIORITY SUGGESTIONS

    # 7. DISTINCT without necessity
    if " distinct " in q:
        suggestions.append({
            "rule": "unnecessary_distinct",
            "priority": "LOW",
            "issue": "DISTINCT clause detected",
            "suggestion": "Verify if DISTINCT is necessary; consider using EXISTS or proper JOINs",
            "impact": "DISTINCT can be expensive on large result sets"
        })

    # 8. ORDER BY without LIMIT on large tables
    if "order by" in q and "limit" not in q:
        suggestions.append({
            "rule": "order_without_limit",
            "priority": "LOW",
            "issue": "ORDER BY without LIMIT sorts entire result set",
            "suggestion": "Consider adding LIMIT if you don't need all results",
            "impact": "Can save significant CPU and memory on large datasets"
        })

    # 9. OR conditions optimization
    or_count = q.count(" or ")
    if or_count > 2:
        suggestions.append({
            "rule": "multiple_or_conditions",
            "priority": "LOW",
            "issue": f"Query contains {or_count} OR conditions",
            "suggestion": "Consider using IN clause or UNION for better performance",
            "example": "WHERE column IN (val1, val2, val3) instead of column = val1 OR column = val2 OR column = val3",
            "impact": "Can improve index usage and performance"
        })

    return suggestions

def format_suggestions(suggestions: List[Dict[str, Any]]) -> str:
    """Format suggestions for display"""
    if not suggestions:
        return "✅ No optimization suggestions - query looks good!"
    
    output = []
    
    # Group by priority
    critical = [s for s in suggestions if s['priority'] == 'CRITICAL']
    high = [s for s in suggestions if s['priority'] == 'HIGH'] 
    medium = [s for s in suggestions if s['priority'] == 'MEDIUM']
    low = [s for s in suggestions if s['priority'] == 'LOW']
    
    for priority, items, emoji in [
        ("CRITICAL", critical, "🚨"),
        ("HIGH", high, "⚠️"),
        ("MEDIUM", medium, "📋"),
        ("LOW", low, "💡")
    ]:
        if items:
            output.append(f"\n{emoji} {priority} PRIORITY:")
            for item in items:
                output.append(f"  • {item['issue']}")
                output.append(f"    💡 {item['suggestion']}")
                if 'example' in item:
                    output.append(f"    📝 Example: {item['example']}")
                output.append(f"    📊 Impact: {item['impact']}")
                output.append("")
    
    return "\n".join(output)

# Backward compatibility
def apply_rules(query: str) -> List[str]:
    """Original function for backward compatibility"""
    enhanced = apply_enhanced_rules(query)
    return [s['suggestion'] for s in enhanced]