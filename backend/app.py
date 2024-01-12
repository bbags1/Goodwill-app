from flask import Flask, jsonify, request
from flask_cors import CORS
import sqlite3
from datetime import datetime
import pytz



app = Flask(__name__)
CORS(app)

@app.route('/categories', methods=['GET'])
def get_categories():
    conn = sqlite3.connect(r'C:\Users\brody\OneDrive\Documents\Copilot\Goodwill\backend\data\gw_data.db')
    c = conn.cursor()
    c.execute("SELECT DISTINCT search_term FROM items")
    categories = [row[0] for row in c.fetchall()]
    conn.close()
    return jsonify(categories)

@app.route('/products', methods=['GET'])
def get_products():
    conn = sqlite3.connect(r'C:\Users\brody\OneDrive\Documents\Copilot\Goodwill\backend\data\gw_data.db')
    c = conn.cursor()

    search_terms = request.args.getlist('search_term')
    seller_names = request.args.getlist('seller_name')

    pacific = pytz.timezone('US/Pacific')
    pacific_time = datetime.now(pacific)
    pacific_time_str = pacific_time.strftime('%Y-%m-%dT%H:%M:%S')

    if search_terms and seller_names:
        placeholders_terms = ', '.join('?' for term in search_terms)
        placeholders_sellers = ', '.join('?' for seller in seller_names)
        query = f'''
        SELECT id, search_term, seller_name, product_name, price, ebay_price, auction_end_time, (ebay_price - price) AS price_difference
        FROM items 
        WHERE ebay_price IS NOT NULL 
        AND auction_end_time > ?
        AND search_term IN ({placeholders_terms})
        AND seller_name IN ({placeholders_sellers})
        ORDER BY price_difference DESC
        LIMIT 2000
        '''
        c.execute(query, [pacific_time_str] + search_terms + seller_names)
    elif search_terms:
        placeholders = ', '.join('?' for term in search_terms)
        query = f'''
        SELECT id, search_term, seller_name, product_name, price, ebay_price, auction_end_time, (ebay_price - price) AS price_difference
        FROM items 
        WHERE ebay_price IS NOT NULL 
        AND auction_end_time > ?
        AND search_term IN ({placeholders})
        ORDER BY price_difference DESC
        LIMIT 2000
        '''
        c.execute(query, [pacific_time_str] + search_terms)
    elif seller_names:
        placeholders = ', '.join('?' for seller in seller_names)
        query = f'''
        SELECT id, search_term, seller_name, product_name, price, ebay_price, auction_end_time, (ebay_price - price) AS price_difference
        FROM items 
        WHERE ebay_price IS NOT NULL 
        AND auction_end_time > ?
        AND seller_name IN ({placeholders})
        ORDER BY price_difference DESC
        LIMIT 2000
        '''
        c.execute(query, [pacific_time_str] + seller_names)
    else:
        query = '''
        SELECT id, search_term, seller_name, product_name, price, ebay_price, auction_end_time, (ebay_price - price) AS price_difference
        FROM items 
        WHERE ebay_price IS NOT NULL 
        AND auction_end_time > ?
        ORDER BY price_difference DESC
        LIMIT 2000
        '''
        c.execute(query, (pacific_time_str,))

    products = [dict(zip([column[0] for column in c.description], row)) for row in c.fetchall()]
    conn.close()

    return jsonify(products)

if __name__ == '__main__':
    app.run(host = '0.0.0.0', debug=True)

@app.route('/', methods=['GET'])
def home():
    return "Hello, this is the home page!"