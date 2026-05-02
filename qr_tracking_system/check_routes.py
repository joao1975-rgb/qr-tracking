import paramiko

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('167.172.217.151', username='root', password='MERcenta2026!.ds')

cmd = "docker exec $(docker ps -qf 'name=project_qr-tracking' | head -n 1) grep -Hn '@app.get(\"/dashboard\"' /app/app.py"
stdin, stdout, stderr = client.exec_command(cmd)
out = stdout.read().decode('utf-8')
print("--- GREP RESULTS ---")
print(out)
client.close()
