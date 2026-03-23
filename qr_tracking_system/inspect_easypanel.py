import paramiko

ip = "167.172.217.151"
user = "root"
password = "MERcenta2026!.ds"

print("🔍 Inspecting EasyPanel App Container Configuration...")

try:
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(ip, username=user, password=password, timeout=10)
    
    # Get the qr-tracking container ID
    stdin, stdout, stderr = client.exec_command("docker ps --format '{{.ID}} {{.Names}}' | grep qr-tracking")
    containers = stdout.read().decode('utf-8').strip()
    print("Contenedores encontrados:")
    print(containers)
    
    container_name = containers.split(' ')[1] if containers else None
    
    if container_name:
        # Inspect environment variables
        cmd = f"docker inspect {container_name} --format '{{{{json .Config.Env}}}}'"
        stdin, stdout, stderr = client.exec_command(cmd)
        env_vars = stdout.read().decode('utf-8')
        print("\n--- Variables de Entorno del Contenedor ---")
        print(env_vars)
        
        # Check EasyPanel configuration JSON if it exists
        stdin, stdout, stderr = client.exec_command("cat /etc/easypanel/projects/*/services/*/meta.json 2>/dev/null | grep qr-tracking -B 2 -A 10")
        print("\n--- EasyPanel Metadata (Branch/Repo) ---")
        print(stdout.read().decode('utf-8'))
        
    client.close()
    
except Exception as e:
    print(f"Error: {e}")
