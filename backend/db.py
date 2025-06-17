import sqlite3
import threading
from contextlib import contextmanager
import os
import json
from datetime import datetime
import pytz

# Database path
DB_PATH = r'/Users/brodybagnall/Documents/goodwill/Goodwill-app/backend/data/gw_data.db'

# Thread-local storage for database connections
local = threading.local()

def get_db():
    """Get a thread-local database connection."""
    if not hasattr(local, "db"):
        local.db = sqlite3.connect(DB_PATH)
        local.db.row_factory = sqlite3.Row
    return local.db

@contextmanager
def get_db_cursor():
    """Context manager for database operations."""
    conn = get_db()
    cursor = conn.cursor()
    try:
        yield cursor
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cursor.close()

def close_db():
    """Close the database connection."""
    if hasattr(local, "db"):
        local.db.close()
        del local.db

def table_has_column(cursor, table_name, column_name):
    """Check if a table has a specific column."""
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = [col[1] for col in cursor.fetchall()]
    return column_name in columns

def upgrade_schema(cursor):
    """Upgrade the database schema if needed."""
    # Check if items table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='items'")
    table_exists = cursor.fetchone() is not None
    
    if table_exists:
        # Add missing columns to items table if needed
        if not table_has_column(cursor, 'items', 'price_update_attempted'):
            print("Adding price_update_attempted column to items table")
            cursor.execute("ALTER TABLE items ADD COLUMN price_update_attempted BOOLEAN DEFAULT 0")
        
        if not table_has_column(cursor, 'items', 'last_price_update'):
            print("Adding last_price_update column to items table")
            cursor.execute("ALTER TABLE items ADD COLUMN last_price_update TEXT")
        
        if not table_has_column(cursor, 'items', 'profit'):
            print("Adding profit column to items table")
            cursor.execute("ALTER TABLE items ADD COLUMN profit REAL")
        
        if not table_has_column(cursor, 'items', 'margin'):
            print("Adding margin column to items table")
            cursor.execute("ALTER TABLE items ADD COLUMN margin REAL")
        
        # Make sure image_url is TEXT, not BLOB
        cursor.execute("PRAGMA table_info(items)")
        columns = cursor.fetchall()
        for col in columns:
            if col[1] == 'image_url' and col[2] == 'BLOB':
                print("Converting image_url from BLOB to TEXT")
                cursor.execute("ALTER TABLE items RENAME TO items_old")
                
                # Create the new items table with correct schema
                create_items_table(cursor)
                
                # Copy data from old to new
                cursor.execute("""
                INSERT INTO items 
                SELECT id, search_term, seller_name, product_name, price, ebay_price, 
                       auction_end_time, image_url, shipping_price, bids, seller_id, 
                       0, NULL, NULL, NULL
                FROM items_old
                """)
                
                # Drop the old table
                cursor.execute("DROP TABLE items_old")
                break

def create_items_table(cursor):
    """Create the items table with the correct schema."""
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS items (
        id TEXT PRIMARY KEY,
        search_term TEXT,
        seller_name TEXT,
        product_name TEXT,
        price REAL,
        ebay_price REAL,
        auction_end_time TEXT,
        image_url TEXT,
        shipping_price REAL,
        bids INTEGER,
        seller_id TEXT,
        price_update_attempted BOOLEAN DEFAULT 0,
        last_price_update TEXT,
        profit REAL,
        margin REAL
    )
    ''')

def init_db():
    """Initialize the database with required tables."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    
    with get_db_cursor() as cursor:
        # Create items table with all columns
        create_items_table(cursor)
        
        # Create settings table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS settings (
            id INTEGER PRIMARY KEY,
            location TEXT,
            margin_threshold INTEGER DEFAULT 50,
            notification_email TEXT,
            notification_phone TEXT,
            notification_type TEXT DEFAULT 'email',
            update_frequency TEXT DEFAULT 'daily',
            search_terms TEXT,
            seller_ids TEXT DEFAULT '["19", "198"]'
        )
        ''')
        
        # Create favorites table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS favorites (
            id INTEGER PRIMARY KEY,
            item_id TEXT,
            date_added TEXT
        )
        ''')
        
        # Create promising table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS promising (
            id INTEGER PRIMARY KEY,
            item_id TEXT,
            date_added TEXT
        )
        ''')
        
        # Upgrade schema if needed
        upgrade_schema(cursor)
        
        # Add indices after all tables and columns exist
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_items_price_update ON items(price_update_attempted, last_price_update)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_items_seller_id ON items(seller_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_items_ebay_price ON items(ebay_price)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_items_auction_end ON items(auction_end_time)')
        
        # Insert default settings if not present
        cursor.execute("SELECT COUNT(*) FROM settings")
        count = cursor.fetchone()['COUNT(*)']
        
        if count == 0:
            cursor.execute('''
            INSERT INTO settings (
                location, margin_threshold, notification_email, notification_phone, 
                notification_type, update_frequency, search_terms, seller_ids
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                '198', 50, '', '', 'email', 'daily', 
                json.dumps(['microwave']), json.dumps(['19', '198'])
            ))

def get_items_for_price_update(batch_size=None, test_mode=False):
    """Get items that need price updates."""
    with get_db_cursor() as cursor:
        # Get current date in Pacific timezone for comparison
        pacific = pytz.timezone('US/Pacific')
        pacific_time = datetime.now(pacific)
        pacific_time_str = pacific_time.strftime('%Y-%m-%dT%H:%M:%S')
        
        query = '''
        SELECT id, product_name, image_url, price, shipping_price
        FROM items
        WHERE (ebay_price IS NULL OR price_update_attempted = 0)
        AND auction_end_time > ?
        '''
        
        params = [pacific_time_str]
        
        if test_mode:
            query += ' LIMIT ?'
            cursor.execute(query, params + [batch_size or 5])
        elif batch_size:
            query += ' LIMIT ?'
            cursor.execute(query, params + [batch_size])
        else:
            cursor.execute(query, params)
            
        # Convert sqlite3.Row objects to dictionaries
        rows = cursor.fetchall()
        return [dict(row) for row in rows]

def update_item_price(item_id, ebay_price, update_time, price=0, shipping_price=0):
    """Update an item's price and margin in the database."""
    with get_db_cursor() as cursor:
        # Calculate profit and margin
        profit = ebay_price - price - shipping_price
        margin = (profit / price * 100) if price > 0 else 0
        
        cursor.execute('''
        UPDATE items
        SET ebay_price = ?,
            price_update_attempted = 1,
            last_price_update = ?,
            profit = ?,
            margin = ?
        WHERE id = ?
        ''', (ebay_price, update_time, profit, margin, item_id))

def get_pending_price_updates_count():
    """Get count of items needing price updates."""
    with get_db_cursor() as cursor:
        # Get current date in Pacific timezone for comparison
        pacific = pytz.timezone('US/Pacific')
        pacific_time = datetime.now(pacific)
        pacific_time_str = pacific_time.strftime('%Y-%m-%dT%H:%M:%S')
        
        cursor.execute('''
        SELECT COUNT(*) as count
        FROM items
        WHERE (ebay_price IS NULL OR price_update_attempted = 0)
        AND auction_end_time > ?
        ''', [pacific_time_str])
        
        result = cursor.fetchone()
        return result['count'] if result else 0 