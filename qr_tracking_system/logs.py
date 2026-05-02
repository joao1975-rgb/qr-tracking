import paramiko
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('167.172.217.151', username='root', password='MERcenta2026!.ds', timeout=10)
stdin, stdout, stderr = client.exec_command("docker ps --format '{{.Names}}'")
containers = stdout.read().decode().strip().split('\n')
container = next((c for c in containers if 'qr-tracking' in c), None)

cmd = f"docker logs --tail 20 {container}"
stdin, stdout, stderr = client.exec_command(cmd)
print('LOGS:', stdout.read().decode())
print('ERROR LOGS:', stderr.read().decode())
client.close()
