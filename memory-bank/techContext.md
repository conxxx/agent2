# Technical Context: Cymbal Home Garden E-commerce Platform & Agent Integration

## 1. Core Technologies
*   **E-commerce Backend Framework:** Flask (Python) - `localhost:5000`
*   **ADK Agent Server:** FastAPI-based (via `adk web` command) - `localhost:8000`
*   **Proxy Server:** Node.js with Express - `localhost:3000`
*   **Programming Languages:** Python 3.x (Flask, ADK), JavaScript (Agent Widget, Proxy Server)
*   **Database (E-commerce):** SQLite
*   **Agent Development:** Google Agent Development Kit (ADK)
*   **Real-time Communication:** WebSockets
*   **Client-Side Audio:** Web Audio API (AudioWorklets)
*   **CSS Custom Properties (Variables):** Utilized for dynamic website theming (e.g., night/day mode implementation in [`style.css`](cymbal_home_garden_backend/static/style.css:0)). Allows JavaScript to easily modify root style definitions.
*   **Browser `localStorage`:** Employed for client-side persistence of user preferences, specifically the selected website theme (managed in [`script.js`](cymbal_home_garden_backend/static/script.js:0)).
*   **`window.postMessage` for iframe-to-parent communication:** Utilized by the [`agent_widget.js`](cymbal_home_garden_backend/static/agent_widget.js:0) to send commands (e.g., theme changes, cart refresh requests) from the embedded agent widget to the main [`script.js`](cymbal_home_garden_backend/static/script.js:0) on the parent page. This is a standard and secure way to enable cross-origin communication between an iframe and its parent.

## 2. Key System Components & Interactions for Agent Widget Integration

### 2.1. E-commerce Platform (`cymbal_home_garden_backend/`, `app.py`)
*   Serves the main website (`index.html`) on `localhost:5000`.
*   `index.html` embeds the `agent_widget.html`.

### 2.2. Agent Widget (`agent_widget.html`, `agent_widget.js`)
*   Runs in the user's browser, loaded from `localhost:5000`.
*   **Session Creation:**
    *   Makes an HTTP POST request to `http://localhost:3000/apps/customer_service/users/user/sessions` (via Proxy).
    *   Sends `body: undefined` and `Accept: application/json, text/plain, */*` header. No `Content-Type` is sent for this request to ensure `Content-Length: 0`.
*   **WebSocket Connection:**
    *   Connects to `ws://localhost:3000/run_live?app_name=...&session_id=...` (via Proxy).

### 2.3. Node.js Proxy Server (`proxy-server.js`) - `localhost:3000`
*   **Purpose:** To overcome CORS restrictions between the widget (`localhost:5000`) and the ADK server (`localhost:8000`), and to correctly route requests.
*   **Key Libraries:** `express`, `cors`, `http` (native), `http-proxy-middleware`.
*   **CORS Handling:**
    *   `app.use(cors({ origin: function (origin, callback) { ... } }));`
    *   Dynamically allows origins `http://localhost:5000` and `http://127.0.0.1:5000`.
*   **Body Parsing:**
    *   `app.use(express.json());` - Ensures JSON bodies are parsed if present.
*   **HTTP Proxy for `/apps/**` (Session Creation):**
    *   Implemented using the native `http` module for fine-grained control.
    *   This was a critical fix because `http-proxy-middleware` was not correctly proxying the empty-body POST request, leading to 405 errors that appeared to originate from the proxy itself (the `onProxyReq` event was not firing).
    *   The manual proxy forwards the request (method, path, headers, ensuring `Content-Length: 0`) to `http://localhost:8000`.
*   **WebSocket Proxy for `/run_live`:**
    *   Uses `http-proxy-middleware`.
    *   Requires explicit handling of the main HTTP server's `upgrade` event:
        ```javascript
        server.on('upgrade', (req, socket, head) => {
            if (req.url.startsWith('/run_live')) {
                wsProxy.upgrade(req, socket, head);
            } else {
                socket.destroy();
            }
        });
        ```
    *   This ensures WebSocket upgrade requests are correctly passed to the middleware.

### 2.4. ADK Server (`adk web` command) - `localhost:8000`
*   **Session Endpoint (`/apps/{app}/users/{user}/sessions`):**
    *   Expects a `POST` request with `Content-Length: 0` (no body) to create a session.
    *   Responds with `200 OK` and a JSON body containing the `id` (session ID).
*   **WebSocket Endpoint (`/run_live`):**
    *   Standard ADK endpoint for real-time agent communication.

## 3. Technical Constraints & Debugging Insights for Proxy Integration
*   **CORS Origin Specificity:** Browsers treat `localhost` and `127.0.0.1` as different origins. Proxy's `Access-Control-Allow-Origin` must match the client's actual origin.
*   **HTTP Proxy Middleware Behavior (`http-proxy-middleware`):**
    *   Can exhibit unexpected behavior with certain request types (e.g., POST with empty body) where its internal request handling might not proceed to the `onProxyReq` stage or the actual proxying step, potentially leading to errors like 405 originating from the proxy itself.
    *   For WebSockets, explicit `server.on('upgrade', ...)` handling is often necessary when integrating with an existing Express server.
*   **Client-Side Request Formatting:** The exact formation of the `fetch` request (headers, body presence/absence) is critical for compatibility with the target server (ADK server in this case). The ADK Dev UI was used as a reference for the correct session creation request.
*   **Iterative Logging:** Adding log statements at each point (client `fetch`, proxy entry, before proxying to target, target response, proxy response to client) was essential to trace request flow and identify where errors or transformations occurred.

## 4. Tool Usage Patterns (for this integration task)
*   **`node proxy-server.js`**: To run the proxy.
*   **Flask app (`python app.py`)**: To serve the e-commerce site embedding the widget.
*   **ADK server (`adk web ...`)**: To run the agent backend.
*   **Browser Developer Tools (Network Tab & Console)**: Essential for inspecting requests/responses from the widget's perspective and seeing client-side errors.
*   **Terminal Output of Proxy Server**: Crucial for seeing how the proxy handles incoming requests and what it sends to the ADK server.
