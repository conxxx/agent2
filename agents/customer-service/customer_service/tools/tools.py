# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# add docstring to this module
"""Tools module for the customer service agent."""

import logging
import uuid
from datetime import datetime, timedelta
from typing import Optional # Added import for Optional
import requests # Added for making HTTP requests
import json # Added for parsing JSON responses

logger = logging.getLogger(__name__)

# Import Config and instantiate it to access settings
try:
    from customer_service.config import Config
    configs = Config()
    BACKEND_API_BASE_URL = configs.BACKEND_API_BASE_URL
except ImportError:
    logger.error("Could not import Config from customer_service.config. Using default URL.")
    # Fallback in case of import issues, though ideally this shouldn't happen
    BACKEND_API_BASE_URL = "http://127.0.0.1:5000/api"


# def send_call_companion_link(phone_number: str) -> str:
#     """
#     Sends a link to the user's phone number to start a video session.

#     Args:
#         phone_number (str): The phone number to send the link to.

#     Returns:
#         dict: A dictionary with the status and message.

#     Example:
#         >>> send_call_companion_link(phone_number='+12065550123')
#         {'status': 'success', 'message': 'Link sent to +12065550123'}
#     """

#     logger.info("Sending call companion link to %s", phone_number)

#     return {"status": "success", "message": f"Link sent to {phone_number}"}


# def approve_discount(discount_type: str, value: float, reason: str) -> str:
#     """
#     Approve the flat rate or percentage discount requested by the user.

#     Args:
#         discount_type (str): The type of discount, either "percentage" or "flat".
#         value (float): The value of the discount.
#         reason (str): The reason for the discount.

#     Returns:
#         str: A JSON string indicating the status of the approval.

#     Example:
#         >>> approve_discount(type='percentage', value=10.0, reason='Customer loyalty')
#         '{"status": "ok"}'
#     """
#     logger.info(
#         "Approving a %s discount of %s because %s", discount_type, value, reason
#     )

#     logger.info("INSIDE TOOL CALL")
#     return '{"status": "ok"}'


# def sync_ask_for_approval(discount_type: str, value: float, reason: str) -> str:
#     """
#     Asks the manager for approval for a discount.

#     Args:
#         discount_type (str): The type of discount, either "percentage" or "flat".
#         value (float): The value of the discount.
#         reason (str): The reason for the discount.

#     Returns:
#         str: A JSON string indicating the status of the approval.

#     Example:
#         >>> sync_ask_for_approval(type='percentage', value=15, reason='Customer loyalty')
#         '{"status": "approved"}'
#     """
#     logger.info(
#         "Asking for approval for a %s discount of %s because %s",
#         discount_type,
#         value,
#         reason,
#     )
#     return '{"status": "approved"}'


# def update_salesforce_crm(customer_id: str, details: dict) -> dict:
#     """
#     Updates the Salesforce CRM with customer details.

#     Args:
#         customer_id (str): The ID of the customer.
#         details (str): A dictionary of details to update in Salesforce.

#     Returns:
#         dict: A dictionary with the status and message.

#     Example:
#         >>> update_salesforce_crm(customer_id='123', details={
#             'appointment_date': '2024-07-25',
#             'appointment_time': '9-12',
#             'services': 'Planting',
#             'discount': '15% off planting',
#             'qr_code': '10% off next in-store purchase'})
#         {'status': 'success', 'message': 'Salesforce record updated.'}
#     """
#     logger.info(
#         "Updating Salesforce CRM for customer ID %s with details: %s",
#         customer_id,
#         details,
#     )
#     return {"status": "success", "message": "Salesforce record updated."}


def access_cart_information(customer_id: str) -> dict:
    """
    Args:
        customer_id (str): The ID of the customer.

    Returns:
        dict: A dictionary representing the cart contents.

    Example:
        >>> access_cart_information(customer_id='123')
        {'items': [{'product_id': 'soil-123', 'name': 'Standard Potting Soil', 'quantity': 1}, {'product_id': 'fert-456', 'name': 'General Purpose Fertilizer', 'quantity': 1}], 'subtotal': 25.98}
    """
    logger.info("Accessing cart information for customer ID: %s", customer_id)
    
    api_url = f"{BACKEND_API_BASE_URL}/cart/{customer_id}"
    try:
        response = requests.get(api_url, timeout=5) # Added timeout
        response.raise_for_status() # Raises an HTTPError for bad responses (4XX or 5XX)
        cart_data = response.json()
        logger.info("Successfully retrieved cart data for customer %s: %s", customer_id, cart_data)
        return cart_data
    except requests.exceptions.HTTPError as http_err:
        logger.error(f"HTTP error occurred while accessing cart for {customer_id}: {http_err} - Response: {response.text}")
        # Return an empty/error structure that the agent might expect
        return {"items": [], "subtotal": 0.0, "error": f"Failed to retrieve cart: {response.status_code}"}
    except requests.exceptions.RequestException as req_err:
        logger.error(f"Request exception occurred while accessing cart for {customer_id}: {req_err}")
        return {"items": [], "subtotal": 0.0, "error": "Failed to connect to cart service."}
    except json.JSONDecodeError as json_err:
        logger.error(f"Failed to decode JSON response from cart API for {customer_id}: {json_err} - Response: {response.text}")
        return {"items": [], "subtotal": 0.0, "error": "Invalid response from cart service."}


def modify_cart(
    customer_id: str, items_to_add: list[dict], items_to_remove: list[dict]
) -> dict:
    """Modifies the user's shopping cart by adding and/or removing items.

    Args:
        customer_id (str): The ID of the customer.
        items_to_add (list): A list of dictionaries, each with 'product_id' and 'quantity'.
        items_to_remove (list): A list of product_ids to remove.

    Returns:
        dict: A dictionary indicating the status of the cart modification.
    Example:
        >>> modify_cart(customer_id='123', items_to_add=[{'product_id': 'soil-456', 'quantity': 1}, {'product_id': 'fert-789', 'quantity': 1}], items_to_remove=[{'product_id': 'fert-112', 'quantity': 1}])
        {'status': 'success', 'message': 'Cart updated successfully.', 'items_added': True, 'items_removed': True}
    """

    logger.info("Modifying cart for customer ID: %s", customer_id)
    logger.info("Adding items: %s", items_to_add)
    logger.info("Removing items: %s", items_to_remove)

    api_url = f"{BACKEND_API_BASE_URL}/cart/modify/{customer_id}"
    payload = {
        "items_to_add": items_to_add if items_to_add is not None else [],
        "items_to_remove": items_to_remove if items_to_remove is not None else []
    }
    
    try:
        response = requests.post(api_url, json=payload, timeout=5)
        response.raise_for_status()
        modification_status = response.json()
        logger.info("Successfully modified cart for customer %s: %s", customer_id, modification_status)
        # Add action to signal frontend refresh and include added item details if applicable
        added_item_details_for_payload = None
        # Check if items were intended to be added and the API reported success for additions
        if items_to_add and modification_status.get("items_added") is True:
            # Assuming the animation is for the first item added.
            # The `items_to_add` list contains dicts like {'product_id': '...', 'quantity': ...}
            first_added_item_info = items_to_add[0]
            product_id_to_fetch = first_added_item_info.get("product_id")

            if product_id_to_fetch:
                logger.info(f"Attempting to fetch details for added product ID: {product_id_to_fetch} for refresh_cart payload.")
                product_api_url = f"{BACKEND_API_BASE_URL}/products/{product_id_to_fetch}"
                try:
                    product_response = requests.get(product_api_url, timeout=5)
                    product_response.raise_for_status()
                    product_data = product_response.json()
                    
                    # Ensure the image_url is correctly formed if needed.
                    # For now, assuming product_data.get("image_url") is sufficient as per get_product_recommendations
                    # and the task scope (not fixing 404s here).
                    image_url = product_data.get("image_url")
                    
                    added_item_details_for_payload = {
                        "product_id": product_data.get("id"), # or product_id_to_fetch
                        "name": product_data.get("name"),
                        "image_url": image_url
                    }
                    logger.info(f"Successfully fetched details for added item for refresh_cart: {added_item_details_for_payload}")
                except requests.exceptions.HTTPError as http_err_prod:
                    logger.error(f"HTTP error fetching product details for {product_id_to_fetch} (for refresh_cart): {http_err_prod} - Response: {product_response.text if 'product_response' in locals() and hasattr(product_response, 'text') else 'N/A'}")
                except requests.exceptions.RequestException as req_err_prod:
                    logger.error(f"Request exception fetching product details for {product_id_to_fetch} (for refresh_cart): {req_err_prod}")
                except json.JSONDecodeError as json_err_prod:
                    logger.error(f"Failed to decode JSON for product details {product_id_to_fetch} (for refresh_cart): {json_err_prod} - Response: {product_response.text if 'product_response' in locals() and hasattr(product_response, 'text') else 'N/A'}")
        
        return_value = {"action": "refresh_cart", **modification_status}
        if added_item_details_for_payload:
            return_value["added_item"] = added_item_details_for_payload
        
        logger.info(f"modify_cart returning: {return_value}")
        return return_value
    except requests.exceptions.HTTPError as http_err:
        logger.error(f"HTTP error occurred while modifying cart for {customer_id}: {http_err} - Response: {response.text}")
        # Return an error structure consistent with what the agent might expect or can handle
        return {"status": "error", "message": f"Failed to modify cart: {response.status_code}", "items_added": False, "items_removed": False}
    except requests.exceptions.RequestException as req_err:
        logger.error(f"Request exception occurred while modifying cart for {customer_id}: {req_err}")
        return {"status": "error", "message": "Failed to connect to cart modification service.", "items_added": False, "items_removed": False}
    except json.JSONDecodeError as json_err:
        logger.error(f"Failed to decode JSON response from cart modification API for {customer_id}: {json_err} - Response: {response.text}")
        return {"status": "error", "message": "Invalid response from cart modification service.", "items_added": False, "items_removed": False}


def get_product_recommendations(product_ids: list[str], customer_id: str) -> dict:
    """Retrieves and formats specific product details for a list of product IDs for recommendation cards.

    Args:
        product_ids: A list of product IDs.
        customer_id: The ID of the customer (currently unused by this tool but kept for consistency).

    Returns:
        A dictionary containing a list of product dictionaries, each with
        id, name, formatted_price, image_url, and product_url.
        {'recommendations': [
            {'id': 'SKU_123', 'name': 'Product Name', 'formatted_price': '$19.99', 'image_url': '...', 'product_url': '...'},
            ...
        ]}
    """
    logger.info(
        "Getting and formatting product details for recommendation cards for IDs: %s for customer %s",
        product_ids,
        customer_id,
    )

    if not product_ids:
        logger.info("No product IDs provided for recommendations.")
        return {"recommendations": []}

    formatted_products_details = []
    errors = []

    for product_id in product_ids:
        api_url = f"{BACKEND_API_BASE_URL}/products/{product_id}"
        try:
            response = requests.get(api_url, timeout=5)
            response.raise_for_status()
            product_data = response.json()
            
            # Ensure price is a float or int for formatting
            price_value = product_data.get("price")
            formatted_price_str = "N/A" # Default if price is missing or not a number
            if isinstance(price_value, (int, float)):
                formatted_price_str = f"${price_value:.2f}"
            elif isinstance(price_value, str):
                try:
                    price_value_float = float(price_value)
                    formatted_price_str = f"${price_value_float:.2f}"
                except ValueError:
                    logger.warning(f"Could not convert price string '{price_value}' to float for product ID {product_id}")
            else:
                 logger.warning(f"Price for product ID {product_id} is missing or not a number: {price_value}")


            formatted_product = {
                "id": product_data.get("id"),
                "name": product_data.get("name"),
                "formatted_price": formatted_price_str,
                "image_url": product_data.get("image_url"),
                "attributes": product_data.get("attributes"),
                # Construct the new product_url
            }
            product_id_for_url = product_data.get("id")
            if product_id_for_url:
                formatted_product["product_url"] = f"/products/{product_id_for_url}"
            else:
                formatted_product["product_url"] = "#" # Fallback if ID is missing
            
            logger.info(f"Product ID {product_id} generated product_url: {formatted_product.get('product_url')}")
            formatted_products_details.append(formatted_product)
            logger.info(f"Successfully retrieved and formatted details for product ID {product_id}")

        except requests.exceptions.HTTPError as http_err:
            error_msg = f"HTTP error for product ID {product_id}: {http_err} - Response: {response.text}"
            logger.error(error_msg)
            errors.append({"product_id": product_id, "error": str(http_err), "status_code": response.status_code if response else "N/A"})
        except requests.exceptions.RequestException as req_err:
            error_msg = f"Request exception for product ID {product_id}: {req_err}"
            logger.error(error_msg)
            errors.append({"product_id": product_id, "error": str(req_err)})
        except json.JSONDecodeError as json_err:
            error_msg = f"Failed to decode JSON for product ID {product_id}: {json_err} - Response: {response.text if response else 'No response'}"
            logger.error(error_msg)
            errors.append({"product_id": product_id, "error": "Invalid JSON response from product details API."})
            
    if errors:
        logger.warning(f"Encountered errors while fetching details for some products: {errors}")
        
    logger.info("Returning formatted details for %d products.", len(formatted_products_details))
    return {"recommendations": formatted_products_details, "errors_fetching_recommendations": errors if errors else None}


def check_product_availability(product_id: str, store_id: str) -> dict:
    """Checks the availability of a product at a specified store (or for pickup).

    Args:
        product_id: The ID of the product to check.
        store_id: The ID of the store (or 'pickup' for pickup availability).

    Returns:
        A dictionary indicating availability.  Example:
        {'available': True, 'quantity': 10, 'store': 'Main Store'}

    Example:
        >>> check_product_availability(product_id='soil-456', store_id='pickup')
        {'available': True, 'quantity': 10, 'store': 'pickup'}
    """
    logger.info(
        "Checking availability of product ID: %s at store: %s",
        product_id,
        store_id,
    )
    api_url = f"{BACKEND_API_BASE_URL}/products/availability/{product_id}/{store_id}"
    try:
        response = requests.get(api_url, timeout=5)
        response.raise_for_status()
        availability_data = response.json()
        logger.info("Successfully retrieved availability for product %s at store %s: %s", product_id, store_id, availability_data)
        return availability_data
    except requests.exceptions.HTTPError as http_err:
        logger.error(f"HTTP error occurred while checking availability for product {product_id} at store {store_id}: {http_err} - Response: {response.text}")
        # For a 404, the API already returns a specific error. For other errors, a generic one.
        if response.status_code == 404:
            try:
                return response.json() # Return the API's 404 error structure
            except json.JSONDecodeError: # If 404 response is not JSON
                 return {"available": False, "quantity": 0, "store": store_id, "error": "Product not found and error response unparseable."}
        return {"available": False, "quantity": 0, "store": store_id, "error": f"Failed to check availability: {response.status_code}"}
    except requests.exceptions.RequestException as req_err:
        logger.error(f"Request exception occurred while checking availability for product {product_id} at store {store_id}: {req_err}")
        return {"available": False, "quantity": 0, "store": store_id, "error": "Failed to connect to availability service."}
    except json.JSONDecodeError as json_err:
        logger.error(f"Failed to decode JSON response from availability API for {product_id} at store {store_id}: {json_err} - Response: {response.text}")
        return {"available": False, "quantity": 0, "store": store_id, "error": "Invalid response from availability service."}

def search_products(query: str, customer_id: str) -> dict:
    """Searches for products based on a query string using the retail search backend.

    Args:
        query: The search term (e.g., "rosemary", "red pots").
        customer_id: The ID of the customer (used as visitor_id for the search API).

    Returns:
        A dictionary containing a list of search results (products). Example:
        {'results': [
            {'product_id': 'SKU_PLANT_ROSEMARY_001', 'name': 'Rosemary \'Arp\'', 'description': '...'},
            {'product_id': 'SKU_SOIL_HERB_MIX_001', 'name': 'Rosemary Herb Mix Soil', 'description': '...'}
        ]}

    Example:
        >>> search_products(query='rosemary', customer_id='123')
        {'results': [{'product_id': 'SKU_PLANT_ROSEMARY_001', 'name': 'Rosemary \'Arp\'', 'description': 'Upright, aromatic herb...'}]}
    """
    logger.info(f"Searching products with query: '{query}' for customer_id (visitor_id): {customer_id}")
    api_url = f"{BACKEND_API_BASE_URL}/retail/search-products"
    payload = {"query": query, "visitor_id": customer_id}

    try:
        response = requests.post(api_url, json=payload, timeout=10) # Increased timeout for search
        response.raise_for_status()
        search_results = response.json()
        # The backend endpoint returns {'recommendations': [...]}, let's rename to 'results' for clarity
        if "recommendations" in search_results:
             search_results["results"] = search_results.pop("recommendations")

        logger.info(f"Successfully retrieved search results for query '{query}': {search_results}")
        return search_results
    except requests.exceptions.HTTPError as http_err:
        logger.error(f"HTTP error occurred during product search for query '{query}': {http_err} - Response: {response.text}")
        # Try to return the error from the backend if possible
        try:
            error_details = response.json()
        except json.JSONDecodeError:
            error_details = {"error": f"Failed to search products: {response.status_code}"}
        return {"results": [], **error_details} # Combine results and error
    except requests.exceptions.RequestException as req_err:
        logger.error(f"Request exception occurred during product search for query '{query}': {req_err}")
        return {"results": [], "error": "Failed to connect to product search service."}
    except json.JSONDecodeError as json_err:
        logger.error(f"Failed to decode JSON response from product search API for query '{query}': {json_err} - Response: {response.text}")
        return {"results": [], "error": "Invalid response from product search service."}

def schedule_planting_service(
    customer_id: str, date: str, time_range: str, details: str
) -> dict:
    """Schedules a planting service appointment.

    Args:
        customer_id: The ID of the customer.
        date:  The desired date (YYYY-MM-DD).
        time_range: The desired time range (e.g., "9-12").
        details: Any additional details (e.g., "Planting Petunias").

    Returns:
        A dictionary indicating the status of the scheduling. Example:
        {'status': 'success', 'appointment_id': '12345', 'date': '2024-07-29', 'time': '9:00 AM - 12:00 PM'}

    Example:
        >>> schedule_planting_service(customer_id='123', date='2024-07-29', time_range='9-12', details='Planting Petunias')
        {'status': 'success', 'appointment_id': 'some_uuid', 'date': '2024-07-29', 'time': '9-12', 'confirmation_time': '2024-07-29 9:00'}
    """
    logger.info(
        "Scheduling planting service for customer ID: %s on %s (%s)",
        customer_id,
        date,
        time_range,
    )
    logger.info("Details: %s", details)
    # MOCK API RESPONSE - Replace with actual API call to your scheduling system
    # Calculate confirmation time based on date and time_range
    start_time_str = time_range.split("-")[0]  # Get the start time (e.g., "9")
    confirmation_time_str = (
        f"{date} {start_time_str}:00"  # e.g., "2024-07-29 9:00"
    )

    return {
        "status": "success",
        "appointment_id": str(uuid.uuid4()),
        "date": date,
        "time": time_range,
        "confirmation_time": confirmation_time_str,  # formatted time for calendar
    }


def get_available_planting_times(date: str) -> list:
    """Retrieves available planting service time slots for a given date.

    Args:
        date: The date to check (YYYY-MM-DD).

    Returns:
        A list of available time ranges.

    Example:
        >>> get_available_planting_times(date='2024-07-29')
        ['9-12', '13-16']
    """
    logger.info("Retrieving available planting times for %s", date)
    # MOCK API RESPONSE - Replace with actual API call
    # Generate some mock time slots, ensuring they're in the correct format:
    return ["9-12", "13-16"]


def send_care_instructions(
    customer_id: str, plant_type: str, delivery_method: str
) -> dict:
    """Sends an email or SMS with instructions on how to take care of a specific plant type.

    Args:
        customer_id:  The ID of the customer.
        plant_type: The type of plant.
        delivery_method: 'email' (default) or 'sms'.

    Returns:
        A dictionary indicating the status.

    Example:
        >>> send_care_instructions(customer_id='123', plant_type='Petunias', delivery_method='email')
        {'status': 'success', 'message': 'Care instructions for Petunias sent via email.'}
    """
    logger.info(
        "Sending care instructions for %s to customer: %s via %s",
        plant_type,
        customer_id,
        delivery_method,
    )
    # MOCK API RESPONSE - Replace with actual API call or email/SMS sending logic
    return {
        "status": "success",
        "message": f"Care instructions for {plant_type} sent via {delivery_method}.",
    }


def generate_qr_code(
    customer_id: str,
    discount_value: float,
    discount_type: str,
    expiration_days: int,
) -> dict:
    """Generates a QR code for a discount.

    Args:
        customer_id: The ID of the customer.
        discount_value: The value of the discount (e.g., 10 for 10%).
        discount_type: "percentage" (default) or "fixed".
        expiration_days: Number of days until the QR code expires.

    Returns:
        A dictionary containing the QR code data (or a link to it). Example:
        {'status': 'success', 'qr_code_data': '...', 'expiration_date': '2024-08-28'}

    Example:
        >>> generate_qr_code(customer_id='123', discount_value=10.0, discount_type='percentage', expiration_days=30)
        {'status': 'success', 'qr_code_data': 'MOCK_QR_CODE_DATA', 'expiration_date': '2024-08-24'}
    """
    logger.info(
        "Generating QR code for customer: %s with %s - %s discount.",
        customer_id,
        discount_value,
        discount_type,
    )
    # MOCK API RESPONSE - Replace with actual QR code generation library
    expiration_date = (
        datetime.now() + timedelta(days=expiration_days)
    ).strftime("%Y-%m-%d")
    return {
        "status": "success",
        "qr_code_data": "MOCK_QR_CODE_DATA",  # Replace with actual QR code
        "expiration_date": expiration_date,
    }


def initiate_checkout_ui(customer_id: str) -> dict:
    """
    Fetches cart information and signals the intent to show the checkout UI.

    Args:
        customer_id (str): The ID of the customer.

    Returns:
        dict: A dictionary with the action 'show_checkout_ui' and the cart_data.
              Example: {'action': 'show_checkout_ui', 'cart_data': {'items': [...], 'subtotal': ...}}
    """
    logger.info(f"Initiating checkout UI for customer ID: {customer_id}")

    cart_data = access_cart_information(customer_id=customer_id)
    
    action_payload = {"action": "show_checkout_ui", "cart_data": cart_data}
    
    logger.info(f"Returning action payload for initiate_checkout_ui: {action_payload}")
    return action_payload

def initiate_shipping_ui(customer_id: str) -> dict:
    """
    Signals the intent to display the shipping UI options.

    Args:
        customer_id (str): The ID of the customer. (Currently unused by this tool but kept for consistency)

    Returns:
        dict: A dictionary with the action 'show_shipping_ui_requested'.
              Example: {'action': 'show_shipping_ui_requested'}
    """
    logger.info(f"Initiating shipping UI for customer ID: {customer_id}")
    action_payload = {"action": "show_shipping_ui_requested"}
    logger.info(f"Returning action payload for initiate_shipping_ui: {action_payload}")
    return action_payload

def initiate_payment_ui(customer_id: str) -> dict:
    """
    Signals the intent to display the payment UI options.

    Args:
        customer_id (str): The ID of the customer. (Currently unused by this tool but kept for consistency)

    Returns:
        dict: A dictionary with the action 'show_payment_ui_requested'.
              Example: {'action': 'show_payment_ui_requested'}
    """
    logger.info(f"Initiating payment UI for customer ID: {customer_id}")
    action_payload = {"action": "show_payment_ui_requested"}
    logger.info(f"Returning action payload for initiate_payment_ui: {action_payload}")
    return action_payload

def agent_processes_shipping_choice(customer_id: str, user_choice_type: str, user_selection_details: Optional[dict] = None) -> dict:
    """
    Processes the user's shipping choice and determines the UI confirmation and agent's verbal response.

    Args:
        customer_id (str): The ID of the customer.
        user_choice_type (str): The type of choice made by the user or UI. 
                                Expected values: "selected_home_delivery", "selected_pickup_initiated", 
                                "selected_pickup_address", "navigated_back_to_cart_review".
        user_selection_details (Optional[dict]): Additional details, e.g., for "selected_pickup_address",
                                                 it might contain {'text': 'Address Name', 'index': 0}.

    Returns:
        dict: A dictionary containing an 'action' for UI confirmation and a 'speak' field for the agent's response.
              Example: {'action': 'confirm_ui_home_delivery', 'speak': 'Okay, Home Delivery selected.'}
    """
    logger.info(f"Agent processing shipping choice for customer {customer_id}. Choice type: {user_choice_type}, Details: {user_selection_details}")

    response_payload = {"action": "no_ui_change_needed", "speak": "An unexpected shipping interaction occurred."} # Default generic response

    if user_choice_type == "selected_home_delivery":
        response_payload = {
            "action": "confirm_ui_home_delivery",
            "speak": "Okay, Home Delivery has been selected. Ready for the next step, payment?"
        }
    elif user_choice_type == "selected_pickup_initiated":
        response_payload = {
            "action": "confirm_ui_pickup_initiated", # This tells UI to show pickup locations if not already visible
            "speak": "Alright, you'd like a pickup point. Please select one of the displayed options."
        }
    elif user_choice_type == "selected_pickup_address":
        if user_selection_details and "text" in user_selection_details and "index" in user_selection_details:
            response_payload = {
                "action": "confirm_ui_pickup_address",
                "address_index": user_selection_details["index"],
                "speak": f"Great, pickup at {user_selection_details['text']} is confirmed. Shall we proceed to payment?"
            }
        else:
            logger.warning(f"Missing details for 'selected_pickup_address': {user_selection_details}")
            response_payload["speak"] = "It seems there was an issue selecting the pickup address. Could you please try again?"
    elif user_choice_type == "navigated_back_to_cart_review":
        response_payload = {
            "action": "no_ui_change_needed", # Or a specific action if UI needs to react to going back
            "speak": "Okay, we are back to your cart review. How can I help?"
        }
    else:
        logger.warning(f"Unhandled user_choice_type in agent_processes_shipping_choice: {user_choice_type}")

    logger.info(f"Agent_processes_shipping_choice returning: {response_payload}")
    return response_payload

def set_website_theme(theme: str) -> dict:
    """
    Sets the website theme to 'night' or 'day'.

    Args:
        theme (str): The desired theme, either "night" or "day".

    Returns:
        dict: A dictionary indicating the action and theme.
              Example: {"action": "set_theme", "theme": "night"}

    Example:
        >>> set_website_theme(theme='night')
        {'action': 'set_theme', 'theme': 'night'}
    """
    logger.info(f"Attempting to set website theme to: {theme}")
    if theme.lower() not in ["night", "day"]:
        logger.warning(f"Invalid theme value received: {theme}. Theme must be 'night' or 'day'.")
        # Potentially return an error or default, based on desired handling
        # For now, we'll pass it through but log a warning.
        # Or, enforce strictness:
        # return {"action": "set_theme_failed", "error": "Invalid theme value", "received_theme": theme}
        pass # Allowing invalid themes through for now as per initial spec, but logged.

    theme_value = theme.lower()
    action_result = {"action": "set_theme", "theme": theme_value}
    logger.info(f"Tool 'set_website_theme' called with theme: '{theme}'. Returning: {action_result}")
    return action_result


def submit_order_and_clear_cart(customer_id: str, cart_items: list[dict], shipping_details: dict, total_amount: float) -> dict:
    """
    Submits the order to the backend, which includes clearing the cart.

    Args:
        customer_id (str): The ID of the customer.
        cart_items (list[dict]): List of items in the cart (e.g., from access_cart_information).
        shipping_details (dict): Shipping information collected.
        total_amount (float): The final total amount for the order.

    Returns:
        dict: A dictionary with the status of the order submission.
              Example: {'status': 'success', 'message': 'Order submitted...', 'order_id': 'SIM_123', 'action': 'refresh_cart_and_show_confirmation'}
    """
    logger.info(f"Submitting order for customer ID: {customer_id}")
    api_url = f"{BACKEND_API_BASE_URL}/checkout/place_order"
    
    payload = {
        "customer_id": customer_id,
        "items": cart_items,
        "shipping_details": shipping_details,
        "total_amount": total_amount
    }
    
    logger.info(f"Order submission payload: {json.dumps(payload, indent=2)}")

    try:
        response = requests.post(api_url, json=payload, timeout=10)
        response.raise_for_status()
        order_status = response.json() # Expected: {"status": "success", "message": "...", "order_id": "..."}
        
        if order_status.get("status") == "success":
            logger.info(f"Order successfully submitted for customer {customer_id}: {order_status}")
            return {
                "status": "success",
                "message": order_status.get("message", "Order submitted and cart cleared."),
                "order_id": order_status.get("order_id"),
                "action": "refresh_cart_and_show_confirmation" # Action for UI
            }
        else:
            logger.error(f"Order submission reported failure by API for customer {customer_id}: {order_status}")
            return {
                "status": "error",
                "message": order_status.get("message", "Order submission failed at API level."),
                "details": order_status
            }

    except requests.exceptions.HTTPError as http_err:
        logger.error(f"HTTP error occurred while submitting order for {customer_id}: {http_err} - Response: {response.text if 'response' in locals() else 'N/A'}")
        return {"status": "error", "message": f"Failed to submit order due to HTTP error: {response.status_code if 'response' in locals() else 'Unknown'}"}
    except requests.exceptions.RequestException as req_err:
        logger.error(f"Request exception occurred while submitting order for {customer_id}: {req_err}")
        return {"status": "error", "message": "Failed to connect to order submission service."}
    except json.JSONDecodeError as json_err:
        logger.error(f"Failed to decode JSON response from order submission API for {customer_id}: {json_err} - Response: {response.text if 'response' in locals() else 'N/A'}")
        return {"status": "error", "message": "Invalid response from order submission service."}


# Deprecated: Replaced by granular UI tools like display_checkout_item_selection_ui, etc.
# def initiate_checkout_ui() -> dict:
#     """
#     Instructs the agent to send a command to the frontend to open the checkout modal.
#
#     Returns:
#         dict: A dictionary with the action to trigger the checkout modal.
#               Example: {'action': 'trigger_checkout_modal'}
#     """
#     logger.info("Initiating checkout UI: instructing frontend to open checkout modal.")
#
#     # Log the action being returned
#     action_payload = {"action": "trigger_checkout_modal"}
#     logger.info(f"Returning action payload for initiate_checkout_ui: {action_payload}")
#
#     return action_payload
