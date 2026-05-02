import paramiko

def rollback_db():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect('167.172.217.151', username='root', password='MERcenta2026!.ds', timeout=15)
        
        py_script = """
import os
import psycopg2

DB_URL = os.environ.get('DATABASE_URL', 'postgresql://postgres:S4nt43D2024*@167.99.155.67:5432/qr_tracking_db')

try:
    conn = psycopg2.connect(DB_URL)
    cursor = conn.cursor()
    cursor.execute("ALTER TABLE scans DROP COLUMN IF EXISTS meta_fbp;")
    cursor.execute("ALTER TABLE scans DROP COLUMN IF EXISTS click_id;")
    cursor.execute("ALTER TABLE scans DROP COLUMN IF EXISTS dark_mode;")
    cursor.execute("ALTER TABLE scans DROP COLUMN IF EXISTS touch_points;")
    conn.commit()
    print("PostgreSQL Database schema rolled back (columns dropped).")
except Exception as e:
    print('Postgres Error:', e)
finally:
    if 'conn' in locals() and conn:
        conn.close()
"""
        
        escaped_script = py_script.replace('$', '\\$').replace('"', '\\"')
        
        cmd = f'''
        CONTAINER_ID=$(docker ps -q -f name=project_qr-tracking | head -n 1)
        docker exec -i $CONTAINER_ID python -c "{escaped_script}"
        '''
        
        stdin, stdout, stderr = client.exec_command(cmd)
        out = stdout.read().decode('utf-8')
        if out: print(out)
            
    except Exception as e:
        print(f"Connection error: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    rollback_db()
