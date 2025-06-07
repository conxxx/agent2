
Starting April 29, 2025, Gemini 1.5 Pro and Gemini 1.5 Flash models are not available in projects that have no prior usage of these models, including new projects. For details, see Model versions and lifecycle.

    Generative AI on Vertex AI
    Documentation

Was this helpful?
Live API

Preview

This feature is subject to the "Pre-GA Offerings Terms" in the General Service Terms section of the Service Specific Terms. Pre-GA features are available "as is" and might have limited support. For more information, see the launch stage descriptions.
To try a tutorial that lets you use your voice and camera to talk to Gemini through the Live API, see the websocket-demo-app tutorial.

The Live API enables low-latency bidirectional voice and video interactions with Gemini. Using the Live API, you can provide end users with the experience of natural, human-like voice conversations, and with the ability to interrupt the model's responses using voice commands. The Live API can process text, audio, and video input, and it can provide text and audio output.
Specifications

The Live API features the following technical specifications:

    Inputs: Text, audio, and video
    Outputs: Text and audio (synthesized speech)
    Default session length: 10 minutes
        Session length can be extended in 10 minute increments as needed
    Context window: 32K tokens
    Selection between 8 voices for responses
    Support for responses in 31 languages

Use the Live API
Note: Live API is only available in gemini-2.0-flash-live-preview-04-09, not gemini-2.0-flash.

The following sections provide examples on how to use the Live API's features.

For more information, see the Live API reference guide.
Send text and receive audio
Gen AI SDK for Python

voice_name = "Aoede"  # @param ["Aoede", "Puck", "Charon", "Kore", "Fenrir", "Leda", "Orus", "Zephyr"]

config = LiveConnectConfig(
    response_modalities=["AUDIO"],
    speech_config=SpeechConfig(
        voice_config=VoiceConfig(
            prebuilt_voice_config=PrebuiltVoiceConfig(
                voice_name=voice_name,
            )
        ),
    ),
)

async with client.aio.live.connect(
    model=MODEL_ID,
    config=config,
) as session:
    text_input = "Hello? Gemini are you there?"
    display(Markdown(f"**Input:** {text_input}"))

    await session.send_client_content(
        turns=Content(role="user", parts=[Part(text=text_input)]))

    audio_data = []
    async for message in session.receive():
        if (
            message.server_content.model_turn
            and message.server_content.model_turn.parts
        ):
            for part in message.server_content.model_turn.parts:
                if part.inline_data:
                    audio_data.append(
                        np.frombuffer(part.inline_data.data, dtype=np.int16)
                    )

    if audio_data:
        display(Audio(np.concatenate(audio_data), rate=24000, autoplay=True))
      

Send and receive text
Gen AI SDK for Python
Install

pip install --upgrade google-genai

To learn more, see the SDK reference documentation.

Set environment variables to use the Gen AI SDK with Vertex AI:

# Replace the `GOOGLE_CLOUD_PROJECT` and `GOOGLE_CLOUD_LOCATION` values
# with appropriate values for your project.
export GOOGLE_CLOUD_PROJECT=GOOGLE_CLOUD_PROJECT


export GOOGLE_CLOUD_LOCATION=global


export GOOGLE_GENAI_USE_VERTEXAI=True

from google import genai
from google.genai.types import (
    Content,
    LiveConnectConfig,
    HttpOptions,
    Modality,
    Part,
)

client = genai.Client(http_options=HttpOptions(api_version="v1beta1"))
model_id = "gemini-2.0-flash-live-preview-04-09"

async with client.aio.live.connect(
    model=model_id,
    config=LiveConnectConfig(response_modalities=[Modality.TEXT]),
) as session:
    text_input = "Hello? Gemini, are you there?"
    print("> ", text_input, "\n")
    await session.send_client_content(
        turns=Content(role="user", parts=[Part(text=text_input)])
    )

    response = []

    async for message in session.receive():
        if message.text:
            response.append(message.text)

    print("".join(response))
# Example output:
# >  Hello? Gemini, are you there?
# Yes, I'm here. What would you like to talk about?

Send audio
Gen AI SDK for Python

import asyncio
import wave
from google import genai

client = genai.Client(api_key="GEMINI_API_KEY", http_options={'api_version': 'v1alpha'})
model = "gemini-2.0-flash-live-preview-04-09"

config = {"response_modalities": ["AUDIO"]}

async def main():
    async with client.aio.live.connect(model=model, config=config) as session:
        wf = wave.open("audio.wav", "wb")
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(24000)

        message = "Hello? Gemini are you there?"
        await session.send_client_content(
            turns=Content(role="user", parts=[Part(text=message)]))

        async for idx,response in async_enumerate(session.receive()):
            if response.data is not None:
                wf.writeframes(response.data)

            # Un-comment this code to print audio data info
            # if response.server_content.model_turn is not None:
            #      print(response.server_content.model_turn.parts[0].inline_data.mime_type)

        wf.close()

if __name__ == "__main__":
    asyncio.run(main())
      

Supported audio formats

The Live API supports the following audio formats:

    Input audio format: Raw 16 bit PCM audio at 16kHz little-endian
    Output audio format: Raw 16 bit PCM audio at 24kHz little-endian

Audio transcription

The Live API can transcribe both input and output audio:
Gen AI SDK for Python

# Set model generation_config
CONFIG = {
    'response_modalities': ['AUDIO'],
}

headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {bearer_token[0]}",
}

# Connect to the server
async with connect(SERVICE_URL, additional_headers=headers) as ws:
    # Setup the session
    await ws.send(
        json.dumps(
            {
                "setup": {
                    "model": "gemini-2.0-flash-live-preview-04-09",
                    "generation_config": CONFIG,
                    'input_audio_transcription': {},
                    'output_audio_transcription': {}
                }
            }
        )
    )

    # Receive setup response
    raw_response = await ws.recv(decode=False)
    setup_response = json.loads(raw_response.decode("ascii"))

    # Send text message
    text_input = "Hello? Gemini are you there?"
    display(Markdown(f"**Input:** {text_input}"))

    msg = {
        "client_content": {
            "turns": [{"role": "user", "parts": [{"text": text_input}]}],
            "turn_complete": True,
        }
    }

    await ws.send(json.dumps(msg))

    responses = []
    input_transcriptions = []
    output_transcriptions = []

    # Receive chucks of server response
    async for raw_response in ws:
        response = json.loads(raw_response.decode())
        server_content = response.pop("serverContent", None)
        if server_content is None:
            break

        if (input_transcription := server_content.get("inputTranscription")) is not None:
            if (text := input_transcription.get("text")) is not None:
                input_transcriptions.append(text)
        if (output_transcription := server_content.get("outputTranscription")) is not None:
            if (text := output_transcription.get("text")) is not None:
                output_transcriptions.append(text)

        model_turn = server_content.pop("modelTurn", None)
        if model_turn is not None:
            parts = model_turn.pop("parts", None)
            if parts is not None:
                for part in parts:
                    pcm_data = base64.b64decode(part["inlineData"]["data"])
                    responses.append(np.frombuffer(pcm_data, dtype=np.int16))

        # End of turn
        turn_complete = server_content.pop("turnComplete", None)
        if turn_complete:
            break

    if input_transcriptions:
        display(Markdown(f"**Input transcription >** {''.join(input_transcriptions)}"))

    if responses:
        # Play the returned audio message
        display(Audio(np.concatenate(responses), rate=24000, autoplay=True))

    if output_transcriptions:
        display(Markdown(f"**Output transcription >** {''.join(output_transcriptions)}"))
      

Change voice and language settings

The Live API uses Chirp 3 to support synthesized speech responses in 8 HD voices and 31 languages.

You can select between the following voices:

    Aoede (female)
    Charon (male)
    Fenrir (male)
    Kore (female)
    Leda (female)
    Orus (male)
    Puck (male)
    Zephyr (female)

For demos of what these voices sound like and for the full list of available languages, see Chirp 3: HD voices.

To set the response voice and language:
Gen AI SDK for Python
Console

config = LiveConnectConfig(
    response_modalities=["AUDIO"],
    speech_config=SpeechConfig(
        voice_config=VoiceConfig(
            prebuilt_voice_config=PrebuiltVoiceConfig(
                voice_name=voice_name,
            )
        ),
        language_code="en-US",
    ),
)
      

For the best results when prompting and requiring the model to respond in a non-English language, include the following as part of your system instructions:

RESPOND IN LANGUAGE

. YOU MUST RESPOND UNMISTAKABLY IN LANGUAGE

.

Have a streamed conversation
Gen AI SDK for Python
Console

Set up a conversation with the API that lets you send text prompts and receive audio responses:

# Set model generation_config
CONFIG = {"response_modalities": ["AUDIO"]}

headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {bearer_token[0]}",
}

async def main() -> None:
    # Connect to the server
    async with connect(SERVICE_URL, additional_headers=headers) as ws:

        # Setup the session
        async def setup() -> None:
            await ws.send(
                json.dumps(
                    {
                        "setup": {
                            "model": "gemini-2.0-flash-live-preview-04-09",
                            "generation_config": CONFIG,
                        }
                    }
                )
            )

            # Receive setup response
            raw_response = await ws.recv(decode=False)
            setup_response = json.loads(raw_response.decode("ascii"))
            print(f"Connected: {setup_response}")
            return

        # Send text message
        async def send() -> bool:
            text_input = input("Input > ")
            if text_input.lower() in ("q", "quit", "exit"):
                return False

            msg = {
                "client_content": {
                    "turns": [{"role": "user", "parts": [{"text": text_input}]}],
                    "turn_complete": True,
                }
            }

            await ws.send(json.dumps(msg))
            return True

        # Receive server response
        async def receive() -> None:
            responses = []

            # Receive chucks of server response
            async for raw_response in ws:
                response = json.loads(raw_response.decode())
                server_content = response.pop("serverContent", None)
                if server_content is None:
                    break

                model_turn = server_content.pop("modelTurn", None)
                if model_turn is not None:
                    parts = model_turn.pop("parts", None)
                    if parts is not None:
                        for part in parts:
                            pcm_data = base64.b64decode(part["inlineData"]["data"])
                            responses.append(np.frombuffer(pcm_data, dtype=np.int16))

                # End of turn
                turn_complete = server_content.pop("turnComplete", None)
                if turn_complete:
                    break

            # Play the returned audio message
            display(Markdown("**Response >**"))
            display(Audio(np.concatenate(responses), rate=24000, autoplay=True))
            return

        await setup()

        while True:
            if not await send():
                break
            await receive()
      

Start the conversation, input your prompts, or type q, quit or exit to exit.

await main()
      

Session length

The default maximum length of a conversation session is 10 minutes. A go_away notification (BidiGenerateContentServerMessage.go_away) will be sent back to the client 60 seconds before the session ends.

When using the API, you can extend the length of your session by 10 minute increments. There is no limit on how many times you can extend a session. For an example of how to extend your session length, see Enable and disable session resumption. This feature is currently only available in the API, not in Vertex AI Studio.
Context window

The maximum context length for a session in the Live API is 32,768 tokens by default, which are allocated to store realtime data that is streamed in at a rate of 25 tokens per second (TPS) for audio and 258 TPS for video, and other contents including text based inputs, model outputs, etc.

If the context window exceeds the maximum context length, the contexts of the oldest turns from context window will be truncated, so that the overall context window size is below the limitation.

The default context length of the session, and the target context length after the truncation, can be configured using context_window_compression.trigger_tokens and context_window_compression.sliding_window.target_tokens field of the setup message respectively.
Concurrent sessions

By default, you can have up to 10 concurrent sessions per project.
Update the system instructions mid-session

The Live API lets you update the system instructions in the middle of an active session. You can use this to adapt the model's responses mid-session, such as changing the language the model responds in to another language or modify the tone you want the model to respond with.
Change voice activity detection settings

By default, the model automatically performs voice activity detection (VAD) on a continuous audio input stream. VAD can be configured with the realtimeInputConfig.automaticActivityDetection field of the setup message.

When the audio stream is paused for more than a second (for example, because the user switched off the microphone), an audioStreamEnd event should be sent to flush any cached audio. The client can resume sending audio data at any time.

Alternatively, the automatic VAD can be disabled by setting realtimeInputConfig.automaticActivityDetection.disabled to true in the setup message. In this configuration the client is responsible for detecting user speech and sending activityStart and activityEnd messages at the appropriate times. An audioStreamEnd isn't sent in this configuration. Instead, any interruption of the stream is marked by an activityEnd message.
Enable and disable session resumption

This feature is disabled by default. It must be enabled by the user every time they call the API by specifying the field in the API request, and project-level privacy is enforced for cached data. Enabling Session Resumption allows the user to reconnect to a previous session within 24 hours by storing cached data, including text, video, and audio prompt data and model outputs, for up to 24 hours. To achieve zero data retention, do not enable this feature.

To enable the session resumption feature, set the session_resumption field of the BidiGenerateContentSetup message. If enabled, the server will periodically take a snapshot of the current cached session contexts, and store it in the internal storage. When a snapshot is successfully taken, a resumption_update will be returned with the handle ID that you can record and use later to resume the session from the snapshot.

Here's an example of enabling session resumption feature, and collect the handle ID information:
Gen AI SDK for Python

# Set model generation_config
CONFIG = {"response_modalities": ["TEXT"]}

headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {bearer_token[0]}",
}

# Connect to the server
async with connect(SERVICE_URL, additional_headers=headers) as ws:
    # Setup the session
    await ws.send(
        json.dumps(
            {
                "setup": {
                    "model": "gemini-2.0-flash-live-preview-04-09",
                    "generation_config": CONFIG,
                    # Enable session resumption.
                    "session_resumption": {},
                }
            }
        )
    )

    # Receive setup response
    raw_response = await ws.recv(decode=False)
    setup_response = json.loads(raw_response.decode("ascii"))

    # Send text message
    text_input = "Hello? Gemini are you there?"
    display(Markdown(f"**Input:** {text_input}"))

    msg = {
        "client_content": {
            "turns": [{"role": "user", "parts": [{"text": text_input}]}],
            "turn_complete": True,
        }
    }

    await ws.send(json.dumps(msg))

    responses = []
    handle_id = ""

    turn_completed = False
    resumption_received = False

    # Receive chucks of server response,
    # wait for turn completion and resumption handle.
    async for raw_response in ws:
        response = json.loads(raw_response.decode())

        server_content = response.pop("serverContent", None)
        resumption_update = response.pop("sessionResumptionUpdate", None)

        if server_content is not None:
          model_turn = server_content.pop("modelTurn", None)
          if model_turn is not None:
              parts = model_turn.pop("parts", None)
              if parts is not None:
                  responses.append(parts[0]["text"])

          # End of turn
          turn_complete = server_content.pop("turnComplete", None)
          if turn_complete:
            turn_completed = True

        elif resumption_update is not None:
          handle_id = resumption_update['newHandle']
          resumption_received = True
        else:
          continue

        if turn_complete and resumption_received:
          break

    # Print the server response
    display(Markdown(f"**Response >** {''.join(responses)}"))
    display(Markdown(f"**Session Handle ID >** {handle_id}"))
      

If you want to resume the previous session, you can set the handle field of the setup.session_resumption configuration to the previously recorded handle ID:
Gen AI SDK for Python

# Set model generation_config
CONFIG = {"response_modalities": ["TEXT"]}

headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {bearer_token[0]}",
}

# Connect to the server
async with connect(SERVICE_URL, additional_headers=headers) as ws:
    # Setup the session
    await ws.send(
        json.dumps(
            {
                "setup": {
                    "model": "gemini-2.0-flash-live-preview-04-09",
                    "generation_config": CONFIG,
                    # Enable session resumption.
                    "session_resumption": {
                        "handle": handle_id,
                    },
                }
            }
        )
    )

    # Receive setup response
    raw_response = await ws.recv(decode=False)
    setup_response = json.loads(raw_response.decode("ascii"))

    # Send text message
    text_input = "What was the last question I asked?"
    display(Markdown(f"**Input:** {text_input}"))

    msg = {
        "client_content": {
            "turns": [{"role": "user", "parts": [{"text": text_input}]}],
            "turn_complete": True,
        }
    }

    await ws.send(json.dumps(msg))

    responses = []
    handle_id = ""

    turn_completed = False
    resumption_received = False

    # Receive chucks of server response,
    # wait for turn completion and resumption handle.
    async for raw_response in ws:
        response = json.loads(raw_response.decode())

        server_content = response.pop("serverContent", None)
        resumption_update = response.pop("sessionResumptionUpdate", None)

        if server_content is not None:
          model_turn = server_content.pop("modelTurn", None)
          if model_turn is not None:
              parts = model_turn.pop("parts", None)
              if parts is not None:
                  responses.append(parts[0]["text"])

          # End of turn
          turn_complete = server_content.pop("turnComplete", None)
          if turn_complete:
            turn_completed = True

        elif resumption_update is not None:
          handle_id = resumption_update['newHandle']
          resumption_received = True
        else:
          continue

        if turn_complete and resumption_received:
          break

    # Print the server response
    # Expected answer: "You just asked if I was there."
    display(Markdown(f"**Response >** {''.join(responses)}"))
    display(Markdown(f"**Session Handle >** {resumption_update}"))
      

If you want to achieve seamless session resumption, you can enable transparent mode:
Gen AI SDK for Python

await ws.send(
        json.dumps(
            {
                "setup": {
                    "model": "gemini-2.0-flash-live-preview-04-09",
                    "generation_config": CONFIG,
                    # Enable session resumption.
                    "session_resumption": {
                        "transparent": True,
                    },
                }
            }
        )
    )
      

After the transparent mode is enabled, the index of the client message that corresponds with the context snapshot is explicitly returned. This helps identify which client message you need to send again, when you resume the session from the resumption handle.
Use function calling

You can use function calling to create a description of a function, then pass that description to the model in a request. The response from the model includes the name of a function that matches the description and the arguments to call it with.

All functions must be declared at the start of the session by sending tool definitions as part of the setup message.
Gen AI SDK for Python

# Set model generation_config
CONFIG = {"response_modalities": ["TEXT"]}

# Define function declarations
TOOLS = {
    "function_declarations": {
        "name": "get_current_weather",
        "description": "Get the current weather in the given location",
        "parameters": {
            "type": "OBJECT",
            "properties": {"location": {"type": "STRING"}},
        },
    }
}

headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {bearer_token[0]}",
}

# Connect to the server
async with connect(SERVICE_URL, additional_headers=headers) as ws:
    # Setup the session
    await ws.send(
        json.dumps(
            {
                "setup": {
                    "model": "gemini-2.0-flash-live-preview-04-09",
                    "generation_config": CONFIG,
                    "tools": TOOLS,
                }
            }
        )
    )

    # Receive setup response
    raw_response = await ws.recv(decode=False)
    setup_response = json.loads(raw_response.decode())

    # Send text message
    text_input = "Get the current weather in Santa Clara, San Jose and Mountain View"
    display(Markdown(f"**Input:** {text_input}"))

    msg = {
        "client_content": {
            "turns": [{"role": "user", "parts": [{"text": text_input}]}],
            "turn_complete": True,
        }
    }

    await ws.send(json.dumps(msg))

    responses = []

    # Receive chucks of server response
    async for raw_response in ws:
        response = json.loads(raw_response.decode("UTF-8"))

        if (tool_call := response.get("toolCall")) is not None:
            for function_call in tool_call["functionCalls"]:
                responses.append(f"FunctionCall: {str(function_call)}\n")

        if (server_content := response.get("serverContent")) is not None:
            if server_content.get("turnComplete", True):
                break

    # Print the server response
    display(Markdown("**Response >** {}".format("\n".join(responses))))
      

Use code execution

You can use code execution with the Live API to generate and execute Python code directly.
Gen AI SDK for Python

# Set model generation_config
CONFIG = {"response_modalities": ["TEXT"]}

# Set code execution
TOOLS = {"code_execution": {}}

headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {bearer_token[0]}",
}

# Connect to the server
async with connect(SERVICE_URL, additional_headers=headers) as ws:
    # Setup the session
    await ws.send(
        json.dumps(
            {
                "setup": {
                    "model": "gemini-2.0-flash-live-preview-04-09",
                    "generation_config": CONFIG,
                    "tools": TOOLS,
                }
            }
        )
    )

    # Receive setup response
    raw_response = await ws.recv(decode=False)
    setup_response = json.loads(raw_response.decode())

    # Send text message
    text_input = "Write code to calculate the 15th fibonacci number then find the nearest palindrome to it"
    display(Markdown(f"**Input:** {text_input}"))

    msg = {
        "client_content": {
            "turns": [{"role": "user", "parts": [{"text": text_input}]}],
            "turn_complete": True,
        }
    }

    await ws.send(json.dumps(msg))

    responses = []

    # Receive chucks of server response
    async for raw_response in ws:
        response = json.loads(raw_response.decode("UTF-8"))

        if (server_content := response.get("serverContent")) is not None:
            if (model_turn:= server_content.get("modelTurn")) is not None:
              if (parts := model_turn.get("parts")) is not None:
                if parts[0].get("text"):
                    responses.append(parts[0]["text"])
                for part in parts:
                    if (executable_code := part.get("executableCode")) is not None:
                        display(
                            Markdown(
                                f"""**Executable code:**
```py
{executable_code.get("code")}
```
                            """
                            )
                        )
            if server_content.get("turnComplete", False):
                break

    # Print the server response
    display(Markdown(f"**Response >** {''.join(responses)}"))
      

Use Grounding with Google Search

You can use Grounding with Google Search with the Live API using google_search:
Gen AI SDK for Python

# Set model generation_config
CONFIG = {"response_modalities": ["TEXT"]}

# Set google search
TOOLS = {"google_search": {}}

headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {bearer_token[0]}",
}

# Connect to the server
async with connect(SERVICE_URL, additional_headers=headers) as ws:
    # Setup the session
    await ws.send(
        json.dumps(
            {
                "setup": {
                    "model": "gemini-2.0-flash-live-preview-04-09",
                    "generation_config": CONFIG,
                    "tools": TOOLS,
                }
            }
        )
    )

    # Receive setup response
    raw_response = await ws.recv(decode=False)
    setup_response = json.loads(raw_response.decode())

    # Send text message
    text_input = "What is the current weather in San Jose, CA?"
    display(Markdown(f"**Input:** {text_input}"))

    msg = {
        "client_content": {
            "turns": [{"role": "user", "parts": [{"text": text_input}]}],
            "turn_complete": True,
        }
    }

    await ws.send(json.dumps(msg))

    responses = []

    # Receive chucks of server response
    async for raw_response in ws:
        response = json.loads(raw_response.decode())
        server_content = response.pop("serverContent", None)
        if server_content is None:
            break

        model_turn = server_content.pop("modelTurn", None)
        if model_turn is not None:
            parts = model_turn.pop("parts", None)
            if parts is not None:
                responses.append(parts[0]["text"])

        # End of turn
        turn_complete = server_content.pop("turnComplete", None)
        if turn_complete:
            break

    # Print the server response
    display(Markdown("**Response >** {}".format("\n".join(responses))))
      
      ADK Streaming Quickstart¶

With this quickstart, you'll learn to create a simple agent and use ADK Streaming to enable voice and video communication with it that is low-latency and bidirectional. We will install ADK, set up a basic "Google Search" agent, try running the agent with Streaming with adk web tool, and then explain how to build a simple asynchronous web app by yourself using ADK Streaming and FastAPI.

Note: This guide assumes you have experience using a terminal in Windows, Mac, and Linux environments.
Supported models for voice/video streaming¶

In order to use voice/video streaming in ADK, you will need to use Gemini models that support the Live API. You can find the model ID(s) that supports the Gemini Live API in the documentation:

    Google AI Studio: Gemini Live API
    Vertex AI: Gemini Live API

1. Setup Environment & Install ADK¶

Create & Activate Virtual Environment (Recommended):

# Create
python -m venv .venv
# Activate (each new terminal)
# macOS/Linux: source .venv/bin/activate
# Windows CMD: .venv\Scripts\activate.bat
# Windows PowerShell: .venv\Scripts\Activate.ps1

Install ADK:

pip install google-adk

2. Project Structure¶

Create the following folder structure with empty files:

adk-streaming/  # Project folder
└── app/ # the web app folder
    ├── .env # Gemini API key
    └── google_search_agent/ # Agent folder
        ├── __init__.py # Python package
        └── agent.py # Agent definition

agent.py¶

Copy-paste the following code block to the agent.py.

For model, please double check the model ID as described earlier in the Models section.

from google.adk.agents import Agent
from google.adk.tools import google_search  # Import the tool

root_agent = Agent(
   # A unique name for the agent.
   name="basic_search_agent",
   # The Large Language Model (LLM) that agent will use.
   model="gemini-2.0-flash-exp",
   # model="gemini-2.0-flash-live-001",  # New streaming model version as of Feb 2025
   # A short description of the agent's purpose.
   description="Agent to answer questions using Google Search.",
   # Instructions to set the agent's behavior.
   instruction="You are an expert researcher. You always stick to the facts.",
   # Add google_search tool to perform grounding with Google search.
   tools=[google_search]
)

Note: To enable both text and audio/video input, the model must support the generateContent (for text) and bidiGenerateContent methods. Verify these capabilities by referring to the List Models Documentation. This quickstart utilizes the gemini-2.0-flash-exp model for demonstration purposes.

agent.py is where all your agent(s)' logic will be stored, and you must have a root_agent defined.

Notice how easily you integrated grounding with Google Search capabilities. The Agent class and the google_search tool handle the complex interactions with the LLM and grounding with the search API, allowing you to focus on the agent's purpose and behavior.

intro_components.png

Copy-paste the following code block to __init__.py and main.py files.
__init__.py

from . import agent

3. Set up the platform¶

To run the agent, choose a platform from either Google AI Studio or Google Cloud Vertex AI:
Gemini - Google AI Studio
Gemini - Google Cloud Vertex AI

    Get an API key from Google AI Studio.

    Open the .env file located inside (app/) and copy-paste the following code.
    .env

    GOOGLE_GENAI_USE_VERTEXAI=FALSE
    GOOGLE_API_KEY=PASTE_YOUR_ACTUAL_API_KEY_HERE

    Replace PASTE_YOUR_ACTUAL_API_KEY_HERE with your actual API KEY.

4. Try the agent with adk web¶

Now it's ready to try the agent. Run the following command to launch the dev UI. First, make sure to set the current directory to app:

cd app

Also, set SSL_CERT_FILE variable with the following command. This is required for the voice and video tests later.

export SSL_CERT_FILE=$(python -m certifi)

Then, run the dev UI:

adk web

Open the URL provided (usually http://localhost:8000 or http://127.0.0.1:8000) directly in your browser. This connection stays entirely on your local machine. Select google_search_agent.
Try with text¶

Try the following prompts by typing them in the UI.

    What is the weather in New York?
    What is the time in New York?
    What is the weather in Paris?
    What is the time in Paris?

The agent will use the google_search tool to get the latest information to answer those questions.
Try with voice and video¶

To try with voice, reload the web browser, click the microphone button to enable the voice input, and ask the same question in voice. You will hear the answer in voice in real-time.

To try with video, reload the web browser, click the camera button to enable the video input, and ask questions like "What do you see?". The agent will answer what they see in the video input.
Stop the tool¶

Stop adk web by pressing Ctrl-C on the console.
Note on ADK Streaming¶

The following features will be supported in the future versions of the ADK Streaming: Callback, LongRunningTool, ExampleTool, and Shell agent (e.g. SequentialAgent).

Congratulations! You've successfully created and interacted with your first Streaming agent using ADK!
Next steps: build custom streaming app¶

In Custom Audio Streaming app tutorial, it overviews the server and client code for a custom asynchronous web app built with ADK Streaming and FastAPI, enabling real-time, bidirectional audio and text communication.