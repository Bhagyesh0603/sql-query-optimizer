# predict_cost.py
import joblib
from ml_optimizer.feature_extraction import extract_features
from cost_model import get_query_cost
import pandas as pd

# Load the trained ML model (if exists)
try:
    md = joblib.load("cost_predictor.joblib")
    model = md["model"] if isinstance(md, dict) and "model" in md else md
    trained_features = md.get("features") if isinstance(md, dict) else None
except Exception:
    model = None
    trained_features = None

def predict_cost(query: str) -> float:
    """
    Predict cost for a SQL query using ML model or fallback to EXPLAIN.
    """
    feats = extract_features(query, None)

    if model and trained_features:
        # Ensure features in correct order
        X = [[feats.get(f, 0) for f in trained_features]]
        try:
            return model.predict(X)[0]
        except Exception:
            return get_query_cost(query)
    elif model:
        # No feature order saved: pass as DataFrame
        try:
            X = pd.DataFrame([feats])
            return model.predict(X)[0]
        except Exception:
            return get_query_cost(query)
    else:
        return get_query_cost(query)

