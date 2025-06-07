import { startAudioPlayerWorklet, startAudioRecorderWorklet, stopMicrophone, pauseMicrophoneInput, resumeMicrophoneInput } from './js/audio-modules.js';

document.addEventListener('DOMContentLoaded', () => {
    const agentWidget = document.querySelector('.agent-widget'); 
    if (!agentWidget) {
        console.error("Agent widget root (.agent-widget) not found.");
        return;
    }
    
    const videoDisplayContainer = agentWidget.querySelector('.video-display-container');
    const textChatContainer = agentWidget.querySelector('.text-chat-container');
    const messageArea = agentWidget.querySelector('.message-area');
    const chatInput = agentWidget.querySelector('.chat-input');

    const micIcon = agentWidget.querySelector('.mic-icon');
    const videoToggleButton = agentWidget.querySelector('.video-toggle-btn');
    const chatIcon = agentWidget.querySelector('.chat-icon');
    const endCallButton = agentWidget.querySelector('.end-call-icon');
    const closeButton = agentWidget.querySelector('.close-btn');
    const minimizeButton = agentWidget.querySelector('.minimize-btn');
    const imageOptionsToggleBtn = agentWidget.querySelector('.image-options-toggle-btn');
    const imageOptionsPopup = agentWidget.querySelector('.image-options-popup');
    const cameraBtn = agentWidget.querySelector('.camera-btn');
    const uploadLocalBtn = agentWidget.querySelector('.upload-local-btn');
    const imageUploadInput = document.getElementById('imageUploadInput');

    // Camera View Elements (for Phase 2)
    const cameraViewContainer = agentWidget.querySelector('.camera-view-container');
    const cameraFeed = document.getElementById('cameraFeed');
    const photoCanvas = document.getElementById('photoCanvas');
    const captureBtn = agentWidget.querySelector('.capture-btn');
    const cancelCameraBtn = agentWidget.querySelector('.cancel-camera-btn');
    
    let stagedImage = null; // For Phase 3: Combined image-text query
    let currentImagePreviewElement = null; // To remove preview if cancelled
    let localCameraStream = null; // For Phase 2: Camera stream
 
    let websocket = null;
    let currentSessionId = null;
    let isWsAudioMode = false; // Reflects the actual mode of the current/last WebSocket connection
    let userDesiredAudioMode = false; // User's intent, toggled by mic button
    console.log(`[AgentWidgetDebug] Initial state: userDesiredAudioMode=${userDesiredAudioMode}, isWsAudioMode=${isWsAudioMode}`);
    
    let audioPlayerNode;
    let audioRecorderNode;
    let localMicStream = null;
    let isMicPausedForAgentSpeech = false; // Tracks if mic is paused due to agent speaking
    console.log(`[AgentWidgetDebug] Initial isMicPausedForAgentSpeech=${isMicPausedForAgentSpeech}`);
    let waitingForAgentPlaybackToFinish = false; // Tracks if waiting for agent audio playback to finish
    console.log(`[AgentWidgetDebug] Initial waitingForAgentPlaybackToFinish=${waitingForAgentPlaybackToFinish}`);
    let hasPendingTurnCompleteSignal = false;
    console.log(`[AgentWidgetDebug] Initial hasPendingTurnCompleteSignal=${hasPendingTurnCompleteSignal}`);
    let recentlySentUICommand = false; // Flag for recent UI command
    console.log(`[AgentWidgetDebug] Initial recentlySentUICommand=${recentlySentUICommand}`);
    let uiCommandGracePeriodTimer = null; // Timer for the flag
    const UI_COMMAND_GRACE_PERIOD_MS = 3500; // Extended to 3.5 seconds, adjustable
    let isMicJustResumed = false; // Flag for mic just resumed
    let micResumedIgnoreTimer = null; 
    const MIC_RESUME_IGNORE_DURATION_MS = 150; // Ignore initial audio for this duration
    
    let currentAgentMessageElement = null;
    let isOverallSessionStart = true; // Tracks if it's the very first interaction in this widget lifecycle
let initialGreetingSent = false; // Tracks if the first user message/greeting has been sent
    let agentMessageClearTimer = null; // Timer to delay clearing of agent message bubble
    const AGENT_MESSAGE_CONTINUATION_DELAY_MS = 350; // Delay in ms, adjustable

    let audioChunkBuffer = [];
    const TARGET_AUDIO_CHUNK_SIZE_BYTES = 3200; // Aim for approx 100ms of 16kHz/16-bit audio (16000*2*0.1)
 
    function arrayBufferToBase64(buffer) {
        let binary = '';
        const bytes = new Uint8Array(buffer);
        for (let i = 0; i < bytes.byteLength; i++) {
            binary += String.fromCharCode(bytes[i]);
        }
        return window.btoa(binary);
    }

    function base64ToArrayBuffer(base64) {
        const binaryString = window.atob(base64);
        const len = binaryString.length;
        const bytes = new Uint8Array(len);
        for (let i = 0; i < len; i++) {
            bytes[i] = binaryString.charCodeAt(i);
        }
        return bytes.buffer;
    }

    function updateMicIcon(isAudioActive, isConnected) {
        if (!micIcon) return;
        micIcon.disabled = !isConnected;
        if (isAudioActive && isConnected) {
            micIcon.classList.add('active');
            micIcon.innerHTML = '<i class="fa-solid fa-microphone-slash"></i>';
        } else {
            micIcon.classList.remove('active');
            micIcon.innerHTML = '<i class="fa-solid fa-microphone"></i>';
        }
    }
    
    function showUIMode(isAudio) {
        if (textChatContainer) textChatContainer.style.display = 'flex'; // Always visible for now
        if (videoDisplayContainer) videoDisplayContainer.style.display = 'none'; // Video not used

        if (isAudio) {
            if (chatIcon) chatIcon.classList.remove('active');
            if (micIcon) micIcon.classList.add('active'); // Icon state managed by updateMicIcon
        } else {
            if (chatIcon) chatIcon.classList.add('active');
            if (micIcon) micIcon.classList.remove('active');
        }
        if (videoToggleButton) videoToggleButton.classList.remove('active');
    }

    async function initializeAndStartAudioCapture() {
        console.log(`[AgentWidgetDebug] initializeAndStartAudioCapture called. Current isWsAudioMode: ${isWsAudioMode}, isMicPausedForAgentSpeech: ${isMicPausedForAgentSpeech}`);
        // console.log("[AudioInit] Attempting to start audio capture. Current WS audio mode:", isWsAudioMode, "Mic paused for agent speech:", isMicPausedForAgentSpeech); // Original log
        isMicPausedForAgentSpeech = false; // Reset on new capture initialization
        console.log(`[AgentWidgetDebug] initializeAndStartAudioCapture: isMicPausedForAgentSpeech reset to ${isMicPausedForAgentSpeech}.`);
        // console.log("[AudioInit] Reset isMicPausedForAgentSpeech to false."); // Original log
        if (!isWsAudioMode) { // Should only be called if ws is in audio mode
            console.warn("[AgentWidgetDebug] initializeAndStartAudioCapture: Not in WebSocket audio mode. Aborting audio start.");
            return;
        }
        if (localMicStream) {
            console.log("[AgentWidgetDebug] initializeAndStartAudioCapture: Microphone stream already exists. Aborting.");
            return;
        }

        try {
            if (!audioPlayerNode) {
                console.log("[AgentWidgetDebug] initializeAndStartAudioCapture: Audio player node does not exist. Starting worklet.");
                const [player] = await startAudioPlayerWorklet();
                audioPlayerNode = player;
                console.log("[AgentWidgetDebug] initializeAndStartAudioCapture: Audio player worklet started.");

                // Setup message handler for playback finished events
                audioPlayerNode.port.onmessage = (event) => {
                    if (event.data && event.data.status === 'playback_finished') {
                        console.log(`[AgentWidgetDebug EVENT] audioPlayerNode.port.onmessage: 'playback_finished'. States: waitingForAgentPlaybackToFinish (before): ${waitingForAgentPlaybackToFinish}, hasPendingTurnCompleteSignal: ${hasPendingTurnCompleteSignal}`);
                        waitingForAgentPlaybackToFinish = false;

                        // Check for and process deferred turn_complete signal
                        if (hasPendingTurnCompleteSignal) {
                            console.log(`[AgentWidgetDebug] audioPlayerNode.port.onmessage: Processing deferred turn_complete. Pending: ${hasPendingTurnCompleteSignal}`);
                            currentAgentMessageElement = null; // Deferred action
                            hasPendingTurnCompleteSignal = false;
                        }

                        if (userDesiredAudioMode && isMicPausedForAgentSpeech) {
                            console.log(`[AgentWidgetDebug MIC_ACTION] audioPlayerNode.port.onmessage: Playback finished. Resuming mic. userDesiredAudioMode=${userDesiredAudioMode}, isMicPausedForAgentSpeech=${isMicPausedForAgentSpeech}`);
                            if (localMicStream) {
                                resumeMicrophoneInput(localMicStream);
                                isMicJustResumed = true; // Set flag
                                console.log(`[AgentWidgetDebug MIC_ACTION] Mic resumed, isMicJustResumed set to true.`);
                                if(micResumedIgnoreTimer) clearTimeout(micResumedIgnoreTimer);
                                micResumedIgnoreTimer = setTimeout(() => {
                                    isMicJustResumed = false;
                                    console.log(`[AgentWidgetDebug MIC_ACTION] Mic resume ignore period ended. isMicJustResumed set to false.`);
                                }, MIC_RESUME_IGNORE_DURATION_MS);
                            } else {
                                console.warn("[AgentWidgetDebug MIC_ACTION] audioPlayerNode.port.onmessage: Cannot resume mic: localMicStream is null.");
                            }
                            isMicPausedForAgentSpeech = false;
                        } else {
                            console.log(`[AgentWidgetDebug MIC_ACTION] audioPlayerNode.port.onmessage: Playback finished. Conditions for resuming mic NOT met. userDesiredAudioMode=${userDesiredAudioMode}, isMicPausedForAgentSpeech=${isMicPausedForAgentSpeech}`);
                        }
                    }
                };
                console.log("[AgentWidgetDebug] initializeAndStartAudioCapture: Audio player port onmessage handler set up.");
            }
            console.log("[AgentWidgetDebug] initializeAndStartAudioCapture: Starting audio recorder worklet.");
            const [recorder, , stream] = await startAudioRecorderWorklet(adkAudioRecorderHandler);
            audioRecorderNode = recorder;
            localMicStream = stream;
            console.log("[AgentWidgetDebug] initializeAndStartAudioCapture: Audio recorder worklet started, localMicStream obtained.");
            
            updateMicIcon(true, websocket && websocket.readyState === WebSocket.OPEN);
            addMessageToChat("system", "Microphone activated.");
            console.log("[AgentWidgetDebug] initializeAndStartAudioCapture: Audio recording started successfully.");
        } catch (err) {
            console.error("[AgentWidgetDebug] initializeAndStartAudioCapture: Error starting audio processing:", err);
            addMessageToChat("error", `Could not start microphone: ${err.message}. Please check permissions.`);
            updateMicIcon(false, websocket && websocket.readyState === WebSocket.OPEN);
            userDesiredAudioMode = false; // Revert desired mode if mic fails
            console.log(`[AgentWidgetDebug] initializeAndStartAudioCapture: userDesiredAudioMode set to ${userDesiredAudioMode} due to error.`);
            isWsAudioMode = false; // Revert actual mode
            console.log(`[AgentWidgetDebug] initializeAndStartAudioCapture: isWsAudioMode set to ${isWsAudioMode} due to error.`);
            // Consider switching back to text mode WebSocket if audio init fails
            if (websocket && websocket.readyState === WebSocket.OPEN) {
                 // If WS was for audio, close it and reconnect in text.
                console.log("[AgentWidgetDebug] initializeAndStartAudioCapture: Mic failed, attempting to revert to text mode WebSocket.");
                await connectWebSocketInternal(false); // Reconnect in text mode
            }
        }
    }

    function stopAudioCaptureAndProcessing() {
        console.log(`[AgentWidgetDebug] stopAudioCaptureAndProcessing called. Current isMicPausedForAgentSpeech: ${isMicPausedForAgentSpeech}`);
        // console.log("[AudioStop] Attempting to stop audio capture. Mic paused for agent speech:", isMicPausedForAgentSpeech); // Original log
        // If there's any pending audio in the buffer, send it before stopping
        if (audioChunkBuffer.length > 0) {
            console.log("[AgentWidgetDebug] stopAudioCaptureAndProcessing: Sending remaining buffered audio before stopping...");
            let totalBufferedBytes = 0;
            for (const chunk of audioChunkBuffer) {
                totalBufferedBytes += chunk.byteLength;
            }
            const concatenatedBuffer = new Uint8Array(totalBufferedBytes);
            let offset = 0;
            for (const chunk of audioChunkBuffer) {
                concatenatedBuffer.set(new Uint8Array(chunk), offset);
                offset += chunk.byteLength;
            }
            const base64Data = arrayBufferToBase64(concatenatedBuffer.buffer);
            const actualSampleRate = 16000;
             sendMessageToServer({
                mime_type: "audio/pcm",
                data: base64Data,
            });
            console.log(`[AudioStop] Sent remaining ${concatenatedBuffer.byteLength} bytes.`);
        }
        audioChunkBuffer = []; // Clear buffer on stop

        if (localMicStream) {
            console.log("[AgentWidgetDebug] stopAudioCaptureAndProcessing: Calling stopMicrophone.");
            stopMicrophone(localMicStream);
            localMicStream = null;
            console.log("[AgentWidgetDebug] stopAudioCaptureAndProcessing: Microphone stream stopped and set to null.");
        }
        if (isMicPausedForAgentSpeech) {
            console.log(`[AgentWidgetDebug] stopAudioCaptureAndProcessing: Resetting isMicPausedForAgentSpeech (was ${isMicPausedForAgentSpeech}) to false.`);
            isMicPausedForAgentSpeech = false;
        }
        // audioRecorderNode and audioPlayerNode are managed by their worklets
        updateMicIcon(false, websocket && websocket.readyState === WebSocket.OPEN);
        // addMessageToChat("system", "Microphone deactivated."); // Message sent by micIcon handler
        console.log("[AgentWidgetDebug] stopAudioCaptureAndProcessing: Audio processing stopped.");
    }
    
    function adkAudioRecorderHandler(pcmDataBuffer) {
        // console.log(`[AgentWidgetDebug] adkAudioRecorderHandler called. isWsAudioMode: ${isWsAudioMode}, WS state: ${websocket ? websocket.readyState : 'null'}, audioRecorderNode: ${!!audioRecorderNode}`);
        if (isMicJustResumed) {
            // console.log(`[AgentWidgetDebug adkAudioRecorderHandler] Mic was just resumed, ignoring this audio packet.`);
            return;
        }

        if (!isWsAudioMode || !websocket || websocket.readyState !== WebSocket.OPEN || !audioRecorderNode || !audioRecorderNode.context) {
            console.warn(`[AgentWidgetDebug] adkAudioRecorderHandler: Conditions not met for sending audio. isWsAudioMode: ${isWsAudioMode}, WS state: ${websocket ? websocket.readyState : 'null'}, audioRecorderNode: ${!!audioRecorderNode}, audioRecorderNode.context: ${audioRecorderNode ? !!audioRecorderNode.context : 'N/A'}. Aborting.`);
            // if (!audioRecorderNode || !audioRecorderNode.context) { // Original log
            //     console.warn("[AudioSend] audioRecorderNode or its context is not available. Cannot send audio with sample rate.");
            // }
            return;
        }

        // pcmDataBuffer is a Float32Array. Convert it to 16-bit PCM.
        // const float32Samples = pcmDataBuffer; // pcmDataBuffer is now expected to be an ArrayBuffer of 16-bit PCM

        // --- BEGIN REFINED CLIENT-SIDE DEBUG LOGGING ---
        // This block seems to be from a previous debugging session, I'll keep its detailed logging.
        if (typeof pcmDataBuffer === 'undefined') {
            console.error("[AgentWidgetDebug] adkAudioRecorderHandler: pcmDataBuffer argument is UNDEFINED. This is unexpected if audio-modules.js is correct.");
            return; // Cannot proceed
        } else if (pcmDataBuffer === null) {
            console.error("[AgentWidgetDebug] adkAudioRecorderHandler: pcmDataBuffer argument is NULL. This is unexpected.");
            return; // Cannot proceed
        } else {
            // pcmDataBuffer should be an ArrayBuffer from audio-modules.js (already 16-bit PCM)
            // console.log(`[AudioSend DEBUG] adkAudioRecorderHandler received pcmDataBuffer. Type: ${typeof pcmDataBuffer}, instanceof ArrayBuffer: ${pcmDataBuffer instanceof ArrayBuffer}, byteLength: ${pcmDataBuffer.byteLength !== undefined ? pcmDataBuffer.byteLength : 'N/A'}`); // Original log
            if (!(pcmDataBuffer instanceof ArrayBuffer)) {
                console.error("[AgentWidgetDebug] adkAudioRecorderHandler: CRITICAL: pcmDataBuffer is NOT an ArrayBuffer as expected from audio-modules.js! Halting audio send.");
                return; // Cannot proceed if not an ArrayBuffer
            }
            if (pcmDataBuffer.byteLength === 0) {
                 console.warn("[AgentWidgetDebug] adkAudioRecorderHandler: pcmDataBuffer from audio-modules has a byteLength of 0. This will result in empty audio data being sent.");
            }
        }
        // if (!audioRecorderNode) console.error("[AudioSend DEBUG] audioRecorderNode is not defined at the time of adkAudioRecorderHandler call!"); // Original log
        // else if (!audioRecorderNode.context) console.error("[AudioSend DEBUG] audioRecorderNode.context is not defined at the time of adkAudioRecorderHandler call!"); // Original log
        // --- END REFINED CLIENT-SIDE DEBUG LOGGING ---

        const int16Buffer = pcmDataBuffer; 

        if (!int16Buffer || int16Buffer.byteLength === 0) {
            console.warn("[AgentWidgetDebug] adkAudioRecorderHandler: Received empty or invalid int16Buffer. Skipping.");
            return;
        }

        audioChunkBuffer.push(int16Buffer);

        let totalBufferedBytes = 0;
        for (const chunk of audioChunkBuffer) {
            totalBufferedBytes += chunk.byteLength;
        }
        // console.log(`[AgentWidgetDebug] adkAudioRecorderHandler: Buffered ${audioChunkBuffer.length} chunks, total bytes: ${totalBufferedBytes}`);


        if (totalBufferedBytes >= TARGET_AUDIO_CHUNK_SIZE_BYTES) {
            const concatenatedBuffer = new Uint8Array(totalBufferedBytes);
            let offset = 0;
            for (const chunk of audioChunkBuffer) {
                concatenatedBuffer.set(new Uint8Array(chunk), offset);
                offset += chunk.byteLength;
            }
            audioChunkBuffer = []; 

            const base64Data = arrayBufferToBase64(concatenatedBuffer.buffer);
            const actualSampleRate = 16000; 
            
            // console.log(`[AudioSend] Sending buffered audio. Total bytes: ${concatenatedBuffer.byteLength}, Sample rate: ${actualSampleRate}, Base64 length: ${base64Data.length}`); // Original log
            
            sendMessageToServer({
                mime_type: "audio/pcm",
                data: base64Data,
            });
        }
    }

    async function connectWebSocketInternal(audioModeForThisConnection) {
        console.log(`[AgentWidgetDebug] connectWebSocketInternal called. audioModeForThisConnection: ${audioModeForThisConnection}, Current WebSocket state: ${websocket ? websocket.readyState : 'null'}, current isWsAudioMode: ${isWsAudioMode}`);
        // console.log(`[WSInternal] connectWebSocketInternal called. audioModeForThisConnection: ${audioModeForThisConnection}, WebSocket state: ${websocket ? websocket.readyState : 'null'}`); // Original log

        if (websocket) {
            console.log(`[AgentWidgetDebug] connectWebSocketInternal: Closing existing WebSocket (state: ${websocket.readyState}) before new connection.`);
            websocket.onopen = null;
            websocket.onmessage = null;
            websocket.onerror = null;
            websocket.onclose = null; 
            if (websocket.readyState === WebSocket.OPEN || websocket.readyState === WebSocket.CONNECTING) {
                console.log(`[AgentWidgetDebug] connectWebSocketInternal: Actively closing WebSocket (state: ${websocket.readyState}).`);
                websocket.close(1000, "Client initiated new connection");
            }
            websocket = null; // Ensure old instance is cleared
            console.log("[AgentWidgetDebug] connectWebSocketInternal: Old WebSocket instance cleared.");
        }
        
        isWsAudioMode = audioModeForThisConnection; // Set mode for this specific connection attempt
        console.log(`[AgentWidgetDebug] connectWebSocketInternal: isWsAudioMode set to ${isWsAudioMode} for this connection.`);
        // Ensure session ID is generated only once per widget lifecycle
        if (!currentSessionId) {
            currentSessionId = 'client_session_' + Date.now();
            console.log(`[AgentWidgetDebug] connectWebSocketInternal: Generated new client session ID: ${currentSessionId}`);
            isOverallSessionStart = true; // Mark that this is the start of an overall session
        } else {
            console.log(`[AgentWidgetDebug] connectWebSocketInternal: Reusing existing client session ID: ${currentSessionId}`);
        }
        const websocketUrl = `ws://localhost:8001/ws/agent_stream/${currentSessionId}?is_audio=${isWsAudioMode}`;

        console.log(`[AgentWidgetDebug] connectWebSocketInternal: Attempting to connect to: ${websocketUrl}`);
        addMessageToChat("system", `Connecting (audio: ${isWsAudioMode})...`);
        
        try {
            websocket = new WebSocket(websocketUrl);
            console.log(`[AgentWidgetDebug] connectWebSocketInternal: New WebSocket object created for ${websocketUrl}`);
        } catch (error) {
            console.error("[AgentWidgetDebug] connectWebSocketInternal: Error creating WebSocket object:", error);
            addMessageToChat("error", `Failed to create WebSocket: ${error.message}`);
            updateMicIcon(userDesiredAudioMode, false);
            isWsAudioMode = false; // Ensure this is reset on failure
            console.log(`[AgentWidgetDebug] connectWebSocketInternal: isWsAudioMode set to ${isWsAudioMode} after WebSocket creation error.`);
            return;
        }

        websocket.onopen = async () => {
            console.log(`[AgentWidgetDebug] websocket.onopen: WebSocket opened (audio: ${isWsAudioMode}). State: ${websocket.readyState}`);
            addMessageToChat("system", "Connection opened.");
            if (chatInput) chatInput.disabled = false;
            updateMicIcon(userDesiredAudioMode, true);

            console.log("[AgentWidgetDebug] websocket.onopen: Sending 'client_ready' message.");
            sendMessageToServer({ mime_type: "text/plain", data: "client_ready" });

            if (isWsAudioMode) { // If this connection is for audio
                console.log("[AgentWidgetDebug] websocket.onopen: Audio mode active. Initializing audio capture.");
                await initializeAndStartAudioCapture();
            } else { // Text mode connection
                console.log("[AgentWidgetDebug] websocket.onopen: Text mode active.");
                if (localMicStream) { // Ensure mic is stopped if we connected in text mode
                    console.log("[AgentWidgetDebug] websocket.onopen: localMicStream exists in text mode, stopping audio capture.");
                    stopAudioCaptureAndProcessing();
                }
                // Only send the initial canned message if it's the very first message of the overall session
                if (isOverallSessionStart) {
                    console.log("[AgentWidgetDebug] websocket.onopen: isOverallSessionStart is true. Sending initial greeting.");
                    sendMessageToServer({ mime_type: "text/plain", data: "Hello, how can you assist me with gardening?" });
                    isOverallSessionStart = false; // Mark that the initial message has been sent for this session
                    console.log(`[AgentWidgetDebug] websocket.onopen: isOverallSessionStart set to ${isOverallSessionStart}.`);
                }
            }
        };

        websocket.onmessage = (event) => {
            // console.log("[AgentWidgetDebug] websocket.onmessage: RAW CHUNK RECEIVED:", event.data); // DIAGNOSTIC LOG
            const rawDataForLog = (typeof event.data === 'string' && event.data.length > 100) ? event.data.substring(0,100) + "..." : event.data;
            let parsedData;
            try {
                parsedData = JSON.parse(event.data);
            } catch (error) {
                console.error("[AgentWidgetDebug] websocket.onmessage: Error parsing JSON:", error, "Raw Data:", event.data);
                if (typeof event.data === 'string') {
                    if (!currentAgentMessageElement) currentAgentMessageElement = addMessageToChat("agent", "");
                    currentAgentMessageElement.textContent += event.data;
                    scrollToBottom();
                }
                return;
            }

            if (parsedData.turn_complete === true || parsedData.interrupted === true || parsedData.interaction_completed === true) {
                let signalType = parsedData.turn_complete ? "turn_complete" : parsedData.interrupted ? "interrupted" : "interaction_completed";
                console.log(`[AgentWidgetDebug EVENT] websocket.onmessage: Agent signal '${signalType}'. States: waitingPlayback=${waitingForAgentPlaybackToFinish}, recentUI=${recentlySentUICommand}, pendingSignal=${hasPendingTurnCompleteSignal}`);

                if ( (waitingForAgentPlaybackToFinish || recentlySentUICommand) ) {
                    console.log(`[AgentWidgetDebug] websocket.onmessage: '${signalType}' received while waitingPlayback OR recentUI. Deferring.`);
                    hasPendingTurnCompleteSignal = true;
                } else {
                    console.log(`[AgentWidgetDebug] websocket.onmessage: '${signalType}' received. Processing normally.`);
                    if (agentMessageClearTimer) clearTimeout(agentMessageClearTimer);
                    agentMessageClearTimer = setTimeout(() => {
                        console.log(`[AgentWidgetDebug] Agent message continuation delay ended for '${signalType}'. Clearing currentAgentMessageElement.`);
                        currentAgentMessageElement = null;
                        agentMessageClearTimer = null;
                    }, AGENT_MESSAGE_CONTINUATION_DELAY_MS);
                }
                return;
            }

            // Preserve non-voice command handling
            if (parsedData.type === "command" && parsedData.command_name === "set_theme") {
                const themeValue = parsedData.payload?.theme;
                if (themeValue) {
                    console.log(`[AgentWidgetDebug] websocket.onmessage: Received 'set_theme': ${themeValue}`);
                    window.parent.postMessage({ "type": "SET_WEBSITE_THEME", "payload": themeValue }, 'http://localhost:5000');
                }
                currentAgentMessageElement = null; return;
            }
            if (parsedData.type === "command" && parsedData.command_name === "refresh_cart") {
                console.log(`[AgentWidgetDebug] websocket.onmessage: Received 'refresh_cart'. Payload:`, parsedData.payload);
                let messageToParent = { "type": "REFRESH_CART_DISPLAY" };
                if (parsedData.payload && parsedData.payload.added_item) { 
                    messageToParent.added_item_details = parsedData.payload.added_item;
                }
                window.parent.postMessage(messageToParent, 'http://localhost:5000');
                currentAgentMessageElement = null; return;
            }
            // Handle display_checkout_modal command
            if (parsedData.type === "command" && parsedData.command_name === "display_checkout_modal") {
                console.log(`[AgentWidgetDebug] websocket.onmessage: Received 'display_checkout_modal'. Payload:`, parsedData.data);
                if (parsedData.data) {
                    window.parent.postMessage({
                        type: 'show_checkout_modal_command',
                        cart: parsedData.data
                    }, 'http://localhost:5000');
                } else {
                    console.warn("[AgentWidgetDebug] websocket.onmessage: 'display_checkout_modal' command received but 'data' (cart_data) is missing.");
                }
                currentAgentMessageElement = null; return;
            }
            // Handle new shipping modal commands from server
            if (parsedData.type === "command" && parsedData.command_name === "display_shipping_modal") {
                console.log(`[AgentWidgetDebug] websocket.onmessage: Received 'display_shipping_modal'.`);
                window.parent.postMessage({ type: 'show_shipping_modal_command' }, 'http://localhost:5000');
                currentAgentMessageElement = null; return;
            }
            // Handle display_payment_modal command
            if (parsedData.type === "command" && parsedData.command_name === "display_payment_modal") {
                console.log(`[AgentWidgetDebug] websocket.onmessage: Received 'display_payment_modal'.`);
                window.parent.postMessage({ type: 'show_payment_modal_command' }, 'http://localhost:5000');
                currentAgentMessageElement = null; return;
            }
            if (parsedData.type === "command" && parsedData.command_name === "agent_confirm_selection") {
                console.log(`[AgentWidgetDebug] websocket.onmessage: Received 'agent_confirm_selection'. Type: ${parsedData.selection_type}`);
                if (parsedData.selection_type === 'home_delivery') {
                    window.parent.postMessage({ type: 'ui_select_shipping_home_delivery' }, 'http://localhost:5000');
                } else if (parsedData.selection_type === 'pickup_initiated') {
                    window.parent.postMessage({ type: 'ui_show_pickup_locations' }, 'http://localhost:5000');
                } else if (parsedData.selection_type === 'pickup_address' && parsedData.address_index !== undefined) {
                    window.parent.postMessage({ type: 'ui_select_pickup_address', address_index: parsedData.address_index }, 'http://localhost:5000');
                }
                currentAgentMessageElement = null; return;
            }
                // Handle order_confirmed_refresh_cart command
            if (parsedData.type === "command" && parsedData.command_name === "order_confirmed_refresh_cart") {
                console.log(`[AgentWidgetDebug] websocket.onmessage: Received 'order_confirmed_refresh_cart'. Payload:`, parsedData.data);
                // Relay to main page to refresh cart and potentially show confirmation
                window.parent.postMessage({
                    type: 'order_confirmed_refresh_cart_command', // Main page will listen for this
                    data: parsedData.data // Contains order_id and message
                }, 'http://localhost:5000');
                currentAgentMessageElement = null; return;
            }

            if (parsedData.type === "product_recommendations" && parsedData.payload) {
               console.log("[AgentWidgetDebug] websocket.onmessage: Received product_recommendations.");
               addProductRecommendationsToChat(parsedData.payload);
               currentAgentMessageElement = null; return;
            }
            else if (parsedData.action === "display_ui" && parsedData.ui_element) {
                // Filter out checkout related UI commands if any were to slip through
                if (parsedData.ui_element === "checkout_item_selection" ||
                    // parsedData.ui_element === "display_shipping_options_ui" || // Keep this if it's a generic name
                    parsedData.ui_element === "display_payment_options_ui") {
                    console.log(`[AgentWidgetDebug] Ignoring checkout-related display_ui command: ${parsedData.ui_element}`);
                    currentAgentMessageElement = null;
                    return;
                }
                
                console.log(`[AgentWidgetDebug] Received 'display_ui'. Element: ${parsedData.ui_element}. Payload:`, JSON.stringify(parsedData.payload));
                
                recentlySentUICommand = true;
                console.log(`[AgentWidgetDebug] websocket.onmessage (display_ui): Set recentlySentUICommand to true.`);
                if (uiCommandGracePeriodTimer) clearTimeout(uiCommandGracePeriodTimer);
                uiCommandGracePeriodTimer = setTimeout(() => {
                    recentlySentUICommand = false;
                    console.log(`[AgentWidgetDebug] websocket.onmessage (display_ui): Grace period ended. Set recentlySentUICommand to false.`);
                }, UI_COMMAND_GRACE_PERIOD_MS);

                window.parent.postMessage({
                    type: "display_ui_component",
                    ui_element: parsedData.ui_element,
                    payload: parsedData.payload
                }, 'http://localhost:5000');
                console.log(`[AgentWidgetDebug] Posted 'display_ui_component' to parent.`);
                currentAgentMessageElement = null;
                // REMOVED return;
            } else if (parsedData.type === "ui_command" && parsedData.command_name) {
                 // Filter out checkout related UI commands
                if (parsedData.command_name === "trigger_checkout_modal" ||
                    parsedData.command_name === "display_shipping_options_ui" ||
                    parsedData.command_name === "checkout_item_selection" ||
                    parsedData.command_name === "display_payment_options_ui") {
                    console.log(`[AgentWidgetDebug] Ignoring checkout-related ui_command: ${parsedData.command_name}`);
                    currentAgentMessageElement = null;
                    return;
                }
                console.log(`[AgentWidgetDebug] Received legacy 'ui_command'. Command: ${parsedData.command_name}. Payload:`, JSON.stringify(parsedData.payload));
                
                recentlySentUICommand = true;
                console.log(`[AgentWidgetDebug] websocket.onmessage (legacy ui_command): Set recentlySentUICommand to true.`);
                if (uiCommandGracePeriodTimer) clearTimeout(uiCommandGracePeriodTimer);
                uiCommandGracePeriodTimer = setTimeout(() => {
                    recentlySentUICommand = false;
                    console.log(`[AgentWidgetDebug] websocket.onmessage (legacy ui_command): Grace period ended. Set recentlySentUICommand to false.`);
                }, UI_COMMAND_GRACE_PERIOD_MS);

                window.parent.postMessage(parsedData, 'http://localhost:5000');
                console.log(`[AgentWidgetDebug] Posted legacy 'ui_command' to parent.`);
                currentAgentMessageElement = null;
                // REMOVED return;
            }

            // Standard content messages
            if (parsedData.mime_type === "audio/pcm" && audioPlayerNode) {
                if (userDesiredAudioMode && localMicStream && !isMicPausedForAgentSpeech) {
                    console.log(`[AgentWidgetDebug MIC_ACTION] websocket.onmessage (audio/pcm): Agent audio starting. Pausing mic. States: userDesiredAudio=${userDesiredAudioMode}, micStream=${!!localMicStream}, micPaused=${isMicPausedForAgentSpeech}`);
                    pauseMicrophoneInput(localMicStream);
                    isMicPausedForAgentSpeech = true;
                    waitingForAgentPlaybackToFinish = true;
                } else {
                     console.log(`[AgentWidgetDebug MIC_ACTION] websocket.onmessage (audio/pcm): Agent audio starting. Conditions for pausing mic NOT met. States: userDesiredAudio=${userDesiredAudioMode}, micStream=${!!localMicStream}, micPaused=${isMicPausedForAgentSpeech}, waitingPlayback=${waitingForAgentPlaybackToFinish}`);
                    if(isMicPausedForAgentSpeech && !waitingForAgentPlaybackToFinish) {
                        waitingForAgentPlaybackToFinish = true;
                        console.log(`[AgentWidgetDebug] websocket.onmessage (audio/pcm): Mic already paused, new audio arriving. Set waitingForAgentPlaybackToFinish=true.`);
                    }
                }

                if (typeof parsedData.data === 'string') {
                    const audioData = base64ToArrayBuffer(parsedData.data);
                    audioPlayerNode.port.postMessage(audioData);
                } else {
                    console.warn("[AgentWidgetDebug] websocket.onmessage: Audio data received from agent is not a string. Cannot play.");
                }
            } else if (parsedData.mime_type === "text/plain" && typeof parsedData.data === 'string') {
                if (agentMessageClearTimer) { // If a timer was pending to clear the bubble, cancel it
                    clearTimeout(agentMessageClearTimer);
                    agentMessageClearTimer = null;
                    console.log(`[AgentWidgetDebug] Received new text chunk, cleared pending message element clear timer.`);
                }
                // DIAGNOSTIC LOG: Temporarily simplify rendering to console.log
                console.log("[AgentWidgetDebug] websocket.onmessage: TEXT_CHUNK:", parsedData.data, "PARTIAL:", parsedData.partial);
                if (!currentAgentMessageElement) {
                    currentAgentMessageElement = addMessageToChat("agent", parsedData.data);
                } else {
                    if (parsedData.partial === true) {
                        currentAgentMessageElement.textContent += parsedData.data;
                    } else {
                        currentAgentMessageElement.textContent = parsedData.data;
                    }
                }
                scrollToBottom();
            } else {
                console.log("[AgentWidgetDebug] websocket.onmessage: Unhandled message structure:", parsedData);
            }
        };

        websocket.onclose = (event) => {
            console.log(`[AgentWidgetDebug] websocket.onclose: Code: ${event.code}, Reason: '${event.reason}', Clean: ${event.wasClean}, WS State before close: ${websocket ? websocket.readyState : 'N/A'}`);
            addMessageToChat("system", `Connection closed. Code: ${event.code}.`);
            if (chatInput) chatInput.disabled = true;
            
            console.log("[AgentWidgetDebug] websocket.onclose: Stopping audio capture and processing.");
            stopAudioCaptureAndProcessing(); 
            isWsAudioMode = false; 
            console.log(`[AgentWidgetDebug] websocket.onclose: isWsAudioMode set to ${isWsAudioMode}.`);
            updateMicIcon(userDesiredAudioMode, false); 
            websocket = null; 
            console.log("[AgentWidgetDebug] websocket.onclose: WebSocket instance set to null.");
        };

        websocket.onerror = (error) => {
            console.error("[AgentWidgetDebug] websocket.onerror:", error);
            addMessageToChat("error", "WebSocket connection error.");
            if (chatInput) chatInput.disabled = true;

            console.log("[AgentWidgetDebug] websocket.onerror: Stopping audio capture and processing.");
            stopAudioCaptureAndProcessing();
            isWsAudioMode = false;
            console.log(`[AgentWidgetDebug] websocket.onerror: isWsAudioMode set to ${isWsAudioMode}.`);
            updateMicIcon(userDesiredAudioMode, false);
            websocket = null;
            console.log("[AgentWidgetDebug] websocket.onerror: WebSocket instance set to null.");
        };
    }

    function sendMessageToServer(payload) {
            // console.log(`[AgentWidgetDebug] sendMessageToServer called. Payload preview:`, payload.mime_type || payload.parts || payload.event_type);
            if (!websocket || websocket.readyState !== WebSocket.OPEN) {
                console.warn(`[AgentWidgetDebug] sendMessageToServer: WebSocket not open/ready. Message not sent. State: ${websocket ? websocket.readyState : 'null'}`);
                addMessageToChat("error", "Cannot send: Connection not open.");
            return;
        }

        let isValidPayload = false;

            if (payload.hasOwnProperty('mime_type') && payload.hasOwnProperty('data')) { // Simple text/audio message
                if (payload.mime_type && typeof payload.data !== 'undefined') {
                    isValidPayload = true;
                }
            } else if (payload.hasOwnProperty('parts') && Array.isArray(payload.parts)) { // Multimodal message
                isValidPayload = true;
                for (const part of payload.parts) {
                    if (!part || !part.mime_type || typeof part.data === 'undefined') {
                        isValidPayload = false; break;
                    }
                }
            } else if (payload.hasOwnProperty('event_type') && payload.hasOwnProperty('interaction')) { // UI interaction event
                 isValidPayload = true;
            }
            
            if (!isValidPayload) {
                console.error("[AgentWidgetDebug] sendMessageToServer: Invalid or unknown payload structure:", payload);
                addMessageToChat("error", "Attempted to send message with invalid structure or content.");
                return;
            }

            const messageJson = JSON.stringify(payload);
            websocket.send(messageJson);
            // console.log("[AgentWidgetDebug] sendMessageToServer: Message sent to WebSocket:", messageJson);
        }

        function clearStagedImage() {
        console.log("[AgentWidgetDebug] clearStagedImage called.");
        stagedImage = null;
        if (currentImagePreviewElement) {
            currentImagePreviewElement.remove();
            currentImagePreviewElement = null;
        }
        if (chatInput) {
            chatInput.placeholder = "Type your message...";
        }
        if (cameraViewContainer && cameraViewContainer.style.display !== 'none') {
            cameraViewContainer.style.display = 'none';
            if (textChatContainer) textChatContainer.style.display = 'flex'; // Show chat
        }
        // console.log("[ImageClear] Staged image cleared."); // Original log
    }

    async function identifyImageAndProceed(imageFile, imageName) {
        addMessageToChat("system", `Identifying ${imageName}...`);
        const formData = new FormData();
        formData.append('image', imageFile, imageName);

        try {
            const response = await fetch('/api/identify-image', {
                method: 'POST',
                body: formData,
            });

            if (!response.ok) {
                const errorResult = await response.json().catch(() => ({ error: "Failed to parse error from image identification." }));
                throw new Error(`Image identification failed: ${response.status} ${response.statusText}. ${errorResult.error || ''}`);
            }

            const result = await response.json();
            const identifiedItem = result.identified_item;

            if (identifiedItem && identifiedItem.toLowerCase() !== 'unknown' && !identifiedItem.startsWith("Error:")) {
                addMessageToChat("system", `Identified: ${identifiedItem}. You can now ask about it.`);
                chatInput.value = `Tell me more about ${identifiedItem}`; // Pre-fill input
                chatInput.focus();
                
                // Display a preview of the image that was identified
                const reader = new FileReader();
                reader.onload = function(e) {
                    addImagePreviewToChat(e.target.result, imageName, `${(imageFile.size / 1024).toFixed(1)} KB`);
                }
                reader.readAsDataURL(imageFile);
                // No longer setting stagedImage here as the primary flow is text-based after identification.

            } else {
                addMessageToChat("error", `Could not clearly identify the item in "${imageName}". Please try another image or describe the item in text.`);
                clearStagedImage(); // BUG FIX: Ensure staged image is cleared on identification failure.
            }
        } catch (error) {
            console.error("Error in identifyImageAndProceed:", error);
            addMessageToChat("error", `Error identifying image: ${error.message}. Please try again.`);
            clearStagedImage(); // BUG FIX: Ensure staged image is cleared on any error.
        }
    }
 
    // Modified to handle both file uploads and camera captures
    function addImagePreviewToChat(base64ImageDataUrl, imageName = "Captured Image", imageSizeText = "") {
        console.log(`[AgentWidgetDebug] addImagePreviewToChat called. Name: ${imageName}, Size: ${imageSizeText}`);
        // console.log(`[ImagePreview] Adding image preview. Name: ${imageName}, Size: ${imageSizeText}`); // Original log
        if (currentImagePreviewElement) { // Clear previous preview if any
            console.log("[AgentWidgetDebug] addImagePreviewToChat: Removing existing preview element.");
            currentImagePreviewElement.remove();
        }
 
        const previewContainer = document.createElement('div');
        previewContainer.classList.add('message', 'user-message', 'staged-image-preview-container');
        
        const textElement = document.createElement('p');
        let previewMessage = `Image ready: ${imageName}`;
        if (imageSizeText) {
            previewMessage += ` (${imageSizeText})`;
        }
        previewMessage += ". Add your query:";
        textElement.textContent = previewMessage;
        
        const imgPreview = document.createElement('img');
        imgPreview.src = base64ImageDataUrl;
        imgPreview.style.maxWidth = '150px';
        imgPreview.style.maxHeight = '150px';
        imgPreview.style.borderRadius = '4px';
        imgPreview.style.marginTop = '5px';
        imgPreview.style.marginBottom = '5px';

        const cancelButton = document.createElement('button');
        cancelButton.innerHTML = '<i class="fa-solid fa-times"></i> Cancel Image';
        cancelButton.classList.add('cancel-staged-image-btn');
        cancelButton.title = "Remove this image before sending";
        cancelButton.onclick = () => {
            clearStagedImage();
        };
        
        previewContainer.appendChild(textElement);
        previewContainer.appendChild(imgPreview);
        previewContainer.appendChild(cancelButton);
        
        messageArea.appendChild(previewContainer);
        currentImagePreviewElement = previewContainer; // Store reference to the new preview
        scrollToBottom();
        if (chatInput) {
            chatInput.placeholder = "Ask a question about the image...";
            chatInput.focus();
        }
        // console.log("[ImagePreview] Image preview added to chat."); // Original log
        console.log("[AgentWidgetDebug] addImagePreviewToChat: Image preview added to chat.");
    }
    
    // --- Start Camera Functionality (Phase 2) ---
    async function startCamera() {
        console.log("[AgentWidgetDebug] startCamera called.");
        // console.log("[Camera] Attempting to start camera."); // Original log
        if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
            console.error("[AgentWidgetDebug] startCamera: getUserMedia not supported on this browser.");
            addMessageToChat("error", "Camera access is not supported by your browser.");
            return;
        }
 
        try {
            localCameraStream = await navigator.mediaDevices.getUserMedia({ video: true, audio: false });
            console.log("[AgentWidgetDebug] startCamera: Camera stream obtained.");
            if (cameraFeed) {
                cameraFeed.srcObject = localCameraStream;
                cameraFeed.onloadedmetadata = () => {
                    cameraFeed.play();
                    console.log("[AgentWidgetDebug] startCamera: Camera feed playing.");
                };
            }
            if (cameraViewContainer) cameraViewContainer.style.display = 'flex';
            if (textChatContainer) textChatContainer.style.display = 'none';
            if (imageOptionsPopup) imageOptionsPopup.style.display = 'none'; // Hide options popup
            console.log("[AgentWidgetDebug] startCamera: Camera view activated.");
        } catch (err) {
            console.error("[AgentWidgetDebug] startCamera: Error accessing camera:", err);
            addMessageToChat("error", `Could not access camera: ${err.message}. Please check permissions.`);
            if (cameraViewContainer) cameraViewContainer.style.display = 'none';
            if (textChatContainer) textChatContainer.style.display = 'flex'; // Revert to chat view
            localCameraStream = null; // Ensure stream is null on error
        }
    }
 
    function stopCamera() {
        console.log("[AgentWidgetDebug] stopCamera called.");
        // console.log("[Camera] Attempting to stop camera stream."); // Original log
        if (localCameraStream) {
            localCameraStream.getTracks().forEach(track => {
                track.stop();
                console.log(`[AgentWidgetDebug] stopCamera: Track stopped: ${track.kind}`);
            });
            localCameraStream = null;
            if (cameraFeed) cameraFeed.srcObject = null;
            console.log("[AgentWidgetDebug] stopCamera: Camera stream stopped and resources released.");
        }
        if (cameraViewContainer) cameraViewContainer.style.display = 'none';
        if (textChatContainer && textChatContainer.style.display === 'none') { 
             textChatContainer.style.display = 'flex';
        }
    }
 
    function capturePhoto() {
        console.log("[AgentWidgetDebug] capturePhoto called.");
        // console.log("[Camera] Attempting to capture photo."); // Original log
        if (!localCameraStream || !cameraFeed || !photoCanvas) {
            console.error("[AgentWidgetDebug] capturePhoto: Cannot capture photo. Stream, feed, or canvas not available.");
            addMessageToChat("error", "Could not capture photo. Camera not ready.");
            return;
        }
 
        const context = photoCanvas.getContext('2d');
        photoCanvas.width = cameraFeed.videoWidth;
        photoCanvas.height = cameraFeed.videoHeight;
        context.drawImage(cameraFeed, 0, 0, photoCanvas.width, photoCanvas.height);
        console.log(`[AgentWidgetDebug] capturePhoto: Photo drawn to canvas. Dimensions: ${photoCanvas.width}x${photoCanvas.height}`);
 
        const imageName = `capture_${Date.now()}.jpg`;
        console.log(`[AgentWidgetDebug] capturePhoto: Capturing photo as ${imageName}`);

        photoCanvas.toBlob(async (blob) => { // Make callback async
            if (blob) {
                console.log(`[AgentWidgetDebug] capturePhoto: Photo captured as blob. Name: ${imageName}, Size: ${blob.size}, Type: ${blob.type}`);
                // Create a File object from the Blob to pass to identifyImageAndProceed
                const imageFile = new File([blob], imageName, { type: blob.type || 'image/jpeg' });
                await identifyImageAndProceed(imageFile, imageName); // Call new function
            } else {
                console.error("[AgentWidgetDebug] capturePhoto: Failed to capture photo blob.");
                addMessageToChat("error", "Failed to capture photo.");
            }
        }, 'image/jpeg'); // Specify MIME type for blob
        
        stopCamera(); // Close camera view after capture
        console.log("[AgentWidgetDebug] capturePhoto: Photo capture process initiated. Camera stopped.");
    }
 
    if (cameraBtn) {
        cameraBtn.addEventListener('click', () => {
            console.log("[AgentWidgetDebug] UI: 'Camera' button clicked.");
            startCamera();
        });
    }
 
    if (captureBtn) {
        captureBtn.addEventListener('click', () => {
            console.log("[AgentWidgetDebug] UI: 'Capture Photo' button clicked.");
            capturePhoto();
        });
    }
 
    if (cancelCameraBtn) {
        cancelCameraBtn.addEventListener('click', () => {
            console.log("[AgentWidgetDebug] UI: 'Cancel Camera' button clicked.");
            stopCamera();
            clearStagedImage(); 
            if (imageOptionsPopup) imageOptionsPopup.style.display = 'none'; 
            console.log("[AgentWidgetDebug] UI: Camera cancelled and view reset.");
        });
    }
    // --- End Camera Functionality (Phase 2) ---
 
    function addMessageToChat(sender, text, imageInfo = null) {
        // console.log(`[AgentWidgetDebug] addMessageToChat called. Sender: ${sender}, Text preview: ${text.substring(0, 50)}...`);
        if (!messageArea) {
            console.error("[addMessageToChat] messageArea is null.");
            return null;
        }
        const messageContainer = document.createElement('div');
        messageContainer.classList.add('message', sender === 'user' ? 'user-message' : 'agent-message');
        
        const textElement = document.createElement('p');
        textElement.textContent = text;
        messageContainer.appendChild(textElement);

        if (sender === 'user' && imageInfo && imageInfo.base64DataUrl) {
            const imgPreview = document.createElement('img');
            imgPreview.src = imageInfo.base64DataUrl;
            imgPreview.alt = imageInfo.name || "User image";
            imgPreview.style.maxWidth = '150px';
            imgPreview.style.maxHeight = '150px';
            imgPreview.style.borderRadius = '4px';
            imgPreview.style.marginTop = '5px';
            messageContainer.appendChild(imgPreview);
        }
        
        const timestampElement = document.createElement('span');
        timestampElement.classList.add('timestamp');
        timestampElement.textContent = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        messageContainer.appendChild(timestampElement);
        
        messageArea.appendChild(messageContainer);
        scrollToBottom();
        return textElement; // Might need to return messageContainer if more complex
    }

   function scrollToBottom() {
       if (messageArea) messageArea.scrollTop = messageArea.scrollHeight;
   }

    function addProductRecommendationsToChat(recommendationPayload) {
       if (!messageArea) { console.error("messageArea null in addProductRecommendationsToChat"); return; }
       const { title, products } = recommendationPayload;
       const recommendationsBlock = document.createElement('div');
       recommendationsBlock.className = 'product-recommendations-block';
       if (title) {
           const titleElement = document.createElement('h3');
           titleElement.className = 'recommendations-title';
           titleElement.textContent = title;
           recommendationsBlock.appendChild(titleElement);
       }
       const cardsContainer = document.createElement('div');
       cardsContainer.className = 'product-cards-container';
       if (products && Array.isArray(products)) {
           products.forEach(product => {
               const card = document.createElement('div');
               card.className = 'product-card';
               if (product.id) card.dataset.productId = product.id;
               const image = document.createElement('img');
               image.className = 'product-card-image';
               image.src = product.image_url || 'https://via.placeholder.com/60';
               image.alt = product.name || 'Product Image';
               const details = document.createElement('div');
               details.className = 'product-card-details';
               const nameElement = document.createElement('p');
               nameElement.className = 'product-card-name';
               nameElement.textContent = product.name || 'Unnamed Product';
               const priceElement = document.createElement('p');
               priceElement.className = 'product-card-price';
               priceElement.textContent = product.price || '';
               details.appendChild(nameElement);
               details.appendChild(priceElement);
               const link = document.createElement('a');
               link.className = 'product-card-link';
               link.href = product.product_url || '#';
               link.target = '_blank';
               link.setAttribute('aria-label', `View product ${product.name || ''}`);
               const icon = document.createElement('i');
               icon.className = 'fas fa-external-link-alt';
               link.appendChild(icon);
               card.appendChild(image);
               card.appendChild(details);
               card.appendChild(link);
               cardsContainer.appendChild(card);
           });
       }
       recommendationsBlock.appendChild(cardsContainer);
       messageArea.appendChild(recommendationsBlock);
       scrollToBottom();
    }

    agentWidget.addEventListener('widgetOpened', () => {
        console.log("[AgentWidgetDebug] Event 'widgetOpened' received. Connecting in text mode.");
        // console.log("Widget opened event received. Connecting in text mode."); // Original log
        userDesiredAudioMode = false; // Ensure initial desire is text
        console.log(`[AgentWidgetDebug] widgetOpened: userDesiredAudioMode set to ${userDesiredAudioMode}.`);
        connectWebSocketInternal(false);
    });

    function closeAndResetWidget() {
        console.log("[AgentWidgetDebug] closeAndResetWidget called.");
        userDesiredAudioMode = false; // Reset desired mode
        console.log(`[AgentWidgetDebug] closeAndResetWidget: userDesiredAudioMode set to ${userDesiredAudioMode}.`);
        if (isWsAudioMode || localMicStream) {
            console.log("[AgentWidgetDebug] closeAndResetWidget: Audio was active, stopping capture.");
            stopAudioCaptureAndProcessing();
        }
        if (websocket && websocket.readyState === WebSocket.OPEN) {
            console.log("[AgentWidgetDebug] closeAndResetWidget: Closing WebSocket.");
            websocket.close(1000, "Widget closing");
        }
        websocket = null;
        isWsAudioMode = false;
        console.log(`[AgentWidgetDebug] closeAndResetWidget: isWsAudioMode set to ${isWsAudioMode}.`);
        if(messageArea) messageArea.innerHTML = '';
        agentWidget.dispatchEvent(new CustomEvent('widgetClosed', { bubbles: true }));
        updateMicIcon(false, false);
        if (chatInput) chatInput.disabled = true;
        console.log("[AgentWidgetDebug] closeAndResetWidget: Widget reset complete.");
    }

    const sendButton = agentWidget.querySelector('.send-btn');
    if (sendButton && chatInput) {
        sendButton.addEventListener('click', () => {
            console.log("[AgentWidgetDebug] UI: Send button clicked.");
            const textMessage = chatInput.value.trim();
            if (stagedImage) {
                console.log("[AgentWidgetDebug] UI Send: Staged image exists.");
                if (textMessage === '') {
                    addMessageToChat("system", "Please add a text query for the staged image.");
                    console.log("[AgentWidgetDebug] UI Send: Text message empty for staged image, prompting user.");
                    return;
                }
                console.log("[AgentWidgetDebug] UI Send: Sending combined image and text.");
                addMessageToChat("user", textMessage, { name: stagedImage.name, base64DataUrl: stagedImage.dataUrl });
                const augmentedTextMessage = "What is in the image I just uploaded? Also, " + textMessage;
                sendMessageToServer({
                    parts: [
                        { mime_type: stagedImage.mime_type, data: stagedImage.data },
                        { mime_type: "text/plain", data: augmentedTextMessage }
                    ]
                });
                clearStagedImage();
                chatInput.value = '';
                initialGreetingSent = true;
                console.log(`[AgentWidgetDebug] UI Send: initialGreetingSent set to ${initialGreetingSent}.`);
            } else if (textMessage !== '') {
                console.log("[AgentWidgetDebug] UI Send: Sending text only message.");
                addMessageToChat("user", textMessage);
                sendMessageToServer({ mime_type: "text/plain", data: textMessage });
                chatInput.value = '';
                initialGreetingSent = true;
                console.log(`[AgentWidgetDebug] UI Send: initialGreetingSent set to ${initialGreetingSent}.`);
            } else {
                console.log("[AgentWidgetDebug] UI Send: No staged image and no text message. Nothing to send.");
            }
        });
    }

    // --- New Image Handling Logic ---
    console.log("[AgentWidgetDebug] Setting up image handling listeners.");
    if (imageOptionsToggleBtn && imageOptionsPopup) {
        imageOptionsToggleBtn.addEventListener('click', (event) => {
            console.log("[AgentWidgetDebug] UI: Image options toggle button clicked.");
            event.stopPropagation(); 
            const isPopupVisible = imageOptionsPopup.style.display === 'flex';
            imageOptionsPopup.style.display = isPopupVisible ? 'none' : 'flex';
            console.log(`[AgentWidgetDebug] UI: Image options popup visibility set to ${imageOptionsPopup.style.display}.`);
        });

        document.addEventListener('click', (event) => {
            if (imageOptionsPopup.style.display === 'flex' &&
                !imageOptionsPopup.contains(event.target) &&
                !imageOptionsToggleBtn.contains(event.target)) {
                console.log("[AgentWidgetDebug] UI: Clicked outside image options popup, hiding it.");
                imageOptionsPopup.style.display = 'none';
            }
        });
    }

    if (uploadLocalBtn && imageUploadInput) {
        uploadLocalBtn.addEventListener('click', () => {
            console.log("[AgentWidgetDebug] UI: Upload local image button clicked.");
            if (!websocket || websocket.readyState !== WebSocket.OPEN) {
                addMessageToChat("error", "Cannot upload image: Connection not open.");
                console.warn("[AgentWidgetDebug] UI Upload: WebSocket not open, cannot upload.");
                return;
            }
            imageUploadInput.click(); 
            if (imageOptionsPopup) imageOptionsPopup.style.display = 'none';
        });
    }

    // Camera button listener already includes logging.
    
    if (imageUploadInput) {
        imageUploadInput.addEventListener('change', async (event) => { // Made async
            console.log("[AgentWidgetDebug] UI: Image upload input 'change' event triggered.");
            const file = event.target.files[0];
            if (file) {
                console.log(`[AgentWidgetDebug] UI ImageUpload: File selected: ${file.name}, size: ${file.size}, type: ${file.type}`);
                if (file.size > 5 * 1024 * 1024) {
                    addMessageToChat("error", "Image is too large. Max 5MB allowed.");
                    imageUploadInput.value = '';
                    return;
                }
                await identifyImageAndProceed(file, file.name); // Call new function
                imageUploadInput.value = ''; // Reset file input
            } else {
                console.log("[AgentWidgetDebug] UI ImageUpload: No file selected in 'change' event.");
            }
        });
    }
    // --- End New Image Handling Logic ---

    if (closeButton) closeButton.addEventListener('click', () => {
        console.log("[AgentWidgetDebug] UI: Close button clicked.");
        clearStagedImage();
        closeAndResetWidget();
    });
    if (minimizeButton) minimizeButton.addEventListener('click', () => {
        console.log("[AgentWidgetDebug] UI: Minimize button clicked.");
        clearStagedImage();
        closeAndResetWidget();
    });
    if (endCallButton) endCallButton.addEventListener('click', () => {
        console.log("[AgentWidgetDebug] UI: End call button clicked.");
        clearStagedImage();
        closeAndResetWidget();
    });

    if (chatInput) {
        chatInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                 console.log("[AgentWidgetDebug] UI: Enter key pressed in chat input.");
                const textMessage = chatInput.value.trim();
                 if (textMessage !== '' || stagedImage) { // Process if there's text OR a staged image
                    if (stagedImage) {
                        console.log("[AgentWidgetDebug] UI EnterKey: Staged image exists.");
                        if (textMessage === '') { // If image exists but no text, prompt
                            addMessageToChat("system", "Please add a text query for the staged image.");
                            console.log("[AgentWidgetDebug] UI EnterKey: Text message empty for staged image, prompting user.");
                            return;
                        }
                        console.log("[AgentWidgetDebug] UI EnterKey: Sending combined image and text.");
                        addMessageToChat("user", textMessage, { name: stagedImage.name, base64DataUrl: stagedImage.dataUrl });
                        const augmentedTextMessage = "What is in the image I just uploaded? Also, " + textMessage;
                        sendMessageToServer({
                            parts: [
                                { mime_type: stagedImage.mime_type, data: stagedImage.data },
                                { mime_type: "text/plain", data: augmentedTextMessage }
                            ]
                        });
                        clearStagedImage();
                        chatInput.value = '';
                        initialGreetingSent = true;
                        console.log(`[AgentWidgetDebug] UI EnterKey: initialGreetingSent set to ${initialGreetingSent}.`);
                    } else if (textMessage !== '') { // Only text, no image
                        console.log("[AgentWidgetDebug] UI EnterKey: Sending text only message.");
                        addMessageToChat("user", textMessage);
                        sendMessageToServer({ mime_type: "text/plain", data: textMessage });
                        chatInput.value = '';
                        initialGreetingSent = true;
                        console.log(`[AgentWidgetDebug] UI EnterKey: initialGreetingSent set to ${initialGreetingSent}.`);
                    }
                 } else {
                     console.log("[AgentWidgetDebug] UI EnterKey: No text and no staged image. Nothing to send.");
                 }
            }
        });
        chatInput.disabled = true; 
    }

    if (micIcon) {
        micIcon.disabled = true; 
        micIcon.addEventListener('click', async () => {
            console.log(`[AgentWidgetDebug] UI: MicIcon Clicked. Current userDesiredAudioMode: ${userDesiredAudioMode}, current isWsAudioMode: ${isWsAudioMode}`);
            // console.log(`[MicIcon Click] Current userDesiredAudioMode: ${userDesiredAudioMode}, current WS audio mode: ${isWsAudioMode}`); // Original log
            const previousUserDesiredAudioMode = userDesiredAudioMode;
            userDesiredAudioMode = !userDesiredAudioMode; // Toggle user's intent
            console.log(`[AgentWidgetDebug] UI MicIcon: userDesiredAudioMode toggled from ${previousUserDesiredAudioMode} to ${userDesiredAudioMode}.`);

            if (userDesiredAudioMode) { // User wants to START audio
                console.log("[AgentWidgetDebug] UI MicIcon: User desires to START audio.");
                addMessageToChat("system", "Switching to audio mode...");
                showUIMode(true); 
                console.log("[AgentWidgetDebug] UI MicIcon: Calling connectWebSocketInternal(true).");
                await connectWebSocketInternal(true); 
            } else { // User wants to STOP audio (switch to text mode)
                console.log("[AgentWidgetDebug] UI MicIcon: User desires to STOP audio (switch to text mode).");
                addMessageToChat("system", "Switching to text mode...");
                console.log("[AgentWidgetDebug] UI MicIcon: Calling stopAudioCaptureAndProcessing.");
                stopAudioCaptureAndProcessing(); 
                showUIMode(false); 
                console.log("[AgentWidgetDebug] UI MicIcon: Calling connectWebSocketInternal(false).");
                await connectWebSocketInternal(false);
            }
            updateMicIcon(userDesiredAudioMode, websocket && websocket.readyState === WebSocket.OPEN);
            console.log("[AgentWidgetDebug] UI MicIcon: Mic icon updated.");
        });
    }

    if (chatIcon) { 
        chatIcon.addEventListener('click', () => {
            console.log("[AgentWidgetDebug] UI: ChatIcon Clicked. Switching to text mode.");
            // console.log("[ChatIcon Click] Switching to text mode."); // Original log
            userDesiredAudioMode = false;
            console.log(`[AgentWidgetDebug] UI ChatIcon: userDesiredAudioMode set to ${userDesiredAudioMode}.`);
            console.log("[AgentWidgetDebug] UI ChatIcon: Calling stopAudioCaptureAndProcessing.");
            stopAudioCaptureAndProcessing();
            showUIMode(false);
            console.log("[AgentWidgetDebug] UI ChatIcon: Calling connectWebSocketInternal(false).");
            connectWebSocketInternal(false);
            updateMicIcon(false, websocket && websocket.readyState === WebSocket.OPEN);
            console.log("[AgentWidgetDebug] UI ChatIcon: Mic icon updated.");
        });
    }
    
    if (videoToggleButton) {
        videoToggleButton.disabled = true; 
    }
    
    // Initial UI state
    console.log("[AgentWidgetDebug] Setting initial UI state.");
    showUIMode(false); // Start in text mode UI
    updateMicIcon(false, false); // Mic disabled initially

        // Listen for payment selection events
        document.addEventListener('checkoutPaymentSelected', (event) => {
            console.log("[AgentWidgetDebug] DOM Event 'checkoutPaymentSelected' received. Detail:", event.detail);
            if (event.detail) { 
                // console.log("[Agent Widget] Received 'checkoutPaymentSelected' DOM event. Detail:", event.detail); // Original log
                
                if (!websocket || websocket.readyState !== WebSocket.OPEN) {
                    console.warn("[AgentWidgetDebug] checkoutPaymentSelected: WebSocket not open/ready. Cannot send payment selection to agent.", event.detail);
                    return;
                }

                sendMessageToServer({
                    event_type: "ui_event", // Changed 'event' to 'event_type' for consistency
                    interaction: "payment_method_selected", // Changed 'sub_type' to 'interaction'
                    details: event.detail // Changed 'data' to 'details'
                });
                console.log("[AgentWidgetDebug] checkoutPaymentSelected: Payment selection details sent to agent via WebSocket.");
            } else {
                console.warn("[AgentWidgetDebug] checkoutPaymentSelected: Received event, but event.detail is missing.");
            }
        });

    // Listen for messages from script.js (parent window)
    window.addEventListener('message', (event) => {
        if (event.origin !== 'http://localhost:5000') { // Replace with your actual parent origin
            // console.warn(`[AgentWidgetDebug] Message from unexpected origin: ${event.origin}. Ignoring.`);
            return;
        }
        const { type, choice, address_text, address_index, reason } = event.data;
        console.log(`[AgentWidgetDebug] Received postMessage from parent: Type: ${type}, Choice: ${choice}, Address: ${address_text}, Index: ${address_index}, Reason: ${reason}`);

        if (type === 'shipping_option_chosen') {
            sendMessageToServer({
                event_type: "user_shipping_interaction",
                interaction: choice === 'home_delivery' ? "selected_home_delivery" : "selected_pickup_initiated"
            });
        } else if (type === 'pickup_address_chosen') {
            sendMessageToServer({
                event_type: "user_shipping_interaction",
                interaction: "selected_pickup_address",
                details: { text: address_text, index: address_index }
            });
        } else if (type === 'shipping_flow_interrupted') {
            sendMessageToServer({
                event_type: "user_shipping_interaction",
                interaction: "navigated_back_to_cart_review",
                details: { reason: reason }
            });
        }
    });
    console.log("[AgentWidgetDebug] Agent widget script fully loaded and initialized.");

    // --- Checkout Modal Logic ---
    console.log("[AgentWidgetDebug] Initializing checkout modal logic.");

    const deliveryModal = document.getElementById('delivery-modal');
    const paymentModal = document.getElementById('payment-modal');

    const continueToPaymentBtn = document.getElementById('continue-to-payment-btn');
    const backToDeliveryBtn = document.getElementById('back-to-delivery-btn');
    const submitPaymentBtn = document.getElementById('submit-payment-btn'); // Added as per HTML

    if (!deliveryModal || !paymentModal) {
        console.error("[AgentWidgetDebug] Checkout modal elements (delivery-modal or payment-modal) not found.");
    }
    if (!continueToPaymentBtn || !backToDeliveryBtn || !submitPaymentBtn) {
        console.error("[AgentWidgetDebug] Checkout navigation buttons not found.");
    }

    function showModal(modalElement) {
        if (modalElement) {
            console.log(`[AgentWidgetDebug] Showing modal: ${modalElement.id}`);
            modalElement.classList.add('modal-active');
            // Specific logs as per plan
            if (modalElement.id === 'delivery-modal') {
                console.log('Delivery modal opened');
            } else if (modalElement.id === 'payment-modal') {
                console.log('Payment modal opened');
            }
        } else {
            console.error("[AgentWidgetDebug] showModal: modalElement is null or undefined.");
        }
    }

    function hideModal(modalElement) {
        if (modalElement) {
            console.log(`[AgentWidgetDebug] Hiding modal: ${modalElement.id}`);
            modalElement.classList.remove('modal-active');
             if (modalElement.id === 'delivery-modal') {
                console.log('Delivery modal closed');
            } else if (modalElement.id === 'payment-modal') {
                console.log('Payment modal closed');
            }
        } else {
            console.error("[AgentWidgetDebug] hideModal: modalElement is null or undefined.");
        }
    }

    // Event Listeners for Modal Close Buttons
    const modalCloseBtns = agentWidget.querySelectorAll('.checkout-modal .modal-close-btn');
    if (modalCloseBtns) {
        modalCloseBtns.forEach(btn => {
            btn.addEventListener('click', (event) => {
                const modalToClose = event.target.closest('.checkout-modal');
                if (modalToClose) {
                    console.log(`[AgentWidgetDebug] Modal close button clicked for ${modalToClose.id}.`);
                    if (modalToClose.id === 'payment-modal') {
                        console.log('Payment modal close button clicked.');
                    } else if (modalToClose.id === 'delivery-modal') {
                        console.log('Delivery modal close button clicked.');
                    }
                    hideModal(modalToClose);
                    console.log('[AgentWidgetDebug] Checkout flow cancelled via close button. UI reverted to pre-checkout state (modals hidden). Temporary data would be cleared here.');
                } else {
                    console.error("[AgentWidgetDebug] Could not find parent modal for close button.");
                }
            });
        });
    } else {
        console.error("[AgentWidgetDebug] No modal close buttons found with class .modal-close-btn.");
    }


    // Event Listener for "Continue to Payment" Button
    if (continueToPaymentBtn && deliveryModal && paymentModal) {
        continueToPaymentBtn.addEventListener('click', () => {
            console.log('[AgentWidgetDebug] Continue to payment clicked. Hiding delivery, showing payment.');
            hideModal(deliveryModal);
            showModal(paymentModal);
        });
    }

    // Event Listener for "Back to Delivery" Button
    if (backToDeliveryBtn && deliveryModal && paymentModal) {
        backToDeliveryBtn.addEventListener('click', () => {
            console.log('[AgentWidgetDebug] Back to delivery clicked. Hiding payment, showing delivery.');
            hideModal(paymentModal);
            showModal(deliveryModal);
        });
    }

    // Event Listener for "Submit Payment" Button (Basic for now)
    if (submitPaymentBtn && paymentModal) {
        submitPaymentBtn.addEventListener('click', () => {
            console.log('[AgentWidgetDebug] Submit payment button clicked.');
            // Future: Implement payment submission logic
            // For now, just hide the payment modal as a placeholder action
            hideModal(paymentModal);
            console.log('[AgentWidgetDebug] Payment submitted (placeholder). Payment modal closed.');
            // Potentially show a success/thank you message or revert to a non-checkout state.
        });
    }
    
    // --- End Checkout Modal Logic ---

    // Example of how to show the delivery modal initially (for testing, remove later)
    // This would typically be triggered by an agent action or another UI event.
    // setTimeout(() => {
    //     if(deliveryModal) {
    //         console.log("[AgentWidgetDebug] TEST: Triggering delivery modal display for testing.");
    //         showModal(deliveryModal);
    //     }
    // }, 5000);


});
