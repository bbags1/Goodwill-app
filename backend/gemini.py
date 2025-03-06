import asyncio
import sqlite3
import google.generativeai as genai
import google.ai.generativelanguage as glm
from google.geneai.types import Tool, GenerateContentConfig, GoogleSearch
import re
from datetime import datetime
import pytz
from dotenv import load_dotenv
import os

load_dotenv()  # take environment variables from .env.
api_key = os.getenv("API_KEY")

genai.configure(api_key=api_key)

# Database path - update this to your actual path
DB_PATH = r'/Users/brodybagnall/Documents/goodwill/Goodwill-app/backend/data/gw_data.db'

pacific = pytz.timezone('US/Pacific')
pacific_time = datetime.now(pacific)
pacific_time_str = pacific_time.strftime('%Y-%m-%dT%H:%M:%S')


async def update_price(row, loop=None):
    try:
        # Use the provided loop or get the current one
        current_loop = loop or asyncio.get_event_loop()
        
        model = genai.GenerativeModel('gemini-2.0-flash-lite')
        # Use the current loop for the API call
        response = await model.generate_content_async(
            glm.Content(
                parts = [
                    glm.Part(
                        inline_data=glm.Blob(
                        mime_type='image/jpeg',
                        data=row[2]
                    )
                ),
                    glm.Part(text=f"Analyze the following product information and image; {row[1]}."),
                    glm.Part(text = '''I am trying to buy and resell the items in the photo. 
                    They are used. Using historic eBay listings of the same or similar items to get sales data. 
                    Reason through those sales to estimate a price that each item could be sold for. 
                    If there are multiple items in the listing, treat each item individually and aggregate the total value. 
                    Do not explain your reasoning, Provide a single dollar amount in your response representing the total potential resale value. 
                    If you are unsure of what the item may be worth, respond with $0. Only respond with a single dollar amount.''')
            ],
        ),
            generation_config = genai.types.GenerationConfig(
                # Only one candidate for now.
                candidate_count=1,
                max_output_tokens=10,
                temperature=1.0),
                safety_settings=[
        {
            "category": "HARM_CATEGORY_HARASSMENT",
            "threshold": "BLOCK_NONE",
        },
        {
            "category": "HARM_CATEGORY_HATE_SPEECH",
            "threshold": "BLOCK_NONE",
        },
        {
            "category": "HARM_CATEGORY_SEXUAL",
            "threshold": "BLOCK_NONE",
        },
        {
            "category": "HARM_CATEGORY_DANGEROUS",
            "threshold": "BLOCK_NONE",
        },
        {
            "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
            "threshold": "BLOCK_NONE",
        },
        {
            "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
            "threshold": "BLOCK_NONE",
        }
    ]
        )

        await asyncio.sleep(1)

        await response.resolve()
        
        # Extract the dollar amount from the response text
        dollar_amount = re.search(r'\$\d+(\.\d{2})?', response.text)
        if dollar_amount:
            # Remove the dollar sign and convert to float
            ebay_price = float(dollar_amount.group(0).replace('$', ''))
        else:
            ebay_price = 0.0
        print(response.text)
        

        # Connect to the SQLite database
        conn = sqlite3.connect(DB_PATH)

        # Create a cursor object
        c = conn.cursor()

        # Update the prices in the database
        c.execute('''
            UPDATE items
            SET ebay_price = ?
            WHERE id = ?
        ''', (ebay_price,  row[0]))

        # Commit the changes
        conn.commit()

        # Close the connection
        conn.close()

    except:
        model = genai.GenerativeModel('gemini-2.0-flash-lite')
        response = await model.generate_content_async(
            glm.Content(
                parts = [
                    glm.Part(text=f"Analyze the following product information; {row[1]}."),
            glm.Part(text = '''I am trying to buy and resell the items in the description. They are used, but in good condition. 
                Using historic eBay listings of the same or similar items to get sales data. 
                Reason through those sales to estimate a price that each item could be sold for. 
                If there are multiple items in the listing, treat each item individually and aggregate the total value. 
                Do not explain your reasoning, Provide a single dollar amount in your response representing the total potential resale value. 
                If you are unsure of what the item may be worth, respond with $0. Only respond with a single dollar amount.''')
                    ],
            ),
            generation_config = genai.types.GenerationConfig(
                # Only one candidate for now.
                candidate_count=1,
                max_output_tokens=20,
                temperature=1.0),
                safety_settings=[
        {
            "category": "HARM_CATEGORY_HARASSMENT",
            "threshold": "BLOCK_NONE",
        },
        {
            "category": "HARM_CATEGORY_HATE_SPEECH",
            "threshold": "BLOCK_NONE",
        },
        {
            "category": "HARM_CATEGORY_SEXUAL",
            "threshold": "BLOCK_NONE",
        },
        {
            "category": "HARM_CATEGORY_DANGEROUS",
            "threshold": "BLOCK_NONE",
        },
        {
            "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
            "threshold": "BLOCK_NONE",
        },
        {
            "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
            "threshold": "BLOCK_NONE",
        }
    ]
        )

        await asyncio.sleep(1)

        await response.resolve()
        
        # Extract the dollar amount from the response text
        dollar_amount = re.search(r'\$\d+(\.\d{2})?', response.text)
        if dollar_amount:
            # Remove the dollar sign and convert to float
            ebay_price = float(dollar_amount.group(0).replace('$', ''))
        else:
            ebay_price = 0.0

        print(response.text)


        # Connect to the SQLite database
        conn = sqlite3.connect(DB_PATH)

        # Create a cursor object
        c = conn.cursor()

        # Update the prices in the database
        c.execute('''
           UPDATE items
           SET ebay_price = ?
            WHERE id = ?
        ''', (ebay_price,  row[0]))

        # Commit the changes
        conn.commit()

        # Close the connection
        conn.close()

async def update_prices(loop=None):
    try:
        # Use the provided loop or get the current one
        current_loop = loop or asyncio.get_event_loop()
        
        # Connect to the SQLite database
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()

        c.execute(f'''
        SELECT id, product_name, image_url
        FROM items
        WHERE ebay_price IS NULL
        AND auction_end_time > ?
        LIMIT 30
        ''', [pacific_time_str])

        # Fetch all rows from the result of the SELECT statement
        rows = c.fetchall()
        
        # Close the connection
        conn.close()

        # If rows is empty, return early
        if not rows:
            print("No rows returned from the query. Stopping function.")
            return

        # Create tasks for each row
        tasks = []
        for row in rows:
            task = asyncio.create_task(update_price(row, loop=current_loop))
            tasks.append(task)

        # Wait for all tasks to complete
        await asyncio.gather(*tasks, return_exceptions=True)
        
    except Exception as e:
        print(f"Error in update_prices: {str(e)}")
        raise  # Re-raise the exception to be caught by the caller

# Run the function once every minute for the next hour
async def run_update_prices():
    for _ in range(240):  # Run 60 times
        await update_prices()
        await asyncio.sleep(61)  # Wait for 60 seconds

#asyncio.run(run_update_prices())