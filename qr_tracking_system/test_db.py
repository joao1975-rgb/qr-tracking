import os
import psycopg2
from psycopg2.extras import DictCursor
from dotenv import load_dotenv

load_dotenv()
db_url = os.environ.get('DATABASE_URL')
# If localhost connection fails, it might mean the DB is remote
if 'localhost' in db_url or '127.0.0.1' in db_url:
    # Use remote DB URL for diagnostic if local doesn't work, wait I don't know the remote URL
    pass

try:
    conn = psycopg2.connect(db_url, cursor_factory=DictCursor)
    cur = conn.cursor()
    cur.execute("SELECT id, user_agent, device_brand, device_model, redirect_completed, duration_seconds FROM scans ORDER BY id DESC LIMIT 5")
    rows = cur.fetchall()
    print("----- RECENT SCANS -----")
    for r in rows:
        print(dict(r))
except Exception as e:
    print(f"ERROR: {e}")
