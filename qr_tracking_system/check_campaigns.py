import paramiko

script_docker = """
import logging
import database
logging.basicConfig(level=logging.INFO)

try:
    with database.get_db_connection() as c:
        cursor = c.cursor()
        cursor.execute("SELECT campaign_code, COUNT(*), MIN(id), MAX(id) FROM scans GROUP BY campaign_code ORDER BY COUNT(*) ASC")
        rows = cursor.fetchall()
        for r in rows:
            print(r)
except Exception as e:
    import traceback
    traceback.print_exc()
"""

try:
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect('167.172.217.151', username='root', password='MERcenta2026!.ds', timeout=10)
    
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
