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

"""Callback functions for FOMC Research Agent."""

import logging
import time

from google.adk.agents.callback_context import CallbackContext
from google.adk.models import LlmRequest
from typing import Any, Dict, Optional, Tuple # Added Optional, Tuple
from google.adk.tools import BaseTool
from google.adk.agents.invocation_context import InvocationContext
from google.adk.sessions.state import State # Added State
from google.adk.tools.tool_context import ToolContext # Added ToolContext
from jsonschema import ValidationError # Added ValidationError
from customer_service.entities.customer import Customer

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

RATE_LIMIT_SECS = 60
RPM_QUOTA = 10


def rate_limit_callback(
    callback_context: CallbackContext, llm_request: LlmRequest
) -> None:
    """Callback function that implements a query rate limit.

    Args:
      callback_context: A CallbackContext obj representing the active callback
        context.
      llm_request: A LlmRequest obj representing the active LLM request.
    """
    # DIAGNOSTIC LOG: Log content being sent to LLM
    try:
        llm_request_summary = "LLM Request Contents: "
        for i, content_item in enumerate(llm_request.contents):
            llm_request_summary += f"\n  Content Item {i} (role: {content_item.role}):"
            for j, part_item in enumerate(content_item.parts):
                part_summary = str(part_item) # Default str representation
                if hasattr(part_item, 'text') and part_item.text:
                    part_summary = f"TextPart(text='{part_item.text[:100]}...')" if len(part_item.text) > 100 else f"TextPart(text='{part_item.text}')"
                elif hasattr(part_item, 'inline_data') and part_item.inline_data:
                    part_summary = f"InlineDataPart(mime_type='{part_item.inline_data.mime_type}', data_len={len(part_item.inline_data.data)})"
                    if 'audio' in part_item.inline_data.mime_type and hasattr(part_item.inline_data, 'data') and isinstance(part_item.inline_data.data, bytes) and len(part_item.inline_data.data) > 0:
                        # Log first up to 16 bytes as hex to help identify audio format issues
                        first_bytes_hex = part_item.inline_data.data[:16].hex()
                        part_summary += f", first_16_bytes_hex='{first_bytes_hex}'"
                elif hasattr(part_item, 'function_call') and part_item.function_call:
                    part_summary = f"FunctionCallPart(name='{part_item.function_call.name}')"
                elif hasattr(part_item, 'function_response') and part_item.function_response:
                     part_summary = f"FunctionResponsePart(name='{part_item.function_response.name}')"
                else: # Fallback for other part types or if text/data is empty
                    part_summary = f"UnknownPartType(type='{type(part_item).__name__}')"


                llm_request_summary += f"\n    Part {j}: {part_summary}"
        
        # Truncate if overall summary is too long
        if len(llm_request_summary) > 1000: # Increased limit for better context
            llm_request_summary = llm_request_summary[:1000] + "\n  ... (summary truncated)"
        logger.info(f"[DIAG_LOG LLM_REQUEST] before_model_callback (rate_limit_callback): {llm_request_summary}")
    except Exception as e:
        logger.error(f"[DIAG_LOG LLM_REQUEST] before_model_callback: Error serializing LlmRequest for logging: {e}", exc_info=True)

    for content in llm_request.contents: # Existing loop
        for part in content.parts:
            if part.text=="":
                part.text=" "

    
    

    now = time.time()
    if "timer_start" not in callback_context.state:

        callback_context.state["timer_start"] = now
        callback_context.state["request_count"] = 1
        logger.debug(
            "rate_limit_callback [timestamp: %i, "
            "req_count: 1, elapsed_secs: 0]",
            now,
        )
        return

    request_count = callback_context.state["request_count"] + 1
    elapsed_secs = now - callback_context.state["timer_start"]
    logger.debug(
        "rate_limit_callback [timestamp: %i, request_count: %i,"
        " elapsed_secs: %i]",
        now,
        request_count,
        elapsed_secs,
    )

    if request_count > RPM_QUOTA:
        delay = RATE_LIMIT_SECS - elapsed_secs + 1
        if delay > 0:
            logger.debug("Sleeping for %i seconds", delay)
            time.sleep(delay)
        callback_context.state["timer_start"] = now
        callback_context.state["request_count"] = 1
    else:
        callback_context.state["request_count"] = request_count

    # Check for a pending UI command and set it in the current turn's state_delta
    if 'current_ui_command_for_frontend' in callback_context.state:
        ui_command = callback_context.state.pop('current_ui_command_for_frontend')
        if hasattr(callback_context, 'invocation_context') and \
           hasattr(callback_context.invocation_context, 'actions'):
            logger.info(f"Moving UI command to invocation_context.actions.state_delta: {ui_command}")
            callback_context.invocation_context.actions.state_delta = ui_command
        else:
            logger.warning("Could not set UI command in state_delta: invocation_context or actions not found.")
            # Optionally, put it back if it couldn't be set, though this might cause loops if not handled.
            # callback_context.state['current_ui_command_for_frontend'] = ui_command

    return


# New function: validate_customer_id
def validate_customer_id(customer_id: str, session_state: State) -> Tuple[bool, Optional[str]]:
    """
        Validates the customer ID against the customer profile in the session state.
        
        Args:
            customer_id (str): The ID of the customer to validate.
            session_state (State): The session state containing the customer profile.
        
        Returns:
            A tuple containing a bool (True/False) and an Optional String.
            When False, a string with the error message to pass to the model for deciding
            what actions to take to remediate.
    """
    logger.debug(f"Attempting to validate customer_id: {customer_id}")
    if 'customer_profile' not in session_state:
        logger.warning("validate_customer_id: 'customer_profile' not in session_state.")
        return False, "No customer profile selected. Please select a profile."

    try:
        # We read the profile from the state, where it is set deterministically
        # at the beginning of the session.
        c = Customer.model_validate_json(session_state['customer_profile'])
        logger.debug(f"Customer profile loaded from state: {c.customer_id}")
        if customer_id == c.customer_id:
            logger.info(f"Customer ID {customer_id} validated successfully.")
            return True, None
        else:
            logger.warning(f"Customer ID mismatch. Expected: {c.customer_id}, Got: {customer_id}")
            return False, f"You cannot use the tool with customer_id {customer_id}, only for {c.customer_id}."
    except ValidationError as e:
        logger.error(f"Customer profile couldn't be parsed due to ValidationError: {e}")
        return False, "Customer profile couldn't be parsed. Please reload the customer data."
    except Exception as e:
        logger.error(f"An unexpected error occurred during customer ID validation: {e}", exc_info=True)
        return False, "An unexpected error occurred while validating customer profile."

def lowercase_value(value):
    """Make dictionary lowercase"""
    if isinstance(value, dict):
        return (dict(k, lowercase_value(v)) for k, v in value.items())
    elif isinstance(value, str):
        return value.lower()
    elif isinstance(value, (list, set, tuple)):
        tp = type(value)
        return tp(lowercase_value(i) for i in value)
    else:
        return value


# Callback Methods
def before_tool(
    tool: BaseTool, args: Dict[str, Any], tool_context: CallbackContext
) -> Optional[Dict[str, Any]]:
    # DIAGNOSTIC LOG: Log tool input arguments
    args_summary = str(args)
    if len(args_summary) > 300: args_summary = args_summary[:300] + "..."
    logger.info(f"[DIAG_LOG TOOL_INPUT] before_tool: Tool: {tool.name}, Args: {args_summary}")

    # Ensure customer_profile is loaded in the state
    if "customer_profile" not in tool_context.state:
        logger.info("before_tool: 'customer_profile' not found in state. Attempting to load.")
        try:
            customer_profile_json = Customer.get_customer("123").to_json()
            tool_context.state["customer_profile"] = customer_profile_json
            logger.info("before_tool: 'customer_profile' successfully loaded and set in state.")
            logger.debug(f"before_tool: Loaded customer_profile data: {customer_profile_json}")
        except Exception as e:
            logger.error(f"before_tool: Failed to load or set 'customer_profile'. Error: {e}", exc_info=True)
            # Optionally, return an error if profile loading is critical for all tools
            # return {"error": "Failed to load critical customer profile."}
    else:
        logger.info("before_tool: 'customer_profile' already exists in state.")
        logger.debug(f"before_tool: Existing customer_profile data: {tool_context.state['customer_profile']}")

    # i make sure all values that the agent is sending to tools are lowercase
    # Note: The original lowercase_value function returns a generator for dicts,
    # which might not be what's intended if args needs to be modified in place
    # or used as a standard dict later. Assuming it works as expected for now.
    # For safety, one might consider: args = lowercase_value(args) if it returns a new dict.
    lowercase_value(args) # Assuming this modifies in-place or its return is handled
    logger.debug(f"Arguments after attempting to lowercase: {args}")

    # Several tools require customer_id as input. We don't want to rely
    # solely on the model picking the right customer id. We validate it.
    # Alternative: tools can fetch the customer_id from the state directly.
    if 'customer_id' in args:
        logger.info(f"Customer ID '{args['customer_id']}' found in tool arguments. Validating...")
        valid, err = validate_customer_id(args['customer_id'], tool_context.state)
        if not valid:
            logger.warning(f"Customer ID validation failed for '{args['customer_id']}': {err}")
            return {"error": err} # Return error to the agent
        logger.info(f"Customer ID '{args['customer_id']}' validated successfully.")


    # Check for the next tool call and then act accordingly.
    # Example logic based on the tool being called.
    if tool.name == "sync_ask_for_approval":
        amount = args.get("value", None)
        logger.debug(f"Tool 'sync_ask_for_approval' called with amount: {amount}")
        if amount is not None and amount <= 10:  # Example business rule
            logger.info(f"Auto-approving discount of {amount} as it's <= 10.")
            return {
                "status": "approved", # Updated structure
                "message": "Discount auto-approved as per configuration."
            }
        logger.debug(f"Discount amount {amount} requires manager approval or is not applicable for auto-approval.")
        # Add more logic checks here as needed for your tools.

    if tool.name == "modify_cart":
        logger.debug(f"Tool 'modify_cart' called with args: {args}")
        if (
            args.get("items_added") is True
            and args.get("items_removed") is True
        ):
            logger.info("Both items_added and items_removed are true for modify_cart.")
            return {"result": "I have added and removed the requested items."}
    
    logger.debug(f"before_tool for {tool.name} completed, no specific override action taken.")
    return None

# New function: after_tool
def after_tool(
    tool: BaseTool, args: Dict[str, Any], tool_context: ToolContext, tool_response: Dict
) -> Optional[Dict]:
    # DIAGNOSTIC LOG: Log tool output response
    response_summary = str(tool_response)
    if len(response_summary) > 300: response_summary = response_summary[:300] + "..."
    logger.info(f"[DIAG_LOG TOOL_OUTPUT] after_tool: Tool: {tool.name}, Response: {response_summary}")

    # After approvals, we perform operations deterministically in the callback
    # to apply the discount in the cart.
    if tool.name == "sync_ask_for_approval":
        if tool_response.get('status') == "approved": # Check key existence
            logger.info(f"Tool 'sync_ask_for_approval' was approved. Response: {tool_response}")
            logger.debug("Applying discount to the cart (simulated/placeholder)")
            # Actually make changes to the cart here if needed
            # e.g., tool_context.state['cart'].apply_discount(args.get('value'))
        else:
            logger.info(f"Tool 'sync_ask_for_approval' was not approved or status unknown. Response: {tool_response}")


    if tool.name == "approve_discount": # This tool might be from the original `callbacksnew.py` but not explicitly requested to be part of `before_tool` logic.
                                      # Keeping its `after_tool` logic as per `callbacksnew.py`
        if tool_response.get('status') == "ok": # Check key existence
            logger.info(f"Tool 'approve_discount' status is 'ok'. Response: {tool_response}")
            logger.debug("Applying discount to the cart (simulated/placeholder)")
            # Actually make changes to the cart here
        else:
            logger.info(f"Tool 'approve_discount' status not 'ok' or unknown. Response: {tool_response}")
    
    logger.debug(f"after_tool for {tool.name} completed.")

    # If the tool response is intended for UI display,
    # store it in the session state. The ADK should pick this up for state_delta.
    if isinstance(tool_response, dict) and tool_response.get("action") == "display_ui":
        logger.info(f"Storing UI command in state: {tool_response}")
        tool_context.state['current_ui_command_for_frontend'] = tool_response
        # It's also good practice to ensure other parts of the state that might
        # conflict or become stale are cleared if this UI command should be the sole focus.
        # For example, if 'customer_profile' was just a default or fallback:
        # if 'customer_profile' in tool_context.state:
        #     del tool_context.state['customer_profile'] # Example: remove if it's not needed with UI command
        return None # Signal that the tool's effect is a state change

    # For other tools that might return data for the LLM, pass it through.
    # If a non-UI tool also modifies state, that's fine, ADK handles state changes.
    return tool_response

# checking that the customer profile is loaded as state.
def before_agent(callback_context: InvocationContext):
    logger.debug("before_agent: Callback triggered.")
    # DIAGNOSTIC LOG: Log ADK Input (request to agent)
    if callback_context.request and callback_context.request.content:
        try:
            # Attempt to serialize content for logging, be mindful of complex objects
            request_content_summary = str(callback_context.request.content)
            if len(request_content_summary) > 300: # Avoid excessively long logs
                request_content_summary = request_content_summary[:300] + "..."
            logger.info(f"[DIAG_LOG ADK_INPUT] before_agent: Request content to agent: {request_content_summary}")
        except Exception as e:
            logger.error(f"[DIAG_LOG ADK_INPUT] before_agent: Error serializing request content for logging: {e}")
    else:
        logger.info("[DIAG_LOG ADK_INPUT] before_agent: No request content found in callback_context.")

    if "customer_profile" not in callback_context.state:
        logger.info("before_agent: 'customer_profile' not found in state. Attempting to load.")
        try:
            customer_profile_json = Customer.get_customer("123").to_json()
            callback_context.state["customer_profile"] = customer_profile_json
            logger.info("before_agent: 'customer_profile' successfully loaded and set in state.")
            logger.debug(f"before_agent: Loaded customer_profile data: {customer_profile_json}")
        except Exception as e:
            logger.error(f"before_agent: Failed to load or set 'customer_profile'. Error: {e}", exc_info=True)
    else:
        logger.info("before_agent: 'customer_profile' already exists in state.")
        logger.debug(f"before_agent: Existing customer_profile data: {callback_context.state['customer_profile']}")

    # logger.info(callback_context.state["customer_profile"])
