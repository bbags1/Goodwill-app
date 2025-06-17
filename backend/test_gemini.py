#!/usr/bin/env python3

import google.generativeai as genai
import os
from dotenv import load_dotenv
import asyncio

# Load environment variables
load_dotenv()
api_key = os.getenv('API_KEY')
print(f'API Key found: {bool(api_key)}')

# Configure Gemini
genai.configure(api_key=api_key)

async def test_gemini_models():
    """Test which Gemini models are available and working."""
    print("\nTesting Gemini API connection...")
    
    try:
        print("\nListing available models:")
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                print(f"- {m.name}")
    except Exception as e:
        print(f"Error listing models: {str(e)}")
    
    # Test different model names
    test_models = [
        'gemini-pro',
        'gemini-1.5-pro',
        'gemini-1.0-pro'
    ]
    
    for model_name in test_models:
        print(f"\nTesting model: {model_name}")
        try:
            model = genai.GenerativeModel(model_name)
            response = await model.generate_content_async("What is 2+2?")
            await response.resolve()
            print(f"Response: {response.text}")
            print(f"Success with model {model_name}")
        except Exception as e:
            print(f"Error with model {model_name}: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_gemini_models()) 