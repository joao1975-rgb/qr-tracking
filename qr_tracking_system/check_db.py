import sqlite3

def check_db():
    try:
        conn = sqlite3.connect('qr_tracking.db')
        cursor = conn.cursor()
        
        # Obtenemos las columnas
        cursor.execute("PRAGMA table_info(scans)")
        columns = [col[1] for col in cursor.fetchall()]
        print("Columns in scans:", columns)
        
        if 'device_brand' in columns:
            print("device_brand EXISTE en la tabla.")
        else:
            print("ERROR: device_brand no está en la tabla.")
            
        # Obtenemos el último registro
        cursor.execute("SELECT user_device_type, device_brand, device_model, browser, operating_system, user_agent FROM scans ORDER BY id DESC LIMIT 1")
        last_row = cursor.fetchone()
        
        if last_row:
            print(f"LAST RECORD -> Type: {last_row[0]}, Brand: {last_row[1]}, Model: {last_row[2]}, Browser: {last_row[3]}, OS: {last_row[4]}")
            print(f"User Agent: {last_row[5]}")
        else:
            print("No hay registros en la tabla scans.")
            
        conn.close()
    except Exception as e:
        print(f"Grave Error: {e}")

if __name__ == '__main__':
    check_db()
