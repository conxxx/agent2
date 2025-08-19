# ADK Streaming Server Coroutine Fix Report

## Issue Summary
The failing machine throws `ValidationError` for `InvocationContext.session` with error:
```
input_value=<coroutine object … get_session …> was never awaited
```

## Root Cause Analysis

**Working Machine (This Machine):**
- Uses `google-adk==0.5.0` 
- `InMemorySessionService.get_session()` and `create_session()` are **SYNCHRONOUS** (return `Session` objects directly)
- Code works because session methods return concrete objects immediately

**Failing Machine:**
- Likely has different `google-adk` version where session methods became **ASYNCHRONOUS** 
- Methods return coroutines that need to be awaited
- Code fails because coroutines are passed to `InvocationContext.session` instead of concrete `Session` objects

**Code Location:**
```python
# File: agents/customer-service/streaming_server.py, Lines 105-110
session_obj: ADKSessionType = session_service.get_session(...)  # Returns coroutine on failing machine
session_obj = session_service.create_session(...)              # Returns coroutine on failing machine
```

## Session Service Implementation (Working Machine)

**Current Implementation in google-adk==0.5.0:**
```python
# Both methods are SYNCHRONOUS (def, not async def)
@override
def get_session(self, *, app_name: str, user_id: str, session_id: str, 
                config: Optional[GetSessionConfig] = None) -> Session:
    # Returns Session object directly (or None)

@override  
def create_session(self, *, app_name: str, user_id: str, 
                   state: Optional[dict[str, Any]] = None, 
                   session_id: Optional[str] = None) -> Session:
    # Returns Session object directly
```

**Verification:**
- `get_session is async: False`
- `create_session is async: False`
- Both return concrete `Session` objects, not coroutines

## Call Site Analysis

**Single usage in repo (NOT AWAITED):**
```python
# File: agents/customer-service/streaming_server.py, Line 105-110
session_obj: ADKSessionType = session_service.get_session(
    app_name=app_name_str, user_id=user_id_str, session_id=session_id
)
if not session_obj:
    session_obj = session_service.create_session(
        app_name=app_name_str, user_id=user_id_str, session_id=session_id
    )
```

**Issue:** If failing machine has async versions, these return coroutines instead of Session objects.

## Runner Behavior Analysis

**Current google-adk==0.5.0 Runner:**
```python
# File: google/adk/runners.py, Line 396-405
return InvocationContext(
    session=session,  # <-- EXPECTS Session object, not coroutine
    # ... other parameters
)
```

**Expectation:** Runner expects synchronous `Session` objects. Does NOT await session retrieval.

## Remediation Options

### Option A: Code Changes (Version-Agnostic)
**Pros:** Works with both sync and async versions
**Cons:** Code complexity, requires async/await handling

### Option B: Pin Dependencies (Recommended)
**Pros:** Simple, no code changes, guaranteed consistency
**Cons:** May miss updates, potential version conflicts

**Recommendation: Option B** - Pin to working versions for stability.

## Working Environment Versions

```
python==3.12.1
google-adk==0.5.0
google-genai==1.14.0
pydantic==2.11.4
pydantic-core==2.33.2
fastapi==0.115.12
starlette==0.46.2
uvicorn==0.34.2
anyio==4.9.0
python-dotenv==1.1.0
websockets==15.0.1
```

## Fix Instructions for Failing Machine

### Step 1: Create constraints.txt
Create a file named `constraints.txt` with exact versions:

```txt
google-adk==0.5.0
google-genai==1.14.0
pydantic==2.11.4
pydantic-core==2.33.2
fastapi==0.115.12
starlette==0.46.2
uvicorn==0.34.2
anyio==4.9.0
python-dotenv==1.1.0
websockets==15.0.1
httpx==0.28.1
httpcore==1.0.9
h11==0.16.0
sniffio==1.3.1
typing_extensions==4.13.2
annotated-types==0.7.0
```

### Step 2: Install Exact Versions
Run these commands on the failing machine:

**Using pip:**
```bash
pip install --force-reinstall -r constraints.txt
```

**Using Poetry (if pyproject.toml exists):**
```bash
cd agents/customer-service
# Update pyproject.toml with exact versions first, then:
poetry install --sync
```

### Step 3: Verify Installation
```bash
python -c "from google.adk.sessions import InMemorySessionService; import inspect; s = InMemorySessionService(); print('get_session is async:', inspect.iscoroutinefunction(s.get_session))"
```

**Expected output:** `get_session is async: False`

## Verification Checklist

### Start Server
```bash
cd agents/customer-service
python streaming_server.py
```

### Success Indicators
1. **Server starts without errors:** 
   ```
   Starting Uvicorn server for streaming_server.py
   ```

2. **Agent loads successfully:** 
   ```
   [DIAG_TIME] Agent import block finished
   ```

3. **No coroutine warnings:** Should NOT see `was never awaited` errors

4. **WebSocket ready:** Server listens on `http://0.0.0.0:8001`

### WebSocket Test
In browser console:
```javascript
const ws = new WebSocket('ws://localhost:8001/ws/agent_stream/test_session');
ws.onopen = () => console.log('Connected');
ws.send(JSON.stringify({mime_type: "text/plain", data: "Hello"}));
```

**Expected success logs:**
```
[DIAG_LOG] WebSocket connection accepted for session_id: test_session
[DIAG_LOG] Attempting to get/create session for session_id: test_session
[DIAG_LOG] New session created for session_id: test_session
```

## Runtime Guardrail (Optional)

Add this validation function to catch the issue early:

```python
import inspect

# Add before line 137 in streaming_server.py:
def validate_session_not_coroutine(session_obj, session_id: str):
    """Validate that session is not a coroutine before passing to InvocationContext."""
    if inspect.iscoroutine(session_obj):
        raise RuntimeError(f"Session object for {session_id} is a coroutine and was never awaited. "
                          "This indicates a version mismatch in google-adk. "
                          "Expected synchronous Session object.")
    return session_obj

# Usage after session creation (around line 120):
session_obj = validate_session_not_coroutine(session_obj, session_id)
```

## Summary

**What to do on failing machine:**
1. Create `constraints.txt` with exact versions listed above
2. Run: `pip install --force-reinstall -r constraints.txt`
3. Test: `cd agents/customer-service && python streaming_server.py`
4. Verify no coroutine errors appear

**No code changes required** when using dependency pinning approach.

## Troubleshooting

**If still getting coroutine errors after version pinning:**
1. Check Python version: `python --version` (should be 3.12.x)
2. Verify ADK version: `pip show google-adk` (should be 0.5.0)
3. Clear pip cache: `pip cache purge`
4. Reinstall in clean environment

**Contact:** If issues persist, the failing machine may need a clean virtual environment rebuild.
