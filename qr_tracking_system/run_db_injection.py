import paramiko

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('167.172.217.151', username='root', password='MERcenta2026!.ds', timeout=10)

stdin, stdout, stderr = client.exec_command("docker ps --format '{{.Names}}'")
containers = stdout.read().decode().strip().split('\n')
container_name = next((c for c in containers if 'qr-tracking' in c), None)

if container_name:
    sftp = client.open_sftp()
    sftp.put(r'C:\Users\joaou\.gemini\antigravity\QR tracking\qr_tracking_system\inject_targets.py', '/tmp/inject_targets.py')
    sftp.close()
    
    cmd = f"docker cp /tmp/inject_targets.py {container_name}:/app/inject_targets.py"
    client.exec_command(cmd)
    
    cmd2 = f"docker exec {container_name} python /app/inject_targets.py"
    stdin2, stdout2, stderr2 = client.exec_command(cmd2)
    print("STDOUT:", stdout2.read().decode())
    print("STDERR:", stderr2.read().decode())

client.close()
