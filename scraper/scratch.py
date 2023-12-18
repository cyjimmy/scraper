import json

# Read JSON data from a file
with open('car_listings.json', 'r') as f:
    parsed_data = json.load(f)

# Find the number of items in the dictionary
num_items = len(parsed_data)

print(f"The number of items in the JSON object is {num_items}")