import asyncio
import google.generativeai as genai
import re
from datetime import datetime
import pytz
from dotenv import load_dotenv
import os
import logging
import sys
import base64
import requests
from io import BytesIO
from db import get_items_for_price_update, update_item_price, get_pending_price_updates_count

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("gemini.log", mode='a'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("gemini")
logger.info("Starting Gemini module")

# Load environment variables
load_dotenv()
api_key = os.getenv("API_KEY")
if not api_key:
    raise ValueError("API_KEY not found in .env file")

# Configure Gemini with API key
genai.configure(api_key=api_key)
logger.info("Gemini API configured")

# Pacific timezone for timestamps
pacific = pytz.timezone('US/Pacific')

# Using flash-lite model for fast multimodal processing
MODEL_NAME = 'models/gemini-2.0-flash-lite'

def get_image_data(image_url):
    """
    Get image data from a URL or base64 string.
    Returns image data in the format required by Gemini API.
    """
    try:
        if not image_url:
            logger.warning("No image URL provided")
            return None
            
        if image_url.startswith('http'):
            # It's a URL, download the image
            logger.info(f"Downloading image from URL: {image_url}")
            response = requests.get(image_url, timeout=10)
            if response.status_code != 200:
                logger.warning(f"Failed to download image: HTTP {response.status_code}")
                return None
                
            image_bytes = BytesIO(response.content).getvalue()
            return {"mime_type": "image/jpeg", "data": image_bytes}
        else:
            # It's already a base64 string
            try:
                # Make sure it's proper base64 by decoding and re-encoding
                image_bytes = base64.b64decode(image_url)
                return {"mime_type": "image/jpeg", "data": image_bytes}
            except Exception as e:
                logger.warning(f"Invalid base64 image data: {str(e)}")
                return None
    except Exception as e:
        logger.error(f"Error processing image: {str(e)}")
        return None

def analyze_item_price(product_name, category_name=None, image_data=None, shipping_price=0):
    """
    Analyze a product's price using Gemini Flash-Lite with multimodal capabilities.
    Uses both product images and text data for more accurate pricing.
    """
    if not product_name or len(product_name.strip()) < 3:
        logger.warning(f"Skipping analysis for invalid product name: '{product_name}'")
        return 0.0
    
    try:
        logger.info(f"Analyzing '{product_name}' with {MODEL_NAME}")
        model = genai.GenerativeModel(model_name=MODEL_NAME)
        
        # Create a more detailed prompt for accurate pricing
        prompt = f"""You are a professional product appraiser specializing in secondhand and resale markets.
        
        ITEM DETAILS:
        - Product Name: {product_name}
        - Category: {category_name or 'Unknown'}
        - Shipping Cost: ${shipping_price:.2f}
        
        TASK:
        Analyze this product from Goodwill and estimate its exact fair market resale value on platforms like eBay.
        
        PRICING GUIDELINES:
        1. Be precise with your price estimate (avoid rounded values like $50.00 or $100.00)
        2. Consider brand, condition, features, and rarity
        3. Bulk or wholesale items are generally not worth as much as you think they are.
        4. Research comparable recent sales when possible
        5. Factor in the product category: {category_name or 'Unknown'}
        6. Your estimate determines whether our company will buy the item or not. If the item is not worth purchasing at all, respond with "$0.00".
        7. If an image is provided, carefully analyze:
           - Item condition from visible wear/damage
           - Brand authenticity markers
           - Special features or details
           - Quality of materials
           - Any defects or issues
        
        RESPONSE FORMAT:
        Respond ONLY with a single precise dollar amount, formatted like "$XX.XX". 
        If you cannot determine a price with confidence, respond with "$0.00".
        """
        
        logger.info(f"Sending request to Gemini for '{product_name}'")
        
        generation_config = genai.types.GenerationConfig(
            candidate_count=1,
            max_output_tokens=50,
            temperature=0.1  # Lower temperature for more consistent results
        )
        
        if image_data:
            # Multimodal request with image
            logger.info("Including image data in request")
            response = model.generate_content(
                [image_data, prompt],
                generation_config=generation_config
            )
        else:
            # Text-only request
            logger.info("Text-only request (no image available)")
            response = model.generate_content(
                prompt,
                generation_config=generation_config
            )
        
        response_text = response.text.strip()
        logger.info(f"Response: '{response_text}'")
        
        # Extract dollar amount with improved regex
        match = re.search(r'\$(\d+(?:\.\d{1,2})?)', response_text)
        if match:
            price = float(match.group(1))
            logger.info(f"Extracted price: ${price:.2f}")
            return price
        elif response_text == "$0.00":
            logger.info(f"Price set to $0.00 for '{product_name}'")
            return 0.0
        
        logger.warning(f"Invalid response format: '{response_text}'")
        return 0.0
    
    except Exception as e:
        logger.error(f"Request failed for '{product_name}': {str(e)}")
        return 0.0

async def process_batch(items, semaphore):
    """Process a batch of items with rate limiting."""
    if not items:
        logger.warning("Empty batch received")
        return 0, 0
    
    logger.info(f"Processing batch of {len(items)} items")
    item_ids = [item.get('id', 'unknown') for item in items]
    print(f"Items to process: {item_ids}")
    
    tasks = [process_item(item, semaphore) for item in items]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    success_count = sum(1 for r in results if not isinstance(r, Exception) and r)
    fail_count = len(results) - success_count
    
    logger.info(f"Batch completed: {success_count} successful, {fail_count} failed")
    return success_count, fail_count

async def process_item(item, semaphore):
    """Process a single item with rate limiting."""
    async with semaphore:
        try:
            item_id = item.get('id', 'unknown')
            product_name = item.get('product_name', '')
            price = float(item.get('price', 0) or 0)
            shipping_price = float(item.get('shipping_price', 0) or 0)
            category_name = item.get('category_name', '')
            image_url = item.get('image_url', '')
            
            if not product_name:
                logger.warning(f"Skipping item {item_id}: No product name")
                return False
            
            logger.info(f"Processing item {item_id}: {product_name}")
            
            # Process image if available
            image_data = None
            if image_url:
                logger.info(f"Item has an image URL, processing...")
                image_data = get_image_data(image_url)
                if image_data:
                    logger.info("Successfully processed image")
                else:
                    logger.warning("Failed to process image, continuing with text-only analysis")
            
            # Add a small delay for rate limiting
            await asyncio.sleep(0.02)  # Rate limiting: ~3000 req/min with 60 concurrent (leaving headroom)
            
            # Get price estimate with all available data
            ebay_price = analyze_item_price(
                product_name=product_name,
                category_name=category_name,
                image_data=image_data,
                shipping_price=shipping_price
            )
            
            update_time = datetime.now(pacific).strftime('%Y-%m-%dT%H:%M:%S')
            
            update_item_price(item_id, ebay_price, update_time, price, shipping_price)
            if ebay_price > 0:
                logger.info(f"Updated item {item_id} with price ${ebay_price:.2f}")
                return True
            logger.info(f"Marked item {item_id} as attempted (price $0.00)")
            return False
        
        except Exception as e:
            logger.error(f"Error processing item {item_id}: {str(e)}")
            return False

async def update_prices(batch_size=30, test_mode=False, max_concurrent=60):
    """Update prices for items without estimated prices."""
    try:
        batch_size = max(1, min(batch_size, 100))  # Allow larger batches
        max_concurrent = max(1, min(max_concurrent, 60))  # Allow up to 60 concurrent requests
        
        total_pending = get_pending_price_updates_count()
        if total_pending == 0:
            logger.info("No items need price updates")
            return
        
        logger.info(f"Found {total_pending} items needing price updates")
        logger.info(f"Config: batch_size={batch_size}, test_mode={test_mode}, max_concurrent={max_concurrent}")
        
        semaphore = asyncio.Semaphore(max_concurrent)
        total_processed = 0
        
        while True:
            items = get_items_for_price_update(batch_size, test_mode)
            if not items:
                logger.info("No more items to process")
                break
            
            success_count, fail_count = await process_batch(items, semaphore)
            total_processed += len(items)
            
            if test_mode:
                logger.info(f"Test mode completed. Processed {total_processed} items")
                break
            
            remaining = get_pending_price_updates_count()
            logger.info(f"Progress: {total_processed} processed, {remaining} remaining")
            if remaining == 0:
                break
        
        logger.info(f"Price update completed. Total items processed: {total_processed}")
        
    except Exception as e:
        logger.error(f"Error in update_prices: {str(e)}")
        raise

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Update item prices using Gemini AI with multimodal analysis')
    parser.add_argument('--test', action='store_true', help='Run in test mode')
    parser.add_argument('--batch-size', type=int, default=30, help='Batch size (1-100)')
    parser.add_argument('--max-concurrent', type=int, default=60, help='Max concurrent calls (1-60)')
    args = parser.parse_args()
    
    try:
        asyncio.run(update_prices(
            batch_size=args.batch_size,
            test_mode=args.test,
            max_concurrent=args.max_concurrent
        ))
    except Exception as e:
        logger.error(f"Main execution error: {str(e)}")
        sys.exit(1)