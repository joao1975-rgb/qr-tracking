import sys
sys.path.append('.')
try:
    from database import get_db_connection
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'scans'")
        print(cur.fetchall())
except BaseException as e:
    print("Error:", e)
