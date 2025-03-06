import sqlite3
import os

# Get the current directory
current_dir = os.path.dirname(os.path.abspath(__file__))

# Database path
DB_PATH = os.path.join(current_dir, 'data/gw_data.db')

def check_microwave_items():
    # Connect to the database
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Query for microwave items
    c.execute('''
    SELECT id, search_term, seller_name, product_name, price 
    FROM items 
    WHERE search_term = "microwave" 
    LIMIT 10
    ''')
    
    # Fetch the results
    rows = c.fetchall()
    
    # Print the results
    print(f"Found {len(rows)} microwave items in the database:")
    print("=" * 50)
    
    for row in rows:
        print(f"ID: {row[0]}")
        print(f"Search Term: {row[1]}")
        print(f"Seller: {row[2]}")
        print(f"Product: {row[3]}")
        print(f"Price: ${row[4]}")
        print("-" * 50)
    
    # Close the connection
    conn.close()

if __name__ == "__main__":
    check_microwave_items() 