# ml_optimizer/retrain.py
import psycopg2
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
import joblib

def fetch_training_data(conn):
    query = """
    SELECT candidate_query, actual_cost
    FROM query_logs
    WHERE actual_cost IS NOT NULL
    """
    df = pd.read_sql(query, conn)
    return df

def featurize_query(query):
    # Example features: number of joins, SELECT cols count, WHERE clause length
    return {
        "join_count": query.upper().count("JOIN"),
        "select_count": query.upper().count(",") + 1,
        "where_present": 1 if "WHERE" in query.upper() else 0,
        "query_length": len(query)
    }

def retrain_model(conn, model_path="ml_optimizer/models/cost_model.pkl"):
    df = fetch_training_data(conn)
    if df.empty:
        print("⚠️ No training data found.")
        return
    
    X = pd.DataFrame([featurize_query(q) for q in df["candidate_query"]])
    y = df["actual_cost"]

    model = RandomForestRegressor(n_estimators=100, random_state=42)
    model.fit(X, y)

    joblib.dump(model, model_path)
    print(f"✅ Model retrained and saved to {model_path}")
