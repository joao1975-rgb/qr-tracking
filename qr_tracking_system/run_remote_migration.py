import paramiko
import os
import sys

def run_migration():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    print("Connecting to server...")
    try:
        client.connect('167.172.217.151', username='root', password='MERcenta2026!.ds', timeout=10)
        
        # Get container name
        stdin, stdout, stderr = client.exec_command("docker ps --format '{{.Names}}' | grep qr-tracking | head -n 1")
        container_name = stdout.read().decode().strip()
        
        if not container_name:
            print("NO CONTAINER FOUND")
            return
            
        print(f"Container found: {container_name}")
        
        # 1. Create runner script
        runner_script = """import os
import sys
sys.path.insert(0, '/app')
from database import get_postgres_connection, IS_POSTGRES
from dotenv import load_dotenv

load_dotenv()

with open("/tmp/migration_campaigns_v280.sql", "r", encoding="utf-8") as f:
    sql = f.read()

try:
    if not IS_POSTGRES:
        print("DATABASE IS NOT CONFIGURED AS POSTGRES. URL:", os.getenv("DATABASE_URL"))
        exit(1)
        
    with get_postgres_connection() as conn:
        cursor = conn.cursor()
        print("Connected to PostgreSQL database.")
        
        statements = [s.strip() for s in sql.split(';') if s.strip()]
        for stmt in statements:
            # remove comment lines to see if it's empty
            clean_stmt = '\\n'.join([line for line in stmt.split('\\n') if not line.strip().startswith('--')]).strip()
            if not clean_stmt:
                continue
            
            try:
                cursor.execute(stmt)
            except Exception as ex:
                if 'already exists' in str(ex).lower():
                    print(f"Skipping (already exists): {stmt[:30]}...")
                    # psycopg2 automatically aborts the transaction on error, so we must rollback
                    conn.rollback()
                else:
                    print(f"Error on: {stmt[:50]}... => {ex}")
                    conn.rollback()
                    raise ex
            else:
                conn.commit()
                
        # List columns in campaigns to verify
        cursor.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'campaigns';")
        cols = [r[0] for r in cursor.fetchall()]
        print("MIGRATION APPLIED SUCCESSFULLY! Columns now in 'campaigns':")
        print(", ".join(cols))
        
except Exception as e:
    print(f"Migration failed: {e}")
"""
        with open("migrate_runner_tmp.py", "w", encoding="utf-8") as f:
            f.write(runner_script)

        # 2. Upload both files
        sftp = client.open_sftp()
        print("Uploading sql script...")
        sftp.put(r'C:\Users\joaou\.gemini\antigravity\QR tracking\qr_tracking_system\migration_campaigns_v280.sql', '/tmp/migration_campaigns_v280.sql')
        print("Uploading runner script...")
        sftp.put('migrate_runner_tmp.py', '/tmp/migrate_runner.py')
        sftp.close()
        
        # 3. Copy to container and execute
        print("Copying into Docker container...")
        client.exec_command(f"docker cp /tmp/migration_campaigns_v280.sql {container_name}:/tmp/migration_campaigns_v280.sql")
        client.exec_command(f"docker cp /tmp/migrate_runner.py {container_name}:/tmp/migrate_runner.py")
        
        print("Executing migration inside the container...")
        stdin, stdout, stderr = client.exec_command(f"docker exec -w /app {container_name} python /tmp/migrate_runner.py")
        
        print("--- STDOUT ---")
        print(stdout.read().decode())
        print("--- STDERR ---")
        print(stderr.read().decode())
        
        # Cleanup
        os.remove("migrate_runner_tmp.py")
        print("Done!")

    except Exception as e:
        print(f"Connection failed: {e}")
    finally:
        client.close()

if __name__ == '__main__':
    run_migration()
