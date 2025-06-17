import sqlite3
import json
import os
from datetime import datetime

# Database path
DB_PATH = r'/Users/brodybagnall/Documents/goodwill/Goodwill-app/backend/data/gw_data.db'

def view_database():
    """View the contents of the database."""
    if not os.path.exists(DB_PATH):
        print(f"Database file not found at: {DB_PATH}")
        return
    
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # This enables column access by name
    c = conn.cursor()
    
    # Get table names
    c.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = c.fetchall()
    
    if not tables:
        print("No tables found in the database.")
        conn.close()
        return
    
    print(f"Found {len(tables)} tables in the database:")
    for table in tables:
        table_name = table['name']
        print(f"\n--- Table: {table_name} ---")
        
        # Get column names
        c.execute(f"PRAGMA table_info({table_name})")
        columns = [column['name'] for column in c.fetchall()]
        print(f"Columns: {', '.join(columns)}")
        
        # Count rows
        c.execute(f"SELECT COUNT(*) FROM {table_name}")
        row_count = c.fetchone()[0]
        print(f"Total rows: {row_count}")
        
        # Show sample data (first 5 rows)
        if row_count > 0:
            c.execute(f"SELECT * FROM {table_name} LIMIT 5")
            rows = c.fetchall()
            print("\nSample data (first 5 rows):")
            for row in rows:
                row_dict = {column: row[column] for column in columns}
                # Truncate long values for display
                for key, value in row_dict.items():
                    if isinstance(value, str) and len(value) > 100:
                        row_dict[key] = value[:100] + "..."
                print(json.dumps(row_dict, indent=2))
    
    conn.close()

def view_items_by_seller():
    """View item counts by seller."""
    if not os.path.exists(DB_PATH):
        print(f"Database file not found at: {DB_PATH}")
        return
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Check if items table exists
    c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='items';")
    if not c.fetchone():
        print("Items table not found in the database.")
        conn.close()
        return
    
    # Count items by seller
    c.execute("SELECT seller_id, seller_name, COUNT(*) as count FROM items GROUP BY seller_id ORDER BY count DESC")
    sellers = c.fetchall()
    
    if not sellers:
        print("No items found in the database.")
        conn.close()
        return
    
    print("\n--- Items by Seller ---")
    for seller_id, seller_name, count in sellers:
        print(f"{seller_name} (ID: {seller_id}): {count} items")
    
    # Get total count
    c.execute("SELECT COUNT(*) FROM items")
    total = c.fetchone()[0]
    print(f"\nTotal items: {total}")
    
    conn.close()

def view_recent_items(limit=10):
    """View the most recently added items."""
    if not os.path.exists(DB_PATH):
        print(f"Database file not found at: {DB_PATH}")
        return
    
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    # Check if items table exists
    c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='items';")
    if not c.fetchone():
        print("Items table not found in the database.")
        conn.close()
        return
    
    # Get recent items
    c.execute(f"""
        SELECT id, seller_name, product_name, price, auction_end_time, bids, category_name
        FROM items
        ORDER BY id DESC
        LIMIT {limit}
    """)
    items = c.fetchall()
    
    if not items:
        print("No items found in the database.")
        conn.close()
        return
    
    print(f"\n--- {limit} Most Recent Items ---")
    for item in items:
        print(f"ID: {item['id']}")
        print(f"Product: {item['product_name']}")
        print(f"Price: ${item['price']}")
        print(f"Seller: {item['seller_name']}")
        print(f"Auction End: {item['auction_end_time']}")
        print(f"Bids: {item['bids']}")
        print(f"Category: {item['category_name']}")
        print("-" * 50)
    
    conn.close()

if __name__ == "__main__":
    print("Database Viewer")
    print("=" * 50)
    
    while True:
        print("\nOptions:")
        print("1. View database tables and structure")
        print("2. View item counts by seller")
        print("3. View recent items")
        print("4. Exit")
        
        choice = input("\nEnter your choice (1-4): ")
        
        if choice == "1":
            view_database()
        elif choice == "2":
            view_items_by_seller()
        elif choice == "3":
            limit = input("How many items to show? (default: 10): ")
            try:
                limit = int(limit) if limit else 10
            except ValueError:
                limit = 10
            view_recent_items(limit)
        elif choice == "4":
            print("Exiting...")
            break
        else:
            print("Invalid choice. Please try again.") 