import asyncio
import aiohttp
import sqlite3
import os
from dotenv import load_dotenv
from urllib.parse import quote_plus
from map import get_seller_name

# Load environment variables
load_dotenv()

# Database path
DB_PATH = r'/Users/brodybagnall/Documents/goodwill/Goodwill-app/backend/data/gw_data.db'

async def fetch_data(session, url, params):
    async with session.get(url, params=params) as response:
        if response.status == 200:
            return await response.json()
        else:
            print(f"Error fetching {url}: HTTP {response.status}")
            return {}  # Return an empty dictionary in case of error

async def fetch_microwaves(session, seller_id="198"):  # Default to Spokane (198)
    url = "https://buyerapi.shopgoodwill.com/api/Search/ItemListingData"
    
    # Parameters for the search
    params = {
        "pn": 4,        # Number of items per page
        "cl": 1,        # Current listing
        "cids": "",     # Category ID
        "scids": "",    # Subcategory ID
        "p": 1,         # Page number (just get the first page)
        "sc": 1,        # Sort column
        "sd": "false",  # Sort direction
        "cid": 0,       # Category ID
        "sg": "Keyword", # Search group
        "st": "microwave" # Search term
    }
    
    # Add seller ID filter if provided
    if seller_id:
        params["sid"] = seller_id
    
    print(f"Fetching microwaves from seller ID: {seller_id}")
    data = await fetch_data(session, url, params)
    
    # If fetch_data returned an empty dictionary, return empty list
    if not data or 'searchResults' not in data or 'items' not in data['searchResults']:
        print("No data returned or invalid response format")
        return []
    
    items = data['searchResults']['items']
    print(f"Found {len(items)} microwave items")
    
    # Process and return the items
    processed_items = []
    for item in items:
        seller_name = get_seller_name(item['sellerId'])
        
        # Create a dictionary with the item details
        processed_item = {
            'id': item['itemId'],
            'title': item['title'],
            'current_price': item['currentPrice'],
            'shipping_price': item['shippingPrice'],
            'end_time': item['endTime'],
            'num_bids': item['numBids'],
            'seller_id': item['sellerId'],
            'seller_name': seller_name,
            'image_url': item['imageURL']
        }
        
        processed_items.append(processed_item)
        
        # Store in database
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        # Check if the item already exists
        c.execute('SELECT id FROM items WHERE id = ?', (item['itemId'],))
        
        # Get the image data
        async with session.get(item['imageURL']) as response:
            image_data = await response.read()
        
        # If the item exists, update it
        if c.fetchone() is not None:
            c.execute('''
            UPDATE items
            SET search_term = ?, seller_name = ?, product_name = ?, price = ?, auction_end_time = ?, image_url = ?, shipping_price = ?, bids = ?, seller_id = ?
            WHERE id = ?
            ''', ('microwave', seller_name, item['title'], item['currentPrice'], item['endTime'], image_data, item['shippingPrice'], item['numBids'], item['sellerId'], item['itemId']))
        # If the item doesn't exist, insert it
        else:
            c.execute('''
            INSERT INTO items (id, search_term, seller_name, product_name, price, auction_end_time, image_url, shipping_price, bids, seller_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (item['itemId'], 'microwave', seller_name, item['title'], item['currentPrice'], item['endTime'], image_data, item['shippingPrice'], item['numBids'], item['sellerId']))
        
        conn.commit()
        conn.close()
    
    return processed_items

async def main():
    async with aiohttp.ClientSession() as session:
        items = await fetch_microwaves(session)
        
        # Print the results
        print("\nMicrowave Items Found:")
        print("=====================")
        for item in items:
            print(f"Title: {item['title']}")
            print(f"Price: ${item['current_price']}")
            print(f"Shipping: ${item['shipping_price']}")
            print(f"Seller: {item['seller_name']} (ID: {item['seller_id']})")
            print(f"Bids: {item['num_bids']}")
            print(f"Ends: {item['end_time']}")
            print(f"Image URL: {item['image_url']}")
            print("---------------------")

if __name__ == "__main__":
    asyncio.run(main()) 