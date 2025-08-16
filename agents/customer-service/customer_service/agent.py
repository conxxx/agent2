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
# limitations under the License.§

"""Agent module for the customer service agent."""

import logging
import warnings
from google.adk import Agent
# Removed DatabaseSessionService import as it's configured via CLI
from .config import Config
from .prompts import GLOBAL_INSTRUCTION, INSTRUCTION
from .shared_libraries.callbacks import (
    rate_limit_callback,
    before_agent,
    before_tool,
    after_tool,
)
from .tools.tools import (
    # send_call_companion_link, # Commented out in tools.py
    # approve_discount, # Commented out in tools.py
    # sync_ask_for_approval, # Commented out in tools.py
    # update_salesforce_crm, # Commented out in tools.py
    access_cart_information,
    modify_cart,
    get_product_recommendations,
    check_product_availability,
    schedule_planting_service,
    get_available_planting_times,
    send_care_instructions,
    generate_qr_code,
    search_products, # Added import for the new tool
    set_website_theme, # Added import for the new theme tool
    initiate_checkout_ui, # Added for checkout UI
    initiate_shipping_ui, # Added for shipping UI
    initiate_payment_ui, # Added for payment UI
    agent_processes_shipping_choice, # Added for processing shipping choices
    submit_order_and_clear_cart, # Added for final order submission
    # display_checkout_item_selection_ui, # REMOVED
    # display_shipping_options_ui, # REMOVED
    # display_pickup_locations_ui, # REMOVED
    # display_payment_methods_ui, # REMOVED
    # display_order_confirmation_ui, # REMOVED
)

warnings.filterwarnings("ignore", category=UserWarning, module=".*pydantic.*")

configs = Config()

# configure logging __name__
logger = logging.getLogger(__name__)


# Session service is configured via the --session_db_url CLI argument for 'adk web'
# No need to instantiate it here.

# Helper function to prepare the product recommendation payload
def _prepare_product_recommendation_payload(products: list[dict], original_query: str) -> dict:
    """
    Prepares the structured JSON payload for product recommendations.
    """
    product_list_for_payload = []
    for product in products:
        # Ensure 'formatted_price' from get_product_recommendations is used for 'price' key
        product_list_for_payload.append({
            "id": product.get("id"),
            "name": product.get("name"),
            "price": product.get("formatted_price"), # Price pre-formatted by get_product_recommendations tool
            "image_url": product.get("image_url"),
            "product_url": product.get("product_url")
        })

    return {
        "type": "product_recommendations",
        "payload": {
            "title": f"Recommendations for {original_query}",
            "products": product_list_for_payload
        }
    }

# New tool to format recommendations for display
def format_product_recommendations_for_display(
    product_details_list: list[dict], original_search_query: str
) -> dict:
    """
    Formats a list of product details and an original search query into a structured
    JSON payload for displaying product recommendation cards on the frontend.
    The 'product_details_list' argument should be the list of product dictionaries
    (each containing id, name, formatted_price, image_url, product_url)
    which is typically the 'recommendations' field from the output of the
    'get_product_recommendations' tool.
    The 'original_search_query' is the user's original search query string that
    led to these recommendations.
    """
    logger.info(
        f"Formatting product recommendations for display. Original query: '{original_search_query}'. "
        f"Number of products: {len(product_details_list) if isinstance(product_details_list, list) else 'N/A'}"
    )
    if not isinstance(product_details_list, list):
        logger.error(
            "Invalid 'product_details_list' argument to format_product_recommendations_for_display: expected list, "
            f"got {type(product_details_list)}. Data: {product_details_list}"
        )
        # Return a structured error or an empty valid payload
        error_payload = {
            "type": "product_recommendations",
            "payload": {
                "title": f"Recommendations for {original_search_query}",
                "products": [],
                "error": "Internal error: Received invalid product data for formatting.",
            },
        }
        logger.info(f"Returning error payload from format_product_recommendations_for_display: {error_payload}")
        return error_payload
    
    # Call the helper to construct the final payload
    recommendation_payload = _prepare_product_recommendation_payload(
        products=product_details_list, original_query=original_search_query
    )
    logger.info(f"Returning product recommendation payload from format_product_recommendations_for_display: {recommendation_payload}")
    return recommendation_payload

root_agent = Agent(
    model=configs.agent_settings.model,
    global_instruction=GLOBAL_INSTRUCTION,
    instruction=INSTRUCTION,
    name=configs.agent_settings.name,
    tools=[
        # send_call_companion_link, # Commented out in tools.py and from imports
        # approve_discount, # Commented out in tools.py and from imports
        # sync_ask_for_approval, # Commented out in tools.py and from imports
        # update_salesforce_crm, # Commented out in tools.py and from imports
        access_cart_information,
        modify_cart,
        get_product_recommendations,
        check_product_availability,
        schedule_planting_service,
        get_available_planting_times,
        send_care_instructions,
        generate_qr_code,
        search_products,
        format_product_recommendations_for_display, # Added new tool
        set_website_theme, # Added new theme tool
        initiate_checkout_ui, # Added for checkout UI
        initiate_shipping_ui, # Added for shipping UI
        initiate_payment_ui, # Added for payment UI
        agent_processes_shipping_choice, # Added for processing shipping choices
        submit_order_and_clear_cart, # Added for final order submission
      
    ],
    before_tool_callback=before_tool,
    after_tool_callback=after_tool,
    before_agent_callback=before_agent,
    before_model_callback=rate_limit_callback,
)
