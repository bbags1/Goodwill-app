import asyncio
import sqlite3
import os
import google.generativeai as genai
import google.ai.generativelanguage as glm
import re
from datetime import datetime
import pytz
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
api_key = os.getenv("API_KEY")

if not api_key:
    print("Error: API_KEY not found in .env file")
    exit(1)

genai.configure(api_key=api_key)

# Get the current directory
current_dir = os.path.dirname(os.path.abspath(__file__))

# Database path
DB_PATH = os.path.join(current_dir, 'data/gw_data.db')

# Set timezone
pacific = pytz.timezone('US/Pacific')
pacific_time = datetime.now(pacific)
pacific_time_str = pacific_time.strftime('%Y-%m-%dT%H:%M:%S')

async def analyze_item(row):
    item_id, product_name, image_data, price, seller_name = row
    
    print(f"Analyzing item: {product_name}")
    print(f"Current price: ${price}")
    print(f"Seller: {seller_name}")
    print("Querying Gemini API for resale value estimation...")
    
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = await model.generate_content_async(
            glm.Content(
                parts = [
                    glm.Part(
                        inline_data=glm.Blob(
                        mime_type='image/jpeg',
                        data=image_data
                    )
                ),
                    glm.Part(text=f"Analyze the following product information and image; {product_name}."),
                    glm.Part(text = '''I am trying to buy and resell the items in the photo. 
                    They are used. Using historic eBay listings of the same or similar items to get sales data. 
                    Reason through those sales to estimate a price that each item could be sold for. 
                    If there are multiple items in the listing, treat each item individually and aggregate the total value. 
                    Do not explain your reasoning, Provide a single dollar amount in your response representing the total potential resale value. 
                    If you are unsure of what the item may be worth, respond with $0. Only respond with a single dollar amount.''')
            ],
        ),
            generation_config = genai.types.GenerationConfig(
                candidate_count=1,
                max_output_tokens=10,
                temperature=1.0),
                safety_settings=[
                    {
                        "category": "HARM_CATEGORY_HARASSMENT",
                        "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                    },
                    {
                        "category": "HARM_CATEGORY_HATE_SPEECH",
                        "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                    },
                    {
                        "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                        "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                    },
                    {
                        "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                        "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                    },
                ]
        )
        
        # Extract the price from the response
        response_text = response.text
        price_match = re.search(r'\$(\d+(?:\.\d+)?)', response_text)
        
        if price_match:
            estimated_price = float(price_match.group(1))
            
            # Calculate profit and margin
            current_price = float(price)
            profit = estimated_price - current_price
            margin = (profit / current_price) * 100 if current_price > 0 else 0
            
            print(f"Estimated resale value: ${estimated_price:.2f}")
            print(f"Potential profit: ${profit:.2f}")
            print(f"Profit margin: {margin:.2f}%")
            
            # Update the database with the estimated price
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            
            c.execute('''
            UPDATE items
            SET ebay_price = ?, profit = ?, margin = ?, last_updated = ?
            WHERE id = ?
            ''', (estimated_price, profit, margin, pacific_time_str, item_id))
            
            conn.commit()
            conn.close()
            
            print("Database updated with the estimated price.")
            print("-" * 50)
            
            return {
                'id': item_id,
                'product_name': product_name,
                'current_price': price,
                'estimated_price': estimated_price,
                'profit': profit,
                'margin': margin
            }
        else:
            print(f"Could not extract price from response: {response_text}")
            print("-" * 50)
            return None
    
    except Exception as e:
        print(f"Error analyzing item: {e}")
        print("-" * 50)
        return None

async def main():
    # Connect to the database
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Query for microwave items
    c.execute('''
    SELECT id, product_name, image_url, price, seller_name
    FROM items
    WHERE search_term = "microwave"
    AND ebay_price IS NULL
    AND product_name LIKE "%Microwave%"
    LIMIT 5
    ''')
    
    # Fetch the items
    rows = c.fetchall()
    conn.close()
    
    if not rows:
        print("No microwave items found in the database that need analysis.")
        return
    
    print(f"Found {len(rows)} microwave items to analyze.")
    print("=" * 50)
    
    # Analyze each item
    tasks = [analyze_item(row) for row in rows]
    results = await asyncio.gather(*tasks)
    
    # Filter out None results
    results = [result for result in results if result]
    
    # Print a summary
    print("\nAnalysis Summary:")
    print("=" * 50)
    
    for result in results:
        print(f"Product: {result['product_name']}")
        print(f"Current Price: ${result['current_price']}")
        print(f"Estimated Resale Value: ${result['estimated_price']:.2f}")
        print(f"Potential Profit: ${result['profit']:.2f}")
        print(f"Profit Margin: {result['margin']:.2f}%")
        print("-" * 50)

if __name__ == "__main__":
    asyncio.run(main()) 