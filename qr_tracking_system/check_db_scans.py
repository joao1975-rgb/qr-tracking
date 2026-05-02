import psycopg2
conn = psycopg2.connect(
    host="167.172.217.151",
    database="postgres",
    user="postgres",
    password="M3renta_DB!2024",
    port="5432"
)
c = conn.cursor()
c.execute("SELECT COUNT(*) FROM scans")
print("COUNT:", c.fetchone()[0])
conn.close()
