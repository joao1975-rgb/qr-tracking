import paramiko
import os

def hot_reload_dashboard():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect('167.172.217.151', username='root', password='MERcenta2026!.ds', timeout=10)
        
        stdin, stdout, stderr = client.exec_command("docker ps --format '{{.Names}}' | grep qr-tracking | head -n 1")
        container_name = stdout.read().decode().strip()
        
        if container_name:
            sftp = client.open_sftp()
            
            # Upload ONLY the dashboard template 
            sftp.put(r'C:\Users\joaou\.gemini\antigravity\QR tracking\qr_tracking_system\templates\dashboard_antigravity_v28.html', '/tmp/dashboard_antigravity_v28.html')
            
            sftp.close()
            
            commands = [
                f"docker cp /tmp/dashboard_antigravity_v28.html {container_name}:/app/templates/dashboard_antigravity_v28.html",
                # Don't technically need to restart container for template changes, but just to be safe
                f"docker exec {container_name} touch /app/templates/dashboard_antigravity_v28.html"
            ]
            
            for cmd in commands:
                client.exec_command(cmd)
            
            print("Dashboard hot-reloaded successfully!")
            
        else:
            print("NO CONTAINER FOUND")
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        client.close()

if __name__ == '__main__':
    hot_reload_dashboard()
