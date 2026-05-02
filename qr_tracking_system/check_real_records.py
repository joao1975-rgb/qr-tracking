import paramiko
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('167.172.217.151', username='root', password='MERcenta2026!.ds', timeout=5)
stdin, stdout, stderr = client.exec_command('docker exec -i postgres-qr psql -U qr_admin -d qr_database -c "SELECT campaign_code, COUNT(*), MIN(id), MAX(id) FROM scans GROUP BY campaign_code ORDER BY COUNT(*) ASC;"')
print(stdout.read().decode('utf-8'))
print(stderr.read().decode('utf-8'))
client.close()
