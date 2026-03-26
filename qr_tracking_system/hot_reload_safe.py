import paramiko
import os
import time

def hot_reload_all():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect('167.172.217.151', username='root', password='MERcenta2026!.ds', timeout=10)
        
        stdin, stdout, stderr = client.exec_command("docker ps --format '{{.Names}}' | grep qr-tracking | head -n 1")
        container_name = stdout.read().decode().strip()
        
        if container_name:
            sftp = client.open_sftp()
            
            # Upload backend files
            sftp.put(r'C:\Users\joaou\.gemini\antigravity\QR tracking\qr_tracking_system\app.py', '/tmp/app.py')
            sftp.put(r'C:\Users\joaou\.gemini\antigravity\QR tracking\qr_tracking_system\database.py', '/tmp/database.py')
            
            # Upload template files
            sftp.put(r'C:\Users\joaou\.gemini\antigravity\QR tracking\qr_tracking_system\templates\phygital_dashboard.html', '/tmp/phygital_dashboard.html')
            sftp.put(r'C:\Users\joaou\.gemini\antigravity\QR tracking\qr_tracking_system\templates\admin_system_benchmarks.html', '/tmp/admin_system_benchmarks.html')
            sftp.put(r'C:\Users\joaou\.gemini\antigravity\QR tracking\qr_tracking_system\templates\admin_campaigns.html', '/tmp/admin_campaigns.html')
            
            sftp.close()
            
            commands = [
                f"docker cp /tmp/app.py {container_name}:/app/app.py",
                f"docker cp /tmp/database.py {container_name}:/app/database.py",
                f"docker cp /tmp/phygital_dashboard.html {container_name}:/app/templates/phygital_dashboard.html",
                f"docker cp /tmp/admin_system_benchmarks.html {container_name}:/app/templates/admin_system_benchmarks.html",
                f"docker cp /tmp/admin_campaigns.html {container_name}:/app/templates/admin_campaigns.html",
                # Instead of docker restart (which changes Swarm IP and causes 502 Traefik mismatch),
                # send a HUP signal to gunicorn to reload its workers gracefully.
                f"docker exec {container_name} kill -HUP 1"
            ]
            
            for cmd in commands:
                client.exec_command(cmd)
            
            print("Backend and Frontend hot-reloaded successfully with SIGHUP!")
            
        else:
            print("NO CONTAINER FOUND")
            
    finally:
        client.close()

if __name__ == '__main__':
    hot_reload_all()
