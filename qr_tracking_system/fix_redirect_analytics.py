import os
import sqlite3
from database import get_db_connection, IS_POSTGRES
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("redirect_analytics_fixer")

def fix_redirect_analytics():
    """
    Sets redirect_completed = TRUE and duration_seconds = 0.1
    for all recent scans that have duration_seconds IS NULL or 0,
    since the new fast redirect bypasses the client-side beacon.
    """
    logger.info(f"Starting redirect analytics correction on {'PostgreSQL' if IS_POSTGRES else 'SQLite'}...")

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            # Update records from the last few days (since the update)
            if IS_POSTGRES:
                cursor.execute("""
                    UPDATE scans 
                    SET redirect_completed = TRUE,
                        duration_seconds = 0.1
                    WHERE (duration_seconds IS NULL OR duration_seconds = 0)
                      AND redirect_completed = FALSE
                      AND scan_timestamp >= NOW() - INTERVAL '5 days'
                """)
            else:
                cursor.execute("""
                    UPDATE scans 
                    SET redirect_completed = 1,
                        duration_seconds = 0.1
                    WHERE (duration_seconds IS NULL OR duration_seconds = 0)
                      AND redirect_completed = 0
                      AND scan_timestamp >= datetime('now', '-5 days')
                """)

            updated = cursor.rowcount
            conn.commit()

            logger.info("Redirect analytics correction completed successfully.")
            logger.info(f"Updated records: {updated}")

    except Exception as e:
        logger.error(f"Error executing redirect analytics correction: {e}")
        raise

if __name__ == "__main__":
    fix_redirect_analytics()
