import paramiko
import os

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
try:
    client.connect('167.172.217.151', username='root', password='MERcenta2026!.ds', timeout=10)
    
    stdin, stdout, stderr = client.exec_command("docker ps -a --format '{{.Names}}' | grep qr-tracking | head -n 1")
    container_name = stdout.read().decode().strip()
    
    if container_name:
        print(f"Fetching logs for {container_name}...")
        stdin, stdout, stderr = client.exec_command(f'docker logs {container_name} --tail 100')
        print(stderr.read().decode())
        print(stdout.read().decode())
    else:
        print("No container found.")
finally:
    client.close()
