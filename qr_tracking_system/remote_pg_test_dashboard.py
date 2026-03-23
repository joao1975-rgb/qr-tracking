import paramiko

ip = "167.172.217.151"
user = "root"
password = "MERcenta2026!.ds"

print("Iniciando Pruebas de Diagnóstico del Dashboard sobre PostgreSQL (DigitalOcean)...")

try:
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(ip, username=user, password=password, timeout=10)
    
    # Check if the container is running and get its ID
    stdin, stdout, stderr = client.exec_command("docker ps --format '{{.ID}}' --filter 'name=postgres-qr'")
    container_id = stdout.read().decode('utf-8').strip().split('\n')[0]
    
    if not container_id:
        print("❌ No se encontró un contenedor Postgres corriendo.")
        exit(1)
        
    db_user = "qr_admin"
    db_name = "qr_database"

    def run_sql(query):
        cmd = f'docker exec {container_id} psql -U {db_user} -d {db_name} -c "{query}"'
        stdin, stdout, stderr = client.exec_command(cmd)
        return stdout.read().decode('utf-8').strip()

    print("\n--- [PRUEBA 1] Variables Análiticas en Campaigns (v2.8) ---")
    out = run_sql("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'campaigns' AND column_name IN ('industry', 'budget_tier', 'benchmark_group');")
    print(out if out else "❌ No se encontraron las columnas. La migración no ha sido ejecutada.")

    print("\n--- [PRUEBA 2] Métricas Activas en Scans ---")
    out = run_sql("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'scans' AND column_name IN ('duration_seconds', 'is_unique');")
    print(out if out else "❌ Columnas obsoletas.")

    print("\n--- [PRUEBA 3] Benchmarks Globales (Simulación Dashboard) ---")
    out = run_sql("SELECT COUNT(*) as total_scans, COUNT(CASE WHEN is_unique THEN 1 END) as unique_visitors, ROUND(AVG(duration_seconds)::numeric, 1) as avg_time FROM scans;")
    print(out)

    client.close()
    
except Exception as e:
    print(f"Error crítico en la conexión SSH: {e}")
