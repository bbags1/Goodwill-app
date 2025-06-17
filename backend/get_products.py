import aiohttp
import asyncio
import sqlite3
import json
import os
from datetime import datetime
import pytz
from map import get_seller_name
from dotenv import load_dotenv
import base64
import time

# Load environment variables
load_dotenv()

# Database path - update this to your actual path
DB_PATH = r'/Users/brodybagnall/Documents/goodwill/Goodwill-app/backend/data/gw_data.db'

# API endpoint
API_URL = "https://buyerapi.shopgoodwill.com/api/Search/ItemListing"

async def fetch_data(session, url, seller_ids, page=1, search_term=""):
    """Fetch data from Goodwill API for specific sellers and page."""
    # Ensure seller_ids is a comma-separated string
    if isinstance(seller_ids, list):
        seller_ids_str = ",".join(str(sid) for sid in seller_ids)
    else:
        seller_ids_str = str(seller_ids)
        
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Accept-Encoding": "gzip, deflate, br, zstd",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
        "Origin": "https://shopgoodwill.com",
        "Referer": "https://shopgoodwill.com/"
    }
    
    payload = {
        "isSize": False,
        "isWeddingCatagory": "false",
        "isMultipleCategoryIds": False,
        "isFromHeaderMenuTab": False,
        "catIds": "",
        "categoryId": 0,
        "categoryLevel": 1,
        "categoryLevelNo": "1",
        "closedAuctionDaysBack": "7",
        "closedAuctionEndingDate": "3/7/2025",
        "highPrice": "999999",
        "isFromHeaderMenuTab": False,
        "isFromHomePage": False,
        "isMultipleCategoryIds": False,
        "isSize": False,
        "isWeddingCatagory": "false",
        "layout": "",
        "lowPrice": "0",
        "page": str(page),
        "pageSize": "40",
        "partNumber": "",
        "savedSearchId": 0,
        "searchBuyNowOnly": "",
        "searchCanadaShipping": "false",
        "searchClosedAuctions": "false",
        "searchDescriptions": "false",
        "searchInternationalShippingOnly": "false",
        "searchNoPickupOnly": "false",
        "searchOneCentShippingOnly": "false",
        "searchPickupOnly": "false",
        "searchText": "",
        "searchUSOnlyShipping": "true",
        "selectedCategoryIds": "",
        "selectedGroup": "",
        "selectedSellerIds": seller_ids_str,
        "sortColumn": "1",
        "sortDescending": "false",
        "useBuyerPrefs": "true"
    }

    print(f"Fetching page {page} for sellers: {seller_ids_str}" + (f" with search term '{search_term}'" if search_term else ""))
    try:
        async with session.post(url, json=payload, headers=headers, timeout=30) as response:
            if response.status == 200:
                data = await response.json()
                if 'searchResults' in data and 'items' in data['searchResults']:
                    total_items = data['searchResults'].get('totalItems', 0)
                    items_count = len(data['searchResults']['items'])
                    print(f"Successfully fetched {items_count} items for sellers {seller_ids_str}, page {page}")
                    return data, total_items
                print(f"No items found for sellers {seller_ids_str}, page {page}")
                return None, 0
            else:
                error_text = await response.text()
                print(f"Error fetching data for sellers {seller_ids_str}, page {page}: HTTP {response.status}")
                print(f"Response: {error_text[:200]}...")
                return None, 0
    except asyncio.TimeoutError:
        print(f"Timeout fetching data for sellers {seller_ids_str}, page {page}")
        return None, 0
    except Exception as e:
        print(f"Exception fetching data for sellers {seller_ids_str}, page {page}: {str(e)}")
        return None, 0

async def get_data(seller_ids=None, search_term=""):
    """Fetch data for specified seller IDs or from settings."""
    if not seller_ids:
        seller_ids = get_settings()
    
    if not seller_ids:
        print("No seller IDs provided and none found in settings")
        return
        
    if isinstance(seller_ids, str):
        try:
            seller_ids = json.loads(seller_ids)
        except:
            seller_ids = [seller_ids]
    
    print(f"Fetching all items from sellers: {seller_ids}" + (f" with search term '{search_term}'" if search_term else ""))
    
    # Connect to database
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    # Process all sellers together
    await process_all_pages(c, seller_ids, search_term)
    
    # Update search term for items if provided
    if search_term:
        c.execute("UPDATE items SET search_term = ? WHERE search_term IS NULL AND seller_id IN ({})".format(
            ','.join(['?'] * len(seller_ids))
        ), [search_term] + seller_ids)
    
    conn.commit()
    conn.close()
    print("Data collection completed and database updated")

async def process_all_pages(c, seller_ids, search_term=""):
    """Process all pages for the given seller IDs."""
    # Add category_name column if it doesn't exist
    try:
        c.execute('ALTER TABLE items ADD COLUMN category_name TEXT')
    except sqlite3.OperationalError:
        # Column already exists, continue
        pass
    
    page = 1
    total_processed = 0
    max_retries = 3
    max_pages = 500 # Limit to 10 pages per seller/search combination for safety
    
    async with aiohttp.ClientSession() as session:
        while page <= max_pages:
            # Try up to max_retries times for each page
            data = None
            for retry in range(max_retries):
                data, total_items = await fetch_data(session, API_URL, seller_ids, page, search_term)
                if data:
                    break
                
                if retry < max_retries - 1:
                    retry_delay = (retry + 1) * 2  # Exponential backoff
                    print(f"Retrying page {page} in {retry_delay} seconds (attempt {retry+1}/{max_retries})")
                    await asyncio.sleep(retry_delay)
                else:
                    print(f"Failed to fetch page {page} after {max_retries} attempts")
            
            # If we still don't have data after all retries, break the loop
            if not data or 'searchResults' not in data or 'items' not in data['searchResults']:
                print(f"End of results reached or error fetching data")
                break
                
            items = data['searchResults']['items']
            if not items:
                print(f"No more items")
                break
                
            saved_count = 0
            print(f"Processing {len(items)} items from page {page}")
            
            for item in items:
                try:
                    item_id = str(item['itemId'])
                    seller_id = str(item['sellerId'])
                    seller_name = get_seller_name(seller_id)
                    
                    # Get and transform category name - map "Size" categories to "Clothing"
                    category_name = item.get('categoryName', '')
                    if category_name and category_name.startswith('Size'):
                        category_name = 'Clothing'
                    
                    # Prepare item data
                    item_data = {
                        'id': item_id,
                        'seller_name': seller_name,
                        'product_name': item['title'],
                        'price': item['currentPrice'],
                        'auction_end_time': item['endTime'],
                        'image_url': item['imageURL'],
                        'shipping_price': item.get('shippingPrice', 0),
                        'bids': item.get('numBids', 0),
                        'seller_id': seller_id,
                        'search_term': search_term,
                        'category_name': category_name
                    }
                    
                    # Check if item exists and update or insert
                    c.execute('SELECT id FROM items WHERE id = ?', (item_id,))
                    if c.fetchone():
                        # Update existing item
                        placeholders = ', '.join([f"{k} = ?" for k in item_data.keys() if k != 'id'])
                        values = [item_data[k] for k in item_data.keys() if k != 'id']
                        values.append(item_id)  # For the WHERE clause
                        
                        c.execute(f"UPDATE items SET {placeholders} WHERE id = ?", values)
                    else:
                        # Insert new item
                        placeholders = ', '.join(['?'] * len(item_data))
                        columns = ', '.join(item_data.keys())
                        values = list(item_data.values())
                        
                        c.execute(f"INSERT INTO items ({columns}) VALUES ({placeholders})", values)
                    
                    saved_count += 1
                    
                except Exception as e:
                    print(f"Error processing item {item.get('itemId', 'unknown')}: {str(e)}")
                    continue
            
            # Commit after each page to avoid data loss
            c.connection.commit()
            
            total_processed += saved_count
            print(f"Page {page}: Processed {len(items)} items, saved {saved_count} items")
            print(f"Total processed: {total_processed} / {total_items if total_items else 'unknown'}")
            
            if len(items) < 40:  # Less than page size means we've reached the end
                print(f"Reached end of items (found {len(items)} on last page)")
                break
                
            page += 1
            if page > max_pages:
                print(f"Reached maximum page limit ({max_pages})")
                break
                
            # Rate limiting to avoid overloading the API
            await asyncio.sleep(1.5)

def get_settings():
    """Get seller IDs from settings."""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute("SELECT seller_ids FROM settings WHERE id = 1")
        result = c.fetchone()
        conn.close()
        
        if result and result['seller_ids']:
            try:
                return json.loads(result['seller_ids'])
            except:
                return ['19', '198']  # Default if JSON parsing fails
        return ['19', '198']  # Default
    except Exception as e:
        print(f"Error getting settings: {str(e)}")
        return ['19', '198']  # Default

async def test_api():
    """Test the API call directly with seller ID 19."""
    print("Testing API call with seller ID 19...")
    
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Accept-Encoding": "gzip, deflate, br, zstd",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
        "Origin": "https://shopgoodwill.com",
        "Referer": "https://shopgoodwill.com/"
    }
    
    payload = {
        "isSize": False,
        "isWeddingCatagory": "false",
        "isMultipleCategoryIds": False,
        "isFromHeaderMenuTab": False,
        "catIds": "",
        "categoryId": 0,
        "categoryLevel": 1,
        "categoryLevelNo": "1",
        "closedAuctionDaysBack": "7",
        "closedAuctionEndingDate": "3/7/2025",
        "highPrice": "999999",
        "isFromHeaderMenuTab": False,
        "isFromHomePage": False,
        "isMultipleCategoryIds": False,
        "isSize": False,
        "isWeddingCatagory": "false",
        "layout": "",
        "lowPrice": "0",
        "page": "1",
        "pageSize": "40",
        "partNumber": "",
        "savedSearchId": 0,
        "searchBuyNowOnly": "",
        "searchCanadaShipping": "false",
        "searchClosedAuctions": "false",
        "searchDescriptions": "false",
        "searchInternationalShippingOnly": "false",
        "searchNoPickupOnly": "false",
        "searchOneCentShippingOnly": "false",
        "searchPickupOnly": "false",
        "searchText": "",
        "searchUSOnlyShipping": "true",
        "selectedCategoryIds": "",
        "selectedGroup": "",
        "selectedSellerIds": "19",
        "sortColumn": "1",
        "sortDescending": "false",
        "useBuyerPrefs": "true"
    }
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(API_URL, json=payload, headers=headers, timeout=30) as response:
                if response.status == 200:
                    data = await response.json()
                    if 'searchResults' in data and 'items' in data['searchResults']:
                        items = data['searchResults']['items']
                        print(f"Success! Found {len(items)} items")
                        if items:
                            print("\nFirst item details:")
                            print(f"Title: {items[0]['title']}")
                            print(f"Price: ${items[0]['currentPrice']}")
                            print(f"End Time: {items[0]['endTime']}")
                            print(f"Seller ID: {items[0]['sellerId']}")
                    else:
                        print("No items found in response")
                else:
                    error_text = await response.text()
                    print(f"Error: HTTP {response.status}")
                    print(f"Response: {error_text[:200]}...")
        except Exception as e:
            print(f"Exception: {str(e)}")

if __name__ == "__main__":
    try:
        print("Testing API call...")
        asyncio.run(test_api())
        
        print("\nRunning product search for default sellers...")
        asyncio.run(get_data())
    except KeyboardInterrupt:
        print("\nProcess interrupted by user")
    except Exception as e:
        print(f"Error in main: {str(e)}")
        exit(1)



