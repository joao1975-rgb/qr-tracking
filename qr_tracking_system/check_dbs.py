import paramiko
import re

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('167.172.217.151', username='root', password='MERcenta2026!.ds', timeout=10)

stdin, stdout, stderr = client.exec_command("docker ps --format '{{.Names}}' | grep postgres-qr")
container_name = stdout.read().decode().strip()

if container_name:
    print(f"Container: {container_name}")
    stdin, out, err = client.exec_command(f"docker exec {container_name} psql -U qr_admin -d qr_database -c \\"SELECT column_name FROM information_schema.columns WHERE table_name = 'campaigns';\\"")
    databases = out.read().decode()
    print("Schema:\n", databases)
    print("ERR:\n", err.read().decode())
else:
    print("No pg container found.")
client.close()
