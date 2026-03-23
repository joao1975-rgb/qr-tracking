import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    print("ERROR: DATABASE_URL not found in environment.")
    exit(1)

SQL_FILE = "migration_campaigns_v280.sql"

try:
    with open(SQL_FILE, "r", encoding="utf-8") as f:
        sql_commands = f.read()
        
    print(f"Connecting to DB at: {DATABASE_URL.split('@')[-1]}")
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()
    
    print("Executing migration...")
    cursor.execute(sql_commands)
    conn.commit()
    
    print("Migration executed successfully!")
    
except Exception as e:
    print(f"Error during migration: {e}")
finally:
    if 'conn' in locals() and conn:
        cursor.close()
        conn.close()
