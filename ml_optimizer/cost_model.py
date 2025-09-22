# cost_model.py
import joblib

def load_cost_model(path="cost_predictor.joblib"):
    """
    Load cost prediction model from joblib file.
    Returns (model, trained_features)
    """
    try:
        md = joblib.load(path)
        if isinstance(md, dict):
            return md.get("model"), md.get("features", [])
        return md, []
    except Exception as e:
        print(f"⚠️ Could not load cost model: {e}")
        return None, []

def get_query_cost(query):
    """
    Placeholder for DB EXPLAIN or heuristic cost.
    Right now returns a dummy value.
    """
    # TODO: integrate with explain_runner.py
    return len(query)  # dummy: length of query as cost
