import sqlite3
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DATABASE_NAME = 'ecommerce.db'
OUTPUT_JSONL_FILE = 'products_vertex_ai.jsonl'

# Fields that are stored as JSON strings in SQLite and need to be parsed
JSON_STRING_FIELDS = [
    'flower_color', 'flowering_season', 'harvest_time',
    'pollinator_types', 'landscape_use', 'companion_plants_ids',
    'recommended_soil_ids', 'recommended_fertilizer_ids'
]

# Fields that are boolean in the Vertex AI schema (SQLite stores them as 0 or 1)
BOOLEAN_FIELDS_VERTEX_AI_MAPPING = {
    'fruit_bearing': 'fruit_bearing',
    'pet_safe': 'pet_safe',
    'attracts_pollinators': 'attracts_pollinators',
    'deer_resistant': 'deer_resistant',
    'drought_tolerant': 'drought_tolerant',
    'organic': 'organic', # For soil/fertilizers
    'pot_drainage_holes': 'pot_drainage_holes' # For pots
}

# Fields that should be numbers in Vertex AI (some might be REAL or INTEGER in SQLite)
NUMERIC_FIELDS_VERTEX_AI_MAPPING = {
    'mature_height_cm': 'mature_height_cm',
    'mature_width_cm': 'mature_width_cm',
    'volume_liters': 'volume_liters',
    'pot_diameter_cm': 'pot_diameter_cm',
    'pot_height_cm': 'pot_height_cm'
}

def fetch_products_from_db():
    conn = sqlite3.connect(DATABASE_NAME)
    conn.row_factory = sqlite3.Row # Access columns by name
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM products")
    products = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return products

def transform_product_for_vertex_ai(product_data):
    vertex_ai_product = {
        "id": product_data.get('id'),
        "title": product_data.get('name'),
        "description": product_data.get('description'),
        "categories": [product_data.get('category')] if product_data.get('category') else [],
        "priceInfo": {
            "currencyCode": "USD", # Assuming USD, make configurable if needed
            "price": product_data.get('price'),
            "originalPrice": product_data.get('original_price') # Add if available
        },
        "availability": "IN_STOCK" if product_data.get('stock', 0) > 0 else "OUT_OF_STOCK",
        "availableQuantity": product_data.get('stock'), # Vertex AI likely handles int or string
        "images": [{"uri": f"https://your-store.com/{product_data.get('image_url')}"}] if product_data.get('image_url') else [],
        "uri": f"https://your-store.com/products/{product_data.get('id')}", # Construct URI
        "languageCode": product_data.get('language_code', 'en') # Default to 'en'
    }

    attributes = {}

    # Handle standard text attributes and parsed JSON strings
    for key, value in product_data.items():
        # Exclude fields already mapped to top-level Vertex AI product schema or not direct attributes
        if key in ['id', 'name', 'description', 'price', 'original_price', 'stock', 'category', 'image_url', 'product_uri', 'language_code']:
            continue

        if value is None:
            continue

        if key in JSON_STRING_FIELDS:
            try:
                parsed_value = json.loads(value) if isinstance(value, str) else value
                if parsed_value: # Ensure not empty list/dict after parsing
                    attributes[key] = {"text": parsed_value if isinstance(parsed_value, list) else [str(parsed_value)]}
            except json.JSONDecodeError:
                logger.warning(f"Could not decode JSON for field {key} in product {product_data.get('id')}. Value: {value}")
        elif key in BOOLEAN_FIELDS_VERTEX_AI_MAPPING:
            attributes[BOOLEAN_FIELDS_VERTEX_AI_MAPPING[key]] = {"text": [str(bool(value)).lower()]}
        elif key in NUMERIC_FIELDS_VERTEX_AI_MAPPING:
            try:
                attributes[NUMERIC_FIELDS_VERTEX_AI_MAPPING[key]] = {"numbers": [float(value)]}
            except (ValueError, TypeError):
                 logger.warning(f"Could not convert field {key} to float for product {product_data.get('id')}. Value: {value}")
        else: # Default to text attribute
            attributes[key] = {"text": [str(value)]}
            
    if attributes:
        vertex_ai_product["attributes"] = attributes

    return vertex_ai_product

def main():
    logger.info(f"Fetching products from '{DATABASE_NAME}'...")
    all_products_data = fetch_products_from_db()
    logger.info(f"Fetched {len(all_products_data)} products.")

    logger.info(f"Transforming products and writing to '{OUTPUT_JSONL_FILE}'...")
    count = 0
    with open(OUTPUT_JSONL_FILE, 'w') as f:
        for product_data in all_products_data:
            try:
                vertex_ai_product = transform_product_for_vertex_ai(product_data)
                f.write(json.dumps(vertex_ai_product) + '\n')
                count += 1
            except Exception as e:
                logger.error(f"Failed to process product {product_data.get('id')}: {e}", exc_info=True)
    
    logger.info(f"Successfully wrote {count} products to '{OUTPUT_JSONL_FILE}'.")

if __name__ == '__main__':
    main()
