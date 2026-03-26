import paramiko

def get_live_errors():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect('167.172.217.151', username='root', password='MERcenta2026!.ds', timeout=10)
        
        stdin, stdout, stderr = client.exec_command("docker ps --format '{{.Names}}' | grep qr-tracking")
        container_name = stdout.read().decode().strip().split('\n')[0]
        
        if container_name:
            cmd2 = f"docker exec {container_name} curl -s http://localhost:8080/api/analytics/dashboard"
            stdin, stdout, stderr = client.exec_command(cmd2)
            res2 = stdout.read().decode()
            print("API DASH 8080:", res2[:1000] if len(res2)>1000 else res2)
            
            cmd_logs = f"docker logs --tail 20 {container_name}"
            stdin, stdout, stderr = client.exec_command(cmd_logs)
            logs = stdout.read().decode()
            print("DOCKER LOGS:", logs)
        else:
            print("NO CONTAINER FOUND")
            
    finally:
        client.close()

if __name__ == '__main__':
    get_live_errors()
