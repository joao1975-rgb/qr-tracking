import paramiko
import sys
import json

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect("167.172.217.151", username="root", password="MERcenta2026!.ds", timeout=10)

stdin, stdout, stderr = client.exec_command("docker ps --format '{{.Names}}'")
container = next((c for c in stdout.read().decode().splitlines() if 'project_qr-tracking' in c and '-db' not in c), None)

if container:
    script = '''import sys, json; sys.path.append('/app'); from database import get_db_connection; import psycopg2.extras
with get_db_connection() as conn:
    c = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    c.execute("""
        WITH IPCategory AS (
            SELECT 
                ip_address,
                MAX(CASE 
                    WHEN operating_system ILIKE '%ios%' THEN 'iOS Premium'
                    WHEN operating_system ILIKE '%android%' THEN 'Android Flagship'
                    ELSE 'Otros' 
                END) as category,
                COUNT(id) as scan_count
            FROM scans
            GROUP BY ip_address
        )
        SELECT 
            category,
            SUM(scan_count) as count,
            COUNT(ip_address) as unique_devices
        FROM IPCategory
        GROUP BY category
        ORDER BY count DESC
    """)
    res = [dict(r) for r in c.fetchall()]
    print(json.dumps(res, indent=2))
'''
    sftp = client.open_sftp()
    with sftp.file('/tmp/t10.py', 'w') as f:
        f.write(script)
    sftp.close()

    cmd = f"docker cp /tmp/t10.py {container}:/tmp/t10.py ; docker exec {container} python3 /tmp/t10.py"
    stdin, stdout, stderr = client.exec_command(cmd)
    res = stdout.read().decode().strip()
    err = stderr.read().decode().strip()
    print("OUTPUT:\n", res)
    if err:
        print("ERR:\n", err)
client.close()
