import os
from dotenv import load_dotenv
import psycopg2
import psycopg2.extras

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

print(f"Connecting to: {DATABASE_URL}")

try:
    conn = psycopg2.connect(DATABASE_URL)
    conn.cursor_factory = psycopg2.extras.RealDictCursor
    cursor = conn.cursor()
    print("Connection successful!")
    
    # Check tables
    cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
    tables = [t['table_name'] for t in cursor.fetchall()]
    print(f"Tables found: {tables}")
    
    # Try a simple query with %s
    cursor.execute("SELECT COUNT(*) FROM campaigns WHERE client = %s", ('test_client',))
    count = cursor.fetchone()['count']
    print(f"Test query successful! Count: {count}")
    
    conn.close()
    print("All tests passed!")
except Exception as e:
    print(f"Error test: {e}")
