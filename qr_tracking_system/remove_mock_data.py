import paramiko

script_docker = """
import logging
import database
logging.basicConfig(level=logging.INFO)

try:
    with database.get_db_connection() as c:
        cursor = c.cursor()
        
        mock_codes = [
            'HIST-01-2025', 
            'HIST-02-2025', 
            'BENCH-RETAIL-01', 
            'BENCH-RETAIL-02', 
            'CENTAURO_Q1_2026'
        ]
        
        # Count before deletion
        cursor.execute("SELECT COUNT(*) FROM scans")
        before_scans = cursor.fetchone()[0]
        
        # Delete dummy scans
        cursor.execute("DELETE FROM scans WHERE campaign_code IN %s", (tuple(mock_codes),))
        deleted_scans = cursor.rowcount
        
        # Delete dummy campaigns
        cursor.execute("DELETE FROM campaigns WHERE campaign_code IN %s", (tuple(mock_codes),))
        deleted_campaigns = cursor.rowcount
        
        c.commit()
        
        # Check remaining
        cursor.execute("SELECT COUNT(*) FROM scans")
        after_scans = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM campaigns")
        after_campaigns = cursor.fetchone()[0]
        
        print(f"DELETED {deleted_scans} fake scans and {deleted_campaigns} fake campaigns.")
        print(f"REMAINING SCANS: {after_scans} (Should be EXACTLY 59)")
        print(f"REMAINING CAMPAIGNS: {after_campaigns}")
        
except Exception as e:
    import traceback
    traceback.print_exc()
"""

try:
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect('167.172.217.151', username='root', password='MERcenta2026!.ds', timeout=10)
    
    stdin, stdout, stderr = client.exec_command("docker ps --format '{{.ID}} {{.Names}}' | grep qr-tracking")
    containers = stdout.read().decode('utf-8').strip()
    container_name = containers.split(' ')[1] if containers else None
    
    if container_name:
        cmd = f"docker exec -i {container_name} python"
        stdin, stdout, stderr = client.exec_command(cmd)
        stdin.write(script_docker)
        stdin.flush()
        stdin.channel.shutdown_write()
        
        print(stdout.read().decode('utf-8'))
        print(stderr.read().decode('utf-8'))
        
    client.close()
except Exception as e:
    print(f"Error: {e}")
