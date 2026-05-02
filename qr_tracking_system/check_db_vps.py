import paramiko
code = '''
import os
import psycopg2
conn = psycopg2.connect("postgresql://qr_platform:centauro2026@qr-tracking-db:5432/qr_tracking")
cur = conn.cursor()
cur.execute("SELECT COUNT(*) FROM scans")
print("TOTAL:", cur.fetchone()[0])
cur.execute("SELECT COUNT(*) FROM scans WHERE redirect_completed = true")
print("EXITOSOS:", cur.fetchone()[0])
'''

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('167.172.217.151', username='root', password='MERcenta2026!.ds')
sftp = client.open_sftp()
with sftp.file('/tmp/check_db.py', 'w') as f:
    f.write(code)
sftp.close()

# get container ID
stdin, stdout, stderr = client.exec_command('docker ps -q -f name=project_qr-tracking.1')
container_id = stdout.read().decode().strip().split('\n')[0]

cmd = f'docker exec {container_id} python /tmp/check_db.py'
stdin, stdout, stderr = client.exec_command(cmd)
print("OUT:", stdout.read().decode())
print("ERR:", stderr.read().decode())
client.close()
