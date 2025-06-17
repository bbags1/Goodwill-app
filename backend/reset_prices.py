#!/usr/bin/env python3
"""
Reset script to clear all resale price estimates and related fields,
allowing items to be reprocessed through the updated Gemini model.
"""

import sqlite3
import logging
import sys
from db import DB_PATH, get_db_cursor
from datetime import datetime
import pytz

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("reset.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("price_reset")

def reset_price_estimates():
    """Reset all price estimates and related fields in the database."""
    try:
        with get_db_cursor() as cursor:
            # Get current time in Pacific timezone
            pacific = pytz.timezone('US/Pacific')
            current_time = datetime.now(pacific).strftime('%Y-%m-%dT%H:%M:%S')
            
            # Get count of items before reset
            cursor.execute("""
                SELECT COUNT(*) as count 
                FROM items 
                WHERE auction_end_time > ? 
                AND ebay_price IS NOT NULL
            """, (current_time,))
            before_count = cursor.fetchone()['count']
            
            # Reset all price-related fields for active items
            cursor.execute("""
                UPDATE items 
                SET ebay_price = NULL,
                    price_update_attempted = 0,
                    last_price_update = NULL,
                    profit = NULL,
                    margin = NULL
                WHERE auction_end_time > ?
            """, (current_time,))
            
            updated_count = cursor.rowcount
            
            logger.info(f"Found {before_count} items with price estimates")
            logger.info(f"Reset {updated_count} active items")
            
            return updated_count
            
    except Exception as e:
        logger.error(f"Error resetting prices: {str(e)}")
        raise

if __name__ == "__main__":
    try:
        logger.info("Starting price reset process...")
        count = reset_price_estimates()
        logger.info(f"Successfully reset {count} items")
    except Exception as e:
        logger.error(f"Reset failed: {str(e)}")
        sys.exit(1) 