# db/logger.py
import psycopg2

def log_query_result(conn, original_query, candidate_query,
                     predicted_cost, actual_cost, execution_time):
    try:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO query_logs (original_query, candidate_query,
                                        predicted_cost, actual_cost, execution_time_ms)
                VALUES (%s, %s, %s, %s, %s)
            """, (original_query, candidate_query, predicted_cost, actual_cost, execution_time))
        conn.commit()
    except Exception as e:
        print("❌ Logging failed:", e)
