# query.py

from get_products import get_data
from gemini import run_update_prices
import asyncio

async def get_items(terms, term_type='search_term', category=None):
    if not isinstance(terms, list):
        terms = [terms]
    await get_data(terms, term_type, category)


searches = ['louboutin', 'zimmermann', 'arula', 'patagonia', 'north face', 'ugg', 'free people', 'vera wang', 'alexander mcqueen', 'ted baker', 'maggie london', 'wtoo', 'bhldn', 'tadash shoji', 'canada goose', 'lunya', 'anthropologie', 'cashmere', 'silk', 'burberry', 'wool', 'banana republic', 'arcteryx']
search_category = 10
for term in searches:
    try:
        asyncio.run(get_items([term], 'search_term', search_category))
    except Exception as e:
        print(f"Error with term {term}: {e}")

searches = ['bike', 'bicycle']
search_category = 12
for term in searches:
    try:
        asyncio.run(get_items([term], 'search_term', search_category))
    except Exception as e:
        print(f"Error with term {term}: {e}")

for_the_home = ['casa luna', 'threshold', 'brooklinen']
category_number = 195
subcategory = 197
for term in for_the_home:
    try:
        asyncio.run(get_items([term], 'search_term', (category_number, subcategory)))
    except Exception as e:
        print(f"Error with term {term}: {e}")

search_terms = ['mira fertility']
for term in search_terms:
    try:
        asyncio.run(get_items([term], 'search_term'))
    except Exception as e:
        print(f"Error with term {term}: {e}")

categories = [(114, 2228), (10, 453), (12,), (7, 183), 1, 33, (15, 71), (7, 465), (7, 30)]
for item in categories:
    try:
        asyncio.run(get_items(item, 'category'))
    except Exception as e:
        print(f"Error with category {item}: {e}")

try:
    asyncio.run(run_update_prices())
except Exception as e:
    print(f"Error running update prices: {e}")

