import paramiko
import os
import json

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect("167.172.217.151", username="root", password="MERcenta2026!.ds", timeout=10)

stdin, stdout, stderr = client.exec_command("docker ps --format '{{.Names}}'")
containers = stdout.read().decode().splitlines()
valid_containers = [c for c in containers if 'project_qr-tracking' in c and '-db' not in c]

print(f"FOUND {len(valid_containers)} APP CONTAINERS TO PATCH: {valid_containers}")

if valid_containers:
    sftp = client.open_sftp()
    
    # Upload backend files to /tmp/
    sftp.put(r'C:\Users\joaou\.gemini\antigravity\QR tracking\qr_tracking_system\app.py', '/tmp/app.py')
    sftp.put(r'C:\Users\joaou\.gemini\antigravity\QR tracking\qr_tracking_system\database.py', '/tmp/database.py')
    
    # Upload templates
    sftp.put(r'C:\Users\joaou\.gemini\antigravity\QR tracking\qr_tracking_system\templates\dashboard_antigravity_v28.html', '/tmp/dashboard_antigravity_v28.html')
    sftp.put(r'C:\Users\joaou\.gemini\antigravity\QR tracking\qr_tracking_system\templates\admin_system_benchmarks.html', '/tmp/admin_system_benchmarks.html')
    sftp.put(r'C:\Users\joaou\.gemini\antigravity\QR tracking\qr_tracking_system\templates\admin_campaigns.html', '/tmp/admin_campaigns.html')
    sftp.close()

    for container_name in valid_containers:
        print(f"\n--- PATCHING {container_name} ---")
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
            stdout.read()
            err = stderr.read().decode()
            if err:
                print(f"Error executing {cmd}: {err}")
            else:
                print(f"SUCCESS: {cmd}")

client.close()
print("\nALL CONTAINERS PATCHED AND RESTARTED!")
