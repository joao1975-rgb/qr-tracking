import psycopg2
import json
import time

NEON_URL = "postgresql://neondb_owner:npg_AOUY8hzcWEX3@ep-silent-bird-acva379a-pooler.sa-east-1.aws.neon.tech/neondb?sslmode=require"

def get_table(conn, table_name):
    # Fetch data
    cursor = conn.cursor()
    cursor.execute(f"SELECT * FROM {table_name}")
    columns = [desc[0] for desc in cursor.description]
    rows = cursor.fetchall()
    
    data = []
    for row in rows:
        # Convert datetime to string
        row_dict = {}
        for i, val in enumerate(row):
            if hasattr(val, 'isoformat'):
                val = val.isoformat()
            row_dict[columns[i]] = val
        data.append(row_dict)
    return data

def main():
    for _ in range(5):
        try:
            print("Connecting to NeonDB...")
            conn = psycopg2.connect(NEON_URL, connect_timeout=10)
            
            export_data = {}
            for t in ["campaigns", "scans", "physical_devices", "qr_generations"]:
                try:
                    export_data[t] = get_table(conn, t)
                except Exception as e:
                    print(f"Skipped {t}: {e}")
            
            with open("neondb_dump.json", "w", encoding="utf-8") as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2)

            print(f"Dumped {sum(len(v) for v in export_data.values())} records from NeonDB.")
            conn.close()
            return
        except Exception as e:
            print(f"NeonDB Connection Error: {e}")
            time.sleep(2)
            
main()
