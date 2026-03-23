import paramiko

ip = "167.172.217.151"
user = "root"
password = "MERcenta2026!.ds"

print("🔍 Obteniendo Logs de Docker en Vivo...")

try:
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(ip, username=user, password=password, timeout=10)
    
    # Get the qr-tracking container ID
    stdin, stdout, stderr = client.exec_command("docker ps -a --format '{{.ID}} {{.Names}}' | grep qr-tracking")
    containers = stdout.read().decode('utf-8').strip()
    
    container_name = containers.split(' ')[1] if containers else None
    
    if container_name:
        print(f"\n--- Sacando los ultimos 50 logs de {container_name} ---")
        stdin, stdout, stderr = client.exec_command(f"docker logs --tail 50 {container_name}")
        print(stdout.read().decode('utf-8'))
        print(stderr.read().decode('utf-8'))
        
    client.close()
    
except Exception as e:
    print(f"Error: {e}")
