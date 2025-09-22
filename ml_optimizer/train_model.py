import pandas as pd
import joblib
from sklearn.ensemble import RandomForestRegressor
from sqlalchemy import create_engine
from dotenv import load_dotenv
import os
import urllib.parse

MODEL_PATH = "cost_predictor.joblib"  # switched to joblib for model + metadata

def train_model_function():
    # Load environment variables
    load_dotenv()

    db_user = os.getenv("DB_USER", "postgres")
    raw_password = os.getenv("DB_PASSWORD", "yourpassword")
    db_pass = urllib.parse.quote_plus(raw_password)
    db_host = os.getenv("DB_HOST", "localhost")
    db_port = os.getenv("DB_PORT", "5432")
    db_name = os.getenv("DB_NAME", "sql_optimizer")

    db_url = f"postgresql+psycopg2://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}"
    engine = create_engine(db_url)

    # Load query logs
    df = pd.read_sql("SELECT * FROM query_logs", engine)

    # --- Normalize runtime column ---
    if "runtime_ms" not in df.columns:
        if "runtime" in df.columns:
            df = df.rename(columns={"runtime": "runtime_ms"})
        else:
            print("⚠️ No runtime column found in query_logs, skipping training.")
            return

    # Drop invalid rows
    df = df.dropna(subset=["runtime_ms", "features_json"])
    df["runtime_ms"] = pd.to_numeric(df["runtime_ms"], errors="coerce")
    df = df.dropna(subset=["runtime_ms"])

    if df.empty:
        print("⚠️ No valid rows for training, skipping.")
        return

    # Expand JSON features
    features = pd.json_normalize(df["features_json"])
    if "plan_cost" in features.columns:
        features = features.drop(columns=["plan_cost"])

    # Select only the most important features to avoid feature mismatch
    important_features = ['num_tables', 'num_joins', 'query_length', 'num_conditions', 'query_complexity', 'has_order_by']
    available_features = [f for f in important_features if f in features.columns]
    
    if len(available_features) < 3:
        print(f"❌ Not enough features available. Found: {available_features}")
        return

    X = features[available_features].fillna(0)
    y = df["runtime_ms"]

    print(f"✅ Training on {len(df)} samples, {len(available_features)} features: {available_features}")

    # Train model
    model = RandomForestRegressor(n_estimators=50, random_state=42)
    model.fit(X, y)

    # Save model + feature names
    joblib.dump({
        "model": model,
        "features": available_features  # Use consistent feature list
    }, MODEL_PATH)

    print(f"🎉 Model trained (runtime-based) and saved to {MODEL_PATH}")
