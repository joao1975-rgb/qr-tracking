import paramiko
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('167.172.217.151', username='root', password='MERcenta2026!.ds')
stdin, stdout, stderr = client.exec_command('docker ps --format "{{.Names}}"')
out = stdout.read().decode().strip()
print('CONTAINERS:', out)
client.close()
