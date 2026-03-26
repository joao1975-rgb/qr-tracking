import os
from database import get_db_connection, IS_POSTGRES
from dotenv import load_dotenv

load_dotenv()

with open("v280_package/migration_campaigns_v280.sql", "r", encoding="utf-8") as f:
    sql = f.read()

# SQLite does not support multiple statements in execute(), so we split by ';'
# Also SQLite 'ALTER TABLE ADD COLUMN IF NOT EXISTS' syntax might not be supported in older versions,
# but let's try. SQLite 3.25.0+ supports IF NOT EXISTS for ADD COLUMN but actually wait, SQLite ALTER TABLE ADD COLUMN does not support IF NOT EXISTS.
# So we need to handle it. 

try:
    with get_db_connection() as conn:
        cursor = conn.cursor()
        print(f"Connected to {'PostgreSQL' if IS_POSTGRES else 'SQLite'} database.")
        
        statements = [s.strip() for s in sql.split(';') if s.strip()]
        for stmt in statements:
            if not IS_POSTGRES:
                if "ADD COLUMN" in stmt.upper():
                    stmt = stmt.replace("IF NOT EXISTS ", "")
                    try:
                        cursor.execute(stmt)
                    except Exception as e:
                        if "duplicate column name" in str(e).lower():
                            continue
                        else:
                            raise e
                    continue
                elif "CREATE OR REPLACE VIEW" in stmt.upper():
                    view_name_start = stmt.upper().find("VIEW ") + 5
                    view_name_end = stmt.upper().find(" AS")
                    view_name = stmt[view_name_start:view_name_end].strip()
                    cursor.execute(f"DROP VIEW IF EXISTS {view_name}")
                    stmt = stmt.replace("CREATE OR REPLACE VIEW", "CREATE VIEW")
                # SQLite doesn't support ILIKE, use LIKE
                if "ILIKE" in stmt.upper():
                    stmt = stmt.replace("ILIKE", "LIKE")
                    stmt = stmt.replace("ilike", "like")
            
            cursor.execute(stmt)
                
        conn.commit()
        print("Migration applied successfully!")
except Exception as e:
    print(f"Migration failed: {e}")
