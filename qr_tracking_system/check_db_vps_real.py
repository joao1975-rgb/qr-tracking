import paramiko
code = '''
from database import get_db_connection

with get_db_connection() as conn:
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM scans")
    print("TOTAL:", cur.fetchone()[0])
    cur.execute("SELECT COUNT(*) FROM scans WHERE redirect_completed = true")
    print("EXITOSOS:", cur.fetchone()[0])
'''

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('167.172.217.151', username='root', password='MERcenta2026!.ds')
stdin, stdout, stderr = client.exec_command('docker ps -q -f name=project_qr-tracking.1 | head -n 1')
cid = stdout.read().decode().strip().split('\n')[0]

sftp = client.open_sftp()
with sftp.file('/tmp/check_api.py', 'w') as f:
    f.write(code)
sftp.close()

stdin, stdout, stderr = client.exec_command(f'docker cp /tmp/check_api.py {cid}:/app/check_api.py && docker exec {cid} python /app/check_api.py')
print('OUT:', stdout.read().decode())
print('ERR:', stderr.read().decode())
client.close()
