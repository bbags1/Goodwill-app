import sqlite3
import os

# Database path
DB_PATH = r'/Users/brodybagnall/Documents/goodwill/Goodwill-app/backend/data/gw_data.db'

def update_schema():
    # Create data directory if it doesn't exist
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    
    # Connect to the database
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Drop existing tables if they exist
    c.execute("DROP TABLE IF EXISTS items")
    c.execute("DROP TABLE IF EXISTS settings")
    c.execute("DROP TABLE IF EXISTS favorites")
    
    # Create items table
    c.execute('''
    CREATE TABLE items (
        id INTEGER PRIMARY KEY,
        seller_id TEXT NOT NULL,
        seller_name TEXT NOT NULL,
        product_name TEXT NOT NULL,
        price REAL NOT NULL,
        shipping_price REAL,
        auction_end_time TEXT,
        image_url BLOB,
        bids INTEGER,
        estimated_price REAL,
        margin REAL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Create settings table
    c.execute('''
    CREATE TABLE settings (
        id INTEGER PRIMARY KEY,
        margin_threshold INTEGER DEFAULT 50,
        notification_email TEXT,
        notification_phone TEXT,
        notification_type TEXT DEFAULT 'email',
        update_frequency TEXT DEFAULT 'daily',
        seller_ids TEXT DEFAULT '["19", "198"]'
    )
    ''')
    
    # Create favorites table
    c.execute('''
    CREATE TABLE favorites (
        id INTEGER PRIMARY KEY,
        item_id INTEGER,
        FOREIGN KEY (item_id) REFERENCES items (id)
    )
    ''')
    
    # Create indices for better performance
    c.execute('CREATE INDEX idx_items_seller_id ON items(seller_id)')
    c.execute('CREATE INDEX idx_items_margin ON items(margin)')
    c.execute('CREATE INDEX idx_items_estimated_price ON items(estimated_price)')
    
    # Insert default settings
    c.execute('''
    INSERT INTO settings (
        id, margin_threshold, notification_email, notification_phone,
        notification_type, update_frequency, seller_ids
    ) VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (1, 50, '', '', 'email', 'daily', '["19", "198"]'))
    
    # Commit changes and close connection
    conn.commit()
    conn.close()
    
    print("Database schema updated successfully")

if __name__ == "__main__":
    update_schema() 