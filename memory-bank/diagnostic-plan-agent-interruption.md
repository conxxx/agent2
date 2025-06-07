# Diagnostic Plan: Agent Response Interruption Issue

This document outlines a structured diagnostic approach to investigate and identify the root cause of the agent's responses being interrupted or cut off.

## 1. Understanding the Problem & Scope

The core issue is interrupted or truncated agent responses, manifesting as:
*   Sentences being cut off mid-way.
*   The agent stopping one thought and abruptly starting another.
*   The stream ending before the complete thought is conveyed.

Investigation covers the entire lifecycle: LLM, Agent Framework (ADK), Backend Servers ([`agents/customer-service/streaming_server.py`](agents/customer-service/streaming_server.py:0), [`proxy-server.js`](proxy-server.js:0)), Frontend UI ([`cymbal_home_garden_backend/static/agent_widget.js`](cymbal_home_garden_backend/static/agent_widget.js:0), [`cymbal_home_garden_backend/templates/agent_widget.html`](cymbal_home_garden_backend/templates/agent_widget.html:0)), and Tool Call Interactions.

User has indicated no explicit console/network errors are visible.

## 2. Key Files for Investigation

*   Frontend:
    *   [`cymbal_home_garden_backend/static/agent_widget.js`](cymbal_home_garden_backend/static/agent_widget.js:0)
    *   [`cymbal_home_garden_backend/templates/agent_widget.html`](cymbal_home_garden_backend/templates/agent_widget.html:0)
*   Proxy:
    *   [`proxy-server.js`](proxy-server.js:0)
*   Backend & ADK:
    *   [`agents/customer-service/streaming_server.py`](agents/customer-service/streaming_server.py:0)
    *   `agents/customer-service/customer_service/live_streaming_agent_handler.py` (or equivalent ADK interaction point)
    *   Relevant ADK internal modules for streaming and tool calls.
*   Example/Reference:
    *   `adk-docs/examples/python/snippets/streaming/adk-streaming/app/google_search_agent/agent.py`

## 3. Hypothesized Potential Root Causes (Summary)

*   **LLM:** Premature stream end, content-related truncation.
*   **ADK / `live_streaming_agent_handler.py`:** Stream processing errors, incorrect chunk management, unhandled exceptions during streaming, state management issues around tool calls.
*   **Backend (`streaming_server.py`, `proxy-server.js`):** Errors in streaming implementation (Python generator, Node.js piping), buffer issues, incorrect error propagation, timeouts (proxy).
*   **Frontend UI (`agent_widget.js`):** Subtle JS stream handling bugs, chunk concatenation/rendering errors, event handling issues, premature client-side stream termination.
*   **Tool Call Interactions:** Flawed stream pause/resume logic, UI state conflicts, backend coordination issues for tool calls.

## 4. Proposed Structured Diagnostic Approach

### Phase 1: Frontend Deep Dive ([`agent_widget.js`](cymbal_home_garden_backend/static/agent_widget.js:0) & [`agent_widget.html`](cymbal_home_garden_backend/templates/agent_widget.html:0))
*   **Goal:** Rule out subtle client-side issues.
*   **Actions:**
    1.  Log all received raw chunks in `agent_widget.js` before processing.
    2.  Inspect frontend's stream termination logic.
    3.  Analyze UI interaction for tool calls (pause/resume stream rendering).
    4.  Temporarily simplify rendering to `console.log()` to isolate DOM issues.
    5.  Examine event listeners for stream messages.

### Phase 2: Proxy Server Investigation ([`proxy-server.js`](proxy-server.js:0))
*   **Goal:** Verify stream integrity through the proxy.
*   **Actions:**
    1.  Log incoming (from Python) and outgoing (to frontend) stream data chunks.
    2.  Review Node.js stream handling code (piping, events, buffers).
    3.  Ensure correct error propagation from the Python backend.

### Phase 3: Python Backend & ADK Investigation ([`streaming_server.py`](agents/customer-service/streaming_server.py:0), `live_streaming_agent_handler.py`, ADK)
*   **Goal:** Pinpoint issues in backend/ADK stream generation and handling.
*   **Actions:**
    1.  Log raw LLM output, ADK input/output chunks, and chunks sent by `streaming_server.py`.
    2.  Inspect stream generation logic (e.g., Python generator) in `streaming_server.py`.
    3.  Examine ADK's (and custom handler's) tool call stream management (pause/resume).
    4.  Review ADK configurations (streaming, timeouts, chunking).
    5.  Isolate ADK vs. custom handler issues if possible.

### Phase 4: LLM Interaction
*   **Goal:** Investigate LLM output characteristics.
*   **Actions:**
    1.  Analyze raw LLM chunks (logged in Phase 3) for anomalies (small/empty chunks, stop sequences).
    2.  Test with different prompts/models if feasible.

### General Diagnostic Principles:
*   Strive for reproducibility.
*   Use incremental logging.
*   Employ divide and conquer strategy.
*   Use version control for diagnostic changes.

## 5. Mermaid Diagram of Investigation Flow

```mermaid
graph TD
    A[Start: User Reports Interruption] --> B{No Console/Network Errors};
    B --> C[Phase 1: Frontend Analysis - agent_widget.js];
    C --> C1[Log Received Chunks];
    C --> C2[Inspect Stream Termination Logic];
    C --> C3[Analyze Tool Call UI Interaction];
    C --> D[Phase 2: Proxy Server Analysis - proxy-server.js];
    D --> D1[Log Incoming/Outgoing Stream Data];
    D --> D2[Review Stream Handling Code];
    D --> E[Phase 3: Python Backend/ADK Analysis];
    E --> E1[Log LLM Output & ADK I/O in live_streaming_agent_handler.py];
    E --> E2[Inspect stream_server.py Generator];
    E --> E3[Examine ADK Tool Call Handling];
    E --> F[Phase 4: LLM Interaction Analysis];
    F --> F1[Analyze Raw LLM Chunks];
    F --> G[Identify Root Cause(s)];
    G --> H[Propose Fixes for Code/Debug Mode];

    subgraph Frontend
        C1
        C2
        C3
    end

    subgraph Proxy
        D1
        D2
    end

    subgraph Backend
        E1
        E2
        E3
    end

    subgraph LLM
        F1
    end