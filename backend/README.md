# Goodwill App Backend

This is the backend service for the Goodwill Auction Analysis Tool. It handles product fetching, price analysis, notifications, and scheduled tasks.

## Core Files

- `app.py` - Main Flask application with API endpoints
- `get_products.py` - Handles fetching products from Goodwill's API
- `gemini.py` - Price analysis using Google's Gemini AI with multimodal capabilities
- `notifications.py` - Email and SMS notification system
- `scheduler.py` - Manages scheduled tasks (product updates, price analysis)
- `map.py` - Maps seller IDs to location names
- `remove_old.py` - Cleans up expired auction items
- `test_gemini_multimodal.py` - Tests multimodal image-based price estimation

## Setup

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create a `.env` file with the following variables:
```
API_KEY=your_gemini_api_key
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USER=your_email@gmail.com
EMAIL_PASSWORD=your_email_password
TWILIO_ACCOUNT_SID=your_twilio_sid
TWILIO_AUTH_TOKEN=your_twilio_token
TWILIO_PHONE_NUMBER=your_twilio_phone_number
```

4. Run the application:
```bash
python app.py
```

The server will start on port 5001.

## AI Price Estimation

The application uses Google's Gemini Pro model for price estimation with the following features:

- **Multimodal Processing**: Analyzes both product descriptions and images to provide more accurate price estimates
- **Category-Aware**: Takes into account the product category when determining market value
- **Shipping Cost Consideration**: Factors in shipping costs for more realistic profitability assessment
- **Precise Pricing**: Avoids rounded estimates (like $50.00) for more realistic valuations

To test the multimodal AI capabilities:
```bash
python test_gemini_multimodal.py
```

## API Endpoints

- `/products` - Get products matching search criteria
- `/locations` - Get available Goodwill locations
- `/settings` - Get/update user settings
- `/manual-search` - Trigger manual product search
- `/manual-price-update` - Trigger manual price analysis
- `/favorites` - Manage favorite items
- `/promising` - Manage promising items

## Database

The application uses SQLite with the following tables:
- `items` - Stores product information
- `settings` - User preferences and configurations
- `favorites` - Saved favorite items
- `promising` - Items marked as promising

The database file is located at `data/gw_data.db`. 

## Batch Processing Controls

When running the price update process manually, you can control the batch size and concurrency:

```bash
# Test mode with 3 items
python gemini.py --test --batch-size 3

# Process all items with custom batch size and concurrency
python gemini.py --batch-size 5 --max-concurrent 1
```

Note: We recommend using a batch size of 5 and max concurrent of 1 for optimal performance with multimodal processing. 