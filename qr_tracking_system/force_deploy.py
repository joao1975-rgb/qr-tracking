import paramiko

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('167.172.217.151', username='root', password='MERcenta2026!.ds')

stdin, stdout, stderr = client.exec_command("docker ps --format '{{.Names}}' | grep easypanel | head -n 1")
easypanel_container = stdout.read().decode('utf-8').strip()

print(f"Encontrado easypanel: {easypanel_container}")

if easypanel_container:
    print("Desplegando project_qr-tracking...")
    cmd = f"docker exec {easypanel_container} easypanel deploy project qr-tracking"
    stdin, stdout, stderr = client.exec_command(cmd)
    for line in stdout:
        print(line, end='')
    
    err = stderr.read().decode('utf-8')
    if err:
        print("Errores: ", err)

client.close()
