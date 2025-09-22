# ml_optimizer/retrain_model.py
import pandas as pd
import joblib
import json
import os
from sqlalchemy import create_engine
from sklearn.ensemble import RandomForestRegressor
from dotenv import load_dotenv
from urllib.parse import quote_plus

# Load .env variables
load_dotenv()

DB_USER = os.getenv("DB_USER")
DB_PASSWORD = quote_plus(os.getenv("DB_PASSWORD"))  # escape special chars
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME")

if not all([DB_USER, DB_PASSWORD, DB_HOST, DB_PORT, DB_NAME]):
    raise ValueError("❌ Database credentials missing in .env")

# Build SQLAlchemy connection string
DB_URL = f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

def retrain(model_file="ml_optimizer/cost_predictor.joblib"):
    engine = create_engine(DB_URL)

    # Fetch logs
    df = pd.read_sql("SELECT * FROM query_logs WHERE db_cost IS NOT NULL", engine)

    if df.empty:
        print("⚠️ No data available for retraining.")
        return

    # Convert JSON features back to DataFrame
    # If features_json is already dict, don’t load again
    features = pd.json_normalize(df["features_json"].apply(lambda x: json.loads(x) if isinstance(x, str) else x))

    X = features
    y = df["db_cost"]

    # Train ML model
    model = RandomForestRegressor(n_estimators=200, random_state=42)
    model.fit(X, y)

    # Save updated model
    joblib.dump(model, model_file)
    print(f"✅ Model retrained on {len(df)} queries. Saved to {model_file}")

if __name__ == "__main__":
    retrain()
