import argparse
import logging
from typing import List, Tuple, Optional
import numpy as np
import pandas as pd
import time
from datetime import datetime
from pathlib import Path

from ml_optimizer.feature_extraction import extract_features
from cost_model import get_query_cost, load_cost_model
from optimizer.candidate_generator import generate_candidates

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# -------------------------------
# Load trained ML modeli
# -------------------------------
cost_model, trained_features = load_cost_model()
if cost_model:
    print("✅ ML cost predictor loaded.")
    
else:
    print("⚠️ No ML model found; falling back to EXPLAIN/heuristic.")


# -------------------------------
# Benchmark query performance
# -------------------------------
def benchmark_query(query: str) -> float:
    """Run EXPLAIN ANALYZE and get actual runtime"""
    try:
        from explain_runner import run_explain
        explain_result = run_explain(query)
        if explain_result and "Execution Time" in explain_result:
            return float(explain_result["Execution Time"])
        elif explain_result and "Plan" in explain_result:
            # Fallback to total cost if execution time not available
            plan = explain_result["Plan"]
            return float(plan.get("Total Cost", 0))
        else:
            # Final fallback to heuristic cost
            from cost_model import get_query_cost
            return get_query_cost(query)
    except Exception as e:
        logger.error(f"Benchmark failed: {e}")
        from cost_model import get_query_cost
        return get_query_cost(query)


# -------------------------------
# Predict costs of candidate queries
# -------------------------------
def predict_cost(query: str, max_permutations: int = 10) -> List[Tuple[str, str, float, float]]:
    """
    Generate candidates, extract features, predict costs.
    Returns a sorted list of (strategy, query, predicted_cost, actual_cost)
    """
    try:
        candidates = generate_candidates(query, limit=max_permutations)
        scored: List[Tuple[str, str, float, float]] = []

        for strategy, cand_query in candidates:
            try:
                feats = extract_features(cand_query, None)
                pred: Optional[float] = None

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
                        logger.warning(f"ML prediction failed for {strategy}: {e}")
                        pred = get_query_cost(cand_query)
                else:
                    pred = get_query_cost(cand_query)

                # Ensure cost is valid
                if pred is None or (isinstance(pred, float) and np.isnan(pred)):
                    pred = get_query_cost(cand_query)

                # Get actual cost (simplified benchmark)
                actual_cost = benchmark_query(cand_query)
                
                scored.append((strategy, cand_query, pred, actual_cost))
                
            except Exception as e:
                logger.error(f"Failed to process candidate {strategy}: {e}")
                continue

        return sorted(scored, key=lambda x: (x[2] if x[2] is not None else float("inf")))
        
    except Exception as e:
        logger.error(f"Failed to generate candidates: {e}")
        original_cost = get_query_cost(query)
        return [("original", query, original_cost, 0.0)]


# -------------------------------
# CLI
# -------------------------------
def main():
    parser = argparse.ArgumentParser(description="SQL Optimizer CLI")
    parser.add_argument("--query", type=str, help="SQL query to optimize", required=True)
    parser.add_argument("--max_permutations", type=int, default=10, help="Max candidate rewrites")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    args = parser.parse_args()

    if args.verbose:
        logger.setLevel(logging.DEBUG)

    logger.info("🔎 Optimizing query:")
    logger.info(args.query)

    start_time = datetime.now()
    scored_candidates = predict_cost(args.query, max_permutations=args.max_permutations)
    
    print("\n📊 Optimization Results:")
    print(f"Generated {len(scored_candidates)} candidates")
    print(f"Time taken: {(datetime.now() - start_time).total_seconds():.2f}s")
    
    print("\nCandidate Analysis:")
    print("-" * 80)
    
    for i, (strategy, query, pred_cost, actual_cost) in enumerate(scored_candidates, 1):
        print(f"\n{i}. Strategy: {strategy}")
        print(f"   Predicted Cost: {pred_cost:.2f}")
        print(f"   Actual Cost: {actual_cost:.2f}")
        print(f"   Query Preview: {query[:80]}...")
    
    # Get best candidate
    if scored_candidates:
        best_strategy, best_query, best_pred_cost, best_actual_cost = scored_candidates[0]
        
        print("\n" + "=" * 80)
        print("✅ BEST OPTIMIZATION RESULT")
        print("=" * 80)
        print(f"Strategy: {best_strategy}")
        print(f"Predicted Cost: {best_pred_cost:.2f}")
        print(f"Actual Cost: {best_actual_cost:.2f}")
        
        # Calculate improvement if we have multiple candidates
        if len(scored_candidates) > 1:
            original = next((c for c in scored_candidates if c[0] == "original"), None)
            if original and original != scored_candidates[0]:
                improvement = ((original[2] - best_pred_cost) / original[2] * 100) if original[2] > 0 else 0
                print(f"Estimated Improvement: {improvement:.1f}%")
        
        print(f"\nOptimized Query:")
        print(best_query)
    else:
        print("❌ No candidates generated")


if __name__ == "__main__":
    main()
