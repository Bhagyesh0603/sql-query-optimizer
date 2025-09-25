import os
import json
import psycopg2
import sqlparse
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "sql_optimizer")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")

import os
from urllib.parse import quote_plus
from dotenv import load_dotenv
from sqlalchemy import create_engine

load_dotenv()

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "sql_optimizer")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")

# Encode password safely
DB_PASSWORD_ENC = quote_plus(DB_PASSWORD)

DATABASE_URL = f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD_ENC}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

engine = create_engine(DATABASE_URL)

engine = create_engine(DATABASE_URL)

def extract_features(query: str) -> dict:
    """
    Super basic feature extractor (can be improved later).
    """
    tokens = query.lower()
    return {
        "tables": tokens.count(" join ") + 1 if " join " in tokens else 1,
        "joins": tokens.count(" join "),
        "filters": tokens.count(" where "),
        "aggregations": sum(tokens.count(word) for word in [" group by", " count", " sum", " avg"]),
        "columns": tokens.count(",") + 1 if "select" in tokens else 0,
    }

def run_explain(query: str) -> float:
    """
    Run EXPLAIN (FORMAT JSON) and return total cost.
    """
    with engine.connect() as conn:
        result = conn.execute(text(f"EXPLAIN (FORMAT JSON) {query}"))
        plan_json = result.fetchone()[0]  # first column is JSON
        plan = plan_json[0]  # unwrap array
        return plan["Plan"]["Total Cost"]

def collect_and_log(queries_file: str):
    """
    Read SQL file, run EXPLAIN, log into query_logs.
    """
    with open(queries_file, "r") as f:
        sql_text = f.read()

    queries = [q.strip() for q in sqlparse.split(sql_text) if q.strip()]

    with engine.begin() as conn:
        for q in queries:
            try:
                cost = run_explain(q)
                features = extract_features(q)
                conn.execute(
                text("INSERT INTO query_logs (query_text, features_json, db_cost) VALUES (:q, :f, :c)"),
                {"q": q, "f": json.dumps(features), "c": cost})

                print(f"✅ Logged query with cost {cost:.2f}")
            except Exception as e:
                print(f"❌ Failed for query:\n{q}\nError: {e}")

if __name__ == "__main__":
    collect_and_log("benchmark_queries.sql")
