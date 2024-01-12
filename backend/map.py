import json

# Load the seller map
with open(r'C:\Users\brody\OneDrive\Documents\Copilot\Goodwill\backend\seller_map.json') as file:
    seller_map = json.load(file)

# Function to map seller ID to seller name
def get_seller_name(seller_id):
    return seller_map.get(str(seller_id), "Unknown Seller")
