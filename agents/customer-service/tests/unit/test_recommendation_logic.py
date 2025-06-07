import unittest
from unittest.mock import AsyncMock, MagicMock, patch

# Assume a structure for AgentContext and how tools are called.
# This is a placeholder for actual implementation details.
# For instance, AgentContext might hold 'recommendation_cycle_count'
# and tool calls might be methods on a 'tool_caller' object or module.

class AgentContext:
    def __init__(self, customer_id="test_customer_123"):
        self.recommendation_cycle_count = 0
        self.customer_id = customer_id
        # Potentially, a log of agent's verbal outputs or actions
        self.agent_responses = []
        self.tool_calls = [] # To log tool calls for assertions

    def add_response(self, response):
        self.agent_responses.append(response)

    def record_tool_call(self, tool_name, **kwargs):
        self.tool_calls.append({"name": tool_name, "args": kwargs})

    def get_last_tool_call(self, name=None):
        if not self.tool_calls:
            return None
        if name:
            for call in reversed(self.tool_calls):
                if call["name"] == name:
                    return call
            return None
        return self.tool_calls[-1]

# Placeholder for how an agent processes a turn.
# In a real scenario, this would involve the agent's core logic,
# interpreting the prompt, and deciding on actions/tool calls.
async def simulate_agent_processing_after_cart_add(agent_context, added_product_id, added_product_name, mock_tool_manager):
    """
    This is a simplified simulation of the agent's logic post-product addition.
    It directly mimics the steps outlined in the prompt for recommendation.
    A real test would likely involve invoking the main agent loop/handler.
    """

    # --- Start of In-lined Recommendation Logic from Prompt ---
    current_product_id = added_product_id
    current_product_name = added_product_name

    # Recommendation Cycle Logic
    # For this simulation, we assume if current_product_id was from a prior recommendation,
    # recommendation_cycle_count would have been preserved by the calling test.
    # The reset logic (if not from prior rec) is handled in Test Case 6.

    if agent_context.recommendation_cycle_count >= 3:
        # Skip to care instructions
        if "plant" in current_product_name.lower(): # Simplified check
            agent_context.add_response(f"Now that we've added {current_product_name} to your cart, would you like summarized care instructions for it?")
            # mock_tool_manager.send_care_instructions(...) # Potentially
        return

    # Fetch Current Product Details
    agent_context.record_tool_call("get_product_recommendations", product_ids=[current_product_id], customer_id=agent_context.customer_id)
    # This call is for the *triggering* product
    current_product_details_response = await mock_tool_manager.get_product_recommendations(product_ids=[current_product_id], customer_id=agent_context.customer_id)
    
    product_details = None
    if current_product_details_response and current_product_details_response.get("recommendations"):
        if current_product_details_response["recommendations"]:
             # Assuming the first item in recommendations is the product detail we want
            product_details = current_product_details_response["recommendations"][0]

    # Check if essential fields are missing (treat missing keys as empty lists for this check)
    if not product_details or not all(k in product_details for k in ["companion_plants_ids", "recommended_soil_ids", "recommended_fertilizer_ids"]):
        # If any essential key is missing, even if it's an empty list, the original check was:
        # "product_details is missing essential fields like companion_plants_ids..."
        # The prompt implies these keys should exist. A more robust check might be:
        # if not product_details or any(product_details.get(k) is None for k in ["companion_plants_ids", ...])
        # For now, sticking to "missing essential fields" means the key itself is absent or product_details is None.
        # The prompt also says: "(treat missing keys as empty lists for this check)" when *extracting* them later,
        # but for the *existence* check, it implies they should be there.
        # Let's refine the condition to: if product_details is None, or if any of the specified keys are not in product_details.
        essential_keys = ["companion_plants_ids", "recommended_soil_ids", "recommended_fertilizer_ids"]
        if not product_details or not all(key in product_details for key in essential_keys):
        if "plant" in current_product_name.lower(): # Simplified check
             agent_context.add_response(f"Now that we've added {current_product_name} to your cart, would you like summarized care instructions for it?")
        return

    # Extract Potential Recommendation IDs
    companion_ids = product_details.get("companion_plants_ids", [])
    soil_ids = product_details.get("recommended_soil_ids", [])
    fertilizer_ids = product_details.get("recommended_fertilizer_ids", [])

    # Compile and Select Recommendation IDs
    all_potential_ids = list(dict.fromkeys(companion_ids + soil_ids + fertilizer_ids)) # unique

    if not all_potential_ids:
        if "plant" in current_product_name.lower(): # Simplified check
             agent_context.add_response(f"Now that we've added {current_product_name} to your cart, would you like summarized care instructions for it?")
        return

    selected_recommendation_ids = []
    for pid in companion_ids:
        if len(selected_recommendation_ids) < 3 and pid in all_potential_ids:
            selected_recommendation_ids.append(pid)
            all_potential_ids.remove(pid) # Ensure uniqueness and correct count
    for pid in soil_ids:
        if len(selected_recommendation_ids) < 3 and pid in all_potential_ids:
            selected_recommendation_ids.append(pid)
            all_potential_ids.remove(pid)
    for pid in fertilizer_ids:
        if len(selected_recommendation_ids) < 3 and pid in all_potential_ids:
            selected_recommendation_ids.append(pid)
            all_potential_ids.remove(pid)
            
    if not selected_recommendation_ids:
        if "plant" in current_product_name.lower(): # Simplified check
             agent_context.add_response(f"Now that we've added {current_product_name} to your cart, would you like summarized care instructions for it?")
        return

    # Increment Recommendation Cycle Counter
    agent_context.recommendation_cycle_count += 1

    # Fetch Details for Recommended Products
    agent_context.record_tool_call("get_product_recommendations", product_ids=selected_recommendation_ids, customer_id=agent_context.customer_id)
    recommended_products_details_list_response = await mock_tool_manager.get_product_recommendations(product_ids=selected_recommendation_ids, customer_id=agent_context.customer_id)
    recommended_products_details_list = recommended_products_details_list_response.get("recommendations", [])

    # Present Recommendations to User
    if recommended_products_details_list:
        intro_message = f"Okay, '{current_product_name}' has been added to your cart! Since you're getting that, you might also be interested in these related items. (This is recommendation cycle {agent_context.recommendation_cycle_count}/3 for items related to the original product):"
        agent_context.add_response(intro_message)
        
        agent_context.record_tool_call("format_product_recommendations_for_display", product_details_list=recommended_products_details_list, original_search_query="Related to " + current_product_name)
        await mock_tool_manager.format_product_recommendations_for_display(product_details_list=recommended_products_details_list, original_search_query="Related to " + current_product_name)

    # Offer Care Instructions
    if "plant" in current_product_name.lower(): # Simplified check
        agent_context.add_response(f"Now that we've added {current_product_name} to your cart, would you like summarized care instructions for it?")
        # Potentially: await mock_tool_manager.send_care_instructions(...)
    # --- End of In-lined Recommendation Logic ---


class TestRecommendationLogic(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        self.mock_tool_manager = MagicMock()
        # Common product definitions
        self.products_db = {
            "SKU_LAVENDER": {"id": "SKU_LAVENDER", "name": "English Lavender 'Munstead'", "companion_plants_ids": ["SKU_ROSEMARY"], "recommended_soil_ids": ["SKU_SOIL_WELLDRAIN"], "type": "plant"},
            "SKU_ROSEMARY": {"id": "SKU_ROSEMARY", "name": "Rosemary officinalis", "companion_plants_ids": ["SKU_SAGE"], "type": "plant"},
            "SKU_SOIL_WELLDRAIN": {"id": "SKU_SOIL_WELLDRAIN", "name": "Well-Draining Potting Mix", "type": "soil"},
            "SKU_SAGE": {"id": "SKU_SAGE", "name": "Garden Sage", "type": "plant"},
            "SKU_PRODUCT_MULTI": {
                "id": "SKU_PRODUCT_MULTI", "name": "Multi-Rec Product", "type": "plant",
                "companion_plants_ids": ["SKU_COMP1", "SKU_COMP2"],
                "recommended_soil_ids": ["SKU_SOIL1", "SKU_SOIL2"],
                "recommended_fertilizer_ids": ["SKU_FERT1", "SKU_FERT2"]
            },
            "SKU_COMP1": {"id": "SKU_COMP1", "name": "Companion 1", "type": "plant"},
            "SKU_COMP2": {"id": "SKU_COMP2", "name": "Companion 2", "type": "plant"},
            "SKU_SOIL1": {"id": "SKU_SOIL1", "name": "Soil 1", "type": "soil"},
            "SKU_PRODUCT_NO_RECS": {"id": "SKU_PRODUCT_NO_RECS", "name": "Plain Plant", "type": "plant", "companion_plants_ids": [], "recommended_soil_ids": [], "recommended_fertilizer_ids": []},
            "SKU_PRODUCT_X": {"id": "SKU_PRODUCT_X", "name": "Product X (New)", "type": "plant", "companion_plants_ids": ["SKU_COMP_X"]},
            "SKU_COMP_X": {"id": "SKU_COMP_X", "name": "Companion X", "type": "plant"},
             "SKU_PRODUCT_A": {"id": "SKU_PRODUCT_A", "name": "Product A", "type": "plant", "companion_plants_ids": ["SKU_PRODUCT_B", "SKU_PRODUCT_C"]},
             "SKU_PRODUCT_B": {"id": "SKU_PRODUCT_B", "name": "Product B", "type": "plant", "companion_plants_ids": ["SKU_PRODUCT_D", "SKU_PRODUCT_E"]},
             "SKU_PRODUCT_C": {"id": "SKU_PRODUCT_C", "name": "Product C", "type": "plant"},
             "SKU_PRODUCT_D": {"id": "SKU_PRODUCT_D", "name": "Product D", "type": "plant", "companion_plants_ids": ["SKU_PRODUCT_F", "SKU_PRODUCT_G"]},
             "SKU_PRODUCT_E": {"id": "SKU_PRODUCT_E", "name": "Product E", "type": "plant"},
             "SKU_PRODUCT_F": {"id": "SKU_PRODUCT_F", "name": "Product F", "type": "plant", "companion_plants_ids": ["SKU_COMP_F"]}, # Used in cycle limit
             "SKU_PRODUCT_G": {"id": "SKU_PRODUCT_G", "name": "Product G", "type": "plant"},
             "SKU_COMP_F": {"id": "SKU_COMP_F", "name": "Companion F", "type": "plant"},
            "SKU_FAIL": {"id": "SKU_FAIL", "name": "Failed Product Plant", "type": "plant"}, # For failure test
        }

    # _setup_mock_search_products might still be useful if other agent parts use it,
    # but for the recommendation trigger, it's replaced by get_product_recommendations.
    # For clarity in these specific tests, we'll focus on get_product_recommendations.
    # If search_products were still needed for other flows, it would remain.

    def _setup_mock_get_product_recommendations(self):
        """
        Sets up mock for get_product_recommendations.
        It handles calls for a single product (fetching current_product_id details)
        and for multiple products (fetching details for generated recommendations).
        """
        async def mock_get_recs_fn(product_ids, customer_id):
            # This function will now be the primary source for product details
            # both for the triggering product and subsequent recommendations.
            recs = []
            for pid in product_ids:
                if pid in self.products_db:
                    # Ensure the full detail as per products_db is returned
                    recs.append(self.products_db[pid]) 
            return {"recommendations": recs, "errors_fetching_recommendations": None}
        self.mock_tool_manager.get_product_recommendations = AsyncMock(side_effect=mock_get_recs_fn)


    def _setup_mock_format_display(self):
        self.mock_tool_manager.format_product_recommendations_for_display = AsyncMock(return_value={"status": "ok"})


    async def test_successful_first_recommendation_set(self):
        agent_context = AgentContext()
        agent_context.recommendation_cycle_count = 0

        self._setup_mock_get_product_recommendations() # Unified mock
        self._setup_mock_format_display()

        await simulate_agent_processing_after_cart_add(
            agent_context, "SKU_LAVENDER", "English Lavender 'Munstead'", self.mock_tool_manager
        )

        # Assert get_product_recommendations was called for current_product_id
        # It will be the first call to this tool.
        first_get_recs_call = agent_context.tool_calls[0]
        self.assertEqual(first_get_recs_call["name"], "get_product_recommendations")
        self.assertCountEqual(first_get_recs_call["args"]["product_ids"], ["SKU_LAVENDER"])

        # Assert get_product_recommendations was called for the actual recommendations
        # This will be the second call to this tool.
        second_get_recs_call = agent_context.tool_calls[1]
        self.assertEqual(second_get_recs_call["name"], "get_product_recommendations")
        self.assertCountEqual(second_get_recs_call["args"]["product_ids"], ["SKU_ROSEMARY", "SKU_SOIL_WELLDRAIN"])
        
        # Assert format_product_recommendations_for_display was called
        format_call = agent_context.get_last_tool_call("format_product_recommendations_for_display")
        self.assertIsNotNone(format_call)
        self.assertEqual(format_call["args"]["original_search_query"], "Related to English Lavender 'Munstead'")
        self.assertEqual(len(format_call["args"]["product_details_list"]), 2)


        self.assertIn(
            "Okay, 'English Lavender 'Munstead'' has been added to your cart! Since you're getting that, you might also be interested in these related items. (This is recommendation cycle 1/3 for items related to the original product):",
            agent_context.agent_responses
        )
        self.assertEqual(agent_context.recommendation_cycle_count, 1)
        self.assertIn(
            "Now that we've added English Lavender 'Munstead' to your cart, would you like summarized care instructions for it?",
            agent_context.agent_responses
        )

    async def test_recommendation_limit_of_3_items_per_set(self):
        agent_context = AgentContext()
        agent_context.recommendation_cycle_count = 0

        self._setup_mock_get_product_recommendations() # Unified mock
        self._setup_mock_format_display()

        await simulate_agent_processing_after_cart_add(
            agent_context, "SKU_PRODUCT_MULTI", "Multi-Rec Product", self.mock_tool_manager
        )

        # First call for SKU_PRODUCT_MULTI
        first_get_recs_call = agent_context.tool_calls[0]
        self.assertEqual(first_get_recs_call["name"], "get_product_recommendations")
        self.assertCountEqual(first_get_recs_call["args"]["product_ids"], ["SKU_PRODUCT_MULTI"])
        
        # Second call for its recommendations
        second_get_recs_call = agent_context.tool_calls[1]
        self.assertEqual(second_get_recs_call["name"], "get_product_recommendations")
        self.assertEqual(len(second_get_recs_call["args"]["product_ids"]), 3)
        self.assertCountEqual(second_get_recs_call["args"]["product_ids"], ["SKU_COMP1", "SKU_COMP2", "SKU_SOIL1"])

        format_call = agent_context.get_last_tool_call("format_product_recommendations_for_display")
        self.assertIsNotNone(format_call)
        self.assertEqual(len(format_call["args"]["product_details_list"]), 3)

        self.assertEqual(agent_context.recommendation_cycle_count, 1)
        self.assertIn(
            "Now that we've added Multi-Rec Product to your cart, would you like summarized care instructions for it?",
            agent_context.agent_responses
        )

    async def test_chained_recommendation_user_selects_recommended_item(self):
        agent_context = AgentContext()
        agent_context.recommendation_cycle_count = 1 # Set by previous cycle for Lavender

        self._setup_mock_get_product_recommendations() # Unified mock
        self._setup_mock_format_display()

        # User adds SKU_ROSEMARY (which was one of the recommendations for Lavender)
        await simulate_agent_processing_after_cart_add(
            agent_context, "SKU_ROSEMARY", "Rosemary officinalis", self.mock_tool_manager
        )

        # First call for SKU_ROSEMARY itself
        first_get_recs_call = agent_context.tool_calls[0]
        self.assertEqual(first_get_recs_call["name"], "get_product_recommendations")
        self.assertCountEqual(first_get_recs_call["args"]["product_ids"], ["SKU_ROSEMARY"])

        # Crucially, cycle count should NOT have been reset
        self.assertEqual(agent_context.recommendation_cycle_count, 2) # Incremented from 1 to 2

        # Second call for Sage (companion of Rosemary)
        second_get_recs_call = agent_context.tool_calls[1]
        self.assertEqual(second_get_recs_call["name"], "get_product_recommendations")
        self.assertCountEqual(second_get_recs_call["args"]["product_ids"], ["SKU_SAGE"])
        
        format_call = agent_context.get_last_tool_call("format_product_recommendations_for_display")
        self.assertIsNotNone(format_call)

        self.assertIn(
            "Okay, 'Rosemary officinalis' has been added to your cart! Since you're getting that, you might also be interested in these related items. (This is recommendation cycle 2/3 for items related to the original product):",
            agent_context.agent_responses
        )
        self.assertIn(
            "Now that we've added Rosemary officinalis to your cart, would you like summarized care instructions for it?",
            agent_context.agent_responses
        )

    async def test_recommendation_cycle_limit_reached_max_3_cycles(self):
        agent_context = AgentContext()
        agent_context.recommendation_cycle_count = 3 

        self._setup_mock_get_product_recommendations() # Unified mock
        # format_product_recommendations_for_display should not be called
        self.mock_tool_manager.format_product_recommendations_for_display = AsyncMock()
        
        await simulate_agent_processing_after_cart_add(
            agent_context, "SKU_PRODUCT_F", "Product F", self.mock_tool_manager
        )
        
        self.assertEqual(agent_context.recommendation_cycle_count, 3)

        # get_product_recommendations for SKU_PRODUCT_F itself *is* called to check its nature for care instructions.
        # This is the only call to get_product_recommendations.
        self.assertEqual(len(agent_context.tool_calls), 1)
        get_recs_call_for_F = agent_context.tool_calls[0]
        self.assertEqual(get_recs_call_for_F["name"], "get_product_recommendations")
        self.assertCountEqual(get_recs_call_for_F["args"]["product_ids"], ["SKU_PRODUCT_F"])

        # No *further* recommendations should be fetched or displayed
        # This means the mock_tool_manager.get_product_recommendations should only have been called ONCE for SKU_PRODUCT_F
        # and format_product_recommendations_for_display should not have been called at all.
        
        # Filter tool_calls to find calls for fetching *subsequent* recommendations (more than 1 id, or not the first call)
        subsequent_rec_calls = [
            call for call in agent_context.tool_calls 
            if call["name"] == "get_product_recommendations" and call["args"]["product_ids"] != ["SKU_PRODUCT_F"]
        ]
        self.assertEqual(len(subsequent_rec_calls), 0, "Should not fetch details for new recommendations")
        
        self.mock_tool_manager.format_product_recommendations_for_display.assert_not_called()
        
        self.assertIn(
            "Now that we've added Product F to your cart, would you like summarized care instructions for it?",
            agent_context.agent_responses
        )
        self.assertNotIn(
            "Okay, 'Product F' has been added to your cart! Since you're getting that, you might also be interested in these related items.",
            "".join(agent_context.agent_responses) # Check all responses
        )


    async def test_no_relevant_ids_found_for_recommendation(self):
        agent_context = AgentContext()
        agent_context.recommendation_cycle_count = 0

        self._setup_mock_get_product_recommendations() # Unified mock
        # format_product_recommendations_for_display should not be called
        self.mock_tool_manager.format_product_recommendations_for_display = AsyncMock()


        await simulate_agent_processing_after_cart_add(
            agent_context, "SKU_PRODUCT_NO_RECS", "Plain Plant", self.mock_tool_manager
        )

        # get_product_recommendations for SKU_PRODUCT_NO_RECS itself is called
        self.assertEqual(len(agent_context.tool_calls), 1)
        get_recs_call_for_no_recs = agent_context.tool_calls[0]
        self.assertEqual(get_recs_call_for_no_recs["name"], "get_product_recommendations")
        self.assertCountEqual(get_recs_call_for_no_recs["args"]["product_ids"], ["SKU_PRODUCT_NO_RECS"])
        
        # No *further* recommendations should be fetched or displayed
        # Check that no other get_product_recommendations call was made for recommendations
        # and format_product_recommendations_for_display was not called.
        # The previous check on len(agent_context.tool_calls) == 1 already implies no further get_product_recommendations.
        self.mock_tool_manager.format_product_recommendations_for_display.assert_not_called()
        
        self.assertEqual(agent_context.recommendation_cycle_count, 0)
        self.assertIn(
            "Now that we've added Plain Plant to your cart, would you like summarized care instructions for it?",
            agent_context.agent_responses
        )
        self.assertNotIn(
            "Okay, 'Plain Plant' has been added to your cart! Since you're getting that, you might also be interested in these related items.",
            "".join(agent_context.agent_responses)
        )

    async def test_user_adds_new_product_not_from_recommendations_counter_reset(self):
        agent_context = AgentContext()
        agent_context.recommendation_cycle_count = 1 # After A's recommendations

        self._setup_mock_get_product_recommendations() # Unified mock
        self._setup_mock_format_display()
        
        agent_context.recommendation_cycle_count = 0 # Simulating reset by main agent flow

        await simulate_agent_processing_after_cart_add(
            agent_context, "SKU_PRODUCT_X", "Product X (New)", self.mock_tool_manager
        )

        # First call for SKU_PRODUCT_X itself
        first_get_recs_call = agent_context.tool_calls[0]
        self.assertEqual(first_get_recs_call["name"], "get_product_recommendations")
        self.assertCountEqual(first_get_recs_call["args"]["product_ids"], ["SKU_PRODUCT_X"])
        
        self.assertEqual(agent_context.recommendation_cycle_count, 1) 

        # Second call for X's companion
        second_get_recs_call = agent_context.tool_calls[1]
        self.assertEqual(second_get_recs_call["name"], "get_product_recommendations")
        self.assertCountEqual(second_get_recs_call["args"]["product_ids"], ["SKU_COMP_X"])

        format_call = agent_context.get_last_tool_call("format_product_recommendations_for_display")
        self.assertIsNotNone(format_call)
        self.assertIn(
             "Okay, 'Product X (New)' has been added to your cart! Since you're getting that, you might also be interested in these related items. (This is recommendation cycle 1/3 for items related to the original product):",
            agent_context.agent_responses
        )
        self.assertIn(
            "Now that we've added Product X (New) to your cart, would you like summarized care instructions for it?",
            agent_context.agent_responses
        )

    async def test_product_added_but_get_recommendations_fails_for_current_product(self):
        agent_context = AgentContext()
        agent_context.recommendation_cycle_count = 0

        # Mock get_product_recommendations to return empty or error for the initial product
        async def mock_get_recs_fail_fn(product_ids, customer_id):
            if product_ids == ["SKU_FAIL"]:
                return {"recommendations": [], "errors_fetching_recommendations": ["Failed to fetch SKU_FAIL"]}
            # Fallback for any other calls (though not expected in this test path if first fails)
            recs = []
            for pid in product_ids:
                if pid in self.products_db:
                    recs.append(self.products_db[pid])
            return {"recommendations": recs}

        self.mock_tool_manager.get_product_recommendations = AsyncMock(side_effect=mock_get_recs_fail_fn)
        self.mock_tool_manager.format_product_recommendations_for_display = AsyncMock()

        await simulate_agent_processing_after_cart_add(
            agent_context, "SKU_FAIL", "Failed Product Plant", self.mock_tool_manager
        )
        
        # Assert get_product_recommendations was called for SKU_FAIL
        self.mock_tool_manager.get_product_recommendations.assert_any_call(product_ids=["SKU_FAIL"], customer_id=agent_context.customer_id)
        
        # No further get_product_recommendations for *subsequent* items should be called
        # And format should not be called
        format_call_count = 0
        for call in agent_context.tool_calls:
            if call["name"] == "format_product_recommendations_for_display":
                format_call_count +=1
        self.assertEqual(format_call_count, 0)
        
        # Check that only one call to get_product_recommendations was made (for SKU_FAIL)
        get_recs_call_count = 0
        for call in agent_context.tool_calls:
            if call["name"] == "get_product_recommendations":
                get_recs_call_count +=1
        self.assertEqual(get_recs_call_count, 1)


        self.assertEqual(agent_context.recommendation_cycle_count, 0)
        self.assertIn(
            "Now that we've added Failed Product Plant to your cart, would you like summarized care instructions for it?",
            agent_context.agent_responses
        )
        self.assertNotIn(
            "Okay, 'Failed Product Plant' has been added to your cart! Since you're getting that, you might also be interested in these related items.",
            "".join(agent_context.agent_responses)
        )

if __name__ == '__main__':
    unittest.main()
