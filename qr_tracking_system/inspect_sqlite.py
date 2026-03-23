import sqlite3
import traceback

print("Checking SQLite schema...")
try:
    c = sqlite3.connect('qr_tracking.db')
    for row in c.execute("SELECT name, sql FROM sqlite_master WHERE sql IS NOT NULL").fetchall():
        print(f"--- {row[0]} ---")
        if "1.0" in row[1]:
            print("FOUND 1.0 IN:", row[0])
            print(row[1])
except Exception as e:
    print(e)
    traceback.print_exc()
