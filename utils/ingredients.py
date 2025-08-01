import json

def extract_text(data):
    """
    Extracts text from various data structures.
    Handles strings, lists of strings, and lists of dictionaries.
    """
    if isinstance(data, str):
        # Split string by newlines and filter out empty strings
        return [s.strip() for s in data.split('\n') if s.strip()]
    
    if not isinstance(data, list):
        return []

    items = []
    for item in data:
        if isinstance(item, str):
            items.append(item)
        elif isinstance(item, dict):
            if 'text' in item:
                text_content = item.get('text')
                if text_content:
                    items.append(text_content)
            # Handle nested structures
            elif 'itemListElement' in item:
                items.extend(extract_text(item.get('itemListElement', [])))
    return items

with open('cookbook-100.json', encoding='utf-8') as f:
    data = json.load(f)

simple = []
for i, r in enumerate(data):
    if i >= 50:
        break
    simple.append({
        "title": r.get("name") or r.get("title"),
        "ingredients": extract_text(r.get("recipeIngredient", [])),
        "steps": extract_text(r.get("recipeInstructions", []))
    })

with open('recipes50.json', 'w', encoding='utf-8') as f:
    json.dump(simple, f, indent=2, ensure_ascii=False)
