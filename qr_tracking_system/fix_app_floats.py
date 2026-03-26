import re

with open('app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace simple ROUND(AVG(x), 2)
# Example: ROUND(AVG(s.duration_seconds), 2) -> ROUND(CAST(AVG(s.duration_seconds) AS numeric), 2)
content = re.sub(
    r"ROUND\(\s*AVG\((.*?)\)\s*,\s*(\d+)\s*\)",
    r"ROUND(CAST(AVG(\1) AS numeric), \2)",
    content,
    flags=re.IGNORECASE
)

# Replace COALESCE variants: ROUND(COALESCE(AVG(x), 0), 2)
# Example: ROUND(COALESCE(AVG(s.duration_seconds), 0), 2) -> ROUND(CAST(COALESCE(AVG(s.duration_seconds), 0) AS numeric), 2)
content = re.sub(
    r"ROUND\(\s*COALESCE\(\s*AVG\((.*?)\)\s*,\s*0\s*\)\s*,\s*(\d+)\s*\)",
    r"ROUND(CAST(COALESCE(AVG(\1), 0) AS numeric), \2)",
    content,
    flags=re.IGNORECASE
)

# Replace any lingering ROUND(avg_duration, 2) where avg_duration might be a float
content = re.sub(
    r"ROUND\(\s*COALESCE\(\s*avg_duration\s*,\s*0\s*\)\s*,\s*(\d+)\s*\)",
    r"ROUND(CAST(COALESCE(avg_duration, 0) AS numeric), \1)",
    content,
    flags=re.IGNORECASE
)

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Patch applied to app.py")
