# Plan: Update Memory Bank for Agent-Triggered Cart Refresh

This document outlines the plan to update the Memory Bank files to reflect the implementation of the agent-triggered cart refresh functionality.

## 1. File: `memory-bank/activeContext.md`

*   **Action:** Add a new entry at the top under "Recent Changes" detailing the implementation of the agent-triggered cart refresh mechanism.
*   **Proposed Text (to be inserted at the beginning of the file):**

    ```markdown
    [YYYY-MM-DD HH:MM:SS] - Recent Changes: Implemented agent-triggered cart refresh functionality.
        - Agent tools (`agents/customer-service/customer_service/tools/tools.py`) updated to potentially return `{"action": "refresh_cart"}`.
        - Streaming Server (`agents/customer-service/streaming_server.py`) updated to send a WebSocket command `{"type": "command", "command_name": "refresh_cart"}`.
        - Agent Widget (`cymbal_home_garden_backend/static/agent_widget.js`) updated to relay this command via `window.parent.postMessage`.
        - Main Page (`cymbal_home_garden_backend/static/script.js`) updated to listen for this `postMessage` and trigger cart re-fetch/re-render.
    [YYYY-MM-DD HH:MM:SS] - Current Focus: Updating Memory Bank to reflect agent-triggered cart refresh feature completion.
    [YYYY-MM-DD HH:MM:SS] - Key Learnings & Patterns:
        - The existing agent-to-frontend communication pattern (WebSocket -> iframe `postMessage` -> main page listener) is reusable for various agent-initiated UI updates, now including cart refresh.
    [YYYY-MM-DD HH:MM:SS] - Next Steps: Evaluate further tasks now that agent-triggered cart refresh is complete.
    ```
    *(Note: `[YYYY-MM-DD HH:MM:SS]` will be replaced with the current timestamp upon implementation.)*

## 2. File: `memory-bank/progress.md`

*   **Action:** Add a new "Task Completed" entry.
*   **Proposed Text (to be inserted after the latest "Task Completed" or "Task Update" entry, likely at the top or near the top):**

    ```markdown
    [YYYY-MM-DD HH:MM:SS] - Task Completed: Agent-initiated cart updates are visually reflected on the website.
        - Description: Implemented a 'refresh_cart' command flow allowing the agent to trigger a visual refresh of the shopping cart on the main website. This involved changes in agent tools, the ADK streaming server, the agent widget JavaScript, and the main page JavaScript.
        - Status: Functionality implemented as reported.
    ```
    *(Note: `[YYYY-MM-DD HH:MM:SS]` will be replaced with the current timestamp upon implementation.)*

## 3. File: `memory-bank/systemPatterns.md`

*   **Action:** Document the new communication pattern for cart refresh, similar to the existing theme change pattern. Add a new subsection under "5. Key Design Patterns & Decisions".
*   **Proposed Text and Mermaid Diagram:**

    ```markdown
    ### 5.5 Agent-to-Frontend Cart Refresh Communication

    A communication pattern enables the agent to trigger a refresh of the shopping cart on the main website, ensuring visual consistency after agent-initiated modifications. This pattern is similar to the theme control communication.

    1.  **Agent Tool Action:** An agent tool (e.g., after modifying the cart) returns an action, such as `{"action": "refresh_cart"}`.
    2.  **Streaming Server (`streaming_server.py`):** Recognizes this action and sends a WebSocket command to the agent widget, like `{"type": "command", "command_name": "refresh_cart"}`.
    3.  **Agent Widget (`agent_widget.js`):** Receives the WebSocket command and uses `window.parent.postMessage({ type: 'refresh_cart_command' }, '*')` to send a message to the main page (parent window).
    4.  **Main Page (`script.js`):** Listens for the `message` event. If the message type is `refresh_cart_command`, it triggers a function to re-fetch cart data from the backend and re-render the cart display.

    ```mermaid
    sequenceDiagram
        participant AgentTool as Agent Tool (`tools.py`)
        participant StreamingServer as Streaming Server (`streaming_server.py`)
        participant AgentWidget as Agent Widget (`agent_widget.js`)
        participant MainPage as Main Page (`script.js`)
        participant BackendAPI as Backend API (`app.py`)
        participant CartUI as Cart UI (DOM)

        AgentTool->>StreamingServer: Returns action: {"action": "refresh_cart"}
        StreamingServer->>AgentWidget: WebSocket: {"type": "command", "command_name": "refresh_cart"}
        AgentWidget->>MainPage: window.parent.postMessage({ type: 'refresh_cart_command' })
        MainPage->>BackendAPI: Fetch updated cart data
        BackendAPI-->>MainPage: Return cart data
        MainPage->>CartUI: Re-render cart display
    ```

    This pattern leverages `postMessage` to securely communicate commands from the sandboxed agent widget iframe to the main application page, enabling real-time UI updates based on agent actions.
    ```

## 4. File: `memory-bank/techContext.md`

*   **Action:** Note any new specific technical details or patterns. Since the `postMessage` pattern is already mentioned for theme control, this will be an addition to emphasize its reuse.
*   **Proposed Text (adding to "Core Technologies"):**

    ```markdown
    *   **`window.postMessage` for iframe-to-parent communication:** Utilized by the `agent_widget.js` to send commands (e.g., theme changes, cart refresh requests) from the embedded agent widget to the main `script.js` on the parent page. This is a standard and secure way to enable cross-origin communication between an iframe and its parent.