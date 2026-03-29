import paramiko
import os

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
            sftp.put(r'C:\Users\joaou\.gemini\antigravity\QR tracking\qr_tracking_system\templates\dashboard_antigravity_v28.html', '/tmp/dashboard_antigravity_v28.html')
            sftp.put(r'C:\Users\joaou\.gemini\antigravity\QR tracking\qr_tracking_system\templates\admin_system_benchmarks.html', '/tmp/admin_system_benchmarks.html')
            sftp.put(r'C:\Users\joaou\.gemini\antigravity\QR tracking\qr_tracking_system\templates\admin_campaigns.html', '/tmp/admin_campaigns.html')
            
            sftp.close()
            
            commands = [
                f"docker cp /tmp/app.py {container_name}:/app/app.py",
                f"docker cp /tmp/database.py {container_name}:/app/database.py",
                f"docker cp /tmp/dashboard_antigravity_v28.html {container_name}:/app/templates/dashboard_antigravity_v28.html",
                f"docker cp /tmp/admin_system_benchmarks.html {container_name}:/app/templates/admin_system_benchmarks.html",
                f"docker cp /tmp/admin_campaigns.html {container_name}:/app/templates/admin_campaigns.html",
                f"docker restart {container_name}"
            ]
            
            for cmd in commands:
                stdin, stdout, stderr = client.exec_command(cmd)
                out = stdout.read().decode()
                err = stderr.read().decode()
                print(f'Ran: {cmd}')
                if out: print('STDOUT:', out)
                if err: print('STDERR:', err)
            
            print("Backend and Frontend hot-reloaded successfully!")
            
            # Get domains
            stdin, stdout, stderr = client.exec_command(f"docker inspect {container_name} --format '{{{{json .Config.Labels}}}}'")
            try:
                import json
                labels = json.loads(stdout.read().decode('utf-8'))
                if labels:
                    for k, v in labels.items():
                        if 'traefik.http.routers' in k and 'rule' in k:
                            print(f"Domain found: {v}")
            except:
                pass
        else:
            print("NO CONTAINER FOUND")
            
    finally:
        client.close()

if __name__ == '__main__':
    hot_reload_all()
