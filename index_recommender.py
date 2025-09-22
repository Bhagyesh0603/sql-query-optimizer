import re
import psycopg2
from typing import List, Dict, Set
from db import get_connection

class IndexRecommender:
    """Intelligent index recommendation system"""
    
    def __init__(self):
        self.connection = get_connection()
    
    def analyze_query(self, query: str) -> Dict:
        """Analyze query and recommend indexes"""
        recommendations = {
            'missing_indexes': [],
            'unused_indexes': [],
            'composite_indexes': [],
            'query_analysis': {}
        }
        
        # Extract WHERE columns
        where_columns = self._extract_where_columns(query)
        
        # Extract JOIN columns
        join_columns = self._extract_join_columns(query)
        
        # Extract ORDER BY columns
        order_columns = self._extract_order_columns(query)
        
        # Get existing indexes
        existing_indexes = self._get_existing_indexes()
        
        # Analyze missing single-column indexes
        all_filtered_columns = where_columns | join_columns | order_columns
        for table, column in all_filtered_columns:
            if not self._has_index(existing_indexes, table, column):
                recommendations['missing_indexes'].append({
                    'table': table,
                    'column': column,
                    'type': 'single',
                    'reason': self._get_index_reason(table, column, query),
                    'priority': self._calculate_priority(table, column, query),
                    'sql': f"CREATE INDEX idx_{table}_{column} ON {table} ({column});"
                })
        
        # Recommend composite indexes for multi-column WHERE clauses
        composite_candidates = self._find_composite_opportunities(query, where_columns)
        for table, columns in composite_candidates.items():
            if len(columns) > 1:
                col_list = ', '.join(columns)
                idx_name = f"idx_{table}_{'_'.join(columns)}"
                recommendations['composite_indexes'].append({
                    'table': table,
                    'columns': columns,
                    'sql': f"CREATE INDEX {idx_name} ON {table} ({col_list});",
                    'reason': f"Composite index for multi-column WHERE clause on {table}"
                })
        
        recommendations['query_analysis'] = {
            'where_columns': len(where_columns),
            'join_columns': len(join_columns),
            'order_columns': len(order_columns),
            'complexity_score': self._calculate_complexity(query)
        }
        
        return recommendations
    
    def _extract_where_columns(self, query: str) -> Set[tuple]:
        """Extract table.column pairs from WHERE clauses"""
        columns = set()
        
        # Pattern for WHERE conditions: table.column operator value
        pattern = r'WHERE\s+(?:.*?\s+)?(\w+)\.(\w+)\s*[<>=!]'
        matches = re.findall(pattern, query, re.IGNORECASE)
        
        # Also check for simple column references (assume main table)
        simple_pattern = r'WHERE\s+(?:.*?\s+)?(\w+)\s*[<>=!]'
        simple_matches = re.findall(simple_pattern, query, re.IGNORECASE)
        
        for match in matches:
            columns.add((match[0], match[1]))
        
        # For simple columns, try to infer table from FROM clause
        from_match = re.search(r'FROM\s+(\w+)', query, re.IGNORECASE)
        if from_match and simple_matches:
            main_table = from_match.group(1)
            for col in simple_matches:
                if '.' not in col:  # Simple column reference
                    columns.add((main_table, col))
        
        return columns
    
    def _extract_join_columns(self, query: str) -> Set[tuple]:
        """Extract columns used in JOIN conditions"""
        columns = set()
        
        # Pattern for JOIN conditions: table1.col1 = table2.col2
        pattern = r'JOIN\s+(\w+)\s+\w+\s+ON\s+(\w+)\.(\w+)\s*=\s*(\w+)\.(\w+)'
        matches = re.findall(pattern, query, re.IGNORECASE)
        
        for match in matches:
            # match: (join_table, table1, col1, table2, col2)
            columns.add((match[1], match[2]))  # Left side
            columns.add((match[3], match[4]))  # Right side
        
        return columns
    
    def _extract_order_columns(self, query: str) -> Set[tuple]:
        """Extract columns from ORDER BY clause"""
        columns = set()
        
        pattern = r'ORDER\s+BY\s+([\w\.,\s]+)'
        match = re.search(pattern, query, re.IGNORECASE)
        
        if match:
            order_clause = match.group(1)
            # Split by comma and extract table.column
            for item in order_clause.split(','):
                item = item.strip().split()[0]  # Remove ASC/DESC
                if '.' in item:
                    table, col = item.split('.', 1)
                    columns.add((table.strip(), col.strip()))
                else:
                    # Infer table from FROM clause
                    from_match = re.search(r'FROM\s+(\w+)', query, re.IGNORECASE)
                    if from_match:
                        columns.add((from_match.group(1), item.strip()))
        
        return columns
    
    def _get_existing_indexes(self) -> Dict:
        """Get all existing indexes from database"""
        indexes = {}
        
        try:
            with self.connection.cursor() as cur:
                cur.execute("""
                    SELECT 
                        schemaname, tablename, indexname, indexdef
                    FROM pg_indexes 
                    WHERE schemaname = 'public'
                """)
                
                for row in cur.fetchall():
                    schema, table, idx_name, idx_def = row
                    if table not in indexes:
                        indexes[table] = []
                    indexes[table].append({
                        'name': idx_name,
                        'definition': idx_def
                    })
        except Exception as e:
            print(f"Error fetching indexes: {e}")
        
        return indexes
    
    def _has_index(self, existing_indexes: Dict, table: str, column: str) -> bool:
        """Check if an index exists on the specified column"""
        if table not in existing_indexes:
            return False
        
        for idx in existing_indexes[table]:
            if f"({column})" in idx['definition'] or f"({column}," in idx['definition']:
                return True
        
        return False
    
    def _get_index_reason(self, table: str, column: str, query: str) -> str:
        """Determine why this index is recommended"""
        q_lower = query.lower()
        
        if f"where" in q_lower and column.lower() in q_lower:
            return f"Used in WHERE clause filter"
        elif f"join" in q_lower and column.lower() in q_lower:
            return f"Used in JOIN condition"
        elif f"order by" in q_lower and column.lower() in q_lower:
            return f"Used in ORDER BY clause"
        else:
            return f"Referenced in query conditions"
    
    def _calculate_priority(self, table: str, column: str, query: str) -> int:
        """Calculate index priority (1-10, 10 being highest)"""
        priority = 5  # Base priority
        q_lower = query.lower()
        
        # Higher priority for WHERE clause columns
        if "where" in q_lower and column.lower() in q_lower:
            priority += 3
        
        # Medium priority for JOIN columns
        if "join" in q_lower and column.lower() in q_lower:
            priority += 2
        
        # Lower priority for ORDER BY only
        if "order by" in q_lower and column.lower() in q_lower:
            priority += 1
        
        return min(priority, 10)
    
    def _find_composite_opportunities(self, query: str, where_columns: Set[tuple]) -> Dict[str, List[str]]:
        """Find opportunities for composite indexes"""
        composite_candidates = {}
        
        # Group columns by table
        table_columns = {}
        for table, column in where_columns:
            if table not in table_columns:
                table_columns[table] = []
            table_columns[table].append(column)
        
        # Suggest composite indexes for tables with multiple WHERE columns
        for table, columns in table_columns.items():
            if len(columns) > 1:
                composite_candidates[table] = columns
        
        return composite_candidates
    
    def _calculate_complexity(self, query: str) -> int:
        """Calculate query complexity score"""
        score = 0
        q_lower = query.lower()
        
        # Count different elements
        score += q_lower.count("join") * 2
        score += q_lower.count("where") * 1
        score += q_lower.count("order by") * 1
        score += q_lower.count("group by") * 1
        score += q_lower.count("having") * 2
        score += q_lower.count("union") * 3
        score += q_lower.count("exists") * 2
        score += q_lower.count("in (") * 1
        
        return score
    
    def generate_report(self, query: str) -> str:
        """Generate formatted index recommendation report"""
        recommendations = self.analyze_query(query)
        
        report = []
        report.append("📊 INDEX ANALYSIS REPORT")
        report.append("=" * 50)
        
        # Query complexity
        analysis = recommendations['query_analysis']
        report.append(f"\n🔍 Query Complexity Score: {analysis['complexity_score']}")
        report.append(f"   • WHERE columns: {analysis['where_columns']}")
        report.append(f"   • JOIN columns: {analysis['join_columns']}")  
        report.append(f"   • ORDER BY columns: {analysis['order_columns']}")
        
        # Missing indexes
        missing = recommendations['missing_indexes']
        if missing:
            report.append(f"\n⚠️ RECOMMENDED INDEXES ({len(missing)} suggestions):")
            for idx in sorted(missing, key=lambda x: x['priority'], reverse=True):
                priority_emoji = "🔴" if idx['priority'] >= 8 else "🟡" if idx['priority'] >= 6 else "🟢"
                report.append(f"   {priority_emoji} Priority {idx['priority']}: {idx['table']}.{idx['column']}")
                report.append(f"      Reason: {idx['reason']}")
                report.append(f"      SQL: {idx['sql']}")
                report.append("")
        
        # Composite indexes
        composite = recommendations['composite_indexes']
        if composite:
            report.append(f"\n🔗 COMPOSITE INDEX OPPORTUNITIES:")
            for idx in composite:
                report.append(f"   • {idx['table']}: {', '.join(idx['columns'])}")
                report.append(f"     SQL: {idx['sql']}")
                report.append("")
        
        if not missing and not composite:
            report.append("\n✅ No immediate index recommendations - query looks well-optimized!")
        
        return "\n".join(report)