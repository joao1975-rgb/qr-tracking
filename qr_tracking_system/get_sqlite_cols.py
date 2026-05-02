import sqlite3
conn = sqlite3.connect('qr_tracking.db')
cur = conn.cursor()
cur.execute("PRAGMA table_info(scans)")
for row in cur.fetchall():
    print(row[1])
