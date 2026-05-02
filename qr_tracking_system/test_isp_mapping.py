import paramiko

def run_remote_python():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        print("Conectando al servidor...")
        client.connect('167.172.217.151', username='root', password='MERcenta2026!.ds', timeout=15)
        
        py_script = """
import os
import json
import psycopg2
from collections import Counter

DB_URL = os.environ.get('DATABASE_URL', 'postgresql://postgres:S4nt43D2024*@167.99.155.67:5432/qr_tracking_db')

try:
    conn = psycopg2.connect(DB_URL)
    cursor = conn.cursor()
    
    # Obtener el historico donde isp_carrier existe pero connection_type es unknown o nulo
    cursor.execute("SELECT id, isp_carrier, connection_type FROM scans WHERE isp_carrier IS NOT NULL AND (connection_type IS NULL OR connection_type = 'unknown' OR connection_type = '')")
    rows = cursor.fetchall()
    
    cellular_keywords = ['digitel', 'movistar', 'movilnet', 'telefonica', 'cellular', 'mobile', 'lte', '4g', '3g', '5g']
    wifi_keywords = ['cantv', 'inter', 'netuno', 'fibra', 'cable', 'thundernet', 'mds', 'datacamp', 'google', 'proton', 'venezuela', 'global']
    
    updated_count = 0
    wifi_count = 0
    cellular_count = 0
    
    print("====== APLICANDO LÓGICA A HISTÓRICO ======")
    
    for row_id, isp, conn_type in rows:
        if not isp or isp == 'Unknown':
            continue
            
        isp_lower = isp.lower()
        new_conn_type = 'wifi' # Por defecto si es un ISP raro
        
        is_cellular = any(kw in isp_lower for kw in cellular_keywords)
        is_wifi = any(kw in isp_lower for kw in wifi_keywords)
        
        if is_cellular and not is_wifi:
            new_conn_type = 'cellular'
        elif is_wifi and not is_cellular:
            new_conn_type = 'wifi'
        elif is_cellular and is_wifi:
            new_conn_type = 'cellular' # Prioridad a celular si dice "telefonica venezolana" (ambas)
            
        if new_conn_type == 'cellular':
            cellular_count += 1
        else:
            wifi_count += 1
            
        # Actualizamos en BD
        cursor.execute('UPDATE scans SET connection_type = %s WHERE id = %s', (new_conn_type, row_id))
        updated_count += 1
        
    conn.commit()
    
    print(f"Total registros históricos actualizados: {updated_count}")
    print(f"Clasificados como Celular: {cellular_count}")
    print(f"Clasificados como Wi-Fi: {wifi_count}")
    print("==========================================")
    
except Exception as e:
    print('Error:', e)
"""
        escaped_script = py_script.replace('$', '\\$').replace('"', '\\"')
        cmd = f'''
        CONTAINER_ID=$(docker ps -q -f name=project_qr-tracking | head -n 1)
        docker exec -i $CONTAINER_ID python -c "{escaped_script}"
        '''
        stdin, stdout, stderr = client.exec_command(cmd)
        out = stdout.read().decode('utf-8')
        err = stderr.read().decode('utf-8')
        if out: print(out)
        if err: print("ERR:", err)
    except Exception as e:
        print(f"Connection error: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    run_remote_python()
