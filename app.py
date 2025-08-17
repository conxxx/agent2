# cymbal_home_garden_backend/app.py
import sys
import os

# --- Start of sys.path modification block ---
print("DEBUG: app.py - Script execution started (sys.path modification block).")
print(f"DEBUG: app.py - Initial sys.path: {sys.path}")

current_file_path = os.path.abspath(__file__) # Should be C:\Users\Lenovo\OneDrive\Desktop\adk-samples\app.py
print(f"DEBUG: app.py - current_file_path (os.path.abspath(__file__)): {current_file_path}")

project_root = os.path.dirname(current_file_path) # Should be C:\Users\Lenovo\OneDrive\Desktop\adk-samples
print(f"DEBUG: app.py - Calculated project_root (os.path.dirname(current_file_path)): {project_root}")

if project_root not in sys.path:
    sys.path.insert(0, project_root)
    print(f"DEBUG: app.py - project_root '{project_root}' was NOT in sys.path. Inserted at index 0.")
else:
    # If it is already there, ensure it's at the front for priority.
    if sys.path[0] != project_root:
        sys.path.remove(project_root)
        sys.path.insert(0, project_root)
        print(f"DEBUG: app.py - project_root '{project_root}' was IN sys.path but not at index 0. Moved to index 0.")
    else:
        print(f"DEBUG: app.py - project_root '{project_root}' was ALREADY at sys.path[0]. No change needed to its position.")

print(f"DEBUG: app.py - Final sys.path (after potential modification): {sys.path}")
print("--- End of sys.path modification block ---")

# --- Load Environment Variables ---
from dotenv import load_dotenv
# Load variables from the specific .env file.
# This will make GEMINI_API_KEY available to os.environ.get()
dotenv_path = os.path.join(project_root, 'agents', 'customer-service', '.env')
load_dotenv(dotenv_path=dotenv_path)
print(f"DEBUG: app.py - Attempted to load .env file from: {dotenv_path}")
if os.path.exists(dotenv_path):
    print(f"DEBUG: app.py - .env file found at path.")
    if os.environ.get("GEMINI_API_KEY"):
        print("DEBUG: app.py - GEMINI_API_KEY was successfully loaded into environment.")
    else:
        print("ERROR: app.py - .env file was found, but it does not contain GEMINI_API_KEY.")
else:
    print(f"ERROR: app.py - .env file NOT found at path: {dotenv_path}")

import sqlite3
import logging
import json # Added for JSON deserialization
import time # Added for time.time()
from flask import Flask, jsonify, request, g, render_template
from werkzeug.exceptions import HTTPException # Added for specific error handling
from google.cloud import retail_v2
from google.api_core.exceptions import GoogleAPICallError
from google.api_core.client_options import ClientOptions # Added for regional endpoint
from google.auth import default as default_auth_credentials # Added for ADC logging
import importlib.util # Required for the workaround

# --- Workaround for importing from a directory with a hyphen ---
# Define the path to the module we want to import
module_name = "image_identifier"
# Note: We use 'customer-service' (hyphen) here to match the actual directory name
module_path = os.path.join(project_root, "agents", "customer-service", "customer_service", "tools", f"{module_name}.py")

# Create a "module spec" from the file path
spec = importlib.util.spec_from_file_location(module_name, module_path)
# Create a module object from the spec
image_identifier_module = importlib.util.module_from_spec(spec)
# "Execute" the module to load its contents
spec.loader.exec_module(image_identifier_module)
# Now we can access the function from the loaded module object
identify_item_in_image = image_identifier_module.identify_item_in_image
# --- End of workaround ---

app = Flask(__name__, template_folder='cymbal_home_garden_backend/templates', static_folder='cymbal_home_garden_backend/static')
# For serving frontend directly from Flask, uncomment above and adjust paths if frontend is in a sibling folder.
# For now, focusing on API. Frontend files will be structured to be served from Flask's default static/template folders.

DATABASE = 'ecommerce.db'

# --- Configuration for Google Cloud Retail API ---
# User needs to fill these in based on their GCP setup
GCP_PROJECT_ID = "elemental-day-467117-h4"  # Replace with your Project ID
RETAIL_API_LOCATION = "global"          # Or your specific location e.g., "us-east1"
RETAIL_CATALOG_ID = "default_catalog"   # Replace with your Catalog ID
# This is the ID of the "Search" Serving Config you create in the Retail Console
RETAIL_SERVING_CONFIG_ID = "default_search" # Replace with your Serving Config ID

# --- Logging Setup ---
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# --- Database Helper Functions ---
def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row # Access columns by name
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

# --- Error Handlers ---
@app.errorhandler(404)
def not_found(error):
    # Check if the request wants JSON or HTML
    # For API routes (like /api/*), return JSON. For page routes, render 404.html.
    if request.path.startswith('/api/'):
        return jsonify({"error": "Not Found", "message": str(error)}), 404
    # For other routes, assume HTML is preferred
    return render_template('404.html', error_message=str(error)), 404


@app.errorhandler(400)
def bad_request(error):
    # If the error is a Werkzeug HTTPException, it has a description.
    # Otherwise, it might be a more generic error Flask caught.
    message = error.description if isinstance(error, HTTPException) else "Invalid request."
    if request.is_json: # Check if the original request claimed to be JSON
        # This handles cases where request.get_json() fails due to malformed JSON
        # but content-type was application/json
        if "Failed to decode JSON object" in message or "unexpected end of data" in message: # Werkzeug specific messages
             message = "Invalid JSON payload provided."
    return jsonify({"error": "Bad Request", "message": message}), 400

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Server Error: {error}")
    # For API routes, return JSON. For page routes, render 500.html (if exists).
    if request.path.startswith('/api/'):
        return jsonify({"error": "Internal Server Error", "message": "An unexpected error occurred."}), 500
    # Optionally, render a 500.html template for user-facing pages
    return render_template('500.html', error_message="An unexpected server error occurred."), 500


# --- API Endpoints ---

# === Product Endpoints (SQLite-backed) ===
@app.route('/api/products', methods=['GET'])
def get_products():
    """Lists all products or filters by name/category."""
    logger.info(f"Received GET request for /api/products. Query params: {request.args}")
    query_params = request.args
    name_filter = query_params.get('name')
    category_filter = query_params.get('category')
    plant_type_filter = query_params.get('plant_type') # New filter

    db = get_db()
    cursor = db.cursor()
    
    # Select all columns from the products table
    query = "SELECT * FROM products" # Changed from specific columns to *
    filters = []
    params = []

    if name_filter:
        filters.append("name LIKE ?")
        params.append(f"%{name_filter}%")
    if category_filter:
        filters.append("category = ?")
        params.append(category_filter)
    if plant_type_filter: # New filter condition
        filters.append("plant_type LIKE ?") # Using LIKE for flexibility, e.g. "Perennial" vs "Perennial Shrub"
        params.append(f"%{plant_type_filter}%")
    
    if filters:
        query += " WHERE " + " AND ".join(filters)
        
    cursor.execute(query, params)
    products_rows = cursor.fetchall()
    products = []
    for row in products_rows:
        product_dict = dict(row)
        # Deserialize JSON strings back into lists for relevant fields
        for field in ['flower_color', 'flowering_season', 'pollinator_types', 
                      'landscape_use', 'companion_plants_ids', 'recommended_soil_ids', 
                      'recommended_fertilizer_ids', 'harvest_time']:
            if product_dict.get(field) and isinstance(product_dict[field], str):
                try:
                    product_dict[field] = json.loads(product_dict[field])
                except json.JSONDecodeError:
                    logger.warning(f"Could not decode JSON for field {field} in product {product_dict['id']}")
                    product_dict[field] = [] # Default to empty list on error
            elif product_dict.get(field) is None:
                 product_dict[field] = [] # Default to empty list if field is None (for consistency in API response)
        products.append(product_dict)

    logger.info(f"Returning {len(products)} products from /api/products.")
    return jsonify(products)

@app.route('/api/products/<string:product_id>', methods=['GET'])
def get_product_detail(product_id):
    """Gets specific product details, including a nested 'attributes' object."""
    logger.info(f"Received GET request for /api/products/{product_id}.")
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM products WHERE id = ?", (product_id,))
    product_row = cursor.fetchone()

    if not product_row:
        logger.warning(f"Product {product_id} not found for GET /api/products/{product_id}.")
        return jsonify({"error": "Product not found"}), 404

    product_data = dict(product_row)
    attributes = {}
    
    # Define which columns from the DB should be nested under "attributes"
    attribute_fields = [
        'botanical_name', 'plant_type', 'mature_height_cm', 'mature_width_cm',
        'light_requirement', 'water_needs', 'watering_frequency_notes',
        'soil_preference', 'soil_ph_preference', 'hardiness_zone', 'flower_color',
        'flowering_season', 'fragrance', 'fruit_bearing', 'care_level', 'pet_safe',
        'attracts_pollinators', 'pollinator_types', 'deer_resistant', 'drought_tolerant',
        'landscape_use', 'indoor_outdoor', 'companion_plants_ids',
        'recommended_soil_ids', 'recommended_fertilizer_ids', 'harvest_time'
    ]

    # Populate the attributes dictionary, deserializing JSON strings where needed
    for field in attribute_fields:
        if field in product_data and product_data[field] is not None:
            value = product_data[field]
            # Fields that are stored as JSON strings in the DB
            json_fields = [
                'flower_color', 'flowering_season', 'pollinator_types', 'landscape_use',
                'companion_plants_ids', 'recommended_soil_ids', 'recommended_fertilizer_ids',
                'harvest_time'
            ]
            if field in json_fields and isinstance(value, str):
                try:
                    attributes[field] = json.loads(value)
                except json.JSONDecodeError:
                    logger.warning(f"Could not decode JSON for field {field} in product {product_data['id']}")
                    attributes[field] = [] # Default to empty list on error
            else:
                attributes[field] = value

    # Construct the final response with top-level keys and the nested attributes
    product_response = {
        'id': product_data.get('id'),
        'name': product_data.get('name'),
        'description': product_data.get('description'),
        'price': product_data.get('price'),
        'category': product_data.get('category'),
        'stock': product_data.get('stock'),
        'image_url': product_data.get('image_url'),
        'product_url': f"/products/{product_data.get('id')}",
        'attributes': attributes # Add the nested attributes object
    }

    logger.info(f"Returning structured details for product {product_id}.")
    return jsonify(product_response)

@app.route('/api/products/availability/<string:product_id>/<string:store_id>', methods=['GET'])
def check_product_availability_endpoint(product_id, store_id):
    """
    Checks product stock from SQLite.
    The 'store_id' is part of the path to match ADK tool, but currently ignored in logic
    as we assume a single inventory source.
    Output matches ADK tool: {'available': bool, 'quantity': int, 'store': str}
    """
    logger.info(f"Received GET request for /api/products/availability/{product_id}/{store_id}.")
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT stock FROM products WHERE id = ?", (product_id,))
    row = cursor.fetchone()
    
    if row:
        stock_quantity = row['stock']
        # For MVP, store_id is acknowledged but fixed response for 'store' field
        # In a real scenario, store_id would query different inventories or locations
        return jsonify({
            "available": stock_quantity > 0,
            "quantity": stock_quantity,
            "store": f"Cymbal Home Warehouse (Queried for {store_id})" # Or simply "Cymbal Home Warehouse"
        })
    else:
        logger.warning(f"Product {product_id} not found for availability check at store {store_id}.")
        # Return the specific 404 error format observed in the logs
        return jsonify({"error": "Product not found for availability check"}), 404

# === Shopping Cart Endpoints (SQLite-backed) ===
@app.route('/api/cart/<string:customer_id>', methods=['GET'])
def get_cart(customer_id):
    """
    Retrieves the customer's cart contents.
    Output matches ADK tool: {'items': [{'product_id': ..., 'name': ..., 'quantity': ...}], 'subtotal': ...}
    """
    logger.info(f"Received GET request for /api/cart/{customer_id}.")
    db = get_db()
    cursor = db.cursor()
    
    # Join cart_items with products to get product name and price
    cursor.execute('''
        SELECT ci.product_id, p.name, ci.quantity, p.price 
        FROM cart_items ci
        JOIN products p ON ci.product_id = p.id
        WHERE ci.customer_id = ?
    ''', (customer_id,))
    
    items = []
    subtotal = 0.0
    for row in cursor.fetchall():
        item_total = row['quantity'] * row['price']
        items.append({
            "product_id": row['product_id'],
            "name": row['name'],
            "quantity": row['quantity'],
            "price_per_unit": row['price'], # Added for clarity on frontend
            "item_total": round(item_total, 2) # Added for clarity on frontend
        })
        subtotal += item_total
        
    logger.info(f"Returning cart for customer {customer_id} with {len(items)} item types, subtotal: {subtotal:.2f}.")
    return jsonify({
        "items": items,
        "subtotal": round(subtotal, 2)
    })

@app.route('/api/cart/modify/<string:customer_id>', methods=['POST'])
def modify_cart_endpoint(customer_id):
    """
    Modifies the user's shopping cart by adding and/or removing items.
    Expects JSON: {'items_to_add': [{'product_id': ..., 'quantity': ...}], 
                   'items_to_remove': [{'product_id': ..., 'quantity': ...}]}
    Output matches ADK tool: {'status': ..., 'message': ..., 'items_added': bool, 'items_removed': bool}
    """
    data = request.get_json()
    logger.info(f"Received POST request for /api/cart/modify/{customer_id}. Payload: {data}")
    if not data:
        logger.error(f"Invalid JSON payload for /api/cart/modify/{customer_id}.")
        return jsonify({"error": "Invalid JSON payload"}), 400

    items_to_add = data.get('items_to_add', [])
    items_to_remove = data.get('items_to_remove', [])
    
    db = get_db()
    cursor = db.cursor()
    
    items_added_flag = False
    items_removed_flag = False

    # Process items to add/update
    if items_to_add:
        for item_add in items_to_add:
            product_id = item_add.get('product_id')
            quantity_to_add = item_add.get('quantity', 0)

            if not product_id or not isinstance(quantity_to_add, int) or quantity_to_add <= 0:
                logger.warning(f"Invalid item to add: {item_add} for customer {customer_id}")
                continue

            # Check product stock
            cursor.execute("SELECT stock FROM products WHERE id = ?", (product_id,))
            product_stock_row = cursor.fetchone()
            if not product_stock_row or product_stock_row['stock'] < quantity_to_add:
                logger.warning(f"Not enough stock for {product_id} or product does not exist.")
                # Potentially return a specific error or just skip adding
                continue

            cursor.execute("SELECT id, quantity FROM cart_items WHERE customer_id = ? AND product_id = ?", (customer_id, product_id))
            cart_item = cursor.fetchone()
            
            if cart_item: # Update quantity if item already in cart
                new_quantity = cart_item['quantity'] + quantity_to_add
                # Ensure new quantity doesn't exceed stock (though initial add check should cover this)
                if new_quantity <= product_stock_row['stock']:
                    cursor.execute("UPDATE cart_items SET quantity = ? WHERE id = ?", (new_quantity, cart_item['id']))
                    items_added_flag = True
                else:
                    logger.warning(f"Cannot add {quantity_to_add} of {product_id}, exceeds stock for existing cart item.")
            else: # Add new item to cart
                cursor.execute("INSERT INTO cart_items (customer_id, product_id, quantity) VALUES (?, ?, ?)",
                               (customer_id, product_id, quantity_to_add))
                items_added_flag = True
    
    # Process items to remove/decrease quantity
    if items_to_remove:
        for item_rem in items_to_remove:
            product_id = item_rem.get('product_id')
            quantity_to_remove = item_rem.get('quantity', 0)

            if not product_id or not isinstance(quantity_to_remove, int) or quantity_to_remove <= 0:
                logger.warning(f"Invalid item to remove: {item_rem} for customer {customer_id}")
                continue

            cursor.execute("SELECT id, quantity FROM cart_items WHERE customer_id = ? AND product_id = ?", (customer_id, product_id))
            cart_item = cursor.fetchone()

            if cart_item:
                if quantity_to_remove >= cart_item['quantity']: # Remove item completely
                    cursor.execute("DELETE FROM cart_items WHERE id = ?", (cart_item['id'],))
                else: # Decrease quantity
                    new_quantity = cart_item['quantity'] - quantity_to_remove
                    cursor.execute("UPDATE cart_items SET quantity = ? WHERE id = ?", (new_quantity, cart_item['id']))
                items_removed_flag = True
    
    db.commit()
    
    message = "Cart updated."
    if not items_added_flag and not items_removed_flag:
        message = "No changes made to the cart (items might be out of stock or invalid)."
    logger.info(f"Cart modification for customer {customer_id} completed. Message: {message}, Added: {items_added_flag}, Removed: {items_removed_flag}")
    return jsonify({
        "status": "success", 
        "message": message,
        "items_added": items_added_flag,
        "items_removed": items_removed_flag
    })

@app.route('/api/cart/<string:customer_id>/item', methods=['POST'])
def add_or_update_cart_item(customer_id):
    """Adds a product to the cart or updates its quantity.
    Expects JSON: {"product_id": "...", "quantity": N (integer)}
    If quantity is 0 or less, the item is effectively removed or quantity reduced.
    For complete removal regardless of quantity, use DELETE /api/cart/<customer_id>/item/<product_id>
    """
    data = request.get_json()
    logger.info(f"Received POST request for /api/cart/{customer_id}/item. Payload: {data}")
    if not data or 'product_id' not in data or 'quantity' not in data:
        logger.error(f"Invalid JSON payload for /api/cart/{customer_id}/item. Payload: {data}")
        return jsonify({"error": "Invalid JSON payload. 'product_id' and 'quantity' are required."}), 400

    product_id = data.get('product_id')
    quantity = data.get('quantity')

    if not isinstance(quantity, int):
        return jsonify({"error": "'quantity' must be an integer."}), 400

    db = get_db()
    cursor = db.cursor()

    # Check product existence and stock
    cursor.execute("SELECT stock FROM products WHERE id = ?", (product_id,))
    product_stock_row = cursor.fetchone()

    if not product_stock_row:
        return jsonify({"error": f"Product {product_id} not found."}), 404

    current_stock = product_stock_row['stock']

    cursor.execute("SELECT id, quantity FROM cart_items WHERE customer_id = ? AND product_id = ?", (customer_id, product_id))
    cart_item = cursor.fetchone()

    if quantity > 0:
        requested_quantity_increase = quantity # How many to add in this request
        if cart_item:
            # Item exists, increment quantity
            new_quantity = cart_item['quantity'] + requested_quantity_increase
            # Check against total stock for the *new total quantity*
            if new_quantity > current_stock:
                return jsonify({"error": f"Not enough stock for {product_id} to increase quantity to {new_quantity}. Available: {current_stock}, Current in cart: {cart_item['quantity']}"}), 400
            cursor.execute("UPDATE cart_items SET quantity = ? WHERE id = ?", (new_quantity, cart_item['id']))
            message = f"Quantity for product {product_id} updated to {new_quantity}."
        else:
            # Item does not exist, add new with the given quantity
            if requested_quantity_increase > current_stock:
                return jsonify({"error": f"Not enough stock for {product_id}. Available: {current_stock}, Requested: {requested_quantity_increase}"}), 400
            cursor.execute("INSERT INTO cart_items (customer_id, product_id, quantity) VALUES (?, ?, ?)",
                           (customer_id, product_id, requested_quantity_increase))
            message = f"Product {product_id} added to cart with quantity {requested_quantity_increase}."
    elif quantity <= 0: # Quantity is 0 or negative, remove item or reduce (though DELETE endpoint is better for full removal)
        if cart_item:
            # For simplicity with this endpoint, if quantity <=0, we remove the item.
            # More complex logic could allow reducing quantity if this endpoint was also for that.
            cursor.execute("DELETE FROM cart_items WHERE id = ?", (cart_item['id'],))
            message = f"Product {product_id} removed from cart due to quantity <= 0."
        else:
            # Trying to set non-existent item to 0 or less quantity - no action needed.
            message = f"Product {product_id} not in cart, no action taken for quantity <= 0."
            return jsonify({"status": "no_action", "message": message}), 200


    db.commit()
    logger.info(f"Cart item operation for customer {customer_id}, product {product_id} (quantity {quantity}) resulted in: {message}")
    return jsonify({"status": "success", "message": message}), 200


@app.route('/api/cart/<string:customer_id>/item/<string:product_id>', methods=['DELETE'])
def remove_cart_item_completely(customer_id, product_id):
    """Removes an entire product line from the customer's cart."""
    logger.info(f"Received DELETE request for /api/cart/{customer_id}/item/{product_id}.")
    db = get_db()
    cursor = db.cursor()
    
    cursor.execute("DELETE FROM cart_items WHERE customer_id = ? AND product_id = ?", (customer_id, product_id))
    db.commit()
    
    if cursor.rowcount > 0:
        logger.info(f"Product {product_id} removed from cart for customer {customer_id}.")
        return jsonify({"status": "success", "message": f"Product {product_id} removed from cart."}), 200
    else:
        logger.warning(f"Product {product_id} not found in cart for customer {customer_id} during DELETE, or already removed.")
        return jsonify({"status": "not_found", "message": f"Product {product_id} not found in cart or already removed."}), 404

@app.route('/api/cart/<string:customer_id>/clear', methods=['DELETE'])
def clear_customer_cart(customer_id):
    """Clears all items from the customer's cart."""
    logger.info(f"Received DELETE request for /api/cart/{customer_id}/clear.")
    db = get_db()
    cursor = db.cursor()
    
    cursor.execute("DELETE FROM cart_items WHERE customer_id = ?", (customer_id,))
    db.commit()
    
    items_deleted_count = cursor.rowcount
    logger.info(f"Cart cleared for customer {customer_id}. Items deleted: {items_deleted_count}.")
    # We can return success even if cart was already empty, as the state is achieved.
    return jsonify({"status": "success", "message": "Cart cleared.", "items_deleted": items_deleted_count}), 200

@app.route('/api/checkout/place_order', methods=['POST'])
def place_order():
    """
    Simulates placing an order.
    Expects JSON: { "customer_id": "...", "items": [...], "shipping_details": {...}, "total_amount": ... }
    """
    data = request.get_json(silent=True) # Use silent=True to prevent it from raising its own 400 error for malformed JSON
    if data is None: # Check if data is None (malformed JSON or wrong content type)
        # If content type was application/json but data is None, it was malformed.
        if request.content_type == 'application/json':
            return jsonify({"error": "Bad Request", "message": "Invalid JSON payload provided."}), 400
        return jsonify({"error": "Bad Request", "message": "Invalid JSON payload or missing Content-Type: application/json."}), 400

    customer_id = data.get('customer_id')
    items = data.get('items')
    shipping_details = data.get('shipping_details')
    total_amount = data.get('total_amount')

    if not all([customer_id, items, shipping_details, total_amount is not None]):
        return jsonify({"error": "Missing required fields for order (customer_id, items, shipping_details, total_amount)"}), 400

    logger.info(f"Simulating order placement for customer_id: {customer_id}")
    logger.info(f"Order Items: {json.dumps(items, indent=2)}")
    logger.info(f"Shipping Details: {json.dumps(shipping_details, indent=2)}")
    logger.info(f"Total Amount: {total_amount}")

    # Simulate clearing the cart for this customer after order placement
    db = get_db()
    cursor = db.cursor()
    cursor.execute("DELETE FROM cart_items WHERE customer_id = ?", (customer_id,))
    db.commit()
    logger.info(f"Cart cleared for customer {customer_id} after simulated order placement.")

    # In a real app, you'd save the order to a new 'orders' table,
    # interact with payment gateways, trigger shipping processes, etc.
    
    return jsonify({
        "status": "success",
        "message": "Order placed successfully (Simulated). Thank you for your purchase!",
        "order_id": f"SIM_{time.time()}" # Generate a pseudo-unique simulated order ID
    }), 201 # 201 Created is often used for successful resource creation

# === Phase 4: Conceptual Order Submission Endpoint ===
@app.route('/api/orders/place_order', methods=['POST'])
def conceptual_place_order():
    """
    Phase 4: Conceptual order placement.
    Logs received order data and returns a mock success response.
    Actual call from frontend is in Phase 5.
    """
    data = request.get_json(silent=True)
    logger.info(f"Received POST request for conceptual /api/orders/place_order. Payload: {data}")

    if data is None:
        if request.content_type == 'application/json':
            logger.error(f"Invalid JSON payload for /api/orders/place_order.")
            return jsonify({"error": "Bad Request", "message": "Invalid JSON payload provided."}), 400
        logger.error(f"Missing Content-Type: application/json for /api/orders/place_order.")
        return jsonify({"error": "Bad Request", "message": "Invalid JSON payload or missing Content-Type: application/json."}), 400

    # Expected structure (similar to checkoutProcessState)
    # customer_id = data.get('customer_id') # Or derive from session/auth in real app
    # selected_items = data.get('selectedItems')
    # shipping_info = data.get('shippingInfo')
    # payment_info = data.get('paymentInfo')
    # total_amount = 0 # Calculate from items or get from payload

    # For MVP, just log the whole thing
    logger.info(f"Conceptual Order Data Received for /api/orders/place_order: {json.dumps(data, indent=2)}")

    # No database interaction or payment processing in this phase for this endpoint.
    
    mock_order_id = f"MOCK_ORDER_{int(time.time())}"
    logger.info(f"Conceptual order {mock_order_id} processed for /api/orders/place_order.")
    
    return jsonify({
        "success": True,
        "message": "Order received (conceptual)",
        "order_id": mock_order_id
    }), 201


# === Image Identification Endpoint ===
@app.route('/api/identify-image', methods=['POST'])
def identify_image_endpoint():
    """
    Identifies the primary item in an uploaded image.
    Expects a multipart/form-data request with an image file under the key 'image'.
    """
    logger.info("Received POST request for /api/identify-image.")
    if 'image' not in request.files:
        logger.error("No image file part in the request for /api/identify-image.")
        return jsonify({"error": "No image file provided in the 'image' field."}), 400

    file = request.files['image']
    if file.filename == '':
        logger.error("No image selected for upload in /api/identify-image.")
        return jsonify({"error": "No image selected for upload."}), 400

    if file:
        try:
            image_bytes = file.read()
            original_filename = file.filename
            logger.info(f"Processing image '{original_filename}' for identification.")
            
            identified_item_name = identify_item_in_image(image_bytes, original_filename)
            
            if identified_item_name.startswith("Error:"):
                logger.error(f"Image identification failed: {identified_item_name}")
                # Return a more generic error to the client for API key issues
                if "API Key not configured" in identified_item_name:
                     return jsonify({"error": "Image identification service error."}), 500
                return jsonify({"error": identified_item_name}), 500 # Or 422 if it's a processing error like bad MIME

            logger.info(f"Identified item: '{identified_item_name}' from image '{original_filename}'.")
            return jsonify({"identified_item": identified_item_name}), 200
            
        except Exception as e:
            logger.error(f"Unexpected error during image identification: {e}", exc_info=True)
            return jsonify({"error": "An unexpected error occurred during image processing."}), 500
    
    return jsonify({"error": "Image processing failed for an unknown reason."}), 500


# === Vertex AI Search for commerce API Endpoint ===
@app.route('/api/retail/search-products', methods=['POST'])
def retail_search_products():
    """
    Queries Google Cloud Retail API for product recommendations.
    Expects JSON: {"query": "search_term", "visitor_id": "id"}
    Output matches ADK tool: {'recommendations': [{'product_id': ..., 'name': ..., 'description': ...}, ...]}
    """
    try:
        credentials, project_id_adc = default_auth_credentials() # project_id_adc to avoid conflict with GCP_PROJECT_ID
        logger.info(f"ADC using credentials: {credentials}")
        if hasattr(credentials, 'service_account_email'):
            logger.info(f"ADC Service Account Email: {credentials.service_account_email}")
        else:
            logger.info(f"ADC is likely using user credentials (gcloud auth application-default login). Active project for ADC: {project_id_adc}")
    except Exception as e:
        logger.error(f"Error getting ADC: {e}")

    # Simplified check: if project ID is still the placeholder, assume not configured.
    # This allows using "default_catalog" and "default_search" if they are actual live IDs.
    if GCP_PROJECT_ID == "your-gcp-project-id":
        logger.error("Retail API not configured. GCP_PROJECT_ID is still set to placeholder 'your-gcp-project-id' in app.py.")
        return jsonify({
            "error": "Retail API not configured on the server (Project ID not set).",
            "recommendations": []
        }), 503 # Service Unavailable

    data = request.get_json()
    if not data or 'query' not in data or 'visitor_id' not in data:
        return jsonify({"error": "Invalid JSON payload. 'query' and 'visitor_id' are required."}), 400

    search_query = data['query']
    visitor_id = data['visitor_id']
    
    # Construct the placement string for the Retail API
    placement = (
        f"projects/{GCP_PROJECT_ID}/locations/{RETAIL_API_LOCATION}/" 
        f"catalogs/{RETAIL_CATALOG_ID}/servingConfigs/{RETAIL_SERVING_CONFIG_ID}"
    )

    #client_options = ClientOptions(api_endpoint=f"{RETAIL_API_LOCATION}-retail.googleapis.com")
    search_client = retail_v2.SearchServiceClient()
    
    # Construct the full path for the default branch
    # default_branch_name = search_client.branch_path(
    #     GCP_PROJECT_ID, RETAIL_API_LOCATION, RETAIL_CATALOG_ID, "0"  # "0" is the default branch ID
    # )

    search_request = retail_v2.SearchRequest(
        placement=placement,
        # branch=default_branch_name, # Explicitly set the branch - REMOVING TO TEST
        query=search_query,
        visitor_id=visitor_id,
        page_size=10 # Or configurable
    )
    
    recommendations = []
    try:
        logger.info(f"Sending search request to Retail API: {search_request}")
        search_response = search_client.search(request=search_request)
        logger.info(f"Received search response from Retail API: {search_response}")
        logger.info(f"Received search response from Retail API. Results count: {len(search_response.results)}")
        
        for result in search_response.results:
            product = result.product
            product_id_from_api = result.id # product.id is the fully qualified name
            
            # Find the product name from SAMPLE_PRODUCTS using product_id_from_api
            product_name_from_sample = "Unknown Product" # Default if not found
            # The following import and list comprehension should ideally be outside the loop or optimized
            # For simplicity in this diff, it's here. Consider moving SAMPLE_PRODUCTS to a more accessible place if not already.
            from sample_data_importer import SAMPLE_PRODUCTS
            found_product_sample = next((p for p in SAMPLE_PRODUCTS if p["id"] == product_id_from_api), None)
            if found_product_sample:
                product_name_from_sample = found_product_sample["name"]

            recommendations.append({
                "product_id": product_id_from_api, # Use the ID directly from the result
                "name": product_name_from_sample, # Use the name looked up from sample data
                "description": product.description if hasattr(product, 'description') and product.description else "No description available.",
            })
            
    except GoogleAPICallError as e:
        logger.error(f"Retail API call failed: {e}")
        return jsonify({"error": "Failed to query Retail API.", "details": str(e)}), 500
    except Exception as e:
        logger.error(f"An unexpected error occurred during Retail API search: {e}")
        return jsonify({"error": "An unexpected error occurred during search."}), 500

    return jsonify({"recommendations": recommendations})

# === Product Detail Page Route ===
@app.route('/products/<string:product_id>')
def product_detail_page(product_id):
    """Serves the product detail page for a given product ID."""
    logger.info(f"Received GET request for product detail page /products/{product_id}.")
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM products WHERE id = ?", (product_id,))
    product_row = cursor.fetchone()

    if product_row:
        product_data = dict(product_row)
        # Deserialize JSON strings back into lists for relevant fields
        for field in ['flower_color', 'flowering_season', 'pollinator_types', 
                      'landscape_use', 'companion_plants_ids', 'recommended_soil_ids', 
                      'recommended_fertilizer_ids', 'harvest_time', 'attributes']: # Added 'attributes'
            if product_data.get(field) and isinstance(product_data[field], str):
                try:
                    product_data[field] = json.loads(product_data[field])
                except json.JSONDecodeError:
                    logger.warning(f"Could not decode JSON for field {field} in product {product_data['id']}")
                    # Decide on default: empty list or keep as is, or None
                    product_data[field] = product_data[field] if isinstance(product_data[field], dict) else [] 
            elif product_data.get(field) is None and field != 'attributes': # attributes can be None
                 product_data[field] = []
        
        # Ensure attributes is a dict if it's None or empty list after potential deserialization
        if not isinstance(product_data.get('attributes'), dict):
            product_data['attributes'] = {}

        logger.info(f"Rendering product_detail.html for product {product_id}.")
        return render_template('product_detail.html', product=product_data)
    else:
        logger.warning(f"Product {product_id} not found. Returning 404 page.")
        # Assuming a 404.html template exists or will be created.
        # If not, the default Flask 404 handler will be used, or @app.errorhandler(404) if defined for HTML.
        # For now, let's use the existing JSON 404 handler via abort,
        # or create a specific 404.html if preferred by user later.
        # For a user-facing page, a rendered 404 page is better.
        # We'll use render_template for a user-friendly 404 page.
        return render_template('404.html', error_message=f"Product with ID {product_id} not found."), 404

@app.route('/')
def index():
    """Serves the main HTML page for the frontend."""
    return render_template('index.html')

@app.route('/agent-widget')
def agent_widget():
    """Serves the agent widget HTML page."""
    return render_template('agent_widget.html')

# --- Main Execution ---
if __name__ == '__main__':
    # Make sure to create static and templates folders in the same directory as app.py
    # if you plan to serve frontend from here.
    # Example:
    # cymbal_home_garden_backend/
    # ├── static/
    # │   ├── style.css
    # │   └── script.js
    # │   └── images/ (optional for product images)
    # ├── templates/
    # │   └── index.html
    # ├── app.py
    # ... (other backend files)
    
    app.run(debug=True, host='127.0.0.1', port=5000)
