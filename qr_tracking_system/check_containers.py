import paramiko
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect("167.172.217.151", username="root", password="MERcenta2026!.ds", timeout=10)

stdin, stdout, stderr = client.exec_command("docker ps --format '{{.Names}}'")
containers = stdout.read().decode().splitlines()
print("ALL CONTAINERS:", [c for c in containers if 'qr-tracking' in c])
client.close()
