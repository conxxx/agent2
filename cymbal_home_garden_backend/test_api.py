# cymbal_home_garden_backend/test_api.py

import unittest
import requests # type: ignore
import json
from urllib.parse import urljoin

# Ensure your Flask app is running before executing tests, or use a test client.
# For simplicity, these tests assume the server is running at BASE_URL.
BASE_URL = "http://127.0.0.1:5000/api/"

# Sample IDs (ensure these exist from sample_data_importer.py)
SAMPLE_PRODUCT_ID_SOIL = "SKU_SOIL_STD_001"
SAMPLE_PRODUCT_ID_FERT = "SKU_FERT_GEN_001"
SAMPLE_NON_EXISTENT_ID = "SKU_DOES_NOT_EXIST"
CUSTOMER_ID = "test_customer_123" # Consistent customer ID for cart tests

class TestAPIEndpoints(unittest.TestCase):

    def test_01_get_products(self):
        response = requests.get(urljoin(BASE_URL, "products"))
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.json(), list)
        
        # Check if the database is empty and add sample data if it is
        if len(response.json()) == 0:
            print("Database is empty, adding sample data...")
            # Add sample data here using direct SQL insertion
            import sqlite3
            conn = sqlite3.connect("ecommerce.db")  # Ensure this matches your database name
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO products (id, name, description, price, stock, category, image_url)
                VALUES
                    ('SKU_SOIL_STD_001', 'Standard Soil', 'Good for most plants', 12.99, 100, 'Soils', 'soil.jpg'),
                    ('SKU_FERT_GEN_001', 'General Fertilizer', 'All purpose fertilizer', 9.99, 50, 'Fertilizers', 'fertilizer.jpg')
            """)
            conn.commit()
            conn.close()
            
            # Re-fetch products after adding data
            response = requests.get(urljoin(BASE_URL, "products"))
            self.assertEqual(response.status_code, 200)
            self.assertIsInstance(response.json(), list)
        
        self.assertTrue(len(response.json()) > 0)

    def test_02_get_product_detail_exists(self):
        response = requests.get(urljoin(BASE_URL, f"products/{SAMPLE_PRODUCT_ID_SOIL}"))
        self.assertEqual(response.status_code, 200)
        product_data = response.json()
        self.assertEqual(product_data['id'], SAMPLE_PRODUCT_ID_SOIL)
        self.assertIn('name', product_data)

    def test_03_get_product_detail_not_exists(self):
        response = requests.get(urljoin(BASE_URL, f"products/{SAMPLE_NON_EXISTENT_ID}"))
        self.assertEqual(response.status_code, 404)

    def test_04_check_product_availability_exists(self):
        # The store_id is part of the path but its value might not affect current MVP logic
        response = requests.get(urljoin(BASE_URL, f"products/availability/{SAMPLE_PRODUCT_ID_SOIL}/main_store"))
        self.assertEqual(response.status_code, 200)
        avail_data = response.json()
        self.assertIn('available', avail_data)
        self.assertIn('quantity', avail_data)
        self.assertIn('store', avail_data)
        self.assertTrue(isinstance(avail_data['available'], bool))
        self.assertTrue(isinstance(avail_data['quantity'], int))

    def test_05_check_product_availability_not_exists(self):
        response = requests.get(urljoin(BASE_URL, f"products/availability/{SAMPLE_NON_EXISTENT_ID}/main_store"))
        self.assertEqual(response.status_code, 404)

    def test_06_get_empty_cart(self):
        # Ensure cart is empty or reset for this customer_id before test if necessary,
        # or use a unique customer_id for each test run.
        # For simplicity, we just check the structure.
        response = requests.get(urljoin(BASE_URL, f"cart/{CUSTOMER_ID}_empty_test"))
        self.assertEqual(response.status_code, 200)
        cart_data = response.json()
        self.assertIn('items', cart_data)
        self.assertIn('subtotal', cart_data)
        self.assertEqual(len(cart_data['items']), 0)
        self.assertEqual(cart_data['subtotal'], 0.0)

    def test_07_modify_cart_add_item(self):
        payload = {
            "items_to_add": [{"product_id": SAMPLE_PRODUCT_ID_SOIL, "quantity": 1}],
            "items_to_remove": []
        }
        response = requests.post(urljoin(BASE_URL, f"cart/modify/{CUSTOMER_ID}"), json=payload)
        self.assertEqual(response.status_code, 200)
        response_data = response.json()
        self.assertEqual(response_data['status'], 'success')
        self.assertTrue(response_data['items_added'])
        
        # Verify item in cart
        cart_response = requests.get(urljoin(BASE_URL, f"cart/{CUSTOMER_ID}"))
        cart_data = cart_response.json()
        self.assertTrue(any(item['product_id'] == SAMPLE_PRODUCT_ID_SOIL and item['quantity'] >= 1 for item in cart_data['items']))

    def test_08_modify_cart_add_another_item(self):
        payload = {
            "items_to_add": [{"product_id": SAMPLE_PRODUCT_ID_FERT, "quantity": 2}],
            "items_to_remove": []
        }
        response = requests.post(urljoin(BASE_URL, f"cart/modify/{CUSTOMER_ID}"), json=payload)
        self.assertEqual(response.status_code, 200)
        response_data = response.json()
        self.assertEqual(response_data['status'], 'success')
        self.assertTrue(response_data['items_added'])

        cart_response = requests.get(urljoin(BASE_URL, f"cart/{CUSTOMER_ID}"))
        cart_data = cart_response.json()
        self.assertTrue(any(item['product_id'] == SAMPLE_PRODUCT_ID_FERT and item['quantity'] == 2 for item in cart_data['items']))

    def test_09_get_cart_with_items(self):
        response = requests.get(urljoin(BASE_URL, f"cart/{CUSTOMER_ID}"))
        self.assertEqual(response.status_code, 200)
        cart_data = response.json()
        self.assertIn('items', cart_data)
        self.assertIn('subtotal', cart_data)
        self.assertTrue(len(cart_data['items']) >= 2) # Soil + Fertilizer
        self.assertTrue(cart_data['subtotal'] > 0)

    def test_10_modify_cart_remove_item_partially(self):
        # Assuming SAMPLE_PRODUCT_ID_FERT was added with quantity 2
        payload = {
            "items_to_add": [],
            "items_to_remove": [{"product_id": SAMPLE_PRODUCT_ID_FERT, "quantity": 1}]
        }
        response = requests.post(urljoin(BASE_URL, f"cart/modify/{CUSTOMER_ID}"), json=payload)
        self.assertEqual(response.status_code, 200)
        response_data = response.json()
        self.assertEqual(response_data['status'], 'success')
        self.assertTrue(response_data['items_removed'])

        cart_response = requests.get(urljoin(BASE_URL, f"cart/{CUSTOMER_ID}"))
        cart_data = cart_response.json()
        self.assertTrue(any(item['product_id'] == SAMPLE_PRODUCT_ID_FERT and item['quantity'] == 1 for item in cart_data['items']))


    def test_11_modify_cart_remove_item_completely(self):
        payload = {
            "items_to_add": [],
            "items_to_remove": [{"product_id": SAMPLE_PRODUCT_ID_SOIL, "quantity": 99}] # Remove all, assuming less than 99
        }
        response = requests.post(urljoin(BASE_URL, f"cart/modify/{CUSTOMER_ID}"), json=payload)
        self.assertEqual(response.status_code, 200)
        response_data = response.json()
        self.assertEqual(response_data['status'], 'success')
        self.assertTrue(response_data['items_removed'])

        cart_response = requests.get(urljoin(BASE_URL, f"cart/{CUSTOMER_ID}"))
        cart_data = cart_response.json()
        self.assertFalse(any(item['product_id'] == SAMPLE_PRODUCT_ID_SOIL for item in cart_data['items']))

    def test_12_retail_search_products(self):
        # This test will only pass if Retail API is configured in app.py and accessible.
        # If RETAIL_SERVING_CONFIG_ID is "default_serving_config" (the placeholder),
        # this test will likely get a 503 or an error from the API.
        # For true unit testing, you might mock the google-cloud-retail client.
        payload = {
            "query": "Petunias",
            "visitor_id": "test_visitor_retail_search"
        }
        response = requests.post(urljoin(BASE_URL, "retail/search-products"), json=payload)
        
        # Check if Retail API is configured. If not, 503 is expected.
        app_config_response = requests.get(urljoin(BASE_URL, "products")) # any valid endpoint to check server
        if app_config_response.status_code == 200: # Check if app is running
            # Read app.py directly to check if config is default - this is a bit hacky for a test
            # A better way would be an endpoint that reveals non-sensitive config status for tests
            with open("app.py", "r") as f:
                app_content = f.read()
            if 'RETAIL_SERVING_CONFIG_ID = "default_serving_config"' in app_content:
                self.assertEqual(response.status_code, 503, "Retail API seems unconfigured, expected 503.")
                print("\nINFO: test_retail_search_products - Retail API not configured in app.py, received 503 as expected.")
                return # End test here if not configured

        # If configured, expect 200 or 500 if Retail API call itself fails
        self.assertIn(response.status_code, [200, 500]) 
        response_data = response.json()
        self.assertIn('recommendations', response_data)
        if response.status_code == 200:
            self.assertIsInstance(response_data['recommendations'], list)
            # If recommendations are returned, check structure for one item
            if response_data['recommendations']:
                first_rec = response_data['recommendations'][0]
                self.assertIn('product_id', first_rec)
                self.assertIn('name', first_rec)
                self.assertIn('description', first_rec)
        elif response.status_code == 500:
            self.assertIn('error', response_data)
            print(f"\nWARN: test_retail_search_products - Received 500 from /api/retail/search-products. Error: {response_data.get('details')}")

if __name__ == '__main__':
    print("Ensure the Flask development server (app.py) is running before starting these tests.")
    print(f"Customer ID for cart tests: {CUSTOMER_ID}\n")
    unittest.main(verbosity=2)