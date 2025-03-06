import sqlite3
import smtplib
import os
import json
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from twilio.rest import Client
from dotenv import load_dotenv
import pytz
from datetime import datetime

# Load environment variables
load_dotenv()

# Database path - update this to your actual path
DB_PATH = r'/Users/brodybagnall/Documents/goodwill/Goodwill-app/backend/data/gw_data.db'

# Email configuration
EMAIL_HOST = os.getenv('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT = int(os.getenv('EMAIL_PORT', 587))
EMAIL_USER = os.getenv('EMAIL_USER', '')
EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD', '')

# Twilio configuration
TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID', '')
TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN', '')
TWILIO_PHONE_NUMBER = os.getenv('TWILIO_PHONE_NUMBER', '')

def get_settings():
    """Retrieve user settings from the database."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    c.execute("SELECT location, margin_threshold, notification_email, notification_phone, notification_type, update_frequency FROM settings WHERE id = 1")
    row = c.fetchone()
    
    if row:
        settings = {
            "location": row[0],
            "margin_threshold": row[1],
            "notification_email": row[2],
            "notification_phone": row[3],
            "notification_type": row[4],
            "update_frequency": row[5]
        }
    else:
        settings = {
            "location": "198",
            "margin_threshold": 50,
            "notification_email": "",
            "notification_phone": "",
            "notification_type": "email",
            "update_frequency": "daily"
        }
    
    conn.close()
    return settings

def get_interesting_items():
    """Find items that meet the margin threshold criteria."""
    settings = get_settings()
    location = settings["location"]
    margin_threshold = settings["margin_threshold"]
    
    # Get location name from seller_map.json
    with open('seller_map.json', 'r') as f:
        seller_map = json.load(f)
    
    location_name = seller_map.get(location, "Unknown Location")
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    pacific = pytz.timezone('US/Pacific')
    pacific_time = datetime.now(pacific)
    pacific_time_str = pacific_time.strftime('%Y-%m-%dT%H:%M:%S')
    
    # Find items with margin above threshold
    query = '''
    SELECT id, product_name, price, ebay_price, (ebay_price - price) AS price_difference, 
           ((ebay_price - price) / ebay_price * 100) AS margin_percentage,
           bids
    FROM items 
    WHERE ebay_price IS NOT NULL 
    AND auction_end_time > ?
    AND seller_name = ?
    AND ((ebay_price - price) / ebay_price * 100) >= ?
    ORDER BY margin_percentage DESC
    LIMIT 10
    '''
    
    c.execute(query, (pacific_time_str, location_name, margin_threshold))
    
    interesting_items = []
    for row in c.fetchall():
        item = {
            'id': row[0],
            'product_name': row[1],
            'price': row[2],
            'ebay_price': row[3],
            'price_difference': row[4],
            'margin_percentage': row[5],
            'is_bin': row[6] == 0 or row[6] is None
        }
        interesting_items.append(item)
    
    conn.close()
    return interesting_items, location_name

def send_email_notification(items, location_name):
    """Send email notification about interesting items."""
    settings = get_settings()
    recipient_email = settings["notification_email"]
    
    if not recipient_email or not EMAIL_USER or not EMAIL_PASSWORD:
        print("Email notification skipped: Missing email configuration")
        return False
    
    # Create email content
    msg = MIMEMultipart()
    msg['From'] = EMAIL_USER
    msg['To'] = recipient_email
    msg['Subject'] = f"Goodwill Alert: {len(items)} Interesting Items Found in {location_name}"
    
    # Create HTML content
    html = f"""
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            h1 {{ color: #4CAF50; }}
            .item {{ margin-bottom: 20px; padding: 15px; border: 1px solid #ddd; border-radius: 5px; }}
            .item h2 {{ margin-top: 0; font-size: 18px; }}
            .price-info {{ display: flex; justify-content: space-between; }}
            .price-column {{ flex: 1; }}
            .bin-badge {{ display: inline-block; background-color: #ff6b6b; color: white; padding: 3px 8px; border-radius: 12px; font-size: 12px; margin-left: 10px; }}
            .view-button {{ display: block; background-color: #4CAF50; color: white; text-align: center; padding: 10px; text-decoration: none; border-radius: 5px; margin-top: 10px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Goodwill Interesting Items Alert</h1>
            <p>We found {len(items)} items in {location_name} with a profit margin of {settings['margin_threshold']}% or higher:</p>
            
            {''.join([f"""
            <div class="item">
                <h2>{item['product_name']} {f'<span class="bin-badge">Buy It Now</span>' if item['is_bin'] else ''}</h2>
                <div class="price-info">
                    <div class="price-column">
                        <p><strong>Current Price:</strong> ${item['price']:.2f}</p>
                        <p><strong>Potential Resale:</strong> ${item['ebay_price']:.2f}</p>
                    </div>
                    <div class="price-column">
                        <p><strong>Profit:</strong> ${item['price_difference']:.2f}</p>
                        <p><strong>Margin:</strong> {item['margin_percentage']:.0f}%</p>
                    </div>
                </div>
                <a href="https://shopgoodwill.com/item/{item['id']}" class="view-button">View Item</a>
            </div>
            """ for item in items])}
            
            <p>Visit the app to see more details and save these items.</p>
        </div>
    </body>
    </html>
    """
    
    msg.attach(MIMEText(html, 'html'))
    
    try:
        server = smtplib.SMTP(EMAIL_HOST, EMAIL_PORT)
        server.starttls()
        server.login(EMAIL_USER, EMAIL_PASSWORD)
        server.send_message(msg)
        server.quit()
        print(f"Email notification sent to {recipient_email}")
        return True
    except Exception as e:
        print(f"Failed to send email: {str(e)}")
        return False

def send_sms_notification(items, location_name):
    """Send SMS notification about interesting items."""
    settings = get_settings()
    recipient_phone = settings["notification_phone"]
    
    if not recipient_phone or not TWILIO_ACCOUNT_SID or not TWILIO_AUTH_TOKEN or not TWILIO_PHONE_NUMBER:
        print("SMS notification skipped: Missing Twilio configuration")
        return False
    
    # Create SMS content
    message_body = f"Goodwill Alert: {len(items)} interesting items found in {location_name} with {settings['margin_threshold']}%+ margin.\n\n"
    
    # Add top 3 items
    for i, item in enumerate(items[:3]):
        message_body += f"{i+1}. {item['product_name'][:40]}{'...' if len(item['product_name']) > 40 else ''}\n"
        message_body += f"   Price: ${item['price']:.2f}, Resale: ${item['ebay_price']:.2f}, Margin: {item['margin_percentage']:.0f}%\n"
        message_body += f"   https://shopgoodwill.com/item/{item['id']}\n\n"
    
    if len(items) > 3:
        message_body += f"+ {len(items) - 3} more items. Check the app for details."
    
    try:
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        message = client.messages.create(
            body=message_body,
            from_=TWILIO_PHONE_NUMBER,
            to=recipient_phone
        )
        print(f"SMS notification sent to {recipient_phone}")
        return True
    except Exception as e:
        print(f"Failed to send SMS: {str(e)}")
        return False

def send_notifications():
    """Send notifications based on user preferences."""
    settings = get_settings()
    notification_type = settings["notification_type"]
    
    # Get interesting items
    interesting_items, location_name = get_interesting_items()
    
    if not interesting_items:
        print("No interesting items found that meet the criteria")
        return
    
    print(f"Found {len(interesting_items)} interesting items in {location_name}")
    
    # Send notifications based on user preference
    if notification_type == "email":
        send_email_notification(interesting_items, location_name)
    elif notification_type == "sms":
        send_sms_notification(interesting_items, location_name)
    elif notification_type == "both":
        send_email_notification(interesting_items, location_name)
        send_sms_notification(interesting_items, location_name)

if __name__ == "__main__":
    send_notifications() 