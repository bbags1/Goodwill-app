import sqlite3
import os

# Get the current directory
current_dir = os.path.dirname(os.path.abspath(__file__))

# Database path
DB_PATH = os.path.join(current_dir, 'data/gw_data.db')

def check_schema():
    # Connect to the database
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Get the schema of the items table
    c.execute("PRAGMA table_info(items)")
    
    # Fetch the results
    columns = c.fetchall()
    
    # Print the column information
    print("Items table schema:")
    print("=" * 50)
    
    for column in columns:
        print(f"Column ID: {column[0]}")
        print(f"Name: {column[1]}")
        print(f"Type: {column[2]}")
        print(f"Not Null: {column[3]}")
        print(f"Default Value: {column[4]}")
        print(f"Primary Key: {column[5]}")
        print("-" * 50)
    
    # Close the connection
    conn.close()

if __name__ == "__main__":
    check_schema() 