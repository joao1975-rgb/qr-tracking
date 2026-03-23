import paramiko

ip = "167.172.217.151"
user = "root"
password = "MERcenta2026!.ds"

print("🔍 Revisando procesos de Python y el Entrypoint del contenedor...")

try:
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(ip, username=user, password=password, timeout=10)
    
    # Get the qr-tracking container ID
    stdin, stdout, stderr = client.exec_command("docker ps --format '{{.ID}} {{.Names}}' | grep qr-tracking")
    containers = stdout.read().decode('utf-8').strip()
    container_name = containers.split(' ')[1] if containers else None
    
    if container_name:
        cmd1 = f"docker exec -i {container_name} ps auxww | grep -i python"
        stdin, stdout, stderr = client.exec_command(cmd1)
        print("--- PROCESOS DE PYTHON ---")
        print(stdout.read().decode('utf-8'))
        
        cmd2 = f"docker inspect {container_name} --format '{{{{json .Config.Cmd}}}}'"
        stdin, stdout, stderr = client.exec_command(cmd2)
        print("\n--- ENTRYPOINT / CMD ---")
        print(stdout.read().decode('utf-8'))
        
    client.close()
    
except Exception as e:
    print(f"Error: {e}")
