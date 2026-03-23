import re

with open('app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace CURRENT_TIMESTAMP with get_caracas_time() for python logic
# We must let postgres handle timezone correctly if we are casting
# The better approach is changing the PostgreSQL timezone to 'America/Caracas'
# OR explicitly setting it during connection.

# Let's write a script to append "SET TIME ZONE 'America/Caracas';" to DB connections
def replacer(match):
    return "conn = psycopg2.connect(DATABASE_PATH)\n    cursor = conn.cursor()\n    cursor.execute(\"SET TIME ZONE 'America/Caracas'\")"

new_content = re.sub(r'conn = psycopg2\.connect\(DATABASE_PATH\)', replacer, content)

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(new_content)

print("DB connection updated.")
