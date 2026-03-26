import paramiko
import json

try:
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect('167.172.217.151', username='root', password='MERcenta2026!.ds')
    
    stdin, stdout, stderr = ssh.exec_command("docker ps --format '{{.ID}}' -f name=qr-tracking | head -n 1")
    cid = stdout.read().decode().strip()
    
    stdin, stdout, stderr = ssh.exec_command("docker service inspect project_qr-tracking")
    data = json.loads(stdout.read().decode())
    if data and len(data) > 0:
        labels = data[0].get('Spec', {}).get('Labels', {})
        urls = []
        for key, value in labels.items():
            if 'traefik.http.routers' in key and 'rule' in key and 'Host(' in value:
                # Value looks like: Host(`example.com`)
                domain = value.split('`')[1] if '`' in value else value.split('(')[1].split(')')[0]
                urls.append(f"https://{domain}")
        if urls:
            print("FOUND URLS:", ", ".join(urls))
        else:
            print("No domains found in labels. Here are all labels:", labels)
    else:
        print("No container found")
except Exception as e:
    print("Error:", e)
finally:
    ssh.close()
