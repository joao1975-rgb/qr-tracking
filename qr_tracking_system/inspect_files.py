import paramiko

ip = "167.172.217.151"
user = "root"
password = "MERcenta2026!.ds"

print("🔍 Revisando los archivos crudos en el contenedor de EasyPanel...")

try:
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(ip, username=user, password=password, timeout=10)
    
    # Get the qr-tracking container ID
    stdin, stdout, stderr = client.exec_command("docker ps --format '{{.ID}} {{.Names}}' | grep qr-tracking")
    containers = stdout.read().decode('utf-8').strip()
    container_name = containers.split(' ')[1] if containers else None
    
    if container_name:
        print("Buscando si existe industria_sub en templates/admin_campaigns.html adentro del container Docker:")
        cmd = f"docker exec -i {container_name} grep -i 'industria' templates/admin_campaigns.html | head -n 5"
        stdin, stdout, stderr = client.exec_command(cmd)
        out = stdout.read().decode('utf-8').strip()
        print("Resultado grep:", out if out else "¡NO SE ENCONTRÓ! (ES EL TEMPLATE VIEJO v2.7)")
        
        print("\nRevisando el inicio de app.py:")
        cmd2 = f"docker exec -i {container_name} head -n 30 app.py"
        stdin2, stdout2, stderr2 = client.exec_command(cmd2)
        print(stdout2.read().decode('utf-8'))
        
    client.close()
    
except Exception as e:
    print(f"Error: {e}")
