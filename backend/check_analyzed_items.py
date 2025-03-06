import sqlite3
import os

# Get the current directory
current_dir = os.path.dirname(os.path.abspath(__file__))

# Database path
DB_PATH = os.path.join(current_dir, 'data/gw_data.db')

def check_analyzed_items():
    # Connect to the database
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Query for items with estimated prices
    c.execute('''
    SELECT id, product_name, price, ebay_price, profit, margin, seller_name
    FROM items
    WHERE ebay_price IS NOT NULL
    ''')
    
    # Fetch the results
    rows = c.fetchall()
    
    # Print the results
    print(f"Found {len(rows)} analyzed items in the database:")
    print("=" * 80)
    
    for row in rows:
        print(f"ID: {row[0]}")
        print(f"Product: {row[1]}")
        print(f"Current Price: ${row[2]}")
        print(f"Estimated Resale Value: ${row[3]}")
        print(f"Potential Profit: ${row[4]}")
        print(f"Profit Margin: {row[5]:.2f}%")
        print(f"Seller: {row[6]}")
        print("-" * 80)
    
    # Close the connection
    conn.close()

if __name__ == "__main__":
    check_analyzed_items() 