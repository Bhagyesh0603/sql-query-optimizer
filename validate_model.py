# ml_optimizer/validate_model.py
import pandas as pd
from sklearn.metrics import mean_absolute_error, r2_score

def validate_logs(log_file="query_logs.sqlite"):
    import sqlite3
    conn = sqlite3.connect(log_file)

    df = pd.read_sql("SELECT predicted_cost, db_cost FROM query_logs WHERE db_cost IS NOT NULL", conn)
    conn.close()

    if df.empty:
        print("⚠️ No logged queries with real DB costs.")
        return

    mae = mean_absolute_error(df["db_cost"], df["predicted_cost"])
    r2 = r2_score(df["db_cost"], df["predicted_cost"])

    print("=== ML Model Validation ===")
    print(f"Queries evaluated: {len(df)}")
    print(f"MAE (lower = better): {mae:.2f}")
    print(f"R² (closer to 1 = better): {r2:.2f}")
