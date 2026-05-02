import psycopg2
import os

try:
    conn = psycopg2.connect(
        host="167.172.217.151",
        database="postgres",
        user="postgres",
        password="M3renta_DB!2024",
        port="5432"
    )
    cursor = conn.cursor()
    cursor.execute("SELECT MIN(scan_timestamp), MAX(scan_timestamp) FROM scans;")
    res = cursor.fetchone()
    print("MIN MAX TIMESTAMPS:", res)
    
    # Let's count scans 30 days
    cursor.execute("SELECT COUNT(*) FROM scans WHERE scan_timestamp >= NOW() - INTERVAL '30 days'")
    scans_30d = cursor.fetchone()[0]
    print("SCANS IN LAST 30 DAYS:", scans_30d)

except Exception as e:
    print("DB ERROR:", e)
