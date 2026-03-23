import paramiko
import os

ip = "167.172.217.151"
user = "root"
password = "MERcenta2026!.ds"

print(f"Connecting to {user}@{ip} via Paramiko SSH...")

try:
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(ip, username=user, password=password, timeout=10)
    
    # Run docker ps to find the postgres container and exposed ports
    print("\n--- Running Docker Check ---")
    stdin, stdout, stderr = client.exec_command("docker ps --format '{{.Names}} | {{.Ports}}' | grep -i postgres")
    output = stdout.read().decode('utf-8').strip()
    print(output)
    
    if not output:
        print("No postgres container found!")
    else:
        # Extract environment variables directly from the docker inspect command
        container_name = output.split("|")[0].strip()
        print(f"\n--- Extracting vars from {container_name} ---")
        
        stdin, stdout, stderr = client.exec_command(f"docker inspect {container_name} | grep -E 'POSTGRES_USER|POSTGRES_PASSWORD|POSTGRES_DB'")
        env_vars = stdout.read().decode('utf-8').strip()
        print(env_vars)

    client.close()
    
except Exception as e:
    print(f"Failed to SSH or execute command: {e}")
