import json
import os

# Get the current directory
current_dir = os.path.dirname(os.path.abspath(__file__))

# Load the category IDs
with open(os.path.join(current_dir, 'category_ids.json')) as f:
    category_ids = json.load(f)

# Invert the category_ids dictionary
category_names = {v: k for k, v in category_ids.items()}

def get_category_name(id):
    if str(id).isdigit():
        return category_names.get(int(id), id)
    else:
        return id
