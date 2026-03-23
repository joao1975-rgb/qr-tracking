import paramiko

ip = "167.172.217.151"
user = "root"
password = "MERcenta2026!.ds"

print("🔍 Validando si existe un .env oculto en EasyPanel que esté anulando la configuración Docker...")

try:
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(ip, username=user, password=password, timeout=10)
    
    # Get the qr-tracking container ID
    stdin, stdout, stderr = client.exec_command("docker ps --format '{{.ID}} {{.Names}}' | grep qr-tracking")
    containers = stdout.read().decode('utf-8').strip()
    container_name = containers.split(' ')[1] if containers else None
    
    if container_name:
        cmd = f"docker exec -i {container_name} cat .env"
        stdin, stdout, stderr = client.exec_command(cmd)
        out = stdout.read().decode('utf-8')
        if not out.strip():
            print("No existe archivo .env o está vacío.")
        else:
            print("CONTENIDO DEL .ENV:")
            print(out)
        
    client.close()
    
except Exception as e:
    print(f"Error: {e}")
