import sqlite3
import json

def fetch_table(cursor, table_name):
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = [col[1] for col in cursor.fetchall()]
    
    cursor.execute(f"SELECT * FROM {table_name}")
    rows = cursor.fetchall()
    
    data = []
    for row in rows:
        data.append(dict(zip(columns, row)))
    return data

def main():
    conn = sqlite3.connect("qr_tracking.db")
    cursor = conn.cursor()
    
    tables = ["campaigns", "physical_devices", "qr_generations", "scans"]
    export_data = {}
    
    for t in tables:
        try:
            export_data[t] = fetch_table(cursor, t)
        except Exception as e:
            print(f"Skipped {t}: {e}")
            
    with open("sqlite_dump.json", "w", encoding="utf-8") as f:
        json.dump(export_data, f, ensure_ascii=False, indent=2)

    print(f"Dumped {sum(len(v) for v in export_data.values())} records.")

if __name__ == "__main__":
    main()
