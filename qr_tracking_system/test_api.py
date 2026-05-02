import paramiko
import json

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('167.172.217.151', username='root', password='MERcenta2026!.ds', timeout=10)

stdin, stdout, stderr = client.exec_command("docker ps --format '{{.Names}}'")
containers = stdout.read().decode().strip().split('\n')
container = next((c for c in containers if 'qr-tracking' in c), None)

cmd = f"docker exec {container} curl -s http://localhost:8000/api/analytics/dashboard"
stdin, stdout, stderr = client.exec_command(cmd)
out = stdout.read().decode()
try:
    print(json.dumps(json.loads(out), indent=2)[:800])
except Exception:
    print('RAW:', out[:800])

client.close()
