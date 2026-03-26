import paramiko

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('167.172.217.151', username='root', password='MERcenta2026!.ds')

stdin, stdout, stderr = client.exec_command("docker exec $(docker ps -q -f name=qr-tracking | head -n 1) curl -s http://localhost:8080/api/analytics/scan-breakdown/CENTAURO_Q1_2026")
out = stdout.read().decode('utf-8')
print("Dashboard Response:")
print(out)
client.close()
