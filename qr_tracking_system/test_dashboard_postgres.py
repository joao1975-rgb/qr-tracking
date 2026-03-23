import os
import psycopg2
import json
from config import DATABASE_URL, IS_POSTGRES

def run_postgres_dashboard_validation():
    print("=" * 60)
    print("🚀 VALIDACIÓN DE DASHBOARD E INDICADORES (POSTGRESQL)")
    print("=" * 60)
    
    if not IS_POSTGRES:
        print("❌ ERROR: DATABASE_URL no apunta a PostgreSQL.")
        print("Asegúrate de configurar DATABASE_URL en tu archivo .env")
        return False
        
    print(f"✅ Conectando a PostgreSQL en EasyPanel...")
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        print("✅ Conexión establecida.\n")
        
        # 1. Validar nuevos campos en tabla campaigns
        print("📊 PRUEBA 1: Validación de Schema v2.8 (campaigns)")
        cur.execute("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'campaigns'
            AND column_name IN ('industry', 'campaign_type', 'budget_tier', 'benchmark_group');
        """)
        columns = cur.fetchall()
        for col in columns:
            print(f"  - Encontrado: {col[0]} ({col[1]})")
            
        if len(columns) < 4:
            print("  ⚠️ Advertencia: No se encontraron todos los campos nuevos v2.8 en campaigns.")
        else:
            print("  ✅ Esquema v2.8 desplegado correctamente en campaigns.")
            
        # 2. Validar tabla scans
        print("\n📊 PRUEBA 2: Validación de Schema (scans)")
        cur.execute("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'scans'
            AND column_name IN ('is_unique', 'duration_seconds', 'device_pixel_ratio');
        """)
        scan_cols = cur.fetchall()
        for col in scan_cols:
            print(f"  - Encontrado: {col[0]} ({col[1]})")
            
        # 3. Prueba de Indicadores del Dashboard
        print("\n📈 PRUEBA 3: Auditar Métricas e Indicadores del Dashboard")
        cur.execute("""
            SELECT 
                COUNT(*) as total_scans,
                COUNT(CASE WHEN is_unique THEN 1 END) as unique_visitors,
                AVG(duration_seconds) as avg_duration
            FROM scans;
        """)
        dashboard_metrics = cur.fetchone()
        print("  - Total Escaneos Globales:", dashboard_metrics[0])
        print("  - Visitantes Únicos Globales:", dashboard_metrics[1])
        print("  - Duración Promedio (segundos):", dashboard_metrics[2] if dashboard_metrics[2] else 0)
        
        # 4. Prueba del Pool de Benchmarks (v_benchmark_pool)
        print("\n🔍 PRUEBA 4: Validación de la vista de Benchmarks Anónimos")
        try:
            cur.execute("SELECT * FROM v_benchmark_pool LIMIT 5;")
            benchmarks = cur.fetchall()
            print(f"  ✅ Vista v_benchmark_pool accesible. {len(benchmarks)} registros semilla encontrados.")
        except psycopg2.errors.UndefinedTable:
            print("  ❌ ERROR: La vista v_benchmark_pool no existe en PostgreSQL.")
            conn.rollback()

    except Exception as e:
        print(f"\n❌ Error Crítico durante la validación: {e}")
    finally:
        if 'conn' in locals() and conn:
            conn.close()
            print("\n✅ Conexión cerrada.")

if __name__ == "__main__":
    run_postgres_dashboard_validation()
