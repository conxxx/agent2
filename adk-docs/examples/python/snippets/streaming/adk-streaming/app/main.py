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

import os
import json
import asyncio
import base64
import logging # Added
from websockets.exceptions import ConnectionClosedOK, ConnectionClosedError # Added

from pathlib import Path
from dotenv import load_dotenv

from google.genai.types import (
    Part,
    Content,
    Blob,
)

from google.adk.runners import Runner
from google.adk.agents import LiveRequestQueue
from google.adk.agents.run_config import RunConfig
from google.adk.sessions.in_memory_session_service import InMemorySessionService

from fastapi import FastAPI, WebSocket
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from google_search_agent.agent import root_agent

#
# ADK Streaming
#

# Load Gemini API Key
load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO) # Or use DEBUG if preferred / controlled by env var

APP_NAME = "ADK Streaming example"
session_service = InMemorySessionService()


def start_agent_session(session_id, is_audio=False):
    """Starts an agent session"""

    # Create a Session
    session = session_service.create_session(
        app_name=APP_NAME,
        user_id=session_id,
        session_id=session_id,
    )

    # Create a Runner
    runner = Runner(
        app_name=APP_NAME,
        agent=root_agent,
        session_service=session_service,
    )

    # Set response modality
    modality = "AUDIO" if is_audio else "TEXT"
    run_config = RunConfig(response_modalities=[modality])

    # Create a LiveRequestQueue for this session
    live_request_queue = LiveRequestQueue()

    # Start agent session
    live_events = runner.run_live(
        session=session,
        live_request_queue=live_request_queue,
        run_config=run_config,
    )
    return live_events, live_request_queue


async def agent_to_client_messaging(websocket: WebSocket, live_events):
    """Agent to client communication"""
    session_id_for_log = websocket.path_params.get('session_id', 'unknown_session')
    try:
        while True:
            async for event in live_events:
                message = None
                # If the turn complete or interrupted, send it
                if event.turn_complete or event.interrupted:
                    message = {
                        "turn_complete": event.turn_complete,
                        "interrupted": event.interrupted,
                    }
                else:
                    # Read the Content and its first Part
                    part: Part = (
                        event.content and event.content.parts and event.content.parts[0]
                    )
                    if not part:
                        continue

                    # If it's audio, send Base64 encoded audio data
                    is_audio_part = part.inline_data and part.inline_data.mime_type.startswith("audio/pcm")
                    if is_audio_part:
                        audio_data = part.inline_data and part.inline_data.data
                        if audio_data:
                            message = {
                                "mime_type": "audio/pcm",
                                "data": base64.b64encode(audio_data).decode("ascii")
                            }
                    # If it's text and a partial text, send it
                    elif part.text and event.partial:
                        message = {
                            "mime_type": "text/plain",
                            "data": part.text
                        }
                    # Check for potential setupComplete message structure (heuristic)
                    # ADK might send it as a simple dict before other events or as part of an event.
                    # This is a guess based on the log `b'{\n  "setupComplete": {}\n}\n'`
                    elif isinstance(event, dict) and "setupComplete" in event:
                        message = event # Assuming event itself is the setupComplete message
                    
                if message:
                    logger.info(f"[ADK_SERVER_DEBUG] Preparing to send message to client #{session_id_for_log}: {message}")
                    if "setupComplete" in message:
                         logger.info(f"[ADK_SERVER_DEBUG] Explicitly sending 'setupComplete' like message to client #{session_id_for_log}: {message}")
                    
                    serialized_message = json.dumps(message)
                    try:
                        await websocket.send_text(serialized_message)
                        logger.info(f"[ADK_SERVER_DEBUG] Successfully sent message to client #{session_id_for_log}: {serialized_message}")
                    except (ConnectionClosedOK, ConnectionClosedError) as e:
                        logger.warning(f"[ADK_SERVER_DEBUG] WebSocket connection closed while sending to client #{session_id_for_log}: {e}")
                        return # Exit loop if connection is closed
                    except Exception as e:
                        logger.error(f"[ADK_SERVER_DEBUG] Error sending message to client #{session_id_for_log}: {e}. Message: {serialized_message}")
                        # Optionally re-raise or handle
                        return # Exit loop on other send errors

    except Exception as e:
        logger.error(f"[ADK_SERVER_DEBUG] Error in agent_to_client_messaging for session #{session_id_for_log}: {e}")
    finally:
        logger.info(f"[ADK_SERVER_DEBUG] agent_to_client_messaging loop ended for session #{session_id_for_log}")


async def client_to_agent_messaging(websocket: WebSocket, live_request_queue):
    """Client to agent communication"""
    session_id_for_log = websocket.path_params.get('session_id', 'unknown_session')
    try:
        while True:
            message_json = None
            try:
                message_json = await websocket.receive_text()
                logger.info(f"[ADK_SERVER_DEBUG] Received raw message from client #{session_id_for_log}: {message_json}")
            except (ConnectionClosedOK, ConnectionClosedError) as e:
                logger.warning(f"[ADK_SERVER_DEBUG] WebSocket connection closed by client #{session_id_for_log} while receiving: {e}")
                return # Exit loop if connection is closed
            except Exception as e:
                logger.error(f"[ADK_SERVER_DEBUG] Error receiving message from client #{session_id_for_log}: {e}")
                # Optionally re-raise or handle
                return # Exit loop on other receive errors

            try:
                message = json.loads(message_json)
                logger.info(f"[ADK_SERVER_DEBUG] Parsed message from client #{session_id_for_log}: {message}")
            except json.JSONDecodeError as e:
                logger.error(f"[ADK_SERVER_DEBUG] JSONDecodeError for message from client #{session_id_for_log}: {e}. Raw: {message_json}")
                continue # Skip malformed message

            mime_type = message.get("mime_type")
            data = message.get("data")

            if mime_type == "text/plain":
                content = Content(role="user", parts=[Part.from_text(text=data)])
                live_request_queue.send_content(content=content)
                logger.info(f"[ADK_SERVER_DEBUG] Relayed text message to agent for session #{session_id_for_log}: {data}")
            elif mime_type == "audio/pcm":
                decoded_data = base64.b64decode(data)
                live_request_queue.send_realtime(Blob(data=decoded_data, mime_type=mime_type))
                logger.info(f"[ADK_SERVER_DEBUG] Relayed audio/pcm message to agent for session #{session_id_for_log}, {len(decoded_data)} bytes")
            else:
                logger.warning(f"[ADK_SERVER_DEBUG] Mime type not supported for client message in session #{session_id_for_log}: {mime_type}. Message: {message}")
                # raise ValueError(f"Mime type not supported: {mime_type}") # Or just log and continue
    except Exception as e:
        logger.error(f"[ADK_SERVER_DEBUG] Error in client_to_agent_messaging for session #{session_id_for_log}: {e}")
    finally:
        logger.info(f"[ADK_SERVER_DEBUG] client_to_agent_messaging loop ended for session #{session_id_for_log}")


#
# FastAPI web app
#

app = FastAPI()

STATIC_DIR = Path("static")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/")
async def root():
    """Serves the index.html"""
    return FileResponse(os.path.join(STATIC_DIR, "index.html"))


@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: int, is_audio: str):
    """Client websocket endpoint"""

    # Wait for client connection
    try:
        await websocket.accept()
        logger.info(f"[ADK_SERVER_DEBUG] WebSocket connection accepted from {websocket.client.host}:{websocket.client.port} for session {session_id}, audio: {is_audio}")
    except Exception as e:
        logger.error(f"[ADK_SERVER_DEBUG] Error accepting WebSocket connection for session {session_id}: {e}")
        return

    session_id_str = str(session_id)
    logger.info(f"[ADK_SERVER_DEBUG] Starting agent session for client #{session_id_str}, audio mode: {is_audio}")
    
    try:
        live_events, live_request_queue = start_agent_session(session_id_str, is_audio == "true")

        # Log before constructing setupComplete (implicitly, this is where ADK starts its internal setup)
        logger.info(f"[ADK_SERVER_DEBUG] ADK runner.run_live called for session #{session_id_str}, setup process initiated.")

        agent_to_client_task = asyncio.create_task(
            agent_to_client_messaging(websocket, live_events)
        )
        client_to_agent_task = asyncio.create_task(
            client_to_agent_messaging(websocket, live_request_queue)
        )
        
        # Wait for both tasks to complete
        done, pending = await asyncio.wait(
            [agent_to_client_task, client_to_agent_task],
            return_when=asyncio.FIRST_COMPLETED,
        )

        for task in pending:
            task.cancel()
        
        # Ensure all tasks are awaited to prevent RuntimeWarning
        await asyncio.gather(*done, *pending, return_exceptions=True)

    except Exception as e:
        logger.error(f"[ADK_SERVER_DEBUG] Error during WebSocket session for client #{session_id_str}: {e}", exc_info=True)
    finally:
        logger.info(f"[ADK_SERVER_DEBUG] Client #{session_id_str} disconnected or session ended.")
        # Ensure WebSocket is closed if not already
        if websocket.client_state != websocket.client_state.CLOSED:
            try:
                await websocket.close()
                logger.info(f"[ADK_SERVER_DEBUG] WebSocket connection explicitly closed for session #{session_id_str}.")
            except Exception as e:
                logger.error(f"[ADK_SERVER_DEBUG] Error closing WebSocket for session #{session_id_str}: {e}")
