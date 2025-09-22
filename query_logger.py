import psycopg2
from psycopg2.extras import Json
from datetime import datetime
import numpy as np

from db import get_connection

def create_query_logs_table():
    """Create query_logs table if it doesn't exist"""
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS query_logs (
                id SERIAL PRIMARY KEY,
                original_query TEXT,
                rewritten_query TEXT,
                original_cost NUMERIC,
                rewritten_cost NUMERIC,
                predicted_cost NUMERIC,
                best_cost NUMERIC,
                db_cost NUMERIC,
                features_json JSONB,
                explain_original JSONB,
                explain_rewritten JSONB,
                runtime_ms NUMERIC,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
    except Exception as e:
        print(f"⚠️ Failed to create query_logs table: {e}")
    finally:
        cur.close()
        conn.close()

def get_table_columns():
    """Fetch actual columns of query_logs table."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT column_name
        FROM information_schema.columns
        WHERE table_name = 'query_logs';
    """)
    cols = [r[0] for r in cur.fetchall()]
    cur.close()
    conn.close()
    return set(cols)

def log_query(
    original_query,
    rewritten_query=None,
    original_cost=None,
    rewritten_cost=None,
    predicted_cost=None,
    best_cost=None,
    db_cost=None,
    features=None,
    explain_original=None,
    explain_rewritten=None,
    runtime=None,   # 👈 comes from EXPLAIN ANALYZE Actual Total Time
):
    conn = get_connection()
    cur = conn.cursor()

    available_cols = get_table_columns()

    # Convert numpy types to Python types to avoid psycopg2 issues
    def convert_numpy(value):
        if isinstance(value, np.number):
            return value.item()
        return value

    # Mapping of Python vars to DB columns
    values_map = {
        "original_query": original_query,
        "rewritten_query": rewritten_query,
        "original_cost": convert_numpy(original_cost),
        "rewritten_cost": convert_numpy(rewritten_cost),
        "predicted_cost": convert_numpy(predicted_cost),
        "best_cost": convert_numpy(best_cost),
        "db_cost": convert_numpy(db_cost) if db_cost is not None else 0.0,
        "runtime_ms": convert_numpy(runtime),   # ✅ renamed for consistency
        "features_json": Json(features) if features else Json({}),
        "explain_original": Json(explain_original) if explain_original else None,
        "explain_rewritten": Json(explain_rewritten) if explain_rewritten else None,
        "created_at": datetime.now(),
        "logged_at": datetime.now(),
    }

    # Keep only valid columns
    valid_cols = [c for c in values_map if c in available_cols]
    valid_vals = [values_map[c] for c in valid_cols]

    sql = f"""
        INSERT INTO query_logs ({", ".join(valid_cols)})
        VALUES ({", ".join(["%s"] * len(valid_cols))})
    """

    try:
        cur.execute(sql, valid_vals)
        conn.commit()
        print(f"✅ Logged query successfully ({len(valid_cols)} cols).")
    except Exception as e:
        conn.rollback()
        print(f"❌ Failed to log query: {e}")
    finally:
        cur.close()
        conn.close()
