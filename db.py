import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "sql_optimizer")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")

def get_connection():
    """Establish and return a new DB connection."""
    conn = psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD
    )
    return conn

def run_sql(query, params=None):
    """
    Run a query and return results as list of dictionaries.
    """
    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, params)
            if cur.description:  # SELECT query
                results = cur.fetchall()
            else:  # INSERT/UPDATE/DELETE
                results = None
                conn.commit()
        return results
    finally:
        conn.close()

def test_connection():
    """Simple test to check DB connection."""
    try:
        result = run_sql("SELECT 1 AS test;")
        print("✅ DB connection successful:", result)
    except Exception as e:
        print("❌ DB connection failed:", e)

if __name__ == "__main__":
    test_connection()
