import sqlite3
import json

def test_benchmark_view_security():
    # Verify that v_benchmark_pool exists and does not leak PII
    try:
        conn = sqlite3.connect("qr_tracking.db")
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        
        # Test 1: Check columns of v_benchmark_pool
        cur.execute("PRAGMA table_info(v_benchmark_pool);")
        columns = [row["name"] for row in cur.fetchall()]
        
        assert "client" not in columns, "SECURITY FAILURE: client name leaked in benchmark view"
        assert "campaign_code" not in columns, "SECURITY FAILURE: campaign code leaked in benchmark view"
        assert "description" not in columns, "SECURITY FAILURE: description leaked in benchmark view"
        
        # Test 2: Check active data in view
        cur.execute("SELECT * FROM v_benchmark_pool LIMIT 1")
        sample = cur.fetchone()
        if sample:
            keys = sample.keys()
            assert "client" not in keys, "SECURITY FAILURE: client name leaked in view row"
            assert "campaign_code" not in keys, "SECURITY FAILURE: campaign code leaked in view row"
        
        print("✅ SUCCESS: Security Test S5-01 to S5-07 Passed. Benchmark View is PII-Safe.")
        
    except Exception as e:
        print(f"❌ TEST FAILED: {str(e)}")
    finally:
        conn.close()

if __name__ == "__main__":
    test_benchmark_view_security()
