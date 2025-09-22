# benchmark_runner.py
import argparse
import json
import csv
from typing import List
import pandas as pd
from rewriter import generate_join_candidates
from explain_runner import run_explain  # returns EXPLAIN (FORMAT JSON) parsed
from cost_model import get_query_cost
from query_logger import log_query
from ml_optimizer.train_model import train_model_function
import joblib
from ml_optimizer.feature_extraction import extract_features
from db import get_connection

# Try load ML predictor
try:
    md = joblib.load("cost_predictor.joblib")
    cost_model = md["model"] if isinstance(md, dict) and "model" in md else md
    trained_features = md.get("features") if isinstance(md, dict) else None
    print("✅ ML cost predictor loaded for benchmark.")
except Exception:
    cost_model = None
    trained_features = None
    print("⚠️ No ML predictor found; using DB EXPLAIN for ranking.")


def best_candidate_for_query(query: str) -> dict:
    """Generate candidates and pick best using ML or EXPLAIN cost."""
    candidates = generate_join_candidates(query, max_permutations=10)
    scored = []

    for q in candidates:
        feats = extract_features(q, None)

        if cost_model and trained_features:
            try:
                # Use only the features the model was trained with
                fv = [feats.get(f, 0) for f in trained_features]
                X = pd.DataFrame([fv], columns=trained_features)
                pred = cost_model.predict(X)[0]
            except Exception as e:
                print(f"⚠️ ML prediction failed: {e}")
                pred = get_query_cost(q)
        elif cost_model:
            try:
                # Try with all features
                X = pd.DataFrame([feats])
                pred = cost_model.predict(X)[0]
            except Exception:
                pred = get_query_cost(q)
        else:
            pred = get_query_cost(q)

        scored.append((q, pred))

    best_q, best_cost = sorted(scored, key=lambda x: x[1])[0]
    return {"best_query": best_q, "best_cost": best_cost, "candidates": scored}


def run_explain_analyze_safe(conn, query: str):
    """Run EXPLAIN ANALYZE (executes query)."""
    try:
        cur = conn.cursor()
        cur.execute("EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON) " + query)
        row = cur.fetchone()
        cur.close()
        if row:
            return row[0][0] if isinstance(row[0], list) else row[0]
    except Exception as e:
        print("❌ EXPLAIN ANALYZE failed:", e)
    return None


def run_benchmark(queries: List[str], mode: str = "explain", retrain: bool = False):
    conn = get_connection() if mode == "analyze" else None
    results = []

    for i, q in enumerate(queries, 1):
        print(f"\n=== Query {i}/{len(queries)} ===")
        print(q.strip()[:400], "...\n")

        # Best candidate
        pick = best_candidate_for_query(q)
        best_q, best_pred = pick["best_query"], pick["best_cost"]

        # EXPLAIN costs
        explain_orig = run_explain(q)
        orig_cost = explain_orig.get("Plan", {}).get("Total Cost") if explain_orig else None
        explain_best = run_explain(best_q)
        best_cost_est = explain_best.get("Plan", {}).get("Total Cost") if explain_best else None

        # ANALYZE runtimes
        orig_analyze, best_analyze = None, None
        orig_runtime, best_runtime = None, None
        if mode == "analyze" and conn:
            print("Running EXPLAIN ANALYZE on original (may execute query) ...")
            orig_analyze = run_explain_analyze_safe(conn, q)
            if orig_analyze and "Actual Total Time" in orig_analyze:
                orig_runtime = orig_analyze["Actual Total Time"]

            print("Running EXPLAIN ANALYZE on best candidate ...")
            best_analyze = run_explain_analyze_safe(conn, best_q)
            if best_analyze and "Actual Total Time" in best_analyze:
                best_runtime = best_analyze["Actual Total Time"]

        # ML prediction
        ml_pred = None
        if cost_model and trained_features:
            try:
                feats = extract_features(q, None)
                fv = [feats.get(f, 0) for f in trained_features]
                X = pd.DataFrame([fv], columns=trained_features)
                ml_pred = cost_model.predict(X)[0]
                if pd.isna(ml_pred):
                    ml_pred = get_query_cost(q)
            except Exception as e:
                print(f"⚠️ ML prediction failed: {e}")
                ml_pred = get_query_cost(q)
        elif cost_model:
            try:
                feats = extract_features(q, None)
                X = pd.DataFrame([feats])
                ml_pred = cost_model.predict(X)[0]
                if pd.isna(ml_pred):
                    ml_pred = get_query_cost(q)
            except Exception as e:
                print(f"⚠️ ML prediction failed: {e}")
                ml_pred = get_query_cost(q)

        # Improvements
        improvement_pct_runtime = None
        improvement_pct_ml = None

        if orig_runtime and best_runtime:
            improvement_pct_runtime = (orig_runtime - best_runtime) / orig_runtime * 100.0
            print(f"Original runtime: {orig_runtime:.2f} ms | Best runtime: {best_runtime:.2f} ms")
            print(f"Improvement (runtime): {improvement_pct_runtime:.2f}%")

        if orig_runtime and ml_pred:
            improvement_pct_ml = (orig_runtime - ml_pred) / orig_runtime * 100.0
            print(f"Original runtime (ANALYZE): {orig_runtime:.2f} ms | ML-pred runtime: {ml_pred:.2f} ms")
            print(f"Estimated improvement (ML vs Original): {improvement_pct_ml:.2f}%")

        print(f"Original cost (EXPLAIN): {orig_cost} | Best estimated (EXPLAIN): {best_cost_est} | ML-picked pred: {ml_pred}")

        # Log
        log_query(
            q, best_q,
            orig_cost or 0.0, best_cost_est or best_pred or 0.0,
            predicted_cost=ml_pred,
            runtime=orig_runtime,
            explain_original=explain_orig,
            explain_rewritten=explain_best
        )

        results.append({
            "original_query": q,
            "best_query": best_q,
            "orig_cost": orig_cost,
            "best_cost_est": best_cost_est,
            "ml_pred": ml_pred,
            "runtime_orig": orig_runtime,
            "runtime_best": best_runtime,
            "improvement_runtime_pct": improvement_pct_runtime,
            "improvement_ml_pct": improvement_pct_ml,
            "explain_original": explain_orig,
            "explain_rewritten": explain_best,
            "analyze_original": orig_analyze,
            "analyze_best": best_analyze
        })

    if conn:
        conn.close()

    if retrain:
        print("\nRetraining ML model from logged data...")
        train_model_function()
        print("Retrain finished.")

    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run benchmark queries through optimizer")
    parser.add_argument("--file", type=str, help="Path to file with queries", required=False)
    parser.add_argument("--mode", choices=["explain", "analyze"], default="explain")
    parser.add_argument("--retrain", action="store_true")
    parser.add_argument("--dummy", action="store_true")
    args = parser.parse_args()

    # Queries
    queries = []
    if args.file:
        raw = open(args.file).read()
        queries = [p.strip() + ";" for p in raw.split(";") if p.strip()]
    elif args.dummy:
        queries = [
            "SELECT e.emp_id, e.first_name, d.dept_name FROM employees e JOIN departments d ON e.dept_id = d.dept_id;",
            "SELECT e.emp_id, e.salary, p.proj_name FROM employees e JOIN projects p ON e.dept_id = p.dept_id JOIN salaries s ON e.emp_id = s.emp_id WHERE s.from_date <= '2020-01-01';",
            "SELECT e.emp_id, e.first_name, v.visit_date, pt.name FROM employees e JOIN visits v ON e.emp_id = v.emp_id JOIN appointments a ON v.visit_id = a.visit_id JOIN patients pt ON a.patient_id = pt.patient_id WHERE v.visit_date BETWEEN '2019-01-01' AND '2019-12-31';",
            "SELECT e.emp_id, e.first_name, d.dept_name, p.proj_name, p.budget FROM employees e JOIN departments d ON e.dept_id = d.dept_id JOIN projects p ON d.dept_id = p.dept_id JOIN salaries s ON e.emp_id = s.emp_id JOIN visits v ON e.emp_id = v.emp_id WHERE p.budget > 50000;",
            "SELECT e.emp_id, e.first_name, e.salary, d.dept_name, p.proj_name, doc.name AS doctor_name FROM employees e JOIN departments d ON e.dept_id = d.dept_id JOIN projects p ON d.dept_id = p.dept_id JOIN salaries s ON e.emp_id = s.emp_id JOIN visits v ON e.emp_id = v.emp_id JOIN appointments a ON v.visit_id = a.visit_id JOIN doctors doc ON a.doctor_id = doc.doctor_id WHERE e.hire_date BETWEEN '2015-01-01' AND '2019-12-31';"
        ]
    else:
        queries = [
            "SELECT * FROM employees e JOIN departments d ON e.dept_id = d.dept_id;"
        ]

    results = run_benchmark(queries, mode=args.mode, retrain=args.retrain)

    # Save JSON
    with open("benchmark_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, default=str, indent=2)

    # Save CSV
    with open("benchmark_results.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "original_query", "best_query", "orig_cost", "best_cost_est",
            "ml_pred", "runtime_orig", "runtime_best",
            "improvement_runtime_pct", "improvement_ml_pct"
        ])
        for r in results:
            writer.writerow([
                r["original_query"], r["best_query"], r["orig_cost"],
                r["best_cost_est"], r["ml_pred"], r["runtime_orig"],
                r["runtime_best"], r["improvement_runtime_pct"],
                r["improvement_ml_pct"]
            ])

    print("\nBenchmark complete. Results written to benchmark_results.json and benchmark_results.csv")
