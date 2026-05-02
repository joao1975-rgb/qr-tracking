import paramiko
import json

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('167.172.217.151', username='root', password='MERcenta2026!.ds', timeout=10)

stdin, stdout, stderr = client.exec_command("docker ps --format '{{.Names}}'")
containers = stdout.read().decode().strip().split('\n')
container = next((c for c in containers if 'qr-tracking' in c), None)

cmd = f"docker exec {container} python -c \"\n\
from database import get_db_connection\n\
with get_db_connection() as conn:\n\
    cursor = conn.cursor()\n\
    cursor.execute('''\n\
        SELECT \n\
            COALESCE(SUM(target_scans), 100) as target_scans,\n\
            COALESCE(SUM(target_unique_visitors), 50) as target_unique_visitors,\n\
            COALESCE(AVG(target_ctr_pct), 2.5) as target_ctr_pct\n\
        FROM campaigns\n\
        WHERE active = true;\n\
    ''')\n\
    targets = dict(cursor.fetchone())\n\
    print(targets)\n\
\""
stdin, stdout, stderr = client.exec_command(cmd)
print('STDOUT:', stdout.read().decode())
print('STDERR:', stderr.read().decode())
client.close()
