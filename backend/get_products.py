import aiohttp
import sqlite3
import asyncio
import json
from urllib.parse import quote_plus
from map import get_seller_name
from get_search_name import get_category_name, category_names 

async def fetch_data(session, url, params):
    async with session.get(url, params=params) as response:
        if response.status == 200:
            return await response.json()
        else:
            print(f"Error fetching {url}: HTTP {response.status}")
            return {}  # Return an empty dictionary in case of error

async def fetch_and_process_page(session, c, url, term, page, term_type='search_term', category=None):
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


    data = await fetch_data(session, url, params)

    # If fetch_data returned an empty dictionary, stop processing
    if not data:
        return

    items = data['searchResults']['items']

    for item in items:
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

        # If the item doesn't exist, insert it
        else:
            c.execute('''
            INSERT INTO items (id, search_term, seller_name, product_name, price, auction_end_time, image_url, shipping_price, bids, seller_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (item['itemId'], term, seller_name, item['title'], item['currentPrice'], item['endTime'], image_data, item['shippingPrice'], item['numBids'], item['sellerId']))

async def get_data_for_term(session, c, url, term, term_type='search_term', category=None):
    if term_type == 'search_term':
        term = quote_plus(term)
    tasks = [fetch_and_process_page(session, c, url, term, page, term_type, category) for page in range(1, 200)]
    await asyncio.gather(*tasks)

async def get_data(terms, term_type='search_term', category=None):
    url = "https://buyerapi.shopgoodwill.com/api/Search/ItemListingData"

    # Connect to the SQLite database
    conn = sqlite3.connect(r'C:\Users\brody\OneDrive\Documents\Copilot\Goodwill\backend\data\gw_data.db')
    print('connected')
    c = conn.cursor()

    async with aiohttp.ClientSession() as session:
        tasks = [get_data_for_term(session, c, url, term, term_type, category) for term in terms]
        await asyncio.gather(*tasks)

    # Commit the changes and close the connection
    conn.commit()
    conn.close()



