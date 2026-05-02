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
    cursor.execute('SELECT COUNT(*) FROM scans;')\n\
    c = cursor.fetchone()[0]\n\
    print('Total scans:', c)\n\
\""
stdin, stdout, stderr = client.exec_command(cmd)
print('STDOUT:', stdout.read().decode())
print('STDERR:', stderr.read().decode())
client.close()
