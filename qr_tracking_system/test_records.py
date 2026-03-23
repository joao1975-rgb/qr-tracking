import paramiko

ip = "167.172.217.151"
user = "root"
password = "MERcenta2026!.ds"

print("🔍 Validando la cantidad real de registros en el contenedor PostgreSQL de EasyPanel...")

script_docker = """
import logging
import database
logging.basicConfig(level=logging.INFO)

try:
    with database.get_db_connection() as c:
        cursor = c.cursor()
        cursor.execute("SELECT COUNT(*) as c FROM campaigns")
        res_camp = cursor.fetchone()
        
        cursor.execute("SELECT COUNT(*) as c FROM scans")
        res_scans = cursor.fetchone()
        
        print("TOTAL CAMPAIGNS:", res_camp)
        print("TOTAL SCANS:", res_scans)
except Exception as e:
    import traceback
    traceback.print_exc()
"""

try:
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(ip, username=user, password=password, timeout=10)
    
    # Get the qr-tracking container ID
    stdin, stdout, stderr = client.exec_command("docker ps --format '{{.ID}} {{.Names}}' | grep qr-tracking")
    containers = stdout.read().decode('utf-8').strip()
    container_name = containers.split(' ')[1] if containers else None
    
    if container_name:
        cmd = f"docker exec -i {container_name} python"
        stdin, stdout, stderr = client.exec_command(cmd)
        stdin.write(script_docker)
        stdin.flush()
        stdin.channel.shutdown_write()
        
        print(stdout.read().decode('utf-8'))
        print(stderr.read().decode('utf-8'))
        
    client.close()
    
except Exception as e:
    print(f"Error: {e}")
