# Speaker Agent Streamlit Applications

This directory contains Streamlit applications demonstrating different ways to interact with the Speaker Agent.

## Applications

1.  **`speaker_app.py` (ADK API Server Mode)**
    - **Purpose:** Interacts with the Speaker Agent *through* the main `adk api_server`.
    - **Requires:** `adk api_server` running on `http://localhost:8000`.
    - **Run:** `streamlit run apps/speaker_app.py`

2.  **`a2a_speaker_app.py` (Standalone A2A Mode)**
    - **Purpose:** Interacts *directly* with the Speaker Agent running as a standalone Agent-to-Agent (A2A) service.
    - **Requires:** Standalone Speaker Agent running (`python -m agents.speaker`) on `http://localhost:8003`.
    - **Run:** `streamlit run apps/a2a_speaker_app.py`

## Key Differences in Interaction

The primary differences lie in how requests are sent and responses are handled:

| Feature              | `speaker_app.py` (via `adk api_server`)                               | `a2a_speaker_app.py` (Standalone A2A)                            |
| :------------------- | :-------------------------------------------------------------------- | :--------------------------------------------------------------- |
| **Target URL**       | `http://localhost:8000/run`                                           | `http://localhost:8003/run`                                      |
| **Session Handling** | Explicit: Must call `/apps/.../sessions` endpoint first (via UI button) | Implicit: `session_id` sent with each `/run` request             |
| **Request Payload**  | ADK structure (`app_name`, `user_id`, `session_id`, `new_message`)    | Simple A2A structure (`message`, `context`, `session_id`)        |
| **Response Format**  | Stream of ADK event JSON objects                                      | Single structured JSON (`AgentResponse` model)                   |
| **Response Parsing** | Iterates through events, looks for `model` role or `functionResponse` | Directly accesses fields like `message` and `data.audio_url`     |
| **Agent Definition** | Relies on `adk api_server` using `agents/speaker/agent.py`            | Relies on `agents/speaker/__main__.py` instantiating the `Agent` |

### Request Payload Example (`speaker_app.py` -> `adk api_server`)

```json
{
  "app_name": "speaker",
  "user_id": "user-xxx",
  "session_id": "session-yyy",
  "new_message": {
    "role": "user",
    "parts": [{"text": "Say hello world"}]
  }
}
```

### Request Payload Example (`a2a_speaker_app.py` -> Standalone Agent)

```json
{
  "message": "Say hello world",
  "context": {
    "user_id": "user-xxx"
  },
  "session_id": "conv-zzz"
}
```

### Response Parsing (`speaker_app.py`)

The app needs to loop through multiple JSON events returned by the `adk api_server`. It looks for specific event structures, like a `functionResponse` from the `text_to_speech` tool, often extracting information from nested text fields (like log messages).

### Response Parsing (`a2a_speaker_app.py`)

The app receives a single JSON object. It directly accesses keys like `response['message']` and `response['data']['audio_url']` based on the expected `AgentResponse` structure defined in `common/a2a_server.py`.

These differences illustrate the distinct communication patterns when interacting with an ADK agent via the framework's `api_server` versus a direct A2A connection to a standalone agent service. 