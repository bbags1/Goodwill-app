import json

# Load the category IDs
with open(r'C:\Users\brody\OneDrive\Documents\Copilot\Goodwill\category_ids.json') as f:
    category_ids = json.load(f)

# Invert the category_ids dictionary
category_names = {v: k for k, v in category_ids.items()}

def get_category_name(id):
    if str(id).isdigit():
        return category_names.get(int(id), id)
    else:
        return id
