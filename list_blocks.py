import json

with open('analysis.json', 'r') as f:
    data = json.load(f)

for item in data:
    if item['blocks']:
        # Filter out generic headers
        blocks = [b for b in item['blocks'] if "flashcards" not in b.lower() and "greenlight" not in b.lower()]
        if blocks:
            print(f"Page {item['page']}: {blocks[0].splitlines()[0]}")
