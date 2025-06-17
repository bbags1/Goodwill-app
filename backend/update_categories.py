import sqlite3
import os
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("category_update.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("category_updater")

# Database path - make sure this matches your app configuration
DB_PATH = r'/Users/brodybagnall/Documents/goodwill/Goodwill-app/backend/data/gw_data.db'

def update_categories():
    """Update all category_name values that start with 'Size' to 'Clothing'"""
    if not os.path.exists(DB_PATH):
        logger.error(f"Database file not found at: {DB_PATH}")
        return False
    
    try:
        # Connect to the database
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        # Get count of items that need updating
        c.execute("SELECT COUNT(*) FROM items WHERE category_name LIKE 'Size%'")
        count = c.fetchone()[0]
        logger.info(f"Found {count} items with category_name starting with 'Size'")
        
        if count == 0:
            logger.info("No items need to be updated")
            conn.close()
            return True
        
        # Update all matching records
        c.execute("UPDATE items SET category_name = 'Clothing' WHERE category_name LIKE 'Size%'")
        updated_count = c.rowcount
        
        # Commit the changes
        conn.commit()
        logger.info(f"Successfully updated {updated_count} items from 'Size*' to 'Clothing'")
        
        # Close the connection
        conn.close()
        return True
        
    except Exception as e:
        logger.error(f"Error updating categories: {str(e)}")
        return False

if __name__ == "__main__":
    logger.info("Starting category update process")
    success = update_categories()
    if success:
        logger.info("Category update completed successfully")
    else:
        logger.error("Category update failed") 