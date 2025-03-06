import sqlite3
import os

# Get the current directory
current_dir = os.path.dirname(os.path.abspath(__file__))

# Database path
DB_PATH = os.path.join(current_dir, 'data/gw_data.db')

def update_schema():
    # Connect to the database
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Add the missing columns
    try:
        c.execute("ALTER TABLE items ADD COLUMN profit REAL")
        print("Added 'profit' column to items table")
    except sqlite3.OperationalError as e:
        print(f"Error adding 'profit' column: {e}")
    
    try:
        c.execute("ALTER TABLE items ADD COLUMN margin REAL")
        print("Added 'margin' column to items table")
    except sqlite3.OperationalError as e:
        print(f"Error adding 'margin' column: {e}")
    
    try:
        c.execute("ALTER TABLE items ADD COLUMN last_updated TEXT")
        print("Added 'last_updated' column to items table")
    except sqlite3.OperationalError as e:
        print(f"Error adding 'last_updated' column: {e}")
    
    # Commit the changes
    conn.commit()
    
    # Verify the schema
    c.execute("PRAGMA table_info(items)")
    columns = c.fetchall()
    
    print("\nUpdated items table schema:")
    print("=" * 50)
    
    for column in columns:
        print(f"{column[0]}: {column[1]} ({column[2]})")
    
    # Close the connection
    conn.close()

if __name__ == "__main__":
    update_schema() 