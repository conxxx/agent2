# Project Workflow Diagram

```mermaid
graph TD
    %% === Subgraphs for Major Components ===
    subgraph "Data Setup & Management"
        direction TB
        DS_Setup[database_setup.py] --> DB[(SQLite: ecommerce.db)]
        DS_Import[sample_data_importer.py] --> DB
        DS_JsonL[generate_vertex_ai_jsonl.py] --> DB
        DS_JsonL --> VertexAISearch[Vertex AI Search for Commerce]
        style VertexAISearch fill:#F9E79F,stroke:#333,stroke-width:2px
    end

    subgraph "E-commerce Platform (localhost:5000)"
        direction TB
        User[End User] --> Browser[User's Browser]
        Browser -- Accesses --> Ecomm_Frontend[Frontend: index.html, script.js, style.css]
        Ecomm_Frontend -- API Calls (Products, Cart) --> Ecomm_API[Flask Backend: app.py]
        Ecomm_API -- CRUD Operations --> DB
        Ecomm_API -- Serves --> Ecomm_Frontend
        Ecomm_Frontend -- Displays --> ProductPages[Product Detail Pages: product_detail.html]
        Ecomm_API -- Serves --> ProductPages
        style Ecomm_Frontend fill:#A7D0F8,stroke:#333,stroke-width:2px
        style Ecomm_API fill:#A7D0F8,stroke:#333,stroke-width:2px
        style ProductPages fill:#A7D0F8,stroke:#333,stroke-width:2px
    end

    subgraph "Agent System Integration"
        direction TB
        Ecomm_Frontend -- Embeds --> AgentWidgetUI[Agent Widget UI: agent_widget.html/js]
        
        subgraph "Proxy Server (localhost:3000)"
            Proxy[Node.js Proxy: proxy-server.js]
            style Proxy fill:#E8DAEF,stroke:#333,stroke-width:2px
        end

        subgraph "ADK Customer Service Agent System (localhost:8000)"
            direction TB
            ADK_HTTP[ADK HTTP Endpoint (Sessions)]
            ADK_WS[ADK WebSocket Endpoint (run_live)]
            ADK_StreamingServer[Streaming Server: streaming_server.py] -- Manages --> ADK_WS
            ADK_Agent[ADK Agent: agent.py, config.py]
            ADK_Tools[Agent Tools: tools.py]
            Gemini[Gemini Live API Model]
            
            ADK_StreamingServer -- Invokes --> ADK_Agent
            ADK_Agent -- Uses --> Gemini
            ADK_Agent -- Uses --> ADK_Tools
            ADK_Tools -- API Calls to E-commerce --> Ecomm_API

            style ADK_HTTP fill:#A9CCE3,stroke:#333,stroke-width:2px
            style ADK_WS fill:#A9CCE3,stroke:#333,stroke-width:2px
            style ADK_StreamingServer fill:#AED6F1,stroke:#333,stroke-width:2px
            style ADK_Agent fill:#AED6F1,stroke:#333,stroke-width:2px
            style ADK_Tools fill:#FAD7A0,stroke:#333,stroke-width:2px
            style Gemini fill:#A2D9CE,stroke:#333,stroke-width:2px
        end
        
        AgentWidgetUI -- HTTP Session Req --> Proxy
        Proxy -- Forwards HTTP --> ADK_HTTP
        ADK_HTTP -- Session ID --> Proxy
        Proxy -- Session ID --> AgentWidgetUI
        
        AgentWidgetUI -- WebSocket Connect & Chat/Voice/Video --> Proxy
        Proxy -- Forwards WebSocket --> ADK_WS

        ADK_StreamingServer -- Agent Responses (Text, Audio, Commands) via WebSocket --> Proxy
        Proxy -- Agent Responses via WebSocket --> AgentWidgetUI
        AgentWidgetUI -- Displays Agent Output --> Browser

        %% Agent-driven UI updates
        AgentWidgetUI -- window.postMessage (Theme, Cart Refresh) --> Ecomm_Frontend
        Ecomm_Frontend -- Updates UI (e.g., applyTheme(), refreshCart()) --> Browser
    end

    %% === General Styling ===
    style User fill:#F5B7B1,stroke:#333,stroke-width:2px
    style Browser fill:#D2B4DE,stroke:#333,stroke-width:2px
    style DB fill:#DBF8A7,stroke:#333,stroke-width:2px
    style AgentWidgetUI fill:#D7BDE2,stroke:#333,stroke-width:2px

    %% === Connections between major subgraphs ===
    Ecomm_API -.-> VertexAISearch_Lookup((Vertex AI Search Lookup))
    VertexAISearch_Lookup -.-> Ecomm_API
    style VertexAISearch_Lookup fill:#F9E79F,stroke:#333,stroke-width:1px,stroke-dasharray: 5 5

    %% Annotations for clarity
    note right of DS_JsonL: Generates feed for search indexing
    note right of Ecomm_API: Handles business logic, data access
    note right of ADK_Agent: Core agent logic, LLM interaction, tool use
    note left of Proxy: Mitigates CORS, routes traffic
end
