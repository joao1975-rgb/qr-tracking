import database

print("Iniciando validación de esquema...")
schema = database.POSTGRES_SCHEMA if database.IS_POSTGRES else database.SQLITE_SCHEMA

with database.get_db_connection() as conn:
    c = conn.cursor()
    for s in schema.split(';'):
        s = s.strip()
        if s:
            try:
                c.execute(s)
            except Exception as e:
                print("--- FAILED STATEMENT ---")
                print(s)
                print("--- ERROR ---")
                print(e)
                break
