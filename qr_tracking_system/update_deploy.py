import paramiko
import os

def hot_reload_backend():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect('167.172.217.151', username='root', password='MERcenta2026!.ds', timeout=10)
        
        stdin, stdout, stderr = client.exec_command("docker ps --format '{{.Names}}' | grep qr-tracking")
        container_name = stdout.read().decode().strip().split('\n')[0]
        
        if container_name:
            sftp = client.open_sftp()
            sftp.put(r'C:\Users\joaou\.gemini\antigravity\QR tracking\qr_tracking_system\app.py', '/tmp/app.py')
            sftp.put(r'C:\Users\joaou\.gemini\antigravity\QR tracking\qr_tracking_system\database.py', '/tmp/database.py')
            sftp.close()
            
            # Copy into container
            client.exec_command(f"docker cp /tmp/app.py {container_name}:/app/app.py")
            client.exec_command(f"docker cp /tmp/database.py {container_name}:/app/database.py")
            
            # Restart container
            print("Restarting container...")
            client.exec_command(f"docker restart {container_name}")
            
            print("Backend hot-reloaded successfully!")
        else:
            print("NO CONTAINER FOUND")
            
    finally:
        client.close()

if __name__ == '__main__':
    hot_reload_backend()
