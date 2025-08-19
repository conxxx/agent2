import unittest
import json
import os
from app import app # Your Flask app instance
from database_setup import create_tables, DATABASE_NAME
from sample_data_importer import insert_sample_data, SAMPLE_PRODUCTS

class TestAPI(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """Set up for all tests in this class."""
        # Configure the app for testing
        app.config['TESTING'] = True
        app.config['DATABASE'] = 'test_' + DATABASE_NAME # Use a separate test database
        cls.client = app.test_client()

        # Ensure a clean test database for each full test run
        if os.path.exists(app.config['DATABASE']):
            os.remove(app.config['DATABASE'])
        
        # Use the original DATABASE_NAME for setup scripts, then rename if needed,
        # or modify scripts to accept a db name. For now, let's assume scripts use their internal const.
        # This means we might be testing against the main db if not careful.
        # A better approach is to parameterize db name in db scripts.
        # For simplicity here, we'll ensure it's clean before each class run.
        create_tables() # This will use 'ecommerce.db' by default
        insert_sample_data() # This will also use 'ecommerce.db'

    @classmethod
    def tearDownClass(cls):
        """Tear down after all tests in this class."""
        # Clean up the test database
        # if os.path.exists(app.config['DATABASE']):
        #     os.remove(app.config['DATABASE'])
        # For now, since we are using the main DB, we might not want to remove it after every test class.
        pass

    def setUp(self):
        """Set up for each test method."""
        # If we need to re-populate data before *each* test, do it here.
        # For now, setUpClass handles it once.
        # To ensure test isolation if tests modify data, it's better to do it here.
        # Re-creating and re-populating for every test can be slow.
        # Let's assume tests are read-only for products for now.
        pass

    # --- Tests for GET /api/products ---
    def test_get_all_products_success(self):
        """Test successful retrieval of all products."""
        response = self.client.get('/api/products')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, 'application/json')
        
        data = json.loads(response.data.decode('utf-8'))
        self.assertIsInstance(data, list)
        self.assertEqual(len(data), len(SAMPLE_PRODUCTS)) # Check if all sample products are returned

        # Check structure of the first product (if data exists)
        if data:
            first_product = data[0]
            self.assertIn('id', first_product)
            self.assertIn('name', first_product)
            self.assertIn('price', first_product)
            self.assertIn('category', first_product)
            # Check for a field that should be a deserialized list
            # Example: Lavender (first in SAMPLE_PRODUCTS) has 'flower_color'
            if first_product['id'] == SAMPLE_PRODUCTS[0]['id']:
                 self.assertIn('flower_color', first_product)
                 self.assertIsInstance(first_product['flower_color'], list)
                 self.assertEqual(first_product['flower_color'], json.loads(SAMPLE_PRODUCTS[0]['flower_color']))

    def test_get_products_filter_by_name_exact(self):
        """Test filtering products by an exact name."""
        # Assuming "English Lavender 'Munstead'" is a unique name from sample data
        lavender_name = "English Lavender 'Munstead'"
        response = self.client.get(f'/api/products?name={lavender_name}')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data.decode('utf-8'))
        self.assertIsInstance(data, list)
        self.assertTrue(len(data) >= 1)
        if len(data) >=1:
            self.assertEqual(data[0]['name'], lavender_name)

    def test_get_products_filter_by_name_partial(self):
        """Test filtering products by a partial name."""
        response = self.client.get('/api/products?name=Lavender')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data.decode('utf-8'))
        self.assertIsInstance(data, list)
        self.assertTrue(len(data) >= 1) # Expect at least one lavender product
        for product in data:
            self.assertIn('Lavender', product['name'])

    def test_get_products_filter_by_category(self):
        """Test filtering products by category."""
        response = self.client.get('/api/products?category=Plants')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data.decode('utf-8'))
        self.assertIsInstance(data, list)
        self.assertTrue(len(data) > 0)
        for product in data:
            self.assertEqual(product['category'], 'Plants')
            
    def test_get_products_filter_by_category_soil(self):
        """Test filtering products by 'Soil' category."""
        response = self.client.get('/api/products?category=Soil')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data.decode('utf-8'))
        self.assertIsInstance(data, list)
        self.assertTrue(len(data) > 0)
        for product in data:
            self.assertEqual(product['category'], 'Soil')

    def test_get_products_filter_by_name_and_category(self):
        """Test filtering products by both name and category."""
        response = self.client.get('/api/products?name=Premium&category=Soil')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data.decode('utf-8'))
        self.assertIsInstance(data, list)
        self.assertTrue(len(data) > 0)
        for product in data:
            self.assertIn('Premium', product['name'])
            self.assertEqual(product['category'], 'Soil')

    def test_get_products_filter_no_results(self):
        """Test filtering that should yield no results."""
        response = self.client.get('/api/products?name=NonExistentProductName123')
        self.assertEqual(response.status_code, 200) # API returns 200 with empty list
        data = json.loads(response.data.decode('utf-8'))
        self.assertIsInstance(data, list)
        self.assertEqual(len(data), 0)

    def test_get_products_filter_by_plant_type(self):
        """Test filtering products by plant_type."""
        # Example: Find all "Perennial Shrub"
        response = self.client.get('/api/products?plant_type=Perennial%20Shrub') # URL encode space
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data.decode('utf-8'))
        self.assertIsInstance(data, list)
        self.assertTrue(len(data) > 0, "Expected at least one 'Perennial Shrub'")
        for product in data:
            self.assertIn('Perennial Shrub', product.get('plant_type', ''))

        # Example: Find all "Herb" (should match "Perennial Herb/Shrub" and "Annual Herb")
        response_herb = self.client.get('/api/products?plant_type=Herb')
        self.assertEqual(response_herb.status_code, 200)
        data_herb = json.loads(response_herb.data.decode('utf-8'))
        self.assertIsInstance(data_herb, list)
        self.assertTrue(len(data_herb) > 0, "Expected at least one product with 'Herb' in plant_type")
        for product in data_herb:
            self.assertIn('Herb', product.get('plant_type', ''))
            
    # --- Tests for GET /api/products/<product_id> ---
    def test_get_product_detail_success(self):
        """Test successful retrieval of a single product by ID."""
        # Use the ID of the first sample product
        product_id_to_test = SAMPLE_PRODUCTS[0]['id']
        expected_product_data = SAMPLE_PRODUCTS[0]

        response = self.client.get(f'/api/products/{product_id_to_test}')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, 'application/json')

        data = json.loads(response.data.decode('utf-8'))
        self.assertIsInstance(data, dict)
        
        # Verify all fields from sample data, accounting for JSON deserialization
        for key, expected_value in expected_product_data.items():
            self.assertIn(key, data)
            if key in ['flower_color', 'flowering_season', 'landscape_use', 'companion_plants_ids', 'recommended_soil_ids', 'recommended_fertilizer_ids', 'pollinator_types', 'harvest_time']: # Fields stored as JSON strings
                if expected_value: # If there's an expected value
                     self.assertEqual(data[key], json.loads(expected_value))
                else: # If expected value is None or empty string (which becomes empty list)
                    self.assertEqual(data[key], []) # app.py defaults None/empty JSON to []
            elif isinstance(expected_value, bool): # Boolean fields
                self.assertEqual(data[key], expected_value)
            else:
                self.assertEqual(data[key], expected_value)
        
        # Explicitly check a deserialized list
        self.assertIsInstance(data['flower_color'], list)
        self.assertEqual(data['flower_color'], json.loads(expected_product_data['flower_color']))

    def test_get_product_detail_all_fields_present(self):
        """Test that all expected fields are present for a detailed product."""
        # Test with a more complex product, e.g., SKU_TOMATO
        tomato_sku = "SKU_PLANT_TOMATO_CELEBRITY_001"
        tomato_data_from_sample = next(p for p in SAMPLE_PRODUCTS if p["id"] == tomato_sku)

        response = self.client.get(f'/api/products/{tomato_sku}')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data.decode('utf-8'))

        for key in tomato_data_from_sample.keys():
            self.assertIn(key, data, f"Key '{key}' missing in response for product {tomato_sku}")
            
            # Check deserialization for list-like fields
            if key in ['flower_color', 'flowering_season', 'harvest_time', 'landscape_use', 'companion_plants_ids', 'recommended_soil_ids', 'recommended_fertilizer_ids']:
                if tomato_data_from_sample[key]:
                    self.assertEqual(data[key], json.loads(tomato_data_from_sample[key]))
                else:
                    self.assertEqual(data[key], [])


    def test_get_product_detail_not_found(self):
        """Test retrieval of a non-existent product ID."""
        non_existent_id = "SKU_DOES_NOT_EXIST_999"
        response = self.client.get(f'/api/products/{non_existent_id}')
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.content_type, 'application/json')
        data = json.loads(response.data.decode('utf-8'))
        self.assertIn('error', data)
        self.assertEqual(data['error'], 'Product not found')

    # --- Tests for GET /api/products/availability/<product_id>/<store_id> ---
    def test_get_product_availability_in_stock(self):
        """Test availability for an in-stock product."""
        product_id_to_test = SAMPLE_PRODUCTS[0]['id'] # Lavender, stock 75
        store_id = "store123" # Store ID is illustrative for this endpoint

        response = self.client.get(f'/api/products/availability/{product_id_to_test}/{store_id}')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, 'application/json')

        data = json.loads(response.data.decode('utf-8'))
        self.assertTrue(data['available'])
        self.assertEqual(data['quantity'], SAMPLE_PRODUCTS[0]['stock'])
        self.assertIn(store_id, data['store']) # Check if store_id is mentioned in the response string

    def test_get_product_availability_non_existent_product(self):
        """Test availability for a non-existent product."""
        non_existent_id = "SKU_DOES_NOT_EXIST_999"
        store_id = "store123"
        response = self.client.get(f'/api/products/availability/{non_existent_id}/{store_id}')
        self.assertEqual(response.status_code, 404)
        data = json.loads(response.data.decode('utf-8'))
        self.assertIn('error', data)
        self.assertEqual(data['error'], 'Product not found for availability check')

    # Note: To test an "out of stock" scenario properly, we'd need a product with stock 0
    # or modify a product's stock during testing, which requires more setup/teardown for isolation.
    # For now, we assume sample products have stock > 0.
    # If we had a product with stock 0:
    # def test_get_product_availability_out_of_stock(self):
    #     product_id_out_of_stock = "SKU_OUT_OF_STOCK_001" # Assume this exists with stock 0
    #     store_id = "store456"
    #     response = self.client.get(f'/api/products/availability/{product_id_out_of_stock}/{store_id}')
    #     self.assertEqual(response.status_code, 200)
    #     data = json.loads(response.data.decode('utf-8'))
    #     self.assertFalse(data['available'])
    #     self.assertEqual(data['quantity'], 0)

    # --- Tests for GET /api/cart/<customer_id> ---
    def test_get_empty_cart(self):
        """Test retrieving an empty cart for a new customer."""
        customer_id = "new_customer_123"
        response = self.client.get(f'/api/cart/{customer_id}')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data.decode('utf-8'))
        self.assertIn('items', data)
        self.assertIsInstance(data['items'], list)
        self.assertEqual(len(data['items']), 0)
        self.assertIn('subtotal', data)
        self.assertEqual(data['subtotal'], 0.0)

    def test_add_item_and_get_cart(self):
        """Test adding an item to the cart and then retrieving the cart."""
        customer_id = "customer_with_item_456"
        product_to_add = SAMPLE_PRODUCTS[0] # Lavender
        quantity_to_add = 2

        # First, add an item to the cart using the modify endpoint
        # (We'll test modify_cart more thoroughly later, but need it here for setup)
        add_payload = {
            "items_to_add": [{"product_id": product_to_add['id'], "quantity": quantity_to_add}]
        }
        response_add = self.client.post(f'/api/cart/modify/{customer_id}', json=add_payload)
        self.assertEqual(response_add.status_code, 200)
        add_data = json.loads(response_add.data.decode('utf-8'))
        self.assertTrue(add_data['items_added'])

        # Now, retrieve the cart
        response_get = self.client.get(f'/api/cart/{customer_id}')
        self.assertEqual(response_get.status_code, 200)
        cart_data = json.loads(response_get.data.decode('utf-8'))
        
        self.assertIsInstance(cart_data['items'], list)
        self.assertEqual(len(cart_data['items']), 1)
        
        cart_item = cart_data['items'][0]
        self.assertEqual(cart_item['product_id'], product_to_add['id'])
        self.assertEqual(cart_item['name'], product_to_add['name'])
        self.assertEqual(cart_item['quantity'], quantity_to_add)
        self.assertEqual(cart_item['price_per_unit'], product_to_add['price'])
        
        expected_subtotal = round(product_to_add['price'] * quantity_to_add, 2)
        self.assertEqual(cart_data['subtotal'], expected_subtotal)

        # Clean up: remove item from cart for this customer to not affect other tests
        # This highlights the need for better test isolation or a dedicated test DB that's reset.
        # For now, we'll manually clear.
        remove_payload = {
            "items_to_remove": [{"product_id": product_to_add['id'], "quantity": quantity_to_add}]
        }
        response_remove = self.client.post(f'/api/cart/modify/{customer_id}', json=remove_payload)
        self.assertEqual(response_remove.status_code, 200) # Ensure cleanup was successful

    # --- Tests for POST /api/cart/modify/<customer_id> ---
    def test_cart_modify_add_new_item_to_empty_cart(self):
        """Test adding a new item to an empty cart."""
        customer_id = "cart_modify_customer_001"
        product = SAMPLE_PRODUCTS[1] # Tomato
        quantity = 1
        
        payload = {"items_to_add": [{"product_id": product['id'], "quantity": quantity}]}
        response = self.client.post(f'/api/cart/modify/{customer_id}', json=payload)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data.decode('utf-8'))
        self.assertTrue(data['items_added'])
        self.assertFalse(data['items_removed'])

        # Verify cart content
        cart_response = self.client.get(f'/api/cart/{customer_id}')
        cart_data = json.loads(cart_response.data.decode('utf-8'))
        self.assertEqual(len(cart_data['items']), 1)
        self.assertEqual(cart_data['items'][0]['product_id'], product['id'])
        self.assertEqual(cart_data['items'][0]['quantity'], quantity)
        
        # Cleanup
        self.client.post(f'/api/cart/modify/{customer_id}', json={"items_to_remove": [{"product_id": product['id'], "quantity": quantity}]})

    def test_cart_modify_increase_quantity(self):
        """Test increasing quantity of an existing item in cart."""
        customer_id = "cart_modify_customer_002"
        product = SAMPLE_PRODUCTS[2] # Monstera
        
        # Add initial quantity
        self.client.post(f'/api/cart/modify/{customer_id}', json={"items_to_add": [{"product_id": product['id'], "quantity": 1}]})
        
        # Increase quantity
        payload = {"items_to_add": [{"product_id": product['id'], "quantity": 2}]}
        response = self.client.post(f'/api/cart/modify/{customer_id}', json=payload)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data.decode('utf-8'))
        self.assertTrue(data['items_added'])

        cart_response = self.client.get(f'/api/cart/{customer_id}')
        cart_data = json.loads(cart_response.data.decode('utf-8'))
        self.assertEqual(len(cart_data['items']), 1)
        self.assertEqual(cart_data['items'][0]['quantity'], 3) # 1 + 2
        
        # Cleanup
        self.client.post(f'/api/cart/modify/{customer_id}', json={"items_to_remove": [{"product_id": product['id'], "quantity": 3}]})

    def test_cart_modify_remove_item_completely(self):
        """Test removing an item completely from the cart."""
        customer_id = "cart_modify_customer_003"
        product = SAMPLE_PRODUCTS[3] # Rosemary
        
        # Add item
        self.client.post(f'/api/cart/modify/{customer_id}', json={"items_to_add": [{"product_id": product['id'], "quantity": 2}]})
        
        # Remove item
        payload = {"items_to_remove": [{"product_id": product['id'], "quantity": 2}]}
        response = self.client.post(f'/api/cart/modify/{customer_id}', json=payload)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data.decode('utf-8'))
        self.assertTrue(data['items_removed'])

        cart_response = self.client.get(f'/api/cart/{customer_id}')
        cart_data = json.loads(cart_response.data.decode('utf-8'))
        self.assertEqual(len(cart_data['items']), 0)

    def test_cart_modify_decrease_quantity(self):
        """Test decreasing quantity of an existing item in cart."""
        customer_id = "cart_modify_customer_004"
        product = SAMPLE_PRODUCTS[4] # Basil
        
        # Add initial quantity
        self.client.post(f'/api/cart/modify/{customer_id}', json={"items_to_add": [{"product_id": product['id'], "quantity": 5}]})
        
        # Decrease quantity
        payload = {"items_to_remove": [{"product_id": product['id'], "quantity": 2}]}
        response = self.client.post(f'/api/cart/modify/{customer_id}', json=payload)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data.decode('utf-8'))
        self.assertTrue(data['items_removed'])

        cart_response = self.client.get(f'/api/cart/{customer_id}')
        cart_data = json.loads(cart_response.data.decode('utf-8'))
        self.assertEqual(len(cart_data['items']), 1)
        self.assertEqual(cart_data['items'][0]['quantity'], 3) # 5 - 2
        
        # Cleanup
        self.client.post(f'/api/cart/modify/{customer_id}', json={"items_to_remove": [{"product_id": product['id'], "quantity": 3}]})

    def test_cart_modify_add_item_insufficient_stock(self):
        """Test adding an item when stock is insufficient."""
        customer_id = "cart_modify_customer_005"
        product = SAMPLE_PRODUCTS[0] # Lavender, stock 75
        quantity_too_high = product['stock'] + 1
        
        payload = {"items_to_add": [{"product_id": product['id'], "quantity": quantity_too_high}]}
        response = self.client.post(f'/api/cart/modify/{customer_id}', json=payload)
        self.assertEqual(response.status_code, 200) # Endpoint returns 200 but indicates no change
        data = json.loads(response.data.decode('utf-8'))
        self.assertFalse(data['items_added']) # Should not be added
        self.assertIn("No changes made", data['message']) # Or similar message indicating issue

        cart_response = self.client.get(f'/api/cart/{customer_id}')
        cart_data = json.loads(cart_response.data.decode('utf-8'))
        self.assertEqual(len(cart_data['items']), 0) # Cart should remain empty

    def test_cart_modify_invalid_product_id(self):
        """Test modifying cart with a non-existent product ID."""
        customer_id = "cart_modify_customer_006"
        payload = {"items_to_add": [{"product_id": "INVALID_SKU", "quantity": 1}]}
        response = self.client.post(f'/api/cart/modify/{customer_id}', json=payload)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data.decode('utf-8'))
        self.assertFalse(data['items_added'])
        
        cart_response = self.client.get(f'/api/cart/{customer_id}')
        cart_data = json.loads(cart_response.data.decode('utf-8'))
        self.assertEqual(len(cart_data['items']), 0)

    def test_cart_modify_add_and_remove_simultaneously(self):
        """Test adding one item and removing another in the same request."""
        customer_id = "cart_modify_customer_007"
        product_to_add = SAMPLE_PRODUCTS[0] # Lavender
        product_to_remove_setup = SAMPLE_PRODUCTS[1] # Tomato
        
        # Setup: add tomato to cart first
        self.client.post(f'/api/cart/modify/{customer_id}', json={"items_to_add": [{"product_id": product_to_remove_setup['id'], "quantity": 1}]})

        payload = {
            "items_to_add": [{"product_id": product_to_add['id'], "quantity": 1}],
            "items_to_remove": [{"product_id": product_to_remove_setup['id'], "quantity": 1}]
        }
        response = self.client.post(f'/api/cart/modify/{customer_id}', json=payload)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data.decode('utf-8'))
        self.assertTrue(data['items_added'])
        self.assertTrue(data['items_removed'])

        cart_response = self.client.get(f'/api/cart/{customer_id}')
        cart_data = json.loads(cart_response.data.decode('utf-8'))
        self.assertEqual(len(cart_data['items']), 1)
        self.assertEqual(cart_data['items'][0]['product_id'], product_to_add['id']) # Lavender should be there
        
        # Cleanup
        self.client.post(f'/api/cart/modify/{customer_id}', json={"items_to_remove": [{"product_id": product_to_add['id'], "quantity": 1}]})

    def test_cart_modify_malformed_item_data(self):
        """Test modifying cart with malformed item data (e.g., missing product_id or invalid quantity type)."""
        customer_id = "cart_modify_customer_008"
        product_valid = SAMPLE_PRODUCTS[0]

        # Payload with one valid item and one malformed item (missing product_id)
        payload1 = {
            "items_to_add": [
                {"product_id": product_valid['id'], "quantity": 1},
                {"quantity": 1} # Missing product_id
            ]
        }
        response1 = self.client.post(f'/api/cart/modify/{customer_id}', json=payload1)
        self.assertEqual(response1.status_code, 200)
        data1 = json.loads(response1.data.decode('utf-8'))
        self.assertTrue(data1['items_added'], "Valid item should have been added")
        # Check that only the valid item was added
        cart_response1 = self.client.get(f'/api/cart/{customer_id}')
        cart_data1 = json.loads(cart_response1.data.decode('utf-8'))
        self.assertEqual(len(cart_data1['items']), 1, "Only the valid item should be in cart")
        self.assertEqual(cart_data1['items'][0]['product_id'], product_valid['id'])
        
        # Cleanup
        self.client.post(f'/api/cart/modify/{customer_id}', json={"items_to_remove": [{"product_id": product_valid['id'], "quantity": 1}]})

        # Payload with invalid quantity type
        payload2 = {
            "items_to_add": [
                {"product_id": product_valid['id'], "quantity": "should_be_int"}
            ]
        }
        response2 = self.client.post(f'/api/cart/modify/{customer_id}', json=payload2)
        self.assertEqual(response2.status_code, 200)
        data2 = json.loads(response2.data.decode('utf-8'))
        self.assertFalse(data2['items_added'], "Item with invalid quantity type should not be added")
        cart_response2 = self.client.get(f'/api/cart/{customer_id}')
        cart_data2 = json.loads(cart_response2.data.decode('utf-8'))
        self.assertEqual(len(cart_data2['items']), 0, "Cart should be empty after trying to add item with invalid quantity type")

    # --- Tests for POST /api/cart/<customer_id>/item ---
    def test_cart_item_endpoint_add_new_to_empty_cart(self):
        """Test POST /api/cart/<customer_id>/item: add new item to empty cart."""
        customer_id = "cart_item_customer_001"
        product = SAMPLE_PRODUCTS[0] # Lavender
        payload = {"product_id": product['id'], "quantity": 1}
        
        response = self.client.post(f'/api/cart/{customer_id}/item', json=payload)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data.decode('utf-8'))
        self.assertEqual(data['status'], 'success')
        self.assertIn(f"Product {product['id']} added to cart", data['message'])

        cart_response = self.client.get(f'/api/cart/{customer_id}')
        cart_data = json.loads(cart_response.data.decode('utf-8'))
        self.assertEqual(len(cart_data['items']), 1)
        self.assertEqual(cart_data['items'][0]['product_id'], product['id'])
        self.assertEqual(cart_data['items'][0]['quantity'], 1)
        # Cleanup
        self.client.delete(f'/api/cart/{customer_id}/item/{product["id"]}')

    def test_cart_item_endpoint_add_different_item_to_existing_cart(self):
        """Test POST /api/cart/<customer_id>/item: add a different new item to an existing cart."""
        customer_id = "cart_item_customer_002"
        product1 = SAMPLE_PRODUCTS[0] # Lavender
        product2 = SAMPLE_PRODUCTS[1] # Tomato

        # Add first item
        self.client.post(f'/api/cart/{customer_id}/item', json={"product_id": product1['id'], "quantity": 1})
        
        # Add second, different item
        payload = {"product_id": product2['id'], "quantity": 2}
        response = self.client.post(f'/api/cart/{customer_id}/item', json=payload)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data.decode('utf-8'))
        self.assertEqual(data['status'], 'success')

        cart_response = self.client.get(f'/api/cart/{customer_id}')
        cart_data = json.loads(cart_response.data.decode('utf-8'))
        self.assertEqual(len(cart_data['items']), 2)
        # Cleanup
        self.client.delete(f'/api/cart/{customer_id}/clear')

    def test_cart_item_endpoint_increment_quantity(self):
        """Test POST /api/cart/<customer_id>/item: increment quantity of existing item."""
        customer_id = "cart_item_customer_003"
        product = SAMPLE_PRODUCTS[2] # Monstera
        
        # Add initial quantity
        self.client.post(f'/api/cart/{customer_id}/item', json={"product_id": product['id'], "quantity": 1})
        
        # Increment quantity
        payload = {"product_id": product['id'], "quantity": 2} # This means "add 2 more"
        response = self.client.post(f'/api/cart/{customer_id}/item', json=payload)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data.decode('utf-8'))
        self.assertEqual(data['status'], 'success')
        self.assertIn(f"Quantity for product {product['id']} updated to 3", data['message'])


        cart_response = self.client.get(f'/api/cart/{customer_id}')
        cart_data = json.loads(cart_response.data.decode('utf-8'))
        self.assertEqual(len(cart_data['items']), 1)
        self.assertEqual(cart_data['items'][0]['quantity'], 3) # 1 initial + 2 added
        # Cleanup
        self.client.delete(f'/api/cart/{customer_id}/clear')

    def test_cart_item_endpoint_add_insufficient_stock(self):
        """Test POST /api/cart/<customer_id>/item: add item with insufficient stock."""
        customer_id = "cart_item_customer_004"
        product = SAMPLE_PRODUCTS[0] # Lavender, stock 75
        quantity_too_high = product['stock'] + 1
        
        payload = {"product_id": product['id'], "quantity": quantity_too_high}
        response = self.client.post(f'/api/cart/{customer_id}/item', json=payload)
        self.assertEqual(response.status_code, 400) # Expecting 400 for insufficient stock
        data = json.loads(response.data.decode('utf-8'))
        self.assertIn('error', data)
        self.assertIn("Not enough stock", data['error'])

        cart_response = self.client.get(f'/api/cart/{customer_id}')
        cart_data = json.loads(cart_response.data.decode('utf-8'))
        self.assertEqual(len(cart_data['items']), 0) # Cart should remain empty

    def test_cart_item_endpoint_add_invalid_product_id(self):
        """Test POST /api/cart/<customer_id>/item: add item with invalid product ID."""
        customer_id = "cart_item_customer_005"
        payload = {"product_id": "INVALID_SKU_XYZ", "quantity": 1}
        response = self.client.post(f'/api/cart/{customer_id}/item', json=payload)
        self.assertEqual(response.status_code, 404) # Expecting 404 for product not found
        data = json.loads(response.data.decode('utf-8'))
        self.assertIn('error', data)
        self.assertIn("Product INVALID_SKU_XYZ not found", data['error'])

    def test_cart_item_endpoint_add_zero_quantity_for_new_item(self):
        """Test POST /api/cart/<customer_id>/item: add new item with quantity 0."""
        customer_id = "cart_item_customer_006"
        product = SAMPLE_PRODUCTS[0]
        payload = {"product_id": product['id'], "quantity": 0}
        response = self.client.post(f'/api/cart/{customer_id}/item', json=payload)
        self.assertEqual(response.status_code, 200) # API handles this as "no action"
        data = json.loads(response.data.decode('utf-8'))
        self.assertEqual(data['status'], 'no_action')

        cart_response = self.client.get(f'/api/cart/{customer_id}')
        cart_data = json.loads(cart_response.data.decode('utf-8'))
        self.assertEqual(len(cart_data['items']), 0)

    def test_cart_item_endpoint_add_zero_quantity_for_existing_item(self):
        """Test POST /api/cart/<customer_id>/item: add quantity 0 for existing item (should remove)."""
        customer_id = "cart_item_customer_007"
        product = SAMPLE_PRODUCTS[1] # Tomato
        # Add item first
        self.client.post(f'/api/cart/{customer_id}/item', json={"product_id": product['id'], "quantity": 2})

        payload = {"product_id": product['id'], "quantity": 0}
        response = self.client.post(f'/api/cart/{customer_id}/item', json=payload)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data.decode('utf-8'))
        self.assertEqual(data['status'], 'success')
        self.assertIn(f"Product {product['id']} removed from cart due to quantity <= 0", data['message'])
        
        cart_response = self.client.get(f'/api/cart/{customer_id}')
        cart_data = json.loads(cart_response.data.decode('utf-8'))
        self.assertEqual(len(cart_data['items']), 0) # Item should be removed

    def test_cart_item_endpoint_add_negative_quantity_for_existing_item(self):
        """Test POST /api/cart/<customer_id>/item: add negative quantity for existing item (should remove)."""
        customer_id = "cart_item_customer_008"
        product = SAMPLE_PRODUCTS[2] # Monstera
        # Add item first
        self.client.post(f'/api/cart/{customer_id}/item', json={"product_id": product['id'], "quantity": 3})

        payload = {"product_id": product['id'], "quantity": -1}
        response = self.client.post(f'/api/cart/{customer_id}/item', json=payload)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data.decode('utf-8'))
        self.assertEqual(data['status'], 'success')
        self.assertIn(f"Product {product['id']} removed from cart due to quantity <= 0", data['message'])

        cart_response = self.client.get(f'/api/cart/{customer_id}')
        cart_data = json.loads(cart_response.data.decode('utf-8'))
        self.assertEqual(len(cart_data['items']), 0) # Item should be removed

    def test_cart_item_endpoint_missing_product_id(self):
        """Test POST /api/cart/<customer_id>/item: missing product_id in payload."""
        customer_id = "cart_item_customer_009"
        payload = {"quantity": 1}
        response = self.client.post(f'/api/cart/{customer_id}/item', json=payload)
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data.decode('utf-8'))
        self.assertIn("'product_id' and 'quantity' are required", data['error'])

    def test_cart_item_endpoint_missing_quantity(self):
        """Test POST /api/cart/<customer_id>/item: missing quantity in payload."""
        customer_id = "cart_item_customer_010"
        product = SAMPLE_PRODUCTS[0]
        payload = {"product_id": product['id']}
        response = self.client.post(f'/api/cart/{customer_id}/item', json=payload)
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data.decode('utf-8'))
        self.assertIn("'product_id' and 'quantity' are required", data['error'])

    def test_cart_item_endpoint_invalid_quantity_type(self):
        """Test POST /api/cart/<customer_id>/item: quantity is not an integer."""
        customer_id = "cart_item_customer_011"
        product = SAMPLE_PRODUCTS[0]
        payload = {"product_id": product['id'], "quantity": "not-an-int"}
        response = self.client.post(f'/api/cart/{customer_id}/item', json=payload)
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data.decode('utf-8'))
        self.assertIn("'quantity' must be an integer", data['error'])

    # --- Tests for DELETE /api/cart/<customer_id>/item/<product_id> ---
    def test_cart_item_delete_endpoint_existing_item(self):
        """Test DELETE /api/cart/<customer_id>/item/<product_id>: remove existing item."""
        customer_id = "cart_item_delete_customer_001"
        product = SAMPLE_PRODUCTS[0] # Lavender
        # Add item first
        self.client.post(f'/api/cart/{customer_id}/item', json={"product_id": product['id'], "quantity": 1})

        response = self.client.delete(f'/api/cart/{customer_id}/item/{product["id"]}')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data.decode('utf-8'))
        self.assertEqual(data['status'], 'success')
        self.assertIn(f"Product {product['id']} removed from cart", data['message'])

        cart_response = self.client.get(f'/api/cart/{customer_id}')
        cart_data = json.loads(cart_response.data.decode('utf-8'))
        self.assertEqual(len(cart_data['items']), 0)

    def test_cart_item_delete_endpoint_item_not_in_cart(self):
        """Test DELETE /api/cart/<customer_id>/item/<product_id>: item not in cart."""
        customer_id = "cart_item_delete_customer_002"
        product = SAMPLE_PRODUCTS[1] # Tomato (assuming it's not in this customer's cart)
        
        response = self.client.delete(f'/api/cart/{customer_id}/item/{product["id"]}')
        self.assertEqual(response.status_code, 404) # Expect 404 if item not found in cart
        data = json.loads(response.data.decode('utf-8'))
        self.assertEqual(data['status'], 'not_found')
        self.assertIn(f"Product {product['id']} not found in cart", data['message'])

    def test_cart_item_delete_endpoint_invalid_product_id(self):
        """Test DELETE /api/cart/<customer_id>/item/<product_id>: invalid product ID."""
        customer_id = "cart_item_delete_customer_003"
        invalid_product_id = "INVALID_SKU_FOR_DELETE"
        
        response = self.client.delete(f'/api/cart/{customer_id}/item/{invalid_product_id}')
        # The current implementation of remove_cart_item_completely doesn't check if product_id exists in products table,
        # only if it exists in the cart for that customer. So it will also return 404 not_found.
        # This behavior is acceptable for this endpoint.
        self.assertEqual(response.status_code, 404) 
        data = json.loads(response.data.decode('utf-8'))
        self.assertEqual(data['status'], 'not_found')

    # --- Tests for DELETE /api/cart/<customer_id>/clear ---
    def test_cart_clear_endpoint_non_empty_cart(self):
        """Test DELETE /api/cart/<customer_id>/clear: clear a non-empty cart."""
        customer_id = "cart_clear_customer_001"
        product1 = SAMPLE_PRODUCTS[0]
        product2 = SAMPLE_PRODUCTS[1]
        # Add items to cart
        self.client.post(f'/api/cart/{customer_id}/item', json={"product_id": product1['id'], "quantity": 1})
        self.client.post(f'/api/cart/{customer_id}/item', json={"product_id": product2['id'], "quantity": 2})

        cart_response_before_clear = self.client.get(f'/api/cart/{customer_id}')
        cart_data_before_clear = json.loads(cart_response_before_clear.data.decode('utf-8'))
        self.assertTrue(len(cart_data_before_clear['items']) > 0, "Cart should have items before clearing")

        response = self.client.delete(f'/api/cart/{customer_id}/clear')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data.decode('utf-8'))
        self.assertEqual(data['status'], 'success')
        self.assertEqual(data['message'], 'Cart cleared.')
        self.assertEqual(data['items_deleted'], 2) # Two distinct product lines

        cart_response_after_clear = self.client.get(f'/api/cart/{customer_id}')
        cart_data_after_clear = json.loads(cart_response_after_clear.data.decode('utf-8'))
        self.assertEqual(len(cart_data_after_clear['items']), 0)
        self.assertEqual(cart_data_after_clear['subtotal'], 0.0)

    def test_cart_clear_endpoint_empty_cart(self):
        """Test DELETE /api/cart/<customer_id>/clear: clear an already empty cart."""
        customer_id = "cart_clear_customer_002" # New customer, cart should be empty
        
        cart_response_before_clear = self.client.get(f'/api/cart/{customer_id}')
        cart_data_before_clear = json.loads(cart_response_before_clear.data.decode('utf-8'))
        self.assertEqual(len(cart_data_before_clear['items']), 0, "Cart should be empty before clearing")

        response = self.client.delete(f'/api/cart/{customer_id}/clear')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data.decode('utf-8'))
        self.assertEqual(data['status'], 'success')
        self.assertEqual(data['message'], 'Cart cleared.')
        self.assertEqual(data['items_deleted'], 0)

    # --- Tests for POST /api/checkout/place_order ---
    def test_checkout_successful_order(self):
        """Test POST /api/checkout/place_order: successful order placement."""
        customer_id = "checkout_customer_001"
        product1 = SAMPLE_PRODUCTS[0] # Lavender
        product2 = SAMPLE_PRODUCTS[1] # Tomato
        
        # Add items to cart
        self.client.post(f'/api/cart/{customer_id}/item', json={"product_id": product1['id'], "quantity": 1}) # Price 5.99
        self.client.post(f'/api/cart/{customer_id}/item', json={"product_id": product2['id'], "quantity": 2}) # Price 4.50 * 2 = 9.00
        # Expected subtotal = 5.99 + 9.00 = 14.99

        cart_response = self.client.get(f'/api/cart/{customer_id}')
        cart_data = json.loads(cart_response.data.decode('utf-8'))
        self.assertEqual(len(cart_data['items']), 2)
        
        checkout_payload = {
            "customer_id": customer_id,
            "items": cart_data['items'], # Pass items from fetched cart
            "shipping_details": {
                "fullName": "Test User",
                "address": "123 Test St",
                "city": "Testville",
                "postalCode": "12345",
                "country": "Testland",
                "paymentMethod": "creditCard"
            },
            "total_amount": cart_data['subtotal'] # Pass subtotal from fetched cart
        }
        
        response = self.client.post('/api/checkout/place_order', json=checkout_payload)
        self.assertEqual(response.status_code, 201) # 201 Created
        data = json.loads(response.data.decode('utf-8'))
        self.assertEqual(data['status'], 'success')
        self.assertIn("Order placed successfully", data['message'])
        self.assertTrue(data['order_id'].startswith("SIM_"))

        # Verify cart is cleared after order
        cart_after_order_response = self.client.get(f'/api/cart/{customer_id}')
        cart_after_order_data = json.loads(cart_after_order_response.data.decode('utf-8'))
        self.assertEqual(len(cart_after_order_data['items']), 0)
        self.assertEqual(cart_after_order_data['subtotal'], 0.0)

    def test_checkout_missing_fields(self):
        """Test POST /api/checkout/place_order: missing required fields."""
        customer_id = "checkout_customer_002"
        # Missing 'items'
        payload_missing_items = {
            "customer_id": customer_id,
            "shipping_details": {"fullName": "Test"},
            "total_amount": 10.00
        }
        response = self.client.post('/api/checkout/place_order', json=payload_missing_items)
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data.decode('utf-8'))
        self.assertIn("Missing required fields", data['error'])

        # Missing 'shipping_details'
        payload_missing_shipping = {
            "customer_id": customer_id,
            "items": [{"product_id": "SKU_TEST", "quantity": 1}],
            "total_amount": 10.00
        }
        response = self.client.post('/api/checkout/place_order', json=payload_missing_shipping)
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data.decode('utf-8'))
        self.assertIn("Missing required fields", data['error'])

    def test_checkout_empty_payload(self):
        """Test POST /api/checkout/place_order: empty JSON payload."""
        response = self.client.post('/api/checkout/place_order', json={})
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data.decode('utf-8'))
        self.assertIn("Missing required fields", data['error'])
        
    def test_checkout_invalid_json_payload(self):
        """Test POST /api/checkout/place_order: invalid JSON payload."""
        response = self.client.post('/api/checkout/place_order', data="this is not json", content_type="application/json")
        self.assertEqual(response.status_code, 400) # Flask handles malformed JSON
        data = json.loads(response.data.decode('utf-8'))
        self.assertEqual(data['error'], "Bad Request") # Check the main error type
        self.assertIn("Invalid JSON payload provided.", data['message']) # Check the specific message

    # --- Tests for POST /api/retail/search-products ---
    def test_retail_search_valid_query_lavender(self):
        """Test retail search with a valid query expected to return 'Lavender'."""
        # First, check if Retail API is configured in app.py to avoid unnecessary API calls if not.
        # This check is a bit of a hack by reading app.py; a dedicated config status endpoint would be better.
        with open("app.py", "r") as f:
            app_content = f.read()
        if 'GCP_PROJECT_ID = "your-gcp-project-id"' in app_content:
            self.skipTest("Retail API project ID is not configured in app.py with non-default values. Skipping live API call.")

        payload = {"query": "Lavender", "visitor_id": "test_visitor_lavender"}
        response = self.client.post('/api/retail/search-products', json=payload)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data.decode('utf-8'))
        self.assertIn('recommendations', data)
        self.assertIsInstance(data['recommendations'], list)
        # Check if SKU_PLANT_LAVENDER_001 is in the recommendations
        found_lavender = any(item['product_id'] == 'SKU_PLANT_LAVENDER_001' and item['name'] == "English Lavender 'Munstead'" for item in data['recommendations'])
        # Depending on search tuning, it might not always be the first, so we check if it's present at all.
        # For a more robust test, one might need to check if *any* item containing "Lavender" is returned if exact match isn't guaranteed.
        self.assertTrue(found_lavender, "Expected 'English Lavender 'Munstead'' (SKU_PLANT_LAVENDER_001) in search results for 'Lavender'")

    def test_retail_search_valid_query_soil(self):
        """Test retail search with a valid query expected to return 'Soil' products."""
        with open("app.py", "r") as f:
            app_content = f.read()
        if 'GCP_PROJECT_ID = "your-gcp-project-id"' in app_content:
            self.skipTest("Retail API project ID is not configured in app.py. Skipping live API call.")

        payload = {"query": "Soil", "visitor_id": "test_visitor_soil"}
        response = self.client.post('/api/retail/search-products', json=payload)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data.decode('utf-8'))
        self.assertIn('recommendations', data)
        self.assertIsInstance(data['recommendations'], list)
        self.assertTrue(len(data['recommendations']) > 0, "Expected at least one soil product for query 'Soil'")
        # Check if SKU_SOIL_WELLDRAIN_PREMIUM_001 is in the recommendations
        found_soil = any(item['product_id'] == 'SKU_SOIL_WELLDRAIN_PREMIUM_001' for item in data['recommendations'])
        self.assertTrue(found_soil, "Expected 'Premium Well-Draining Potting Mix' (SKU_SOIL_WELLDRAIN_PREMIUM_001) in search results for 'Soil'")

    def test_retail_search_query_no_results(self):
        """Test retail search with a query expected to return no results."""
        with open("app.py", "r") as f:
            app_content = f.read()
        if 'GCP_PROJECT_ID = "your-gcp-project-id"' in app_content:
            self.skipTest("Retail API project ID is not configured in app.py. Skipping live API call.")
            
        payload = {"query": "XyzAbc123NonExistentFloralPattern", "visitor_id": "test_visitor_no_results"}
        response = self.client.post('/api/retail/search-products', json=payload)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data.decode('utf-8'))
        self.assertIn('recommendations', data)
        self.assertIsInstance(data['recommendations'], list)
        self.assertEqual(len(data['recommendations']), 0)

    def test_retail_search_empty_query_string(self):
        """Test retail search with an empty query string."""
        with open("app.py", "r") as f:
            app_content = f.read()
        if 'GCP_PROJECT_ID = "your-gcp-project-id"' in app_content:
            self.skipTest("Retail API project ID is not configured in app.py. Skipping live API call.")

        payload = {"query": "", "visitor_id": "test_visitor_empty_query"}
        response = self.client.post('/api/retail/search-products', json=payload)
        self.assertEqual(response.status_code, 200) # Vertex AI might return all or error; app should handle
        data = json.loads(response.data.decode('utf-8'))
        self.assertIn('recommendations', data) # Should always have the key
        self.assertIsInstance(data['recommendations'], list)
        # Depending on Vertex AI config, empty query might return all items or an error.
        # If it's an error from Vertex, app.py's try-except should catch it and return 500.
        # If it returns items, len(data['recommendations']) could be > 0.
        # For this test, we primarily ensure the endpoint doesn't crash and returns the expected structure.

    def test_retail_search_missing_query_in_payload(self):
        """Test retail search with missing 'query' in payload."""
        # This test does not depend on Retail API configuration itself, but on app.py validation
        payload = {"visitor_id": "test_visitor_missing_query"}
        response = self.client.post('/api/retail/search-products', json=payload)
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data.decode('utf-8'))
        self.assertIn('error', data)
        self.assertEqual(data['error'], "Invalid JSON payload. 'query' and 'visitor_id' are required.")

    def test_retail_search_missing_visitor_id_in_payload(self):
        """Test retail search with missing 'visitor_id' in payload."""
        payload = {"query": "lavender"}
        response = self.client.post('/api/retail/search-products', json=payload)
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data.decode('utf-8'))
        self.assertIn('error', data)
        self.assertEqual(data['error'], "Invalid JSON payload. 'query' and 'visitor_id' are required.")

    def test_retail_search_unconfigured_service(self):
        """Test retail search when service is explicitly unconfigured (using placeholder IDs)."""
        # Temporarily mock the app's config for this test if possible, or ensure it's default
        # For now, this test relies on the default check in app.py
        # This test is more robust in cymbal_home_garden_backend/test_api.py which reads app.py
        # Here, we assume if the other tests run, the config is likely non-default.
        # A better way is to mock app.config or the retail_v2.SearchServiceClient for this specific test.
        # If the global config in app.py IS "your-gcp-project-id", this test should reflect that.
        # Let's assume for this test file, if it reaches here, the config is usually set.
        # So, this test is more of a placeholder unless we can dynamically alter app.config for one test.
        # The check in app.py is:
        # if not all([GCP_PROJECT_ID != "your-gcp-project-id", ...]) return 503
        # If the actual GCP_PROJECT_ID in app.py IS "your-gcp-project-id", this test should expect 503.
        # This test is tricky without proper config mocking for the test client environment.
        # For now, we'll assume if other tests are running, it's configured.
        # The test in the other file (cymbal_home_garden_backend/test_api.py) is better for this specific scenario.
        pass # Placeholder, as robustly testing the "unconfigured" state here is complex without mocking app.config


if __name__ == '__main__':
    unittest.main()
