from app import get_caracas_time
from database import execute_query, get_db_connection

def run_demo():
    print("\n--- DEMO DE HUSO HORARIO (CARACAS) ---")
    
    current_time = get_caracas_time().isoformat()
    print(f"1. Generando timestamp con la lógica corregida: {current_time}")
    
    # 2. Insertar directamente en la BD simulando el endpoint
    print("2. Insertando registro simulado en SQLite...")
    
    query = """
        INSERT INTO scans (
            campaign_code, client, destination, device_id, device_name, 
            location, venue, user_device_type, browser, operating_system, 
            user_agent, ip_address, session_id, scan_timestamp,
            utm_source, utm_medium, utm_campaign, utm_term, utm_content,
            device_brand, device_model
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """
    params = (
        "DEMO", "Demo Client", "http://demo", "DEV_DEMO", "Demo Device",
        "Demo Loc", "Demo Venue", "mobile", "chrome", "android",
        "demo-agent", "127.0.0.1", "demo-sess", current_time,
        "", "", "", "", "", "Unknown", "Unknown"
    )
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        conn.commit()
        
        cursor.execute("SELECT scan_timestamp, device_id FROM scans WHERE campaign_code = 'DEMO' ORDER BY id DESC LIMIT 1")
        row = cursor.fetchone()
        
        if row:
            timestamp_db = row['scan_timestamp']
            print(f"\n=> REGISTRO ENCONTRADO EN BASE DE DATOS:")
            print(f"   Device ID: {row['device_id']}")
            print(f"   Scan Timestamp: {timestamp_db}")
            
            # Verificar si termina en -04:00
            if "-04:00" in timestamp_db:
                print("\n✅ ¡ÉXITO! El registro almacenado contiene explícitamente la zona horaria de Caracas (-04:00).")
                print("Esto demuestra que la corrección horaria está operativa para todas las nuevas transacciones.")
            else:
                print("\n❌ ERROR: El registro no tiene el offset de Caracas.")
        else:
            print("\n❌ No se encontró el registro de prueba.")

if __name__ == "__main__":
    run_demo()
