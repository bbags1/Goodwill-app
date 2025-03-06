from flask import Flask, jsonify, request
from flask_cors import CORS
import sqlite3
from datetime import datetime
import pytz
import json
import os

app = Flask(__name__)
CORS(app)

# Database path - update this to your actual path
DB_PATH = r'/Users/brodybagnall/Documents/goodwill/Goodwill-app/backend/data/gw_data.db'

# Ensure the settings table exists
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Create settings table if it doesn't exist
    c.execute('''
    CREATE TABLE IF NOT EXISTS settings (
        id INTEGER PRIMARY KEY,
        location TEXT,
        margin_threshold INTEGER,
        notification_email TEXT,
        notification_phone TEXT,
        notification_type TEXT,
        update_frequency TEXT,
        search_terms TEXT,
        seller_ids TEXT
    )
    ''')
    
    # Create favorites table if it doesn't exist
    c.execute('''
    CREATE TABLE IF NOT EXISTS favorites (
        id INTEGER PRIMARY KEY,
        item_id TEXT,
        date_added TEXT
    )
    ''')
    
    # Create promising table if it doesn't exist
    c.execute('''
    CREATE TABLE IF NOT EXISTS promising (
        id INTEGER PRIMARY KEY,
        item_id TEXT,
        date_added TEXT
    )
    ''')
    
    # Insert default settings if not present
    c.execute("SELECT COUNT(*) FROM settings")
    if c.fetchone()[0] == 0:
        c.execute('''
        INSERT INTO settings (location, margin_threshold, notification_email, notification_phone, notification_type, update_frequency, search_terms, seller_ids)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', ('198', 50, '', '', 'email', 'daily', json.dumps(['microwave']), json.dumps(['19', '198'])))
    else:
        # Check if the search_terms and seller_ids columns exist
        c.execute("PRAGMA table_info(settings)")
        columns = [column[1] for column in c.fetchall()]
        
        # If columns don't exist, add them
        if 'search_terms' not in columns:
            c.execute("ALTER TABLE settings ADD COLUMN search_terms TEXT")
            c.execute("UPDATE settings SET search_terms = ? WHERE id = 1", (json.dumps(['microwave']),))
        
        if 'seller_ids' not in columns:
            c.execute("ALTER TABLE settings ADD COLUMN seller_ids TEXT")
            c.execute("UPDATE settings SET seller_ids = ? WHERE id = 1", (json.dumps(['19', '198']),))
    
    conn.commit()
    conn.close()

# Initialize database on startup
init_db()

@app.route('/categories', methods=['GET'])
def get_categories():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT DISTINCT search_term FROM items")
    categories = [row[0] for row in c.fetchall()]
    conn.close()
    return jsonify(categories)

@app.route('/products', methods=['GET'])
def get_products():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    search_terms = request.args.getlist('search_term')
    seller_ids = request.args.getlist('seller_name')  # The frontend still sends as 'seller_name' parameter

    pacific = pytz.timezone('US/Pacific')
    pacific_time = datetime.now(pacific)
    pacific_time_str = pacific_time.strftime('%Y-%m-%dT%H:%M:%S')

    if search_terms and seller_ids:
        placeholders_terms = ', '.join('?' for term in search_terms)
        placeholders_sellers = ', '.join('?' for seller in seller_ids)
        query = f'''
        SELECT id, search_term, seller_name, product_name, price, ebay_price, auction_end_time, (ebay_price - price) AS price_difference, shipping_price, bids, seller_id, image_url
        FROM items 
        WHERE ebay_price IS NOT NULL 
        AND auction_end_time > ?
        AND search_term IN ({placeholders_terms})
        AND seller_id IN ({placeholders_sellers})
        ORDER BY price_difference DESC
        LIMIT 2000
        '''
        c.execute(query, [pacific_time_str] + search_terms + seller_ids)
    elif search_terms:
        placeholders = ', '.join('?' for term in search_terms)
        query = f'''
        SELECT id, search_term, seller_name, product_name, price, ebay_price, auction_end_time, (ebay_price - price) AS price_difference, shipping_price, bids, seller_id, image_url
        FROM items 
        WHERE ebay_price IS NOT NULL 
        AND auction_end_time > ?
        AND search_term IN ({placeholders})
        ORDER BY price_difference DESC
        LIMIT 2000
        '''
        c.execute(query, [pacific_time_str] + search_terms)
    elif seller_ids:
        placeholders = ', '.join('?' for seller in seller_ids)
        query = f'''
        SELECT id, search_term, seller_name, product_name, price, ebay_price, auction_end_time, (ebay_price - price) AS price_difference, shipping_price, bids, seller_id, image_url
        FROM items 
        WHERE ebay_price IS NOT NULL 
        AND auction_end_time > ?
        AND seller_id IN ({placeholders})
        ORDER BY price_difference DESC
        LIMIT 2000
        '''
        c.execute(query, [pacific_time_str] + seller_ids)
    else:
        query = '''
        SELECT id, search_term, seller_name, product_name, price, ebay_price, auction_end_time, (ebay_price - price) AS price_difference, shipping_price, bids, seller_id, image_url
        FROM items 
        WHERE ebay_price IS NOT NULL 
        AND auction_end_time > ?
        ORDER BY price_difference DESC
        LIMIT 2000
        '''
        c.execute(query, (pacific_time_str,))

    products = []
    for row in c.fetchall():
        product = {
            'id': row[0],
            'search_term': row[1],
            'seller_name': row[2],
            'product_name': row[3],
            'price': row[4],
            'ebay_price': row[5],
            'auction_end_time': row[6],
            'price_difference': row[7],
            'shipping_price': row[8],
            'bids': row[9],
            'seller_id': row[10]
        }
        
        # Convert binary image data to base64 string
        if row[11]:
            import base64
            product['image_url'] = base64.b64encode(row[11]).decode('utf-8')
        
        products.append(product)
    
    conn.close()
    return jsonify(products)

@app.route('/locations', methods=['GET'])
def get_locations():
    try:
        with open('seller_map.json', 'r') as f:
            seller_map = json.load(f)
        return jsonify(seller_map)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/settings', methods=['GET', 'POST'])
def handle_settings():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    if request.method == 'POST':
        data = request.json
        
        # Convert lists to JSON strings for database storage
        if 'search_terms' in data and isinstance(data['search_terms'], list):
            data['search_terms'] = json.dumps(data['search_terms'])
        
        if 'seller_ids' in data and isinstance(data['seller_ids'], list):
            data['seller_ids'] = json.dumps(data['seller_ids'])
        
        c.execute('''
        UPDATE settings 
        SET location = ?, 
            margin_threshold = ?, 
            notification_email = ?, 
            notification_phone = ?, 
            notification_type = ?, 
            update_frequency = ?,
            search_terms = ?,
            seller_ids = ?
        WHERE id = 1
        ''', (
            data.get('location', '198'),
            data.get('margin_threshold', 50),
            data.get('notification_email', ''),
            data.get('notification_phone', ''),
            data.get('notification_type', 'email'),
            data.get('update_frequency', 'daily'),
            data.get('search_terms', json.dumps(['microwave'])),
            data.get('seller_ids', json.dumps(['19', '198']))
        ))
        
        conn.commit()
        conn.close()
        
        return jsonify({"status": "success"})
    
    else:  # GET
        c.execute("SELECT location, margin_threshold, notification_email, notification_phone, notification_type, update_frequency, search_terms, seller_ids FROM settings WHERE id = 1")
        row = c.fetchone()
        
        settings = {}
        if row:
            settings = {
                "location": row[0],
                "margin_threshold": row[1],
                "notification_email": row[2],
                "notification_phone": row[3],
                "notification_type": row[4],
                "update_frequency": row[5]
            }
            
            # Parse JSON strings for search_terms and seller_ids
            if len(row) > 6 and row[6]:
                try:
                    settings["search_terms"] = json.loads(row[6])
                except json.JSONDecodeError:
                    settings["search_terms"] = ["microwave"]
            else:
                settings["search_terms"] = ["microwave"]
                
            if len(row) > 7 and row[7]:
                try:
                    settings["seller_ids"] = json.loads(row[7])
                except json.JSONDecodeError:
                    settings["seller_ids"] = ["19", "198"]
            else:
                settings["seller_ids"] = ["19", "198"]
        else:
            settings = {
                "location": "198",
                "margin_threshold": 50,
                "notification_email": "",
                "notification_phone": "",
                "notification_type": "email",
                "update_frequency": "daily",
                "search_terms": ["microwave"],
                "seller_ids": ["19", "198"]
            }
        
        conn.close()
        return jsonify(settings)

@app.route('/favorites', methods=['GET', 'POST', 'DELETE'])
def handle_favorites():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    if request.method == 'POST':
        data = request.json
        item_id = data.get('item_id')
        
        if not item_id:
            conn.close()
            return jsonify({"status": "error", "message": "Item ID is required"}), 400
        
        pacific = pytz.timezone('US/Pacific')
        pacific_time = datetime.now(pacific)
        pacific_time_str = pacific_time.strftime('%Y-%m-%dT%H:%M:%S')
        
        c.execute("INSERT INTO favorites (item_id, date_added) VALUES (?, ?)", (item_id, pacific_time_str))
        conn.commit()
        conn.close()
        return jsonify({"status": "success"})
    
    elif request.method == 'DELETE':
        item_id = request.args.get('item_id')
        
        if not item_id:
            conn.close()
            return jsonify({"status": "error", "message": "Item ID is required"}), 400
        
        c.execute("DELETE FROM favorites WHERE item_id = ?", (item_id,))
        conn.commit()
        conn.close()
        return jsonify({"status": "success"})
    
    else:  # GET
        c.execute("SELECT item_id FROM favorites")
        favorites = [row[0] for row in c.fetchall()]
        conn.close()
        return jsonify(favorites)

@app.route('/promising', methods=['GET', 'POST', 'DELETE'])
def handle_promising():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    if request.method == 'POST':
        data = request.json
        item_id = data.get('item_id')
        
        if not item_id:
            conn.close()
            return jsonify({"status": "error", "message": "Item ID is required"}), 400
        
        pacific = pytz.timezone('US/Pacific')
        pacific_time = datetime.now(pacific)
        pacific_time_str = pacific_time.strftime('%Y-%m-%dT%H:%M:%S')
        
        c.execute("INSERT INTO promising (item_id, date_added) VALUES (?, ?)", (item_id, pacific_time_str))
        conn.commit()
        conn.close()
        return jsonify({"status": "success"})
    
    elif request.method == 'DELETE':
        item_id = request.args.get('item_id')
        
        if not item_id:
            conn.close()
            return jsonify({"status": "error", "message": "Item ID is required"}), 400
        
        c.execute("DELETE FROM promising WHERE item_id = ?", (item_id,))
        conn.commit()
        conn.close()
        return jsonify({"status": "success"})
    
    else:  # GET
        c.execute("SELECT item_id FROM promising")
        promising = [row[0] for row in c.fetchall()]
        conn.close()
        return jsonify(promising)

@app.route('/', methods=['GET'])
def home():
    return "Hello, this is the home page!"

@app.route('/manual-search', methods=['POST'])
def manual_search():
    try:
        data = request.json
        search_terms = data.get('search_terms', [])
        seller_ids = data.get('seller_ids', [])  # These are already seller IDs, not location names
        
        if not search_terms or not seller_ids:
            return jsonify({"error": "Search terms and seller IDs are required"}), 400
        
        # No need to convert location names to seller IDs since we're already receiving seller IDs
        # Just validate that the seller IDs exist in our seller_map
        try:
            with open('seller_map.json', 'r') as f:
                seller_map = json.load(f)
            
            # Filter out any invalid seller IDs
            valid_seller_ids = [sid for sid in seller_ids if sid in seller_map]
            
            if not valid_seller_ids:
                return jsonify({"error": "No valid seller IDs found"}), 400
                
            # Import the necessary modules
            import asyncio
            from get_products import get_data
            
            # Log the search request
            print(f"Manual search initiated for terms: {search_terms} on seller IDs: {valid_seller_ids}")
            
            # Create a new event loop for this request
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                # Run the search with the valid seller IDs as targets, passing the loop
                loop.run_until_complete(get_data(search_terms, target_seller_ids=valid_seller_ids, loop=loop))
            finally:
                # Always close the loop
                loop.close()
            
            return jsonify({
                "success": True, 
                "message": f"Search completed for terms: {search_terms} on sellers: {valid_seller_ids}"
            })
        except Exception as e:
            print(f"Error in manual search: {str(e)}")
            return jsonify({"error": f"Error processing seller IDs: {str(e)}"}), 500
            
    except Exception as e:
        print(f"Error in manual search: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/manual-price-update', methods=['POST'])
def manual_price_update():
    try:
        print("Manual price update initiated")
        
        # Import the necessary modules
        import asyncio
        from gemini import update_prices
        
        # Create a new event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            # Run the update_prices function with the loop
            loop.run_until_complete(update_prices(loop=loop))
            return jsonify({"success": True, "message": "Price update completed successfully"})
        except Exception as e:
            print(f"Error in manual price update: {str(e)}")
            return jsonify({"error": str(e)}), 500
        finally:
            # Clean up the loop
            try:
                # Cancel all running tasks
                pending = asyncio.all_tasks(loop)
                for task in pending:
                    task.cancel()
                # Run the event loop one last time to clean up
                if pending:
                    loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
                # Close the loop
                loop.close()
            except Exception as e:
                print(f"Error cleaning up loop: {str(e)}")
    except Exception as e:
        print(f"Error in manual price update: {str(e)}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    init_db()
    app.run(host = '0.0.0.0', port=5001, debug=True)