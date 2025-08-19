# Customer Service Agent Enhancement Plan

This document outlines the plan to implement several enhancements to the customer service agent.

## Phase 1: Implement `after_tool_callback` Functionality

1.  **Modify [`agents/customer-service/customer_service/agent.py`](agents/customer-service/customer_service/agent.py):**
    *   **Import `after_tool`:**
        *   Locate the import block for callbacks:
            ```python
            from .shared_libraries.callbacks import (
                rate_limit_callback,
                before_agent,
                before_tool,
            )
            ```
        *   Add `after_tool` to this import statement. It should look like:
            ```python
            from .shared_libraries.callbacks import (
                rate_limit_callback,
                before_agent,
                before_tool,
                after_tool, # Added
            )
            ```
    *   **Register `after_tool_callback`:**
        *   In the `Agent` instantiation (around line 122), add the `after_tool_callback` parameter:
            ```python
            root_agent = Agent(
                model=configs.agent_settings.model,
                global_instruction=GLOBAL_INSTRUCTION,
                instruction=INSTRUCTION,
                name=configs.agent_settings.name,
                tools=[...], # Existing tools
                before_tool_callback=before_tool,
                after_tool_callback=after_tool, # Added
                before_agent_callback=before_agent,
                before_model_callback=rate_limit_callback,
            )
            ```
    *   **Considerations for `after_tool` in [`callbacks.py`](agents/customer-service/customer_service/shared_libraries/callbacks.py):**
        *   The existing `after_tool` function (lines 193-220) currently includes specific logic for `sync_ask_for_approval` and `approve_discount`.
        *   For the initial implementation of this task, this existing logic can remain. The primary goal is to register the callback. The function already includes logging (`logger.debug(f"after_tool triggered for tool: {tool.name}...")`) which will be beneficial. No immediate changes to the internal logic of `after_tool` are required for this specific task, beyond ensuring it's correctly imported and registered.

## Phase 2: Add "Don't output code" Prompt Constraint

1.  **Modify [`agents/customer-service/customer_service/prompts.py`](agents/customer-service/customer_service/prompts.py):**
    *   **Locate `INSTRUCTION` String:** This multi-line string starts around line 23.
    *   **Add Constraint:** Navigate to the `**Constraints:**` section (around line 102). Add the new constraint as a bullet point. The section should look similar to this:
        ```
        **Constraints:**

        *   You must use markdown to render any tables.
        *   **Never mention "tool_code", "tool_outputs", or "print statements" to the user.** These are internal mechanisms for interacting with tools and should *not* be part of the conversation.  Focus solely on providing a natural and helpful customer experience.  Do not reveal the underlying implementation details.
        *   Always confirm actions with the user before executing them (e.g., "Would you like me to update your cart?").
        *   Be proactive in offering help and anticipating customer needs.
        *   Don't output code even if user asks for it. # Added
        ```

## Phase 3: Dependency Review and Update

1.  **Verified Latest Package Versions:**
    *   `google-cloud-aiplatform`: `1.93.1` (Source: PyPI JSON API - `https://pypi.org/pypi/google-cloud-aiplatform/json`)
    *   `google-adk`: `1.0.0` (Source: PyPI JSON API - `https://pypi.org/pypi/google-adk/json`)

2.  **Modify [`agents/customer-service/pyproject.toml`](agents/customer-service/pyproject.toml):**
    *   **Update `google-cloud-aiplatform`:**
        *   Locate the line: `google-cloud-aiplatform = {extras = ["adk","agent_engine"], version = "^1.88.0"}` (around line 15).
        *   Change `^1.88.0` to `^1.93.1`.
        *   Locate the line in `[tool.poetry.group.dev.dependencies]`: `google-cloud-aiplatform = {extras = ["evaluation"], version = "^1.88.0"}` (around line 27).
        *   Change `^1.88.0` to `^1.93.1`.
    *   **Add `google-adk`:**
        *   Under `[tool.poetry.dependencies]`, add a new line: `google-adk = "^1.0.0"`.
        *   Example placement:
            ```toml
            [tool.poetry.dependencies]
            python = "^3.11"
            pydantic-settings = "^2.8.1"
            tabulate = "^0.9.0"
            cloudpickle = "^3.1.1"
            pylint = "^3.3.6"
            google-cloud-aiplatform = {extras = ["adk","agent_engine"], version = "^1.93.1"} # Updated
            google-adk = "^1.0.0" # Added
            requests = "^2.31.0"
            ```
    *   **Maintain `requests` and other dependencies:** Ensure `requests = "^2.31.0"` (line 16) and all other existing dependencies are preserved.

3.  **Verification Steps (Post-Modification, to be handled in Code Mode):**
    *   Run `poetry lock` in the `agents/customer-service/` directory.
    *   Run `poetry install` in the `agents/customer-service/` directory.
    *   (Optional but Recommended) Perform a basic test run of the agent.

## Mermaid Diagram of the Plan

```mermaid
graph TD
    A[Start: User Request for Enhancements] --> B{Phase 1: Implement after_tool_callback};
    B --> B1[Modify agent.py: Import after_tool];
    B --> B2[Modify agent.py: Register after_tool_callback];
    B --> B3[Review existing after_tool in callbacks.py - No changes needed];
    B --> C{Phase 2: Add Prompt Constraint};
    C --> C1[Modify prompts.py: Add 'Don't output code' to INSTRUCTION];
    C --> D{Phase 3: Dependency Review & Update};
    D --> D1[Verified latest versions: google-cloud-aiplatform (1.93.1) & google-adk (1.0.0)];
    D1 --> D2[Modify pyproject.toml: Update google-cloud-aiplatform to ^1.93.1];
    D1 --> D3[Modify pyproject.toml: Add google-adk ^1.0.0];
    D2 --> D4[Maintain other dependencies];
    D3 --> D4;
    D4 --> D5[Post-Mod Verification: poetry lock];
    D5 --> D6[Post-Mod Verification: poetry install];
    D6 --> D7[Post-Mod Verification: Basic agent test (optional)];
    D7 --> E[End: Plan Ready for Implementation];