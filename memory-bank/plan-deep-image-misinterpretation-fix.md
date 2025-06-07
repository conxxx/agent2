# Plan: Deep Dive into Image Misinterpretation and Agent Robustness (v2)

**User Reported Issue:** The `customer_service_agent` consistently misinterprets diverse images, often responding with a description like, "I see a close-up of what appears to be a green leafy vegetable, possibly lettuce or spinach..." regardless of the actual image content. This occurs even after previous attempts to fix client-side prompting, server-side data handling, model selection, and system prompt generalization.

**Overall Goal:** Identify why the `customer_service_agent` exhibits this behavior and implement a robust solution.

**Key Hypotheses:**
1.  The currently configured model (`gemini-2.0-flash-live-preview-04-09`) has a default or very low-quality image analysis output that consistently falls into a "leafy vegetable" category.
2.  A less obvious hardcoded response or fallback logic within the agent or its components gets triggered when an image is processed, specifically yielding this description.
3.  Interaction with tools (like `search_products`) based on a flawed initial image interpretation perpetuates the error.

**Investigation & Solution Phases:**

```mermaid
graph TD
    A[Start: Consistent "Leafy Vegetable" Misinterpretation] --> B{Phase 1: Isolate Core Model Behavior};
    B --> C[1.1 Minimal Test: Current 'Live' Model (`gemini-2.0-flash-live-preview-04-09`)];
    C -- "Leafy" Output? --> D{Live Model is Source};
    C -- Diverse Output? --> E{Live Model NOT Sole Source};
    D --> F[1.2 Ensure 'Pro' Model Config (e.g., `gemini-1.5-pro-latest`)];
    F --> G[1.3 Minimal Test: 'Pro' Model];
    G -- "Leafy" Output? --> H[Issue Deeper than Model Choice/ADK - Re-evaluate];
    G -- Diverse Output? --> I{Pro Model OK - Proceed to Phase 2};
    E --> F;
    I --> J{Phase 2: ADK Agent Configuration & Logic for Robustness};
    J --> K[2.1 Simplify/Default `generate_content_config` in Agent];
    J --> L[2.2 Strengthen Prompt for Low-Confidence Vision & Ambiguity];
    J --> M[2.3 Temp. Disable Tools (e.g., `search_products`) Post-Image Input];
    K & L & M --> N{Test Agent Accuracy & Behavior};
    N -- Improved? --> S[End: Improved Accuracy & Robustness];
    N -- No/Partial Improvement --> O{Phase 3: Advanced ADK Debugging};
    O --> P[3.1 'Clean Slate' Minimal ADK Vision Agent Test];
    P -- Works? --> Q[Compare Minimal Agent with `customer_service_agent`];
    P -- Fails? --> R[3.2 Examine ADK `Content` Object Structure / Suspect ADK/SDK Bug];
    Q --> S;
    R --> S;
    H --> S;
```

**Phase 1: Isolate Core Model Image Interpretation**
*   **Action 1.1 (Critical): Minimal Model Test Script with *Current* Model (`gemini-2.0-flash-live-preview-04-09`)**
    *   **Task:** Create a simple Python script using the `google-generativeai` SDK (outside of ADK) to send diverse test images directly to `gemini-2.0-flash-live-preview-04-09`.
    *   **Script Details:**
        *   Import `google.generativeai as genai`.
        *   Configure with API key.
        *   Instantiate `GenerativeModel(model_name="gemini-2.0-flash-live-preview-04-09")`.
        *   For each test image: Load image bytes, call `model.generate_content([image_part, "Describe this image in detail."])`, print response.
    *   **Goal:** Determine if this model itself is the source of the "leafy vegetable" response when used directly.
    *   **[MEMORIZE]** Verify latest `google-generativeai` SDK version and API. (Assumed `~0.7.1`). Source: `https://ai.google.dev/gemini-api/docs/get-started/python`

*   **Action 1.2: Confirm/Implement Correct "Pro" Model Usage**
    *   **Task:** If Action 1.1 shows the live model is problematic, ensure the agent configuration (`agents/customer-service/customer_service/config.py` and environment variables) is correctly and actively using a non-live "Pro" model (e.g., `gemini-1.5-pro-latest` or latest suitable equivalent).
    *   **Goal:** Switch to a model better suited for static image analysis if the current one is confirmed to be the issue.

*   **Action 1.3: Minimal Model Test Script with "Pro" Model**
    *   **Task:** If a "Pro" model is implemented/confirmed, repeat the minimal test script from Action 1.1 using this "Pro" model.
    *   **Goal:** Confirm the "Pro" model's baseline image understanding capability outside ADK.

**Phase 2: ADK Agent Configuration & Logic for Robustness**
*(Proceed if Phase 1 indicates the model (current or Pro) *can* interpret images correctly in isolation).*

*   **Action 2.1: Ensure `generate_content_config` is Minimal/Safe**
    *   **Task:** Review the `LlmAgent` instantiation in `agents/customer-service/customer_service/agent.py`. If `generate_content_config` is used, ensure it doesn't have extreme settings (e.g., very low `temperature`, restrictive `safety_settings`, unusual `top_p`, `top_k`). Temporarily simplify or remove it to use defaults.
    *   **Goal:** Rule out advanced model parameters as a cause of skewed output.

*   **Action 2.2: Strengthen Prompt for Handling Ambiguous/Failed Initial Interpretations**
    *   **Task:** Modify the image handling section in `agents/customer-service/customer_service/prompts.py` (lines 42-47).
    *   **Change Idea:** Add explicit instructions for the agent if its initial "objective description" is low-confidence or generic (e.g., "If your initial analysis is very generic, or if you have low confidence, explicitly state your uncertainty. In such cases, DO NOT immediately proceed to search for products. Instead, ask the user for more details.").
    *   **Goal:** Make the agent more cautious and interactive when its own image understanding is poor, rather than blindly proceeding with tools based on bad data.

*   **Action 2.3: Temporarily Disable `search_products` Tool Invocation After Image Input**
    *   **Task:** As a diagnostic step, temporarily modify the prompt logic in `agents/customer-service/customer_service/prompts.py` to *prevent* the agent from calling `search_products` (or related tools) immediately after an image is provided. Force it to *only* provide its objective description and then stop for user input.
    *   **Goal:** Clearly observe the agent's raw image interpretation within ADK, without it being immediately followed/masked by tool calls.

**Phase 3: Advanced ADK Debugging & "Clean Slate" Test**
*(Proceed if issues persist despite a good model and improved prompting).*

*   **Action 3.1: Create a "Clean Slate" Minimal Vision ADK Agent**
    *   **Task:** Create a new, extremely simple ADK `LlmAgent` in a separate test file.
    *   **Configuration:** Use the confirmed "Pro" Gemini model, minimal instruction ("Describe the image provided."), no tools, no complex `generate_content_config`, no `global_instruction`, no `examples`.
    *   **Test:** Send diverse images to this minimal agent.
    *   **Goal:** Establish a baseline for ADK's handling of multimodal input. If this works, the issue is in the `customer_service_agent`'s specifics. If it fails, it points to a deeper ADK/SDK issue.

*   **Action 3.2: Examine ADK `Content` Object Construction**
    *   **Task:** If the "clean slate" ADK agent also fails, investigate how the image `Part` is being added to the `Content` object that ADK sends to the Gemini API. This might involve adding debug logging to see the `Content` object structure.
    *   **Goal:** Ensure `mime_type` and image data (`inline_data` or `file_data`) are correctly populated and structured.

**Testing Strategy:**
*   Use a consistent set of diverse test images throughout all phases.
*   Log agent responses meticulously.
*   Restart the agent and test with new sessions after significant changes to avoid caching.
*   Consider checking ADK/SDK changelogs for known multimodal issues if problems are intractable.
*   If possible, log the exact payload sent to the Gemini API by ADK during later phases if the issue isn't resolved.