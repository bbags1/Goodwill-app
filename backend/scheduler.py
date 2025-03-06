import schedule
import time
import subprocess
import os
import sqlite3
import logging
from datetime import datetime
import pytz

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("scheduler.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("goodwill_scheduler")

# Database path - update this to your actual path
DB_PATH = r'/Users/brodybagnall/Documents/goodwill/Goodwill-app/backend/data/gw_data.db'

def get_update_frequency():
    """Get the update frequency from the settings."""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT update_frequency FROM settings WHERE id = 1")
        row = c.fetchone()
        conn.close()
        
        if row:
            return row[0]
        return "daily"  # Default to daily
    except Exception as e:
        logger.error(f"Error getting update frequency: {str(e)}")
        return "daily"  # Default to daily

def run_scraper():
    """Run the product scraper."""
    try:
        logger.info("Starting product scraper...")
        
        # Get the current directory
        current_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Run the get_products.py script
        result = subprocess.run(
            ["python", os.path.join(current_dir, "get_products.py")],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            logger.info("Product scraper completed successfully")
        else:
            logger.error(f"Product scraper failed: {result.stderr}")
    except Exception as e:
        logger.error(f"Error running product scraper: {str(e)}")

def run_price_updater():
    """Run the Gemini price updater."""
    try:
        logger.info("Starting price updater...")
        
        # Get the current directory
        current_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Run the gemini.py script
        result = subprocess.run(
            ["python", os.path.join(current_dir, "gemini.py")],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            logger.info("Price updater completed successfully")
        else:
            logger.error(f"Price updater failed: {result.stderr}")
    except Exception as e:
        logger.error(f"Error running price updater: {str(e)}")

def run_notifications():
    """Run the notifications system."""
    try:
        logger.info("Starting notifications system...")
        
        # Get the current directory
        current_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Run the notifications.py script
        result = subprocess.run(
            ["python", os.path.join(current_dir, "notifications.py")],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            logger.info("Notifications sent successfully")
        else:
            logger.error(f"Notifications failed: {result.stderr}")
    except Exception as e:
        logger.error(f"Error sending notifications: {str(e)}")

def run_cleanup():
    """Run the cleanup script to remove old items."""
    try:
        logger.info("Starting cleanup process...")
        
        # Get the current directory
        current_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Run the remove_old.py script
        result = subprocess.run(
            ["python", os.path.join(current_dir, "remove_old.py")],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            logger.info("Cleanup completed successfully")
        else:
            logger.error(f"Cleanup failed: {result.stderr}")
    except Exception as e:
        logger.error(f"Error running cleanup: {str(e)}")

def run_full_update():
    """Run the complete update process."""
    logger.info("Starting full update process...")
    
    # Run each step in sequence
    run_scraper()
    run_price_updater()
    run_notifications()
    run_cleanup()
    
    logger.info("Full update process completed")
    
    # Log current time in Pacific timezone
    pacific = pytz.timezone('US/Pacific')
    pacific_time = datetime.now(pacific)
    logger.info(f"Update completed at {pacific_time.strftime('%Y-%m-%d %H:%M:%S')} Pacific Time")

def setup_schedule():
    """Set up the schedule based on the user's preferences."""
    frequency = get_update_frequency()
    
    logger.info(f"Setting up schedule with frequency: {frequency}")
    
    if frequency == "hourly":
        schedule.every().hour.do(run_full_update)
    elif frequency == "twice_daily":
        schedule.every().day.at("08:00").do(run_full_update)
        schedule.every().day.at("20:00").do(run_full_update)
    elif frequency == "weekly":
        schedule.every().monday.at("08:00").do(run_full_update)
    else:  # Default to daily
        schedule.every().day.at("08:00").do(run_full_update)
    
    # Run immediately on startup
    run_full_update()

def main():
    """Main function to run the scheduler."""
    logger.info("Starting Goodwill scheduler...")
    
    setup_schedule()
    
    logger.info("Scheduler is running. Press Ctrl+C to exit.")
    
    try:
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
    except KeyboardInterrupt:
        logger.info("Scheduler stopped by user")
    except Exception as e:
        logger.error(f"Scheduler error: {str(e)}")

if __name__ == "__main__":
    main() 