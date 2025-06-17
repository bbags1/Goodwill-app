import sqlite3
import json
import os
from datetime import datetime

def get_db_connection():
    conn = sqlite3.connect('data/gw_data.db')
    conn.row_factory = sqlite3.Row
    return conn

def export_items():
    conn = get_db_connection()
    items = conn.execute('SELECT * FROM items').fetchall()
    conn.close()
    return [dict(item) for item in items]

def export_settings():
    conn = get_db_connection()
    settings = conn.execute('SELECT * FROM settings').fetchall()
    conn.close()
    return [dict(setting) for setting in settings]

def export_favorites():
    conn = get_db_connection()
    favorites = conn.execute('SELECT * FROM favorites').fetchall()
    conn.close()
    return [dict(favorite) for favorite in favorites]

def export_promising():
    conn = get_db_connection()
    promising = conn.execute('SELECT * FROM promising').fetchall()
    conn.close()
    return [dict(promising_item) for promising_item in promising]

def create_search_index(items):
    search_index = {}
    for item in items:
        # Create search terms from product name
        terms = f"{item['product_name']}".lower().split()
        for term in terms:
            if term not in search_index:
                search_index[term] = []
            search_index[term].append(item['id'])
    return search_index

def main():
    # Create output directory if it doesn't exist
    os.makedirs('kv_data', exist_ok=True)
    
    # Export data
    items = export_items()
    settings = export_settings()
    favorites = export_favorites()
    promising = export_promising()
    search_index = create_search_index(items)
    
    # Save data to JSON files
    with open('kv_data/items.json', 'w') as f:
        json.dump(items, f)
    
    with open('kv_data/settings.json', 'w') as f:
        json.dump(settings, f)
    
    with open('kv_data/favorites.json', 'w') as f:
        json.dump(favorites, f)
    
    with open('kv_data/promising.json', 'w') as f:
        json.dump(promising, f)
    
    with open('kv_data/search_index.json', 'w') as f:
        json.dump(search_index, f)
    
    print("Data exported successfully to kv_data directory")

if __name__ == '__main__':
    main() 