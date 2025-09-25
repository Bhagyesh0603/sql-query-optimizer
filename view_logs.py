#!/usr/bin/env python3
"""
Query Logs Viewer - Display contents of query_logs table in a readable format
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from db import get_connection
import json
from datetime import datetime

def view_query_logs():
    """Display query logs in a readable format"""
    try:
        conn = get_connection()
        cur = conn.cursor()
        
        # First, get count of total queries
        cur.execute("SELECT COUNT(*) FROM query_logs;")
        total_count = cur.fetchone()[0]
        print(f"📊 Total queries in log: {total_count}")
        print("=" * 80)
        
        if total_count == 0:
            print("❌ No queries found in query_logs table.")
            return
        
        # Get all queries with formatted output
        query = """
        SELECT 
            id,
            original_query,
            rewritten_query,
            original_cost,
            predicted_cost,
            best_cost,
            db_cost,
            created_at,
            features_json
        FROM query_logs 
        ORDER BY created_at DESC 
        LIMIT 10;
        """
        
        cur.execute(query)
        rows = cur.fetchall()
        
        for i, row in enumerate(rows, 1):
            id_val, orig_query, rewritten, orig_cost, pred_cost, best_cost, db_cost, created_at, features_json = row
            
            print(f"🔍 Query #{id_val} - {created_at}")
            print("-" * 60)
            
            print("📝 Original Query:")
            print(f"   {orig_query[:100]}{'...' if len(orig_query) > 100 else ''}")
            
            if rewritten and rewritten != orig_query:
                print("✨ Rewritten Query:")
                print(f"   {rewritten[:100]}{'...' if len(rewritten) > 100 else ''}")
            
            print("💰 Costs:")
            print(f"   Original: {orig_cost}")
            print(f"   Predicted: {pred_cost}")
            print(f"   Best: {best_cost}")
            print(f"   DB Cost: {db_cost}")
            
            if features_json:
                try:
                    features = json.loads(features_json)
                    print("🔧 Features:")
                    for key, value in features.items():
                        if isinstance(value, float):
                            print(f"   {key}: {value:.2f}")
                        else:
                            print(f"   {key}: {value}")
                except:
                    print("🔧 Features: [JSON parsing error]")
            
            print("=" * 80)
            
            if i >= 5:  # Limit to first 5 for readability
                remaining = total_count - 5
                if remaining > 0:
                    print(f"... and {remaining} more queries")
                break
        
        cur.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Error viewing query logs: {e}")

def view_simple_logs():
    """Display just the queries in a simple format"""
    try:
        conn = get_connection()
        cur = conn.cursor()
        
        query = """
        SELECT 
            id,
            original_query,
            created_at
        FROM query_logs 
        ORDER BY created_at DESC;
        """
        
        cur.execute(query)
        rows = cur.fetchall()
        
        print(f"📋 Query Log Summary ({len(rows)} queries):")
        print("=" * 80)
        
        for id_val, orig_query, created_at in rows:
            print(f"ID {id_val}: {orig_query[:80]}{'...' if len(orig_query) > 80 else ''}")
            print(f"        Created: {created_at}")
            print("-" * 40)
        
        cur.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Error viewing simple logs: {e}")

if __name__ == "__main__":
    print("🚀 SQL Query Optimizer - Query Logs Viewer")
    print("=" * 50)
    
    if len(sys.argv) > 1 and sys.argv[1] == "--simple":
        view_simple_logs()
    else:
        view_query_logs()
        
    print("\n💡 Use --simple flag for basic query list")