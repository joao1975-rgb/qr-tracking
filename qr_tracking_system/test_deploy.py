import paramiko

ip = "167.172.217.151"
user = "root"
password = "MERcenta2026!.ds"

print("🚀 Disparando el despliegue de EasyPanel vía SSH CLI...")

try:
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(ip, username=user, password=password, timeout=10)
    
    # Executing the deployment command inside the easypanel environment
    # Sometimes it's just `docker pull` and `docker stack deploy` but EasyPanel handles it via internal webhooks or CLI.
    # We will try the undocumented easypanel CLI or curl the webhook if we had it.
    # Alternatively, the safest CLI command is rebooting the Nixpacks builder.
    # Let's see if `easypanel --help` works.
    
    stdin, stdout, stderr = client.exec_command("easypanel --help")
    out = stdout.read().decode('utf-8')
    
    if "deploy" in out:
        print("easypanel CLI detectada, disparando despliegue de qr-tracking...")
        stdin, stdout, stderr = client.exec_command("easypanel deploy project_qr-tracking")
        print(stdout.read().decode('utf-8'))
    else:
        print("La CLI no tiene el comando deploy genérico. Verificando alternativas de webhook...")
        
    client.close()
    
except Exception as e:
    print(f"Error: {e}")
