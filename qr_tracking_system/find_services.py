import paramiko

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('167.172.217.151', username='root', password='MERcenta2026!.ds')

python_script = """
import os, json
for root, dirs, files in os.walk('/etc/easypanel'):
    for file in files:
        if file == 'meta.json':
            path = os.path.join(root, file)
            with open(path, 'r') as f:
                c = f.read()
                if 'qr' in c:
                    print(f"FOUND IN: {path}")
                    try:
                        d = json.loads(c)
                        if 'source' in d and 'deployWebhookUrl' in d['source']:
                            print("WEBHOOK:", d['source']['deployWebhookUrl'])
                    except: pass
"""

stdin, stdout, stderr = client.exec_command(f'python3 -c "{python_script}"')
print("STDOUT:", stdout.read().decode())
print("STDERR:", stderr.read().decode())

client.close()
