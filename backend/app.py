from flask import Flask, jsonify, request
from flask_cors import CORS
import sqlite3
from datetime import datetime
import pytz
import json
import os
import asyncio
from get_products import get_data
from notifications import send_notifications
from dotenv import load_dotenv
from gemini import analyze_item_price, update_prices
import schedule
import time
import threading
from db import get_db_cursor, init_db, get_pending_price_updates_count, DB_PATH
from map import get_seller_name  

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)

# Initialize database on startup
init_db()

@app.route('/categories', methods=['GET'])
def get_categories():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT DISTINCT search_term FROM items WHERE search_term IS NOT NULL")
    categories = [row['search_term'] for row in c.fetchall() if row['search_term']]
    conn.close()
    return jsonify(categories)

@app.route('/product-categories', methods=['GET'])
def get_product_categories():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT DISTINCT category_name FROM items WHERE category_name IS NOT NULL AND category_name != ''")
    
    # Get all categories from the database
    all_categories = [row['category_name'] for row in c.fetchall()]
    conn.close()
    
    # Ensure consistency - if any Size categories are still in the database, map them to Clothing
    # and remove duplicates
    unique_categories = set()
    for category in all_categories:
        if category.startswith('Size'):
            unique_categories.add('Clothing')
        else:
            unique_categories.add(category)
    
    return jsonify(sorted(list(unique_categories)))

@app.route('/products', methods=['GET'])
def get_products():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    search_terms = request.args.getlist('search_term')
    seller_ids = request.args.getlist('seller_name')  # The frontend still sends as 'seller_name' parameter

    pacific = pytz.timezone('US/Pacific')
    pacific_time = datetime.now(pacific)
    pacific_time_str = pacific_time.strftime('%Y-%m-%dT%H:%M:%S')

    params = [pacific_time_str]
    
    if search_terms and seller_ids:
        placeholders_terms = ', '.join('?' for _ in search_terms)
        placeholders_sellers = ', '.join('?' for _ in seller_ids)
        query = f'''
        SELECT id, search_term, seller_name, product_name, price, ebay_price, auction_end_time, 
               (ebay_price - price) AS price_difference, shipping_price, bids, seller_id, image_url,
               profit, margin, category_name
        FROM items 
        WHERE ebay_price IS NOT NULL AND ebay_price > 0
        AND auction_end_time > ?
        AND search_term IN ({placeholders_terms})
        AND seller_id IN ({placeholders_sellers})
        ORDER BY price_difference DESC
        '''
        params.extend(search_terms)
        params.extend(seller_ids)
    elif search_terms:
        placeholders = ', '.join('?' for _ in search_terms)
        query = f'''
        SELECT id, search_term, seller_name, product_name, price, ebay_price, auction_end_time, 
               (ebay_price - price) AS price_difference, shipping_price, bids, seller_id, image_url,
               profit, margin, category_name
        FROM items 
        WHERE ebay_price IS NOT NULL AND ebay_price > 0
        AND auction_end_time > ?
        AND search_term IN ({placeholders})
        ORDER BY price_difference DESC
        '''
        params.extend(search_terms)
    elif seller_ids:
        placeholders = ', '.join('?' for _ in seller_ids)
        query = f'''
        SELECT id, search_term, seller_name, product_name, price, ebay_price, auction_end_time, 
               (ebay_price - price) AS price_difference, shipping_price, bids, seller_id, image_url,
               profit, margin, category_name
        FROM items 
        WHERE ebay_price IS NOT NULL AND ebay_price > 0
        AND auction_end_time > ?
        AND seller_id IN ({placeholders})
        ORDER BY price_difference DESC
        '''
        params.extend(seller_ids)
    else:
        query = '''
        SELECT id, search_term, seller_name, product_name, price, ebay_price, auction_end_time, 
               (ebay_price - price) AS price_difference, shipping_price, bids, seller_id, image_url,
               profit, margin, category_name
        FROM items 
        WHERE ebay_price IS NOT NULL AND ebay_price > 0
        AND auction_end_time > ?
        ORDER BY price_difference DESC
        '''

    c.execute(query, params)
    rows = c.fetchall()
    
    products = []
    for row in rows:
        product = dict(row)
        
        # Handle base64 images
        if product.get('image_url') and isinstance(product['image_url'], bytes):
            import base64
            product['image_url'] = base64.b64encode(product['image_url']).decode('utf-8')
        
        products.append(product)
    
    conn.close()
    return jsonify(products)

@app.route('/locations', methods=['GET'])
def get_locations():
    try:
        # Load the seller map from JSON file
        with open('seller_map.json', 'r') as f:
            seller_map = json.load(f)
            
        # Return all available locations
        return jsonify(seller_map)
        
    except Exception as e:
        print(f"Error fetching locations: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/settings', methods=['GET'])
def get_settings():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    c.execute("SELECT * FROM settings WHERE id = 1")
    row = c.fetchone()
    
    if row:
        # Convert row to dict and handle JSON fields
        settings = dict(row)
        if settings.get('seller_ids'):
            try:
                settings['seller_ids'] = json.loads(settings['seller_ids'])
            except:
                settings['seller_ids'] = ['19', '198']
                
        if settings.get('search_terms'):
            try:
                settings['search_terms'] = json.loads(settings['search_terms'])
            except:
                settings['search_terms'] = ['microwave']
    else:
        settings = {
            'margin_threshold': 50,
            'notification_email': '',
            'notification_phone': '',
            'notification_type': 'email',
            'update_frequency': 'daily',
            'seller_ids': ['19', '198'],
            'search_terms': ['microwave']
        }
        
        c.execute('''
        INSERT INTO settings (
            id, margin_threshold, notification_email, notification_phone, 
            notification_type, update_frequency, seller_ids, search_terms
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (1, settings['margin_threshold'], settings['notification_email'],
              settings['notification_phone'], settings['notification_type'],
              settings['update_frequency'], json.dumps(settings['seller_ids']),
              json.dumps(settings['search_terms'])))
        conn.commit()
    
    conn.close()
    return jsonify(settings)

@app.route('/settings', methods=['POST'])
def update_settings():
    try:
        data = request.get_json(silent=True)
        if not data:
            return jsonify({'error': 'Invalid JSON data'}), 400
            
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        # Validate seller_ids
        seller_ids = data.get('seller_ids', ['19', '198'])
        if not isinstance(seller_ids, list):
            return jsonify({'error': 'Invalid seller_ids format'}), 400
        
        # Validate search_terms
        search_terms = data.get('search_terms', ['microwave'])
        if not isinstance(search_terms, list):
            return jsonify({'error': 'Invalid search_terms format'}), 400
        
        c.execute('''
        UPDATE settings SET
            margin_threshold = ?,
            notification_email = ?,
            notification_phone = ?,
            notification_type = ?,
            update_frequency = ?,
            seller_ids = ?,
            search_terms = ?
        WHERE id = 1
        ''', (
            data.get('margin_threshold', 50),
            data.get('notification_email', ''),
            data.get('notification_phone', ''),
            data.get('notification_type', 'email'),
            data.get('update_frequency', 'daily'),
            json.dumps(seller_ids),
            json.dumps(search_terms)
        ))
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/favorites', methods=['GET', 'POST', 'DELETE'])
def handle_favorites():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    if request.method == 'POST':
        data = request.get_json(silent=True)
        if not data:
            conn.close()
            return jsonify({"status": "error", "message": "Invalid JSON data"}), 400
            
        item_id = data.get('item_id')
        
        if not item_id:
            conn.close()
            return jsonify({"status": "error", "message": "Item ID is required"}), 400
        
        pacific = pytz.timezone('US/Pacific')
        pacific_time = datetime.now(pacific)
        pacific_time_str = pacific_time.strftime('%Y-%m-%dT%H:%M:%S')
        
        # Check if item already exists
        c.execute("SELECT COUNT(*) as count FROM favorites WHERE item_id = ?", (item_id,))
        count = c.fetchone()['count']
        
        if count == 0:
            c.execute("INSERT INTO favorites (item_id, date_added) VALUES (?, ?)", (item_id, pacific_time_str))
            conn.commit()
            conn.close()
            return jsonify({"status": "success", "message": "Item added to favorites"})
        else:
            conn.close()
            return jsonify({"status": "success", "message": "Item already in favorites"})
    
    elif request.method == 'DELETE':
        item_id = request.args.get('item_id')
        
        if not item_id:
            conn.close()
            return jsonify({"status": "error", "message": "Item ID is required"}), 400
        
        c.execute("DELETE FROM favorites WHERE item_id = ?", (item_id,))
        conn.commit()
        conn.close()
        return jsonify({"status": "success", "message": "Item removed from favorites"})
    
    else:  # GET
        c.execute("SELECT item_id FROM favorites")
        favorites = [row['item_id'] for row in c.fetchall()]
        conn.close()
        return jsonify(favorites)

@app.route('/', methods=['GET'])
def home():
    return "Goodwill Auction Analysis Tool API - Status: Running"

@app.route('/manual-search', methods=['POST'])
def manual_search():
    try:
        data = request.get_json(silent=True)
        if not data:
            return jsonify({"error": "Invalid JSON data"}), 400
            
        seller_ids = data.get('seller_ids', [])
        search_term = data.get('search_term', '')
        
        if not seller_ids:
            return jsonify({"error": "No seller IDs provided"}), 400
            
        print(f"Starting manual search for sellers: {seller_ids} with search term '{search_term}'")
        
        # Run the search asynchronously
        asyncio.run(get_data(seller_ids, search_term))
        
        # Count total items in database
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute("SELECT COUNT(*) as count FROM items")
        total_items = c.fetchone()['count']
        
        # Count items for the specific search
        if search_term:
            c.execute("SELECT COUNT(*) as count FROM items WHERE search_term = ?", (search_term,))
            search_items = c.fetchone()['count']
        else:
            search_items = total_items
            
        conn.close()
        
        return jsonify({
            "success": True,
            "message": "Manual search completed successfully",
            "total_items": total_items,
            "search_items": search_items
        })
        
    except Exception as e:
        print(f"Error in manual search: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/manual-price-update', methods=['POST'])
def manual_price_update():
    try:
        # Get request data, defaulting to empty dict if None
        data = request.get_json(silent=True) or {}
        
        # Parse and validate parameters with better defaults
        try:
            batch_size = int(data.get('batch_size', 50))  # Reduced from 50 to 10
            test_mode = bool(data.get('test_mode', False))
            max_concurrent = int(data.get('max_concurrent', 3))  # Reduced from 5 to 3
        except (ValueError, TypeError) as e:
            return jsonify({
                'error': 'Invalid parameters',
                'message': str(e)
            }), 400
        
        # Run the async price analysis
        asyncio.run(update_prices(
            batch_size=batch_size,
            test_mode=test_mode,
            max_concurrent=max_concurrent
        ))
        
        # Get statistics
        remaining_updates = get_pending_price_updates_count()
        
        return jsonify({
            'success': True,
            'remaining_updates': remaining_updates,
            'message': 'Price update process completed successfully'
        })
        
    except Exception as e:
        print(f"Error during price update: {str(e)}")
        return jsonify({
            'error': str(e),
            'message': 'Error during price update process'
        }), 500

@app.route('/items', methods=['GET'])
def get_items():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    # Get query parameters
    min_margin = request.args.get('min_margin', type=float, default=0)
    max_items = request.args.get('max_items', type=int, default=100)
    seller_ids_str = request.args.get('seller_ids', type=str, default=None)
    
    # Convert seller_ids string to list if provided
    seller_ids = None
    if seller_ids_str:
        try:
            seller_ids = json.loads(seller_ids_str)
        except:
            return jsonify({"error": "Invalid seller_ids format"}), 400
    
    # Get current date in Pacific timezone for comparison
    pacific = pytz.timezone('US/Pacific')
    pacific_time = datetime.now(pacific)
    pacific_time_str = pacific_time.strftime('%Y-%m-%dT%H:%M:%S')
    
    # Build the query
    params = [min_margin, pacific_time_str]
    
    query = '''
    SELECT * FROM items 
    WHERE ebay_price IS NOT NULL AND ebay_price > 0
    AND margin >= ?
    AND auction_end_time > ?
    '''
    
    if seller_ids:
        placeholders = ','.join('?' * len(seller_ids))
        query += f' AND seller_id IN ({placeholders})'
        params.extend(seller_ids)
    
    query += ' ORDER BY margin DESC LIMIT ?'
    params.append(max_items)
    
    # Execute the query
    c.execute(query, params)
    
    # Process rows to handle image data properly
    items = []
    for row in c.fetchall():
        item = dict(row)
        
        # Handle image_url - could be a string URL or binary data
        if 'image_url' in item and item['image_url'] and isinstance(item['image_url'], bytes):
            import base64
            item['image_url'] = base64.b64encode(item['image_url']).decode('utf-8')
        
        items.append(item)
    
    conn.close()
    return jsonify(items)

def run_scheduled_tasks():
    while True:
        schedule.run_pending()
        time.sleep(60)

def scheduled_search():
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        
        # Get seller_ids from settings
        c.execute("SELECT seller_ids, search_terms FROM settings WHERE id = 1")
        row = c.fetchone()
        conn.close()
        
        seller_ids = []
        search_terms = []
        
        if row:
            if row['seller_ids']:
                try:
                    seller_ids = json.loads(row['seller_ids'])
                except:
                    seller_ids = ['19', '198']
                    
            if row['search_terms']:
                try:
                    search_terms = json.loads(row['search_terms'])
                except:
                    search_terms = ['microwave']
        
        # If no seller IDs, use default
        if not seller_ids:
            seller_ids = ['19', '198']
            
        # If no search terms, use empty string to get all items
        if not search_terms:
            # Run a single search with empty term
            asyncio.run(get_data(seller_ids, ''))
        else:
            # Run a search for each term
            for term in search_terms:
                asyncio.run(get_data(seller_ids, term))
        
        print(f"Scheduled search completed at {datetime.now()}")
    except Exception as e:
        print(f"Error in scheduled search: {str(e)}")

def scheduled_price_update():
    try:
        # Update prices with smaller batches and fewer concurrent requests
        asyncio.run(update_prices(batch_size=10, test_mode=False, max_concurrent=3))
        print(f"Scheduled price update completed at {datetime.now()}")
    except Exception as e:
        print(f"Error in scheduled price update: {str(e)}")

def setup_schedules():
    """Set up scheduled tasks based on user settings."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    # Get update frequency from settings
    c.execute("SELECT update_frequency FROM settings WHERE id = 1")
    row = c.fetchone()
    conn.close()
    
    # Default to daily if no settings found
    frequency = row['update_frequency'] if row else 'daily'
    
    # Schedule tasks based on frequency
    if frequency == 'hourly':
        schedule.every().hour.do(scheduled_search)
        schedule.every().hour.at(":30").do(scheduled_price_update)
    elif frequency == 'twice_daily':
        schedule.every().day.at("08:00").do(scheduled_search)
        schedule.every().day.at("20:00").do(scheduled_search)
        schedule.every().day.at("08:30").do(scheduled_price_update)
        schedule.every().day.at("20:30").do(scheduled_price_update)
    elif frequency == 'weekly':
        schedule.every().monday.at("08:00").do(scheduled_search)
        schedule.every().monday.at("08:30").do(scheduled_price_update)
    else:  # Default to daily
        schedule.every().day.at("08:00").do(scheduled_search)
        schedule.every().day.at("08:30").do(scheduled_price_update)
    
    print(f"Scheduled tasks set up with {frequency} frequency")

if __name__ == '__main__':
    # Setup the scheduler
    setup_schedules()
    
    # Start the scheduler in a separate thread
    scheduler_thread = threading.Thread(target=run_scheduled_tasks, daemon=True)
    scheduler_thread.start()
    
    # Start the Flask app
    app.run(host='0.0.0.0', port=5001)