import sqlite3
import glob

files = glob.glob('backups/*.db')
files.append('qr_tracking.db')

for f in files:
    try:
        c = sqlite3.connect(f)
        cur = c.cursor()
        cur.execute("SELECT COUNT(*) FROM scans")
        val = cur.fetchone()[0]
        print(f"{f} scans table: {val}")
    except Exception as e:
        try:
            cur.execute("SELECT COUNT(*) FROM qr_scans")
            val = cur.fetchone()[0]
            print(f"{f} qr_scans table: {val}")
        except Exception as e2:
            print(f"{f}: no valid scans table found.")
