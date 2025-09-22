import re
import json
from typing import Dict, List, Set, Tuple
from collections import defaultdict, Counter
from dataclasses import dataclass
from enum import Enum

class QueryPattern(Enum):
    N_PLUS_ONE = "n_plus_one"
    CARTESIAN_PRODUCT = "cartesian_product"
    UNNECESSARY_SUBQUERY = "unnecessary_subquery"
    MISSING_INDEX_PATTERN = "missing_index"
    INEFFICIENT_PAGINATION = "inefficient_pagination"
    REDUNDANT_JOIN = "redundant_join"
    EXPENSIVE_FUNCTION = "expensive_function"
    UNBOUNDED_RESULT = "unbounded_result"
    COMPLEX_WHERE = "complex_where"
    NESTED_SUBQUERY = "nested_subquery"

@dataclass
class PatternMatch:
    pattern: QueryPattern
    confidence: float
    description: str
    suggestion: str
    example: str
    impact: str
    line_number: int = 0

class QueryPatternDetector:
    """Advanced pattern detection for SQL queries"""
    
    def __init__(self):
        self.patterns = {
            QueryPattern.N_PLUS_ONE: self._detect_n_plus_one,
            QueryPattern.CARTESIAN_PRODUCT: self._detect_cartesian_product,
            QueryPattern.UNNECESSARY_SUBQUERY: self._detect_unnecessary_subquery,
            QueryPattern.MISSING_INDEX_PATTERN: self._detect_missing_index_pattern,
            QueryPattern.INEFFICIENT_PAGINATION: self._detect_inefficient_pagination,
            QueryPattern.REDUNDANT_JOIN: self._detect_redundant_join,
            QueryPattern.EXPENSIVE_FUNCTION: self._detect_expensive_function,
            QueryPattern.UNBOUNDED_RESULT: self._detect_unbounded_result,
            QueryPattern.COMPLEX_WHERE: self._detect_complex_where,
            QueryPattern.NESTED_SUBQUERY: self._detect_nested_subquery
        }
        
        # Common expensive functions
        self.expensive_functions = {
            'upper', 'lower', 'substring', 'replace', 'like', 'ilike',
            'regexp_replace', 'to_char', 'extract', 'date_part'
        }
        
    def analyze_query(self, query: str) -> List[PatternMatch]:
        """Analyze query for all patterns"""
        matches = []
        
        for pattern_type, detector_func in self.patterns.items():
            try:
                match = detector_func(query)
                if match:
                    matches.append(match)
            except Exception as e:
                print(f"Error detecting {pattern_type}: {e}")
                
        return sorted(matches, key=lambda x: x.confidence, reverse=True)
    
    def _detect_n_plus_one(self, query: str) -> PatternMatch:
        """Detect N+1 query patterns"""
        q_lower = query.lower()
        
        # Look for subquery in WHERE IN clause
        if re.search(r'where\s+\w+\s+in\s*\(\s*select', q_lower):
            return PatternMatch(
                pattern=QueryPattern.N_PLUS_ONE,
                confidence=0.8,
                description="Potential N+1 query pattern detected",
                suggestion="Replace subquery with JOIN for better performance",
                example="SELECT ... FROM table1 t1 JOIN table2 t2 ON t1.id = t2.foreign_id",
                impact="Can reduce query count from N+1 to 1, dramatically improving performance"
            )
        
        # Look for EXISTS subqueries that could be JOINs
        if re.search(r'where\s+exists\s*\(\s*select', q_lower):
            return PatternMatch(
                pattern=QueryPattern.N_PLUS_ONE,
                confidence=0.6,
                description="EXISTS subquery could potentially be optimized",
                suggestion="Consider JOIN if you need data from the subquery table",
                example="Use JOIN instead of EXISTS when you need columns from both tables",
                impact="May improve performance and readability"
            )
        
        return None
    
    def _detect_cartesian_product(self, query: str) -> PatternMatch:
        """Detect potential cartesian products"""
        q_lower = query.lower()
        
        # Count tables and JOINs
        from_matches = re.findall(r'from\s+(\w+)', q_lower)
        join_matches = re.findall(r'join\s+(\w+)', q_lower)
        
        total_tables = len(from_matches) + len(join_matches)
        
        # Count JOIN conditions
        join_conditions = len(re.findall(r'on\s+\w+\.\w+\s*=\s*\w+\.\w+', q_lower))
        
        # Also check WHERE conditions that could be JOIN conditions
        where_joins = len(re.findall(r'where.*?\w+\.\w+\s*=\s*\w+\.\w+', q_lower))
        
        total_conditions = join_conditions + where_joins
        
        if total_tables > 1 and total_conditions < total_tables - 1:
            return PatternMatch(
                pattern=QueryPattern.CARTESIAN_PRODUCT,
                confidence=0.9,
                description=f"Potential cartesian product: {total_tables} tables, {total_conditions} join conditions",
                suggestion="Ensure all tables are properly joined with ON conditions",
                example="SELECT ... FROM t1 JOIN t2 ON t1.id = t2.t1_id JOIN t3 ON t2.id = t3.t2_id",
                impact="CRITICAL: Can cause exponential result growth and extreme performance issues"
            )
        
        return None
    
    def _detect_unnecessary_subquery(self, query: str) -> PatternMatch:
        """Detect subqueries that could be simplified"""
        q_lower = query.lower()
        
        # Simple subquery that just selects a single value
        if re.search(r'=\s*\(\s*select\s+\w+\s+from\s+\w+\s+where\s+[^)]+\)', q_lower):
            return PatternMatch(
                pattern=QueryPattern.UNNECESSARY_SUBQUERY,
                confidence=0.7,
                description="Simple subquery detected that might be optimizable",
                suggestion="Consider using JOIN or EXISTS instead of subquery",
                example="Use JOIN when you need to filter based on related table data",
                impact="Can improve query performance and readability"
            )
        
        return None
    
    def _detect_missing_index_pattern(self, query: str) -> PatternMatch:
        """Detect patterns suggesting missing indexes"""
        q_lower = query.lower()
        
        # LIKE with leading wildcard
        if re.search(r"like\s+'%", q_lower):
            return PatternMatch(
                pattern=QueryPattern.MISSING_INDEX_PATTERN,
                confidence=0.8,
                description="LIKE with leading wildcard prevents index usage",
                suggestion="Consider full-text search or restructure query to avoid leading wildcard",
                example="Use column LIKE 'prefix%' instead of column LIKE '%suffix'",
                impact="Forces full table scan, severely impacting performance on large tables"
            )
        
        # Functions in WHERE clause
        func_pattern = r'where\s+\w*\(\s*\w+\s*\)\s*[<>=!]'
        if re.search(func_pattern, q_lower):
            return PatternMatch(
                pattern=QueryPattern.MISSING_INDEX_PATTERN,
                confidence=0.7,
                description="Function in WHERE clause prevents index usage",
                suggestion="Create functional index or restructure query",
                example="CREATE INDEX idx_upper_name ON table (UPPER(name))",
                impact="May cause full table scan instead of index scan"
            )
        
        return None
    
    def _detect_inefficient_pagination(self, query: str) -> PatternMatch:
        """Detect inefficient pagination patterns"""
        q_lower = query.lower()
        
        # OFFSET without proper indexing
        offset_match = re.search(r'offset\s+(\d+)', q_lower)
        if offset_match:
            offset_value = int(offset_match.group(1))
            
            if offset_value > 1000:
                return PatternMatch(
                    pattern=QueryPattern.INEFFICIENT_PAGINATION,
                    confidence=0.9,
                    description=f"Large OFFSET ({offset_value}) can be very inefficient",
                    suggestion="Use cursor-based pagination with WHERE id > last_id",
                    example="WHERE id > 1000 ORDER BY id LIMIT 10 instead of OFFSET 1000 LIMIT 10",
                    impact="Performance degrades linearly with offset size"
                )
        
        return None
    
    def _detect_redundant_join(self, query: str) -> PatternMatch:
        """Detect potentially redundant joins"""
        q_lower = query.lower()
        
        # Extract all table aliases and their usage
        join_pattern = r'join\s+(\w+)(?:\s+(?:as\s+)?(\w+))?'
        joins = re.findall(join_pattern, q_lower)
        
        # Extract SELECT columns
        select_part = re.search(r'select\s+(.*?)\s+from', q_lower)
        if select_part:
            select_columns = select_part.group(1)
            
            # Check if any joined table is not used in SELECT
            for table, alias in joins:
                table_ref = alias if alias else table
                if table_ref not in select_columns:
                    return PatternMatch(
                        pattern=QueryPattern.REDUNDANT_JOIN,
                        confidence=0.6,
                        description=f"Table '{table}' is joined but not used in SELECT",
                        suggestion="Remove unnecessary JOIN or add columns from joined table",
                        example="Remove JOIN if only used for filtering, or add needed columns to SELECT",
                        impact="Unnecessary JOINs add computation overhead"
                    )
        
        return None
    
    def _detect_expensive_function(self, query: str) -> PatternMatch:
        """Detect expensive functions in WHERE clauses"""
        q_lower = query.lower()
        
        for func in self.expensive_functions:
            if re.search(rf'where.*?{func}\s*\(', q_lower):
                return PatternMatch(
                    pattern=QueryPattern.EXPENSIVE_FUNCTION,
                    confidence=0.7,
                    description=f"Expensive function '{func}' used in WHERE clause",
                    suggestion="Consider pre-computing values or using functional index",
                    example=f"CREATE INDEX idx_func ON table ({func}(column))",
                    impact="Function evaluation on every row can be expensive"
                )
        
        return None
    
    def _detect_unbounded_result(self, query: str) -> PatternMatch:
        """Detect queries without LIMIT that could return large results"""
        q_lower = query.lower()
        
        if 'limit' not in q_lower and 'where' not in q_lower:
            return PatternMatch(
                pattern=QueryPattern.UNBOUNDED_RESULT,
                confidence=0.8,
                description="Query has no LIMIT or WHERE clause",
                suggestion="Add appropriate WHERE filters or LIMIT clause",
                example="Add WHERE conditions to filter data or LIMIT to control result size",
                impact="May return entire table, consuming excessive memory and bandwidth"
            )
        
        return None
    
    def _detect_complex_where(self, query: str) -> PatternMatch:
        """Detect overly complex WHERE clauses"""
        q_lower = query.lower()
        
        # Count conditions
        and_count = q_lower.count(' and ')
        or_count = q_lower.count(' or ')
        not_count = q_lower.count(' not ')
        
        total_conditions = and_count + or_count + not_count
        
        if total_conditions > 10:
            return PatternMatch(
                pattern=QueryPattern.COMPLEX_WHERE,
                confidence=0.6,
                description=f"Very complex WHERE clause with {total_conditions} conditions",
                suggestion="Consider breaking into multiple queries or using temporary tables",
                example="Split complex conditions or use Common Table Expressions (CTEs)",
                impact="Complex WHERE clauses can be hard to optimize and maintain"
            )
        
        return None
    
    def _detect_nested_subquery(self, query: str) -> PatternMatch:
        """Detect deeply nested subqueries"""
        # Count nesting levels
        nesting_level = 0
        max_nesting = 0
        
        for char in query.lower():
            if char == '(':
                nesting_level += 1
                max_nesting = max(max_nesting, nesting_level)
            elif char == ')':
                nesting_level -= 1
        
        # Check if there are subqueries with high nesting
        if max_nesting > 3 and 'select' in query.lower():
            select_count = query.lower().count('select')
            if select_count > 2:  # More than 2 SELECT statements
                return PatternMatch(
                    pattern=QueryPattern.NESTED_SUBQUERY,
                    confidence=0.7,
                    description=f"Deeply nested subqueries detected (nesting level: {max_nesting})",
                    suggestion="Consider using CTEs or temporary tables for better readability",
                    example="WITH cte AS (SELECT ...) SELECT ... FROM cte",
                    impact="Deep nesting can hurt performance and maintainability"
                )
        
        return None
    
    def generate_pattern_report(self, query: str) -> str:
        """Generate comprehensive pattern analysis report"""
        matches = self.analyze_query(query)
        
        if not matches:
            return "✅ No problematic patterns detected - query looks good!"
        
        report = []
        report.append("🔍 QUERY PATTERN ANALYSIS")
        report.append("=" * 50)
        
        # Group by severity
        critical = [m for m in matches if m.confidence >= 0.9]
        high = [m for m in matches if 0.7 <= m.confidence < 0.9]
        medium = [m for m in matches if 0.5 <= m.confidence < 0.7]
        
        for severity, patterns, emoji in [
            ("CRITICAL", critical, "🚨"),
            ("HIGH RISK", high, "⚠️"),
            ("MEDIUM RISK", medium, "💡")
        ]:
            if patterns:
                report.append(f"\n{emoji} {severity} PATTERNS:")
                report.append("-" * 30)
                
                for pattern in patterns:
                    report.append(f"\n📌 {pattern.description}")
                    report.append(f"   Pattern: {pattern.pattern.value}")
                    report.append(f"   Confidence: {pattern.confidence:.1%}")
                    report.append(f"   💡 Suggestion: {pattern.suggestion}")
                    report.append(f"   📝 Example: {pattern.example}")
                    report.append(f"   📊 Impact: {pattern.impact}")
        
        return "\n".join(report)

class QueryComplexityAnalyzer:
    """Analyze overall query complexity"""
    
    @staticmethod
    def calculate_complexity_score(query: str) -> Dict[str, any]:
        """Calculate comprehensive complexity metrics"""
        q_lower = query.lower()
        
        metrics = {
            'basic_metrics': {
                'length': len(query),
                'lines': len(query.split('\n')),
                'words': len(query.split())
            },
            'structural_complexity': {
                'num_selects': q_lower.count('select'),
                'num_joins': q_lower.count('join'),
                'num_where_conditions': q_lower.count('where'),
                'num_subqueries': q_lower.count('(select'),
                'max_nesting_depth': QueryComplexityAnalyzer._calculate_nesting_depth(query)
            },
            'operation_complexity': {
                'has_aggregates': any(func in q_lower for func in ['sum(', 'count(', 'avg(', 'max(', 'min(']),
                'has_window_functions': any(func in q_lower for func in ['over (', 'partition by', 'row_number']),
                'has_cte': 'with ' in q_lower,
                'has_union': 'union' in q_lower,
                'has_case_when': 'case when' in q_lower
            }
        }
        
        # Calculate overall complexity score (0-100)
        score = 0
        
        # Length-based complexity
        score += min(metrics['basic_metrics']['length'] / 100, 20)
        
        # Structural complexity
        score += metrics['structural_complexity']['num_joins'] * 5
        score += metrics['structural_complexity']['num_subqueries'] * 8
        score += metrics['structural_complexity']['max_nesting_depth'] * 3
        
        # Operation complexity
        if metrics['operation_complexity']['has_aggregates']:
            score += 10
        if metrics['operation_complexity']['has_window_functions']:
            score += 15
        if metrics['operation_complexity']['has_cte']:
            score += 5
        if metrics['operation_complexity']['has_union']:
            score += 8
        if metrics['operation_complexity']['has_case_when']:
            score += 5
        
        metrics['overall_score'] = min(score, 100)
        
        # Complexity level
        if score < 20:
            metrics['complexity_level'] = 'Simple'
        elif score < 50:
            metrics['complexity_level'] = 'Moderate'
        elif score < 80:
            metrics['complexity_level'] = 'Complex'
        else:
            metrics['complexity_level'] = 'Very Complex'
        
        return metrics
    
    @staticmethod
    def _calculate_nesting_depth(query: str) -> int:
        """Calculate maximum nesting depth of parentheses"""
        depth = 0
        max_depth = 0
        
        for char in query:
            if char == '(':
                depth += 1
                max_depth = max(max_depth, depth)
            elif char == ')':
                depth -= 1
        
        return max_depth