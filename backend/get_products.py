import aiohttp
import sqlite3
import asyncio
import json
from urllib.parse import quote_plus
from map import get_seller_name
from get_search_name import get_category_name, category_names 
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database path - update this to your actual path
DB_PATH = r'/Users/brodybagnall/Documents/goodwill/Goodwill-app/backend/data/gw_data.db'

async def fetch_data(session, url, params):
    async with session.get(url, params=params) as response:
        if response.status == 200:
            return await response.json()
        else:
            print(f"Error fetching {url}: HTTP {response.status}")
            return {}  # Return an empty dictionary in case of error

async def fetch_and_process_page(session, c, url, term, page, term_type='search_term', category=None, seller_id=None, target_seller_ids=None):
    print(f"Preparing to fetch page: {page}")
    params = {
        "pn": 4,
        "cl": 1,
        "cids": "",
        "scids": "",
        "p": page,
        "sc": 1,
        "sd": "false",
        "cid": 0,
        "sg": "Keyword",
        "st": ""
    }

    if term_type == 'search_term':
        params["st"] = term
        if isinstance(category, int):
            params['scids'] = str(category)
        elif isinstance(category, tuple):
            params['cids'] = str(category[0])
            params['scids'] = str(category[1])
            
    if term_type == 'category':
        if isinstance(term, tuple):
            params["cids"] = str(term[0])
            params["scids"] = str(term[1])
        elif isinstance(term, int):
            params["scids"] = str(term)

    # Note: We're not adding seller_id to params anymore since we want to filter after fetching
    # This allows us to get all items and then filter by seller_id

    data = await fetch_data(session, url, params)

    # If fetch_data returned an empty dictionary, stop processing
    if not data:
        return {"has_items": False, "has_matching_items": False}

    items = data['searchResults']['items']
    
    # If there are no items at all, we've reached the end of the search results
    if len(items) == 0:
        print(f"No items found on page {page}, end of search results for term: {term}")
        return {"has_items": False, "has_matching_items": False}
    
    saved_count = 0

    for item in items:
        # Check if this item's seller ID is in our target list
        if target_seller_ids and str(item['sellerId']) not in target_seller_ids:
            continue  # Skip this item if it's not from a seller we're interested in
            
        # Get the seller name
        seller_name = get_seller_name(item['sellerId'])

        # If the term is a category, convert it to a category name
        if term_type == 'category':
            if isinstance(term, int):
                term = get_category_name(term)
            elif isinstance(term, tuple):
                term = get_category_name(term[0])
  
        # Convert the image url to binary data
        async with session.get(item['imageURL']) as response:
            image_data = await response.read()

        await asyncio.sleep(1)

        # Check if the item already exists
        c.execute('''
        SELECT id FROM items WHERE id = ?
        ''', (item['itemId'],))

        # If the item exists, update it
        if c.fetchone() is not None:
            c.execute('''
            UPDATE items
            SET search_term = ?, seller_name = ?, product_name = ?, price = ?, auction_end_time = ?, image_url = ?, shipping_price = ?, bids = ?, seller_id = ?
            WHERE id = ?
            ''', (term, seller_name, item['title'], item['currentPrice'], item['endTime'], image_data, item['shippingPrice'], item['numBids'], item['sellerId'], item['itemId']))
            saved_count += 1

        # If the item doesn't exist, insert it
        else:
            c.execute('''
            INSERT INTO items (id, search_term, seller_name, product_name, price, auction_end_time, image_url, shipping_price, bids, seller_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (item['itemId'], term, seller_name, item['title'], item['currentPrice'], item['endTime'], image_data, item['shippingPrice'], item['numBids'], item['sellerId']))
            saved_count += 1
    
    print(f"Page {page}: Processed {len(items)} items, saved {saved_count} items matching seller IDs")
    return {
        "has_items": True,  # We found items on this page
        "has_matching_items": saved_count > 0  # We saved at least one item that matched our seller IDs
    }

async def get_data_for_term(session, c, url, term, term_type='search_term', category=None, seller_id=None, target_seller_ids=None):
    if term_type == 'search_term':
        term = quote_plus(term)
    
    # Limit to 200 pages to avoid timeouts and errors
    max_pages = 200
    
    # Process pages one by one and stop when we reach the end of search results
    for page in range(1, max_pages + 1):
        result = await fetch_and_process_page(
            session, c, url, term, page, term_type, category, seller_id, target_seller_ids
        )
        
        # If there are no more items at all, we've reached the end of search results
        if not result["has_items"]:
            print(f"End of search results reached for term: {term}")
            break
            
        # Small delay between pages to avoid overwhelming the API
        await asyncio.sleep(1)

async def get_data(terms, term_type='search_term', category=None, seller_id=None, target_seller_ids=None, loop=None):
    # Use the provided loop or get the current one
    current_loop = loop or asyncio.get_event_loop()
    
    url = "https://buyerapi.shopgoodwill.com/api/Search/ItemListingData"

    # If seller_id is provided but target_seller_ids is not, use seller_id as the only target
    if seller_id and not target_seller_ids:
        target_seller_ids = [str(seller_id)]
    
    # Connect to the SQLite database
    conn = sqlite3.connect(DB_PATH)
    print('Connected to database')
    c = conn.cursor()
    
    print(f"Searching for terms: {terms}")
    print(f"Filtering for seller IDs: {target_seller_ids}")

    # Use the current loop for the ClientSession
    async with aiohttp.ClientSession(loop=current_loop) as session:
        tasks = [
            get_data_for_term(
                session, c, url, term, term_type, category, seller_id, target_seller_ids
            ) for term in terms
        ]
        await asyncio.gather(*tasks)

    # Commit the changes and close the connection
    conn.commit()
    conn.close()
    print("Search completed and database updated")

def get_settings():
    """Retrieve user settings from the database."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    c.execute("SELECT location, search_terms, seller_ids FROM settings WHERE id = 1")
    row = c.fetchone()
    
    settings = {
        'location': '198',  # Default to Spokane
        'search_terms': ['microwave'],
        'seller_ids': ['19', '198']  # Default to Spokane seller IDs
    }
    
    if row:
        settings['location'] = row[0]
        
        # Parse search_terms JSON
        if row[1]:
            try:
                settings['search_terms'] = json.loads(row[1])
            except json.JSONDecodeError:
                pass  # Keep default
                
        # Parse seller_ids JSON
        if row[2]:
            try:
                settings['seller_ids'] = json.loads(row[2])
            except json.JSONDecodeError:
                pass  # Keep default
    
    conn.close()
    return settings

if __name__ == "__main__":
    # Get user settings
    settings = get_settings()
    
    # Get all categories
    with open('category_ids.json', 'r') as f:
        categories = json.load(f)
    
    # Use the seller IDs from settings
    seller_ids = settings['seller_ids']
    
    # Process search terms with all seller IDs as targets
    search_terms = settings['search_terms']
    if search_terms and len(search_terms) > 0:
        print(f"Fetching data for search terms: {search_terms} with seller IDs: {seller_ids}")
        asyncio.run(get_data(search_terms, target_seller_ids=seller_ids))
    
    # Then process categories if needed
    # Uncomment the following code if you want to also fetch by categories
    # print(f"Fetching data for categories with seller IDs: {seller_ids}")
    # asyncio.run(get_data(categories, term_type='category', target_seller_ids=seller_ids))



