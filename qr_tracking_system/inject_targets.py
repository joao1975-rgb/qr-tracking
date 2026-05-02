from database import get_db_connection
import sys

def main():
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            # Set manual targets for the active campaign 
            # (DEMO_COMPLETA, or all active campaigns since there's only 1 for this test)
            cursor.execute("""
                UPDATE campaigns
                SET target_scans = 500,
                    target_unique_visitors = 250,
                    target_ctr_pct = 3.75
                WHERE active = true;
            """)
            conn.commit()
            print(f"Updated {cursor.rowcount} campaigns with exact targets: 500, 250, 3.75%")
            cursor.close()
    except Exception as e:
        print(f"Failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
