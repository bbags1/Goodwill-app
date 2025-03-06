import json
import os

# Get the current directory
current_dir = os.path.dirname(os.path.abspath(__file__))

# Load the seller map
with open(os.path.join(current_dir, 'seller_map.json')) as file:
    seller_map = json.load(file)

# Function to map seller ID to seller name
def get_seller_name(seller_id):
    return seller_map.get(str(seller_id), "Unknown Seller")
