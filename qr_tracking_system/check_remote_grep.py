import paramiko
import os

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
try:
    client.connect('167.172.217.151', username='root', password='MERcenta2026!.ds', timeout=10)
    
    stdin, stdout, stderr = client.exec_command("docker ps -a --format '{{.Names}}' | grep qr-tracking | head -n 1")
    container_name = stdout.read().decode().strip()
    
    if container_name:
        cmd = f"docker exec {container_name} bash -c 'grep kpi-tooltip /app/templates/dashboard_antigravity_v28.html | wc -l'"
        print("Running", cmd)
        stdin, stdout, stderr = client.exec_command(cmd)
        print("Occurrences of kpi-tooltip remotely:", stdout.read().decode().strip())
    else:
        print("No container found.")
finally:
    client.close()
