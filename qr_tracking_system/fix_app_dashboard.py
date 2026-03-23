import re

with open('app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace SQLite datetimes with PostgreSQL syntax
content = re.sub(r"datetime\('now', '-(.*?)'\)", r"NOW() - INTERVAL '\1'", content)

# I also want to add iOS % and avg_duration to get_dashboard_analytics.
# Currently it is:
#             cursor.execute("""
#                 SELECT
#                     (SELECT COUNT(*) FROM campaigns WHERE active = TRUE) as active_campaigns,
#                     ...
#                     (SELECT COUNT(*) FROM scans WHERE scan_timestamp >= NOW() - INTERVAL '7 days') as scans_7d,
#                     (SELECT COUNT(DISTINCT ip_address) FROM scans) as unique_visitors
#             """)
# Let's add avg_duration and ios_pct to the main SELECT.
new_stats_sql = """
                SELECT
                    (SELECT COUNT(*) FROM campaigns WHERE active = TRUE) as active_campaigns,
                    (SELECT COUNT(*) FROM physical_devices WHERE active = TRUE) as active_devices,
                    (SELECT COUNT(*) FROM scans) as total_scans,
                    (SELECT COUNT(*) FROM scans WHERE redirect_completed = TRUE) as completed_redirects,
                    (SELECT COUNT(DISTINCT client) FROM campaigns WHERE client != '') as total_clients,
                    (SELECT COUNT(*) FROM scans WHERE scan_timestamp >= NOW() - INTERVAL '24 hours') as scans_24h,
                    (SELECT COUNT(*) FROM scans WHERE scan_timestamp >= NOW() - INTERVAL '7 days') as scans_7d,
                    (SELECT COUNT(DISTINCT ip_address) FROM scans) as unique_visitors,
                    (SELECT AVG(duration_seconds) FROM scans) as avg_duration,
                    (SELECT COUNT(*) * 100.0 / NULLIF((SELECT COUNT(*) FROM scans), 0) FROM scans WHERE operating_system ILIKE '%ios%') as ios_pct
"""

old_stats_sql_pattern = r"SELECT\s*\(SELECT\s+COUNT\(\*\)\s+FROM\s+campaigns\s+WHERE\s+active\s+=\s+TRUE\)\s+as\s+active_campaigns,.*?\(\s*SELECT\s+COUNT\(DISTINCT\s+ip_address\)\s+FROM\s+scans\s*\)\s+as\s+unique_visitors"

content = re.sub(old_stats_sql_pattern, new_stats_sql.strip(), content, flags=re.DOTALL)

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(content)
