import asyncio
import logging
import time # <-- Add time import
import os
import base64
import json
from typing import Optional, TYPE_CHECKING

from dotenv import load_dotenv
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from starlette.websockets import WebSocketState

# Configure logging FIRST
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
# Set higher logging levels for verbose libraries
logging.getLogger("google.adk").setLevel(logging.WARNING)
logging.getLogger("google.adk.models.registry").setLevel(logging.WARNING)
logging.getLogger("google_genai").setLevel(logging.WARNING)
logging.getLogger("google.ai.generativelanguage").setLevel(logging.WARNING)
logging.getLogger("google.auth").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)

# Updated ADK Imports
from google.adk.sessions import InMemorySessionService, Session as ADKSessionType
from google.adk.runners import Runner
from google.adk.agents.run_config import RunConfig
from google.adk.agents import LiveRequestQueue

if TYPE_CHECKING:
    # Import for type-hinting only to satisfy Pylance
    from google.genai.types import Part as _PartType

try:
    from google.genai.types import Content, Part, Blob
    logger.info("Successfully imported Content, Part, and Blob from google.genai.types.")
except ImportError:
    logger.error("Failed to import Content, Part, and Blob from google.genai.types. This is a critical dependency for ADK streaming examples. Ensure 'google-generativeai' is installed.")
    Content, Part, Blob = None, None, None

# Load environment variables from .env file
dotenv_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path=dotenv_path)
else:
    logger.warning(f".env file not found at: {dotenv_path}. Relying on pre-set environment variables.")

CUSTOMER_SERVICE_AGENT_LOADED = False
customer_service_agent = None
ADK_MODEL_ID = None

logger.info("[DIAG_TIME] Starting agent import block...")
_agent_load_start_time = time.perf_counter()
try:
    from customer_service.agent import root_agent as imported_agent
    from customer_service.config import Config as CustomerServiceConfig

    customer_service_agent = imported_agent
    cfg = CustomerServiceConfig()
    ADK_MODEL_ID = getattr(getattr(cfg, "agent_settings", object()), "model", None)
    if not ADK_MODEL_ID: 
        ADK_MODEL_ID = getattr(cfg, "ADK_MODEL_ID", None)

    if customer_service_agent:
        CUSTOMER_SERVICE_AGENT_LOADED = True
    if not ADK_MODEL_ID:
        ADK_MODEL_ID = "gemini-2.0-flash-exp" 
        logger.warning(f"Agent's Model ID not found in customer_service.config. Using default: {ADK_MODEL_ID} for agent context.")

except ImportError as e:
    logger.error(f"Error importing agent or config from customer_service: {e}", exc_info=True)
    if ADK_MODEL_ID is None: ADK_MODEL_ID = "gemini-2.0-flash-exp"
    logger.warning(f"customer_service_agent or its config not found. Agent will not run. Fallback model: {ADK_MODEL_ID}")
except Exception as e:
    logger.error(f"An unexpected error occurred during agent/config import: {e}", exc_info=True)
    if ADK_MODEL_ID is None: ADK_MODEL_ID = "gemini-2.0-flash-exp"
_agent_load_end_time = time.perf_counter()
logger.info(f"[DIAG_TIME] Agent import block finished. Took: {_agent_load_end_time - _agent_load_start_time:.4f} seconds.")

app = FastAPI()

origins = [
    "http://localhost:5000", "http://127.0.0.1:5000",
    "http://localhost:3000", "http://127.0.0.1:3000",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins, allow_credentials=True,
    allow_methods=["*"], allow_headers=["*"],
)

async def start_agent_session(session_id: str, is_audio: bool):
    _sas_start_time = time.perf_counter()
    logger.info(f"[DIAG_TIME] Enter start_agent_session for session_id: {session_id}, is_audio: {is_audio}")
    if not CUSTOMER_SERVICE_AGENT_LOADED or customer_service_agent is None:
        logger.error(f"[DIAG_LOG] customer_service_agent is not loaded. Cannot start runner for session_id: {session_id}.")
        raise RuntimeError("Customer service agent could not be loaded.")

    session_service = InMemorySessionService()
    app_name_str = "cymbal_home_garden_streaming_chat"
    user_id_str = f"user_{session_id}"
    
    logger.info(f"[DIAG_LOG] Attempting to get/create session for session_id: {session_id}")
    session_obj: ADKSessionType = session_service.get_session(
        app_name=app_name_str, user_id=user_id_str, session_id=session_id
    )
    if not session_obj:
        logger.info(f"[DIAG_LOG] No existing session found for session_id: {session_id}. Creating new one.")
        session_obj = session_service.create_session(
            app_name=app_name_str, user_id=user_id_str, session_id=session_id
        )
        if session_obj:
            logger.info(f"[DIAG_LOG] New session created for session_id: {session_id}, session_obj_id: {id(session_obj)}")
        else:
            logger.error(f"[DIAG_LOG] Critical error: Failed to create session for {session_id}")
            raise RuntimeError(f"Session object is None after creation attempt for {session_id}")
    else:
        logger.info(f"[DIAG_LOG] Existing session retrieved for session_id: {session_id}, session_obj_id: {id(session_obj)}")

    if not session_obj: # Should be redundant due to checks above, but as a safeguard
        logger.error(f"[DIAG_LOG] Critical error: session_obj is None for {session_id} before runner init.")
        raise RuntimeError(f"Session object is None for {session_id}")

    logger.info(f"[DIAG_TIME] Initializing Runner for session_id: {session_id}...")
    _runner_init_start_time = time.perf_counter()
    runner = Runner(agent=customer_service_agent, app_name=app_name_str, session_service=session_service)
    _runner_init_end_time = time.perf_counter()
    logger.info(f"[DIAG_TIME] Runner initialized for session_id: {session_id}. Took: {_runner_init_end_time - _runner_init_start_time:.4f} seconds.")
    live_request_queue = LiveRequestQueue()
    logger.info(f"[DIAG_LOG] Created LiveRequestQueue for session_id: {session_id}, queue_id: {id(live_request_queue)}")
    
    run_config = RunConfig(
        response_modalities=["AUDIO"] if is_audio else ["TEXT"],
    )
    
    logger.info(f"[DIAG_TIME] Calling runner.run_live for session_id: {session_id}, session_obj_id: {id(session_obj)}")
    _run_live_start_time = time.perf_counter()
    live_events = runner.run_live(
        session=session_obj,
        live_request_queue=live_request_queue,
        run_config=run_config,
    )
    _run_live_end_time = time.perf_counter()
    logger.info(f"[DIAG_TIME] runner.run_live completed for session_id: {session_id}. Took: {_run_live_end_time - _run_live_start_time:.4f} seconds. Iterator_id: {id(live_events)}")
    _sas_end_time = time.perf_counter()
    logger.info(f"[DIAG_TIME] Exit start_agent_session for session_id: {session_id}. Total time: {_sas_end_time - _sas_start_time:.4f} seconds.")
    return live_events, live_request_queue

# Rewritten agent_to_client_messaging based on ADK documentation
async def agent_to_client_messaging(ws: WebSocket, events_iter: any, session_id: str):
    logger.info(f"[DIAG_LOG S2C] Start agent_to_client_messaging for session: {session_id}, events_iter_id: {id(events_iter)}")
    _first_agent_event_received_time = None
    _first_meaningful_chunk_sent_time = None
    try:
        async for agent_event in events_iter:
            if _first_agent_event_received_time is None:
                _first_agent_event_received_time = time.perf_counter()
                logger.info(f"[DIAG_TIME S2C {session_id}] First agent_event received. Timestamp: {_first_agent_event_received_time:.4f}")
            event_type_str = f"type: {type(agent_event).__name__}"
            # logger.info(f"[DIAG_LOG S2C {session_id}] Received agent_event ({event_type_str})")

            is_turn_complete = getattr(agent_event, 'turn_complete', False)
            is_interrupted = getattr(agent_event, 'interrupted', False)
            is_interaction_completed = getattr(agent_event, 'interaction_completed', False)

            if is_turn_complete or is_interrupted or is_interaction_completed:
                status_message = {
                    "turn_complete": is_turn_complete,
                    "interrupted": is_interrupted,
                    "interaction_completed": is_interaction_completed,
                }
                logger.info(f"[DIAG_LOG S2C {session_id}] Sending status: {status_message}")
                await ws.send_json(status_message)
                continue
            
            server_content = getattr(agent_event, 'server_content', None) or getattr(agent_event, 'content', None)
            if not server_content:
                logger.info(f"[DIAG_LOG S2C {session_id}] Event has no server_content. Skipping.")
                continue
            
            # --- Start: Preserve existing non-voice command handling ---
            # Check for theme change instruction (Example of preserving custom logic)
            theme_action_details = None
            if isinstance(server_content, dict) and server_content.get("action") == "set_theme":
                theme_action_details = server_content
            elif hasattr(server_content, 'parts') and server_content.parts and \
                 hasattr(server_content.parts[0], 'function_response') and \
                 hasattr(server_content.parts[0].function_response, 'response') and \
                 isinstance(server_content.parts[0].function_response.response, dict) and \
                 server_content.parts[0].function_response.response.get("action") == "set_theme":
                theme_action_details = server_content.parts[0].function_response.response
            
            if theme_action_details:
                theme_value = theme_action_details.get("theme")
                if theme_value:
                    logger.info(f"[DIAG_LOG S2C {session_id}] Handling 'set_theme': {theme_value}")
                    await ws.send_json({"type": "command", "command_name": "set_theme", "payload": {"theme": theme_value}})
                    continue
                else:
                    logger.warning(f"[DIAG_LOG S2C {session_id}] 'set_theme' action missing value.")
                    continue
            
            # Check for cart refresh instruction
            cart_refresh_action = None
            if isinstance(server_content, dict) and server_content.get("action") == "refresh_cart":
                cart_refresh_action = True
            elif hasattr(server_content, 'parts') and server_content.parts and \
                 hasattr(server_content.parts[0], 'function_response') and \
                 hasattr(server_content.parts[0].function_response, 'response') and \
                 isinstance(server_content.parts[0].function_response.response, dict) and \
                 server_content.parts[0].function_response.response.get("action") == "refresh_cart":
                cart_refresh_action = True

            if cart_refresh_action:
                logger.info(f"[DIAG_LOG S2C {session_id}] Handling 'refresh_cart'")
                await ws.send_json({"type": "command", "command_name": "refresh_cart"})
                continue

            # Product recommendations
            product_recommendation_dict = None
            if hasattr(server_content, 'parts') and server_content.parts and \
               hasattr(server_content.parts[0], 'function_response') and \
               hasattr(server_content.parts[0].function_response, 'response') and \
               isinstance(server_content.parts[0].function_response.response, dict) and \
               server_content.parts[0].function_response.response.get("type") == "product_recommendations":
                product_recommendation_dict = server_content.parts[0].function_response.response
            elif isinstance(server_content, dict) and server_content.get("type") == "product_recommendations":
                 product_recommendation_dict = server_content
            
            if product_recommendation_dict:
                logger.info(f"[DIAG_LOG S2C {session_id}] Handling 'product_recommendations'")
                await ws.send_text(json.dumps(product_recommendation_dict)) # Client expects raw JSON string for this
                continue

            # Check for generic ui_command
            # This expects the LLM to output a valid JSON string in part.text
            # if the content is a ui_command.
            
            # New handler for direct tool responses that are UI commands
            direct_ui_command_payload = None
            if hasattr(server_content, 'parts') and server_content.parts and \
               hasattr(server_content.parts[0], 'function_response') and \
               hasattr(server_content.parts[0].function_response, 'response') and \
               isinstance(server_content.parts[0].function_response.response, dict):
                
                tool_response_dict = server_content.parts[0].function_response.response

                # Handle 'show_checkout_ui' action
                if tool_response_dict.get("action") == "show_checkout_ui":
                    cart_data = tool_response_dict.get("cart_data")
                    if cart_data is not None:
                        logger.info(f"[DIAG_LOG S2C {session_id}] Handling 'show_checkout_ui'. Cart data present.")
                        # Ensure agent's speech for this turn is sent before this command.
                        # The current loop structure processes events one by one.
                        # If speech parts came before this tool_response part in the stream for the same agent turn, they'd be sent.
                        # This command is sent when the tool_result event is processed.
                        await ws.send_json({
                            "type": "command",
                            "command_name": "display_checkout_modal",
                            "data": cart_data
                        })
                        logger.info(f"[DIAG_LOG S2C {session_id}] Sent 'display_checkout_modal' command with cart data.")
                        continue # Command handled, move to next agent_event
                    else:
                        logger.warning(f"[DIAG_LOG S2C {session_id}] 'show_checkout_ui' action received, but 'cart_data' is missing or None. Payload: {tool_response_dict}")
                        # Optionally, send an error or a specific message to the client if cart_data is crucial and missing.
                        # For now, just log and continue. The client might need to handle missing cart_data gracefully.
                        continue
                
                # Handle new shipping UI actions
                if tool_response_dict.get("action") == "show_shipping_ui_requested":
                    logger.info(f"[DIAG_LOG S2C {session_id}] Handling 'show_shipping_ui_requested'.")
                    await ws.send_json({
                        "type": "command",
                        "command_name": "display_shipping_modal"
                    })
                    continue

                # Handle new payment UI action
                if tool_response_dict.get("action") == "show_payment_ui_requested":
                    logger.info(f"[DIAG_LOG S2C {session_id}] Handling 'show_payment_ui_requested'.")
                    await ws.send_json({
                        "type": "command",
                        "command_name": "display_payment_modal" # Client will listen for this
                    })
                    continue
                
                action_to_selection_type_map = {
                    "confirm_ui_home_delivery": "home_delivery",
                    "confirm_ui_pickup_initiated": "pickup_initiated",
                    "confirm_ui_pickup_address": "pickup_address"
                }
                tool_action = tool_response_dict.get("action")
                if tool_action in action_to_selection_type_map:
                    selection_type = action_to_selection_type_map[tool_action]
                    command_payload = {
                        "type": "command",
                        "command_name": "agent_confirm_selection",
                        "selection_type": selection_type
                    }
                    if selection_type == "pickup_address":
                        command_payload["address_index"] = tool_response_dict.get("address_index")
                    
                    # Send speech first if present in tool response
                    agent_speech = tool_response_dict.get("speak")
                    if agent_speech:
                        logger.info(f"[DIAG_LOG S2C {session_id}] Sending agent speech for '{tool_action}': '{agent_speech[:70]}...'")
                        await ws.send_json({"mime_type": "text/plain", "data": agent_speech})

                    logger.info(f"[DIAG_LOG S2C {session_id}] Handling '{tool_action}'. Sending command: {command_payload}")
                    await ws.send_json(command_payload)
                    continue

                if tool_response_dict.get("action") == "no_ui_change_needed":
                    agent_speech = tool_response_dict.get("speak")
                    if agent_speech:
                        logger.info(f"[DIAG_LOG S2C {session_id}] Handling 'no_ui_change_needed'. Sending agent speech: '{agent_speech[:70]}...'")
                        await ws.send_json({"mime_type": "text/plain", "data": agent_speech})
                    else:
                        logger.info(f"[DIAG_LOG S2C {session_id}] Handling 'no_ui_change_needed' but no speech provided.")
                    continue
                
                # Handle 'refresh_cart_and_show_confirmation' action from submit_order_and_clear_cart tool
                if tool_response_dict.get("action") == "refresh_cart_and_show_confirmation":
                    logger.info(f"[DIAG_LOG S2C {session_id}] Handling 'refresh_cart_and_show_confirmation'.")
                    # Send agent speech first if available (e.g., "Order submitted successfully!")
                    agent_speech_for_confirmation = tool_response_dict.get("message") # Tool returns message from API
                    order_id_for_confirmation = tool_response_dict.get("order_id")
                    if agent_speech_for_confirmation:
                        logger.info(f"[DIAG_LOG S2C {session_id}] Sending agent speech for order confirmation: '{agent_speech_for_confirmation[:70]}...'")
                        await ws.send_json({"mime_type": "text/plain", "data": agent_speech_for_confirmation})
                    
                    # Send command to UI
                    await ws.send_json({
                        "type": "command",
                        "command_name": "order_confirmed_refresh_cart", # Client will listen for this
                        "data": {"order_id": order_id_for_confirmation, "message": agent_speech_for_confirmation }
                    })
                    logger.info(f"[DIAG_LOG S2C {session_id}] Sent 'order_confirmed_refresh_cart' command.")
                    continue


                if tool_response_dict.get("action") == "display_ui" and "ui_element" in tool_response_dict and "payload" in tool_response_dict:
                    direct_ui_command_payload = {
                        "type": "ui_command", # Standardize the type for client
                        "command_name": tool_response_dict.get("ui_element"),
                        "payload": tool_response_dict.get("payload")
                    }
                    log_command_name = direct_ui_command_payload.get('command_name')
                    logger.info(f"[DIAG_LOG S2C {session_id}] Handling direct 'display_ui' tool response: {log_command_name}")
                    await ws.send_json(direct_ui_command_payload)
                    continue # Command handled

            # ADK Documentation style for content parts (text/audio)
            part: Optional[_PartType] = (
                server_content.parts[0]
                if hasattr(server_content, 'parts') and server_content.parts
                else None
            )
            if not part:
                logger.info(f"[DIAG_LOG S2C {session_id}] No parts in server_content. Skipping.")
                continue

            # Check for generic ui_command using the correctly defined 'part' (e.g. from LLM text output)
            ui_command_details_from_text = None
            if part.text: # Ensure part.text exists before trying to load it
                try:
                    potential_command = json.loads(part.text)
                    if isinstance(potential_command, dict) and potential_command.get("type") == "ui_command":
                        ui_command_details_from_text = potential_command
                except json.JSONDecodeError:
                    # Not a JSON command, or malformed JSON.
                    # It will be handled by the subsequent text/audio block.
                    pass
                except Exception as e:
                    # Catch any other unexpected errors during parsing or checking
                    logger.error(f"[DIAG_LOG S2C {session_id}] Error processing ui_command in part.text: {e}", exc_info=True)

            if ui_command_details_from_text:
                command_name = ui_command_details_from_text.get("command_name", "Unknown UI Command")
                logger.info(f"[DIAG_LOG S2C {session_id}] Handling 'ui_command' from text: {command_name}")
                await ws.send_json(ui_command_details_from_text)
                continue
            
            message_to_send = None
            if part.text:
                message_to_send = {"mime_type": "text/plain", "data": part.text}
                logger.info(f"[DIAG_LOG S2C {session_id}] Sending text: '{part.text[:70]}...'")
            elif part.inline_data and part.inline_data.mime_type == "audio/pcm":
                audio_data = part.inline_data.data
                if audio_data:
                    base64_encoded_audio = base64.b64encode(audio_data).decode("ascii")
                    message_to_send = {"mime_type": "audio/pcm", "data": base64_encoded_audio}
                    # logger.info(f"[DIAG_LOG S2C {session_id}] Sending audio/pcm: {len(audio_data)} bytes raw.")
                else:
                    logger.info(f"[DIAG_LOG S2C {session_id}] Audio part present but data is empty.")
            
            if message_to_send:
                if _first_meaningful_chunk_sent_time is None and (part.text or (part.inline_data and part.inline_data.mime_type == "audio/pcm")):
                    _first_meaningful_chunk_sent_time = time.perf_counter()
                    logger.info(f"[DIAG_TIME S2C {session_id}] Preparing to send first meaningful chunk (text/audio). Timestamp: {_first_meaningful_chunk_sent_time:.4f}")
                    if _first_agent_event_received_time:
                         logger.info(f"[DIAG_TIME S2C {session_id}] Time from first agent event to first meaningful chunk send: {_first_meaningful_chunk_sent_time - _first_agent_event_received_time:.4f} seconds.")

                # DIAGNOSTIC LOG: Log chunks sent from streaming_server.py to WebSocket client (proxy)
                log_data_summary = str(message_to_send)
                if len(log_data_summary) > 150: # Avoid overly long logs for audio data
                    log_data_summary = log_data_summary[:150] + "..."
                # logger.info(f"[DIAG_LOG S2C {session_id}] SENDING CHUNK TO WS CLIENT (PROXY): {log_data_summary}")
                await ws.send_json(message_to_send)
            else:
                logger.info(f"[DIAG_LOG S2C {session_id}] No text or audio/pcm data in part to send.")

    except WebSocketDisconnect:
        logger.info(f"[DIAG_LOG S2C] WebSocket disconnected for session: {session_id}")
    except asyncio.CancelledError:
        logger.info(f"[DIAG_LOG S2C] Task cancelled for session: {session_id}")
    except Exception as e:
        logger.error(f"[DIAG_LOG S2C] Error in agent_to_client_messaging for session {session_id}: {e}", exc_info=True)
    finally:
        logger.info(f"[DIAG_LOG S2C] Agent messaging finished for session: {session_id}")

# Rewritten client_to_agent_messaging based on ADK documentation
async def client_to_agent_messaging(ws: WebSocket, queue_to_agent: LiveRequestQueue, session_id: str):
    logger.info(f"[DIAG_LOG C2S] Start client_to_agent_messaging for session: {session_id}, queue_id: {id(queue_to_agent)}")
    _first_client_message_sent_to_agent_time = None
    try:
        while True:
            raw_client_message = await ws.receive_text()
            # Avoid logging full raw_client_message if it's very long (e.g., audio data)
            log_msg_summary = raw_client_message[:200] + ('...' if len(raw_client_message) > 200 else '')
            logger.debug(f"[DIAG_LOG C2S {session_id}] Received raw message (len: {len(raw_client_message)}): '{log_msg_summary}'") # Changed to debug
            
            try:
                client_message_json = json.loads(raw_client_message)
            except json.JSONDecodeError:
                logger.error(f"[DIAG_LOG C2S {session_id}] Failed to decode JSON from client.", exc_info=True)
                continue

            if "parts" in client_message_json:
                logger.info(f"[DIAG_LOG C2S {session_id}] Processing 'parts' array.")
                parts_for_adk = []
                valid_parts_assembly = True
                client_parts_data = client_message_json.get("parts", [])

                for i, part_data in enumerate(client_parts_data):
                    part_mime_type = part_data.get("mime_type")
                    part_content_data = part_data.get("data")

                    if not part_mime_type or part_content_data is None:
                        logger.warning(f"[DIAG_LOG C2S {session_id}] Invalid part {i} (missing mime_type/data).")
                        valid_parts_assembly = False; break
                    
                    data_len_str = f"len: {len(part_content_data)}" if isinstance(part_content_data, (str, bytes)) else "type: non-str/bytes"
                    logger.info(f"[DIAG_LOG C2S {session_id}] Part {i}: mime='{part_mime_type}', {data_len_str}")

                    if part_mime_type.startswith("image/"):
                        try:
                            decoded_bytes = base64.b64decode(part_content_data)
                            parts_for_adk.append(Part(inline_data=Blob(mime_type=part_mime_type, data=decoded_bytes)))
                        except Exception as e:
                            logger.error(f"[DIAG_LOG C2S {session_id}] Error decoding image part {i}: {e}", exc_info=True)
                            valid_parts_assembly = False; break
                    elif part_mime_type == "text/plain":
                        parts_for_adk.append(Part(text=str(part_content_data)))
                    else:
                        logger.warning(f"[DIAG_LOG C2S {session_id}] Unsupported mime_type '{part_mime_type}' in part {i}.")
                
                if valid_parts_assembly and parts_for_adk:
                    adk_content_obj = Content(role="user", parts=parts_for_adk)
                    if _first_client_message_sent_to_agent_time is None:
                        _first_client_message_sent_to_agent_time = time.perf_counter()
                        logger.info(f"[DIAG_TIME C2S {session_id}] Sending first multi-part message to agent queue. Timestamp: {_first_client_message_sent_to_agent_time:.4f}")
                    logger.info(f"[DIAG_LOG C2S {session_id}] Sending {len(parts_for_adk)} parts to agent queue.")
                    queue_to_agent.send_content(content=adk_content_obj)
                elif not valid_parts_assembly:
                    logger.warning(f"[DIAG_LOG C2S {session_id}] Not sending to agent due to invalid parts.")
                else: # valid_parts_assembly is true, but parts_for_adk is empty
                    logger.warning(f"[DIAG_LOG C2S {session_id}] No processable parts found, nothing to send.")

            elif "mime_type" in client_message_json:
                mime_type = client_message_json.get("mime_type")
                data = client_message_json.get("data")
                logger.debug(f"[DIAG_LOG C2S {session_id}] Fallback: mime_type='{mime_type}', data_len={len(data) if data else 'None'}") # Changed to debug

                if not mime_type or data is None:
                    logger.warning(f"[DIAG_LOG C2S {session_id}] Fallback: Missing mime_type or data.")
                    continue

                if mime_type == "text/plain":
                    text_data = str(data)
                    if text_data == "client_ready":
                        logger.info(f"[DIAG_LOG C2S {session_id}] Received 'client_ready'. Ignoring.")
                        continue
                    content = Content(role="user", parts=[Part.from_text(text=text_data)])
                    if _first_client_message_sent_to_agent_time is None:
                        _first_client_message_sent_to_agent_time = time.perf_counter()
                        logger.info(f"[DIAG_TIME C2S {session_id}] Sending first text (fallback) message to agent queue. Timestamp: {_first_client_message_sent_to_agent_time:.4f}")
                    logger.info(f"[DIAG_LOG C2S {session_id}] Sending text (fallback) to agent: '{text_data[:70]}...'")
                    queue_to_agent.send_content(content=content)
                elif mime_type == "audio/pcm":
                    try:
                        decoded_audio_bytes = base64.b64decode(str(data))
                        # Threshold to filter out very short audio packets (e.g., mic pops)
                        MIN_AUDIO_BYTES_THRESHOLD = 640  # Approx 20ms of 16kHz 16-bit mono audio
                        if len(decoded_audio_bytes) < MIN_AUDIO_BYTES_THRESHOLD:
                            logger.info(f"[DIAG_LOG C2S {session_id}] Audio packet too short ({len(decoded_audio_bytes)} bytes), below threshold ({MIN_AUDIO_BYTES_THRESHOLD} bytes). Skipping send_realtime.")
                            continue
                        if _first_client_message_sent_to_agent_time is None:
                            _first_client_message_sent_to_agent_time = time.perf_counter()
                            logger.info(f"[DIAG_TIME C2S {session_id}] Sending first audio (fallback) message to agent queue. Timestamp: {_first_client_message_sent_to_agent_time:.4f}")
                        logger.debug(f"[DIAG_LOG C2S {session_id}] Sending audio (fallback) to agent: {len(decoded_audio_bytes)} bytes.") # Changed to debug
                        queue_to_agent.send_realtime(Blob(data=decoded_audio_bytes, mime_type="audio/pcm"))
                    except Exception as e:
                        logger.error(f"[DIAG_LOG C2S {session_id}] Error decoding/sending audio (fallback): {e}", exc_info=True)
                        continue
                elif mime_type.startswith("image/"):
                    try:
                        decoded_image_bytes = base64.b64decode(str(data))
                        image_blob = Blob(data=decoded_image_bytes, mime_type=mime_type)
                        content = Content(role="user", parts=[Part(inline_data=image_blob)])
                        if _first_client_message_sent_to_agent_time is None:
                            _first_client_message_sent_to_agent_time = time.perf_counter()
                            logger.info(f"[DIAG_TIME C2S {session_id}] Sending first image (fallback) message to agent queue. Timestamp: {_first_client_message_sent_to_agent_time:.4f}")
                        logger.info(f"[DIAG_LOG C2S {session_id}] Sending image (fallback) to agent: {mime_type}, {len(decoded_image_bytes)} bytes.")
                        queue_to_agent.send_content(content=content)
                    except Exception as e:
                        logger.error(f"[DIAG_LOG C2S {session_id}] Error decoding/sending image (fallback): {e}", exc_info=True)
                        continue
                else:
                    logger.warning(f"[DIAG_LOG C2S {session_id}] Fallback: Unhandled mime_type '{mime_type}'.")
            
            elif client_message_json.get("event_type") == "user_shipping_interaction":
                interaction_data = client_message_json # The whole JSON is the interaction data
                logger.info(f"[DIAG_LOG C2S {session_id}] Processing 'user_shipping_interaction': {interaction_data}")
                # Re-package this as a text message or a structured event for the agent
                # For simplicity, sending as a structured text message that prompts can parse
                # Or, if agent is set up for custom events, use that.
                # Example: "User selected shipping: home_delivery"
                # Example: "User selected pickup address: Cymbal Store Downtown - 123 Main St, Anytown, USA (index 0)"
                interaction_type = interaction_data.get("interaction")
                details = interaction_data.get("details", {})
                
                user_text_for_agent = f"UI_SHIPPING_EVENT: type='{interaction_type}'"
                if details:
                    user_text_for_agent += f", details={json.dumps(details)}"

                logger.info(f"[DIAG_LOG C2S {session_id}] Sending shipping interaction to agent as text: '{user_text_for_agent}'")
                content = Content(role="user", parts=[Part.from_text(text=user_text_for_agent)])
                queue_to_agent.send_content(content=content)
            
            else:
                logger.warning(f"[DIAG_LOG C2S {session_id}] Unknown message structure: {client_message_json}")

    except WebSocketDisconnect:
        logger.info(f"[DIAG_LOG C2S] WebSocket disconnected for session: {session_id}")
    except asyncio.CancelledError:
        logger.info(f"[DIAG_LOG C2S] Task cancelled for session: {session_id}")
    except Exception as e:
        logger.error(f"[DIAG_LOG C2S] Error in client_to_agent_messaging for session {session_id}: {e}", exc_info=True)
    finally:
        logger.info(f"[DIAG_LOG C2S] Client messaging finished for session: {session_id}")


@app.websocket("/ws/agent_stream/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str, is_audio: bool = False):
    _ws_endpoint_start_time = time.perf_counter()
    logger.info(f"[DIAG_TIME] Enter websocket_endpoint for session_id: {session_id}, is_audio: {is_audio}, client: {websocket.client}. Timestamp: {_ws_endpoint_start_time:.4f}")
    
    try:
        await websocket.accept()
        logger.info(f"[DIAG_LOG] WebSocket connection accepted for session_id: {session_id}, is_audio: {is_audio}, client: {websocket.client}")
    except WebSocketDisconnect:
        logger.warning(f"[DIAG_LOG] WebSocket disconnected before/during accept for session_id: {session_id}, client: {websocket.client}")
        return
    except Exception as e:
        logger.error(f"[DIAG_LOG] Error accepting WebSocket for session_id: {session_id}, client: {websocket.client}: {e}", exc_info=True)
        if websocket.client_state != WebSocketState.DISCONNECTED:
            try:
                logger.info(f"[DIAG_LOG] Attempting to close WebSocket due to accept error for session_id: {session_id}")
                await websocket.close(code=1011)
            except Exception as close_e:
                 logger.error(f"[DIAG_LOG] Error closing WebSocket after accept error for session_id: {session_id}: {close_e}", exc_info=True)
        return

    live_events_iterator = None
    agent_send_queue = None
    agent_task = None
    client_task = None
    logger.info(f"[DIAG_LOG] Initialized task variables to None for session_id: {session_id}")

    try:
        logger.info(f"[DIAG_TIME] Attempting to start agent session for session_id: {session_id} from websocket_endpoint.")
        _ws_call_sas_start_time = time.perf_counter()
        live_events_iterator, agent_send_queue = await start_agent_session(session_id, is_audio)
        _ws_call_sas_end_time = time.perf_counter()
        logger.info(f"[DIAG_TIME] Agent session started successfully for session_id: {session_id}. Call took: {_ws_call_sas_end_time - _ws_call_sas_start_time:.4f} seconds. Events_iter_id: {id(live_events_iterator)}, Queue_id: {id(agent_send_queue)}")

        agent_task_name = f"agent_to_client_{session_id}_{id(live_events_iterator)}"
        agent_task = asyncio.create_task(agent_to_client_messaging(websocket, live_events_iterator, session_id))
        agent_task.set_name(agent_task_name)
        logger.info(f"[DIAG_LOG] Created agent_task: {agent_task_name} for session_id: {session_id}")
        
        client_task_name = f"client_to_agent_{session_id}_{id(agent_send_queue)}"
        client_task = asyncio.create_task(client_to_agent_messaging(websocket, agent_send_queue, session_id))
        client_task.set_name(client_task_name)
        logger.info(f"[DIAG_LOG] Created client_task: {client_task_name} for session_id: {session_id}")

        logger.info(f"[DIAG_LOG] Awaiting completion of tasks for session_id: {session_id}: {agent_task_name}, {client_task_name}")
        done, pending = await asyncio.wait(
            [agent_task, client_task],
            return_when=asyncio.FIRST_COMPLETED,
        )
        logger.info(f"[DIAG_LOG] asyncio.wait completed for session_id: {session_id}. Done tasks: {[t.get_name() for t in done]}. Pending tasks: {[t.get_name() for t in pending]}.")

        for task_done in done:
            task_name = task_done.get_name()
            try:
                task_done.result()
                logger.info(f"[DIAG_LOG] Task {task_name} completed normally for session_id: {session_id}.")
            except asyncio.CancelledError:
                 logger.info(f"[DIAG_LOG] Task {task_name} was cancelled for session_id: {session_id}.")
            except WebSocketDisconnect:
                 logger.info(f"[DIAG_LOG] Task {task_name} encountered WebSocketDisconnect for session_id: {session_id}.")
            except Exception as e:
                logger.error(f"[DIAG_LOG] Task {task_name} completed with error for session_id: {session_id}: {e}", exc_info=True)

        for task_pending in pending:
            task_name = task_pending.get_name()
            logger.info(f"[DIAG_LOG] Cancelling pending task: {task_name} for session_id: {session_id}")
            task_pending.cancel()
        
        if pending:
            logger.info(f"[DIAG_LOG] Gathering cancelled pending tasks for session_id: {session_id}")
            await asyncio.gather(*pending, return_exceptions=True)
            logger.info(f"[DIAG_LOG] Finished gathering cancelled pending tasks for session_id: {session_id}")

    except WebSocketDisconnect:
        logger.info(f"[DIAG_LOG] WebSocket disconnected in main endpoint for session_id: {session_id}, client: {websocket.client}")
    except RuntimeError as e:
        logger.error(f"Runtime error in WebSocket endpoint for session {session_id}: {e}", exc_info=True)
        if websocket.client_state != WebSocketState.DISCONNECTED:
            try: await websocket.send_json({"error": str(e), "type": "RuntimeError"})
            except: pass
    except Exception as e: 
        logger.error(f"Unhandled exception in WebSocket endpoint for session {session_id}: {e}", exc_info=True)
        if websocket.client_state != WebSocketState.DISCONNECTED:
            try: await websocket.send_json({"error": "Internal server error.", "type": "ServerError"})
            except: pass
    finally:
        logger.info(f"Cleaning up WebSocket endpoint for session {session_id}...")
        tasks_to_clean = [t for t in [agent_task, client_task] if t and not t.done()]
        for task in tasks_to_clean:
            if not task.done():
                logger.info(f"Final cancellation for task {task.get_name()} in session {session_id}")
                task.cancel()
        if tasks_to_clean:
            await asyncio.gather(*tasks_to_clean, return_exceptions=True)
        
        if agent_send_queue: # ADK LiveRequestQueue doesn't have an explicit close in examples
            logger.debug(f"LiveRequestQueue for session {session_id} cleanup considered (managed by ADK runner).")

        if websocket.client_state != WebSocketState.DISCONNECTED:
            logger.info(f"Closing WebSocket connection from server side for session {session_id}.")
            try:
                await websocket.close(code=1000) 
            except Exception as e_close:
                logger.error(f"Error closing WebSocket for session {session_id} in finally: {e_close}", exc_info=True)
        logger.info(f"WebSocket endpoint for session {session_id} fully cleaned up.")

if __name__ == "__main__":
    import uvicorn
    logger.info("Starting Uvicorn server for streaming_server.py")
    
    if not CUSTOMER_SERVICE_AGENT_LOADED:
        logger.critical("CRITICAL: customer_service_agent could not be loaded.")
    if not ADK_MODEL_ID: 
        logger.warning("Agent's primary Model ID is not set.")
        
    uvicorn.run("streaming_server:app", host="0.0.0.0", port=8001, reload=True)
