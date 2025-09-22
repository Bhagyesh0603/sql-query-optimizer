import sqlparse
import itertools
import random
import logging
import re
import pandas as pd
import numpy as np
import argparse
from typing import List, Tuple, Dict, Optional
from dataclasses import dataclass

from ml_optimizer.feature_extraction import extract_features
from cost_model import get_query_cost, load_cost_model

logger = logging.getLogger(__name__)

@dataclass
class TableInfo:
    name: str
    alias: Optional[str]
    join_conditions: List[str]

@dataclass
class QueryStructure:
    select_clause: str
    from_table: TableInfo
    joins: List[TableInfo]
    where_clause: Optional[str]
    group_by: Optional[str]
    having: Optional[str]
    order_by: Optional[str]
    limit: Optional[str]

def extract_structure(query: str) -> Dict:
    """Enhanced query structure extraction"""
    # Extract SELECT clause
    select_match = re.search(r'SELECT\s+(.+?)\s+FROM', query, re.IGNORECASE | re.DOTALL)
    select_clause = select_match.group(1) if select_match else "*"
    
    # Extract FROM table with alias
    from_match = re.search(r'FROM\s+(\w+)(?:\s+(\w+))?', query, re.IGNORECASE)
    from_table = from_match.group(1) if from_match else None
    from_alias = from_match.group(2) if from_match else None
    
    # Extract JOIN clauses with their conditions
    join_pattern = r'((?:INNER\s+|LEFT\s+|RIGHT\s+|FULL\s+)?JOIN)\s+(\w+)(?:\s+(\w+))?\s+ON\s+([^;]+?)(?=\s+(?:INNER\s+|LEFT\s+|RIGHT\s+|FULL\s+)?JOIN|\s+WHERE|\s+GROUP|\s+ORDER|\s*$)'
    joins = []
    for match in re.finditer(join_pattern, query, re.IGNORECASE | re.DOTALL):
        joins.append({
            'type': match.group(1).strip(),
            'table': match.group(2),
            'alias': match.group(3),
            'condition': match.group(4).strip()
        })
    
    # Extract WHERE clause
    where_match = re.search(r'WHERE\s+(.+?)(?=\s+GROUP|\s+ORDER|\s*$)', query, re.IGNORECASE | re.DOTALL)
    where_clause = where_match.group(1).strip() if where_match else None
    
    return {
        'select': select_clause,
        'from_table': from_table,
        'from_alias': from_alias,
        'joins': joins,
        'where': where_clause
    }

def generate_join_permutations(struct: Dict, limit: int = 5) -> List[str]:
    """Generate different join orders"""
    if not struct['joins']:
        return []
    
    candidates = []
    joins = struct['joins']
    
    # Generate permutations for small join counts
    if len(joins) <= 3:
        perms = list(itertools.permutations(joins))
    else:
        # Sample permutations for larger join counts
        perms = []
        for _ in range(limit):
            perm = joins.copy()
            random.shuffle(perm)
            perms.append(tuple(perm))
        # Remove duplicates
        perms = list(set(perms))[:limit]
    
    for perm in perms[:limit]:
        query_parts = [f"SELECT {struct['select']}"]
        
        # FROM clause
        if struct['from_alias']:
            query_parts.append(f"FROM {struct['from_table']} {struct['from_alias']}")
        else:
            query_parts.append(f"FROM {struct['from_table']}")
        
        # JOIN clauses in new order
        for join in perm:
            join_clause = f"{join['type']} {join['table']}"
            if join['alias']:
                join_clause += f" {join['alias']}"
            join_clause += f" ON {join['condition']}"
            query_parts.append(join_clause)
        
        # WHERE clause
        if struct['where']:
            query_parts.append(f"WHERE {struct['where']}")
        
        candidates.append(' '.join(query_parts))
    
    return candidates

def generate_candidates(query: str, limit: int = 10, deterministic: bool = False) -> List[Tuple[str, str]]:
    """Generate query candidates using various optimization strategies"""
    if deterministic:
        random.seed(42)
    
    candidates = [("original", query)]
    
    try:
        struct = extract_structure(query)
        
        # 1. Join order permutations (generate more variants)
        join_perms = generate_join_permutations(struct, limit//2 + 2)
        for i, q in enumerate(join_perms):
            candidates.append((f"join_order_{i+1}", q))
        
        # 2. Index hints (add more variations)
        if 'employees e' in query.lower():
            # Different index hint styles
            hinted1 = query.replace('employees e', 'employees e /*+ USE_NL(e) */')
            candidates.append(("index_hint_nested_loop", hinted1))
            
            hinted2 = query.replace('employees e', 'employees e /*+ USE_HASH(e) */')
            candidates.append(("index_hint_hash", hinted2))
        
        if 'departments d' in query.lower():
            hinted3 = query.replace('departments d', 'departments d /*+ INDEX(d, PRIMARY) */')
            candidates.append(("index_hint_primary", hinted3))
        
        # 3. Query restructuring (add WHERE clause optimization)
        if 'WHERE' in query.upper() and 'AND' in query.upper():
            # Try reordering WHERE conditions
            where_reordered = reorder_where_conditions(query)
            if where_reordered != query:
                candidates.append(("where_reorder", where_reordered))
        
        # Remove duplicates
        seen = set()
        unique_candidates = []
        for strategy, q in candidates:
            normalized_q = ' '.join(q.split())
            if normalized_q not in seen:
                unique_candidates.append((strategy, q))
                seen.add(normalized_q)
        
        return unique_candidates[:limit]
        
    except Exception as e:
        logger.error(f"Error generating candidates: {e}")
        return [("original", query)]

def reorder_where_conditions(query: str) -> str:
    """Reorder WHERE conditions for potential optimization"""
    try:
        where_match = re.search(r'WHERE\s+(.+?)(?:\s+GROUP|\s+ORDER|\s*$)', query, re.IGNORECASE | re.DOTALL)
        if not where_match:
            return query
            
        where_clause = where_match.group(1).strip()
        conditions = [c.strip() for c in where_clause.split(' AND ')]
        
        if len(conditions) > 1:
            # Simple heuristic: put more selective conditions first
            # Conditions with = are typically more selective than > or <
            def selectivity_score(condition):
                if '=' in condition and 'BETWEEN' not in condition.upper():
                    return 1  # Most selective
                elif any(op in condition for op in ['BETWEEN', 'IN (']):
                    return 2  # Moderately selective
                elif any(op in condition for op in ['>', '<', '>=', '<=']):
                    return 3  # Less selective
                else:
                    return 4  # Least selective
            
            conditions.sort(key=selectivity_score)
            reordered_where = ' AND '.join(conditions)
            return query.replace(where_match.group(1), reordered_where)
    except Exception:
        pass
    
    return query

# Load ML model
cost_model, trained_features = load_cost_model()
if cost_model:
    print("✅ ML cost predictor loaded.")
else:
    print("⚠️ No ML model found; falling back to EXPLAIN/heuristic.")

def predict_cost(query, max_permutations=10):
    """Generate candidates, extract features, predict costs."""
    candidates = generate_candidates(query, limit=max_permutations)
    scored = []

    for strategy, cand_query in candidates:
        feats = extract_features(cand_query, None)

        # ML prediction
        if cost_model is not None:
            try:
                if trained_features:
                    row = [feats.get(f, 0) for f in trained_features]
                    X = pd.DataFrame([row], columns=trained_features)
                else:
                    X = pd.DataFrame([feats])
                pred = float(cost_model.predict(X)[0])
            except Exception as e:
                print(f"⚠️ Prediction failed for {strategy}: {e}")
                pred = get_query_cost(cand_query)
        else:
            pred = get_query_cost(cand_query)

        # Ensure cost is valid
        if pred is None or (isinstance(pred, float) and np.isnan(pred)):
            pred = get_query_cost(cand_query)

        scored.append((strategy, cand_query, pred))

    # Sort by predicted cost
    return sorted(scored, key=lambda x: (x[2] if x[2] is not None else float("inf")))

# -------------------------------
# CLI
# -------------------------------
def main():
    parser = argparse.ArgumentParser(description="SQL Optimizer CLI")
    parser.add_argument("--query", type=str, help="SQL query to optimize", required=True)
    parser.add_argument("--max_permutations", type=int, default=10, help="Max candidate rewrites")
    args = parser.parse_args()

    print("\n🔎 Optimizing query:")
    print(args.query)

    scored_candidates = predict_cost(args.query, max_permutations=args.max_permutations)

    print("\n📊 Candidate queries and predicted costs:")
    for strat, q, c in scored_candidates:
        c_str = f"{c:.2f}" if isinstance(c, (int, float)) else str(c)
        preview = q if len(q) <= 100 else q[:100] + "..."
        print(f"[{strat}] Cost: {c_str} | Query preview: {preview}")

    best_strategy, best_query, best_cost = scored_candidates[0]
    print("\n✅ Best query selected:")
    print(f"Strategy: {best_strategy}")
    print(best_query)
    print(f"Predicted cost: {best_cost:.2f}")

if __name__ == "__main__":
    main()