import paramiko

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('167.172.217.151', username='root', password='MERcenta2026!.ds')

stdin, stdout, stderr = client.exec_command("docker exec $(docker ps -qf 'name=project_qr-tracking' | head -n 1) cat /app/app.py | grep -i 'def dashboard' -A 10")
out = stdout.read().decode('utf-8')
print("--- APP.PY IN CONTAINER ---")
print(out)
client.close()
