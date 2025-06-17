#!/usr/bin/env python3
"""
Test script for the multimodal capabilities of the Gemini AI integration.
This script tests the price estimation with an image and product details.
"""

import asyncio
import logging
import sys
from gemini import analyze_item_price, get_image_data
from dotenv import load_dotenv
import os

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("test_gemini_multimodal")

# Load environment variables
load_dotenv()
api_key = os.getenv("API_KEY")
if not api_key:
    raise ValueError("API_KEY not found in .env file")

async def test_with_image():
    """Test the price estimation with an image."""
    # Test URLs - uncomment one to test
    test_items = [
        {
            "product_name": "Samsung 50-inch 4K Smart TV with HDR",
            "category_name": "Electronics",
            "image_url": "https://images.shopgoodwill.com/30/9-23-2023/184157235211170Aas.jpg",
            "shipping_price": 25.00
        },
        {
            "product_name": "Vintage Levi's 501 Jeans 32x34",
            "category_name": "Clothing",
            "image_url": "https://images.shopgoodwill.com/42/5-7-2022/150472873160903616.jpg",
            "shipping_price": 8.50
        },
        {
            "product_name": "Hamilton Khaki Field Automatic Watch",
            "category_name": "Jewelry & Watches",
            "image_url": "https://images.shopgoodwill.com/21/3-4-2023/7274117283903875fMH.jpg",
            "shipping_price": 12.00
        }
    ]

    results = []
    
    for item in test_items:
        logger.info(f"Testing with item: {item['product_name']}")
        
        # Get image data
        image_data = await get_image_data(item["image_url"])
        if not image_data:
            logger.error(f"Failed to get image data for {item['product_name']}")
            continue
            
        # Test with image
        logger.info("Testing price estimation with image...")
        price_with_image = await analyze_item_price(
            product_name=item["product_name"],
            category_name=item["category_name"],
            image_data=image_data,
            shipping_price=item["shipping_price"]
        )
        
        # Test without image for comparison
        logger.info("Testing price estimation without image...")
        price_without_image = await analyze_item_price(
            product_name=item["product_name"],
            category_name=item["category_name"],
            image_data=None,
            shipping_price=item["shipping_price"]
        )
        
        result = {
            "item": item["product_name"],
            "category": item["category_name"],
            "price_with_image": price_with_image,
            "price_without_image": price_without_image,
            "difference": price_with_image - price_without_image
        }
        
        results.append(result)
        logger.info(f"Results for {item['product_name']}:")
        logger.info(f"  With image: ${price_with_image:.2f}")
        logger.info(f"  Without image: ${price_without_image:.2f}")
        logger.info(f"  Difference: ${(price_with_image - price_without_image):.2f}")
        logger.info("-" * 50)
    
    # Summary
    logger.info("\nSummary of Results:")
    for result in results:
        logger.info(f"{result['item']} ({result['category']})")
        logger.info(f"  With image: ${result['price_with_image']:.2f}")
        logger.info(f"  Without image: ${result['price_without_image']:.2f}")
        logger.info(f"  Difference: ${result['difference']:.2f}")
        logger.info("")

if __name__ == "__main__":
    try:
        logger.info("Starting multimodal test...")
        asyncio.run(test_with_image())
        logger.info("Test completed successfully")
    except Exception as e:
        logger.error(f"Test failed: {str(e)}")
        sys.exit(1) 