import sqlite3
import os

db_path = "qr_tracking.db"
if not os.path.exists(db_path):
    print(f"Warning: {db_path} not found.")
    db_path = "qr_tracking_system.db" # fallback
    if not os.path.exists(db_path):
        db_path = "database.db"

print(f"Applying SQLite migration to: {db_path}")

columns_to_add = [
    ("product_name", "TEXT"),
    ("start_date", "DATE"),
    ("end_date", "DATE"),
    ("campaign_status", "TEXT DEFAULT 'draft'"),
    ("campaign_phase", "TEXT DEFAULT 'pre_launch'"),
    ("account_manager", "TEXT"),
    ("hashtag", "TEXT"),
    ("tags", "TEXT"),
    ("industry", "TEXT"),
    ("industry_sub", "TEXT"),
    ("geo_country", "TEXT"),
    ("geo_region", "TEXT"),
    ("is_benchmark_eligible", "BOOLEAN DEFAULT FALSE"),
    ("campaign_type", "TEXT DEFAULT 'branding'"),
    ("campaign_objective", "TEXT"),
    ("dooh_format", "TEXT"),
    ("creative_type", "TEXT"),
    ("venue_category", "TEXT"),
    ("budget_tier", "TEXT"),
    ("budget_currency", "TEXT DEFAULT 'USD'"),
    ("target_audience", "TEXT"),
    ("social_amplification", "BOOLEAN DEFAULT FALSE"),
    ("social_platforms", "TEXT"),
    ("influencer_support", "BOOLEAN DEFAULT FALSE"),
    ("internal_notes", "TEXT"),
    ("target_scans", "INTEGER"),
    ("target_unique_visitors", "INTEGER"),
    ("target_ctr_pct", "REAL"),
    ("benchmark_group", "TEXT"),
    ("planned_duration_days", "INTEGER")
]

conn = sqlite3.connect(db_path)
cur = conn.cursor()

for col, dtype in columns_to_add:
    try:
        cur.execute(f"ALTER TABLE campaigns ADD COLUMN {col} {dtype}")
        print(f"Added {col}")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e).lower():
            pass # already exists
        else:
            print(f"Error adding {col}: {e}")

conn.commit()
conn.close()
print("SQLite migration complete.")
