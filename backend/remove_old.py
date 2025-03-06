import sqlite3
from datetime import datetime
import pytz
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database path - update this to your actual path
DB_PATH = r'/Users/brodybagnall/Documents/goodwill/Goodwill-app/backend/data/gw_data.db'

pacific = pytz.timezone('US/Pacific')
pacific_time = datetime.now(pacific)
pacific_time_str = pacific_time.strftime('%Y-%m-%dT%H:%M:%S')

# Connect to the database
conn = sqlite3.connect(DB_PATH)
c = conn.cursor()

# Delete all items from the database where the auction end time is in the past
c.execute('''
    DELETE FROM items
    WHERE auction_end_time < ?
    ''', (pacific_time_str,))

print(f"Removed {c.rowcount} expired items from the database")

# Commit the changes and close the connection
conn.commit()
conn.close()


