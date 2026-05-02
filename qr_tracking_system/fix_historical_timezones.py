import os
import sqlite3
from database import get_db_connection, IS_POSTGRES
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("timezone_fixer")

def fix_historical_timezones():
    """
    Subtacts 4 hours from existing historical records to correctly adjust
    them from UTC to America/Caracas (UTC-4) timezone.
    """
    logger.info(f"Starting historical timezone correction on {'PostgreSQL' if IS_POSTGRES else 'SQLite'}...")

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            if IS_POSTGRES:
                # In PostgreSQL, we subtract 4 hours from the TIMESTAMP columns.
                # scans table
                cursor.execute("""
                    UPDATE scans 
                    SET scan_timestamp = scan_timestamp - INTERVAL '4 hours',
                        redirect_timestamp = redirect_timestamp - INTERVAL '4 hours'
                    WHERE scan_timestamp IS NOT NULL
                """)
                scans_updated = cursor.rowcount

                # campaigns table
                cursor.execute("""
                    UPDATE campaigns 
                    SET created_at = created_at - INTERVAL '4 hours',
                        updated_at = updated_at - INTERVAL '4 hours'
                    WHERE created_at IS NOT NULL
                """)
                campaigns_updated = cursor.rowcount

                # physical_devices table
                cursor.execute("""
                    UPDATE physical_devices 
                    SET created_at = created_at - INTERVAL '4 hours',
                        updated_at = updated_at - INTERVAL '4 hours'
                    WHERE created_at IS NOT NULL
                """)
                devices_updated = cursor.rowcount

                # qr_generations table
                cursor.execute("""
                    UPDATE qr_generations 
                    SET generated_at = generated_at - INTERVAL '4 hours'
                    WHERE generated_at IS NOT NULL
                """)
                qr_updated = cursor.rowcount

            else:
                # In SQLite, we use datetime() function to subtract 4 hours
                cursor.execute("""
                    UPDATE scans 
                    SET scan_timestamp = datetime(scan_timestamp, '-4 hours'),
                        redirect_timestamp = datetime(redirect_timestamp, '-4 hours')
                    WHERE scan_timestamp IS NOT NULL
                """)
                scans_updated = cursor.rowcount

                cursor.execute("""
                    UPDATE campaigns 
                    SET created_at = datetime(created_at, '-4 hours'),
                        updated_at = datetime(updated_at, '-4 hours')
                    WHERE created_at IS NOT NULL
                """)
                campaigns_updated = cursor.rowcount

                cursor.execute("""
                    UPDATE physical_devices 
                    SET created_at = datetime(created_at, '-4 hours'),
                        updated_at = datetime(updated_at, '-4 hours')
                    WHERE created_at IS NOT NULL
                """)
                devices_updated = cursor.rowcount

                cursor.execute("""
                    UPDATE qr_generations 
                    SET generated_at = datetime(generated_at, '-4 hours')
                    WHERE generated_at IS NOT NULL
                """)
                qr_updated = cursor.rowcount

            conn.commit()

            logger.info("Timezone correction completed successfully.")
            logger.info(f"Updated records:")
            logger.info(f"- Scans: {scans_updated}")
            logger.info(f"- Campaigns: {campaigns_updated}")
            logger.info(f"- Physical Devices: {devices_updated}")
            logger.info(f"- QR Generations: {qr_updated}")

    except Exception as e:
        logger.error(f"Error executing timezone correction: {e}")
        raise

if __name__ == "__main__":
    fix_historical_timezones()
