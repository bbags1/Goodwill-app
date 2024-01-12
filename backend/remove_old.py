import sqlite3
from datetime import datetime
import pytz

pacific = pytz.timezone('US/Pacific')
pacific_time = datetime.now(pacific)
pacific_time_str = pacific_time.strftime('%Y-%m-%dT%H:%M:%S')

# Connect to the database
conn = sqlite3.connect(r'C:\Users\brody\OneDrive\Documents\Copilot\Goodwill\data\gw_data.db')
c = conn.cursor()

# Delete all items from the database where the auction end time is in the past
c.execute('''
    DELETE FROM items
    WHERE auction_end_time < ?
    ''', (pacific_time_str,))


# Commit the changes and close the connection
conn.commit()
conn.close()


