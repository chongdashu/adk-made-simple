# Lesson 4: Serving Agents via A2A Protocol

## Project Folder Summary

In this lesson, we will be focusing on the Agent-to-Agent (A2A) protocol. Here's a summary of the key file changes within the project structure:

```
project-root/
├── common/
│   └── a2a_server.py            # ADDED: Core A2A server framework
├── agents/
│   └── speaker/
│       ├── __main__.py          # ADDED: A2A server entry point for Speaker Agent
│       ├── task_manager.py      # ADDED: Handles A2A requests/responses for Speaker
│       ├── agent.py             # MODIFIED: Align instructions for A2A
│       └── .well-known/
│           └── agent.json       # ADDED: A2A metadata for Speaker Agent (auto-generated)
├── apps/
│   └── a2a_speaker_app.py       # ADDED: Streamlit UI for A2A Speaker Agent
└── requirements.txt             # MODIFIED: Add FastAPI, Uvicorn
```

**Legend:**
- `ADDED`: New file created in this lesson.
- `MODIFIED`: Existing file updated in this lesson.

---

In this lesson, we'll explore how to serve our agents using the Agent-to-Agent (A2A) protocol, which provides a standardized way for agents to communicate with each other and with external systems.

## Key Components

### 1. A2A Server Implementation (`common/a2a_server.py`)

The core server implementation provides standardized request/response models and server creation:

```python
class AgentRequest(BaseModel):
    message: str = Field(..., description="The message to process")
    context: Dict[str, Any] = Field(default_factory=dict)
    session_id: Optional[str] = Field(None)

class AgentResponse(BaseModel):
    message: str = Field(..., description="The response message")
    status: str = Field(default="success")
    data: Dict[str, Any] = Field(default_factory=dict)
    session_id: Optional[str] = Field(None)

def create_agent_server(name: str, description: str, task_manager: Any) -> FastAPI:
    app = FastAPI(title=f"{name} Agent", description=description)
    # ... server setup ...
    return app
```

### 2. Agent Server Setup (`agents/speaker/__main__.py`)

The Speaker Agent uses the A2A server implementation:

```python
from common.a2a_server import AgentRequest, AgentResponse, create_agent_server

async def main():
    # Initialize agent and task manager
    agent_instance, exit_stack = await root_agent
    task_manager_instance = TaskManager(agent=agent_instance)
    
    # Create A2A server
    app = create_agent_server(
        name=agent_instance.name,
        description=agent_instance.description,
        task_manager=task_manager_instance 
    )
    
    # Run server on port 8003
    config = uvicorn.Config(app, host=host, port=port)
    await server.serve()
```

### 3. Task Processing (`agents/speaker/task_manager.py`)

The TaskManager handles A2A requests and formats responses:

```python
async def process_task(self, message: str, context: Dict[str, Any], session_id: Optional[str]) -> Dict[str, Any]:
    try:
        # Run the agent
        events_async = self.runner.run_async(
            user_id=context.get("user_id", "default_user"),
            session_id=session_id,
            new_message=request_content
        )
        
        # Process and format response
        return {
            "message": final_message,
            "status": "success",
            "data": {
                "audio_url": audio_url,
                "raw_events": raw_events[-3:]
            }
        }
    except Exception as e:
        return {
            "message": f"Error: {str(e)}",
            "status": "error",
            "data": {"error_type": type(e).__name__}
        }
```

### 4. Agent Metadata (`.well-known/agent.json`)

The A2A server automatically generates metadata about the agent's capabilities:

```json
{
  "name": "speaker_agent",
  "description": "Text-to-speech agent that converts written content to spoken audio using Eleven Labs",
  "endpoints": ["run", "health", "speak"],
  "version": "1.0.0",
  "capabilities": ["text_to_speech", "audio_synthesis", "voice_selection"],
  "input_format": "text/plain",
  "output_format": "application/json",
  "dependencies": ["elevenlabs"]
}
```

This metadata enables automatic discovery and integration.

## Using the A2A Protocol

### 1. Starting the Agent in A2A Mode

To run your Speaker Agent with the A2A server, navigate to your project's root directory and execute its main module:

```bash
python -m agents.speaker
```

This command starts the FastAPI server (via Uvicorn) typically on `http://127.0.0.1:8003` (or as configured by environment variables `SPEAKER_A2A_HOST` and `SPEAKER_A2A_PORT`). You should see log output indicating the server has started, for example:

```
INFO:     Uvicorn running on http://127.0.0.1:8003 (Press CTRL+C to quit)
INFO:     Started reloader process [xxxxx] using statreload
INFO:     Started server process [xxxxx]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

### 2. Verifying with Basic Requests

Once the server is running, you can verify its basic functionality using `curl` or a tool like Postman.

**A. Check Agent Metadata:**

First, let's retrieve the agent's capabilities from the `.well-known/agent.json` endpoint. This confirms the agent is discoverable and describes its endpoints.

```bash
curl http://127.0.0.1:8003/.well-known/agent.json
```

Or in Postman:
- Method: `GET`
- URL: `http://127.0.0.1:8003/.well-known/agent.json`

You should receive a JSON response similar to the `agent.json` content shown earlier, detailing the agent's name, description, and available endpoints (e.g., "run", "health", "speak").

**B. Test the `/run` Endpoint:**

Next, send a POST request to the `/run` endpoint to make the agent perform its primary task (text-to-speech).

```bash
curl -X POST "http://127.0.0.1:8003/run" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Hello, A2A world!",
    "context": {"user_id": "test-user-123"},
    "session_id": "test-session-abc"
  }'
```

Or in Postman:
- Method: `POST`
- URL: `http://127.0.0.1:8003/run`
- Headers: `Content-Type: application/json`
- Body (raw, JSON):
  ```json
  {
    "message": "Hello, A2A world!",
    "context": {"user_id": "test-user-123"},
    "session_id": "test-session-abc"
  }
  ```

A successful request will return a JSON response structured like the `AgentResponse` model, including the agent's spoken message and a URL to the generated audio file:

```json
{
  "message": "I've converted your text to speech. The audio file is saved at `/tmp/audio_output/audio_xyz.mp3`",
  "status": "success",
  "data": {
    "audio_url": "file:///tmp/audio_output/audio_xyz.mp3",
    "raw_events": [...]
  },
  "session_id": "test-session-abc"
}
```

If you receive these responses, your A2A Speaker Agent is running correctly!

### 3. Interactive Demo Application (`apps/a2a_speaker_app.py`)

A Streamlit application demonstrates how to interact with the A2A agent:

```python
# Initialize session state
if "user_id" not in st.session_state:
    st.session_state.user_id = f"user-{uuid.uuid4()}"
if "session_id" not in st.session_state:
    st.session_state.session_id = f"conv-{uuid.uuid4()}"

def send_message(message):
    """Send message to A2A endpoint and process response."""
    payload = {
        "message": message,
        "context": {
            "user_id": st.session_state.user_id
        },
        "session_id": st.session_state.session_id
    }
    
    response = requests.post(
        f"{API_BASE_URL}/run",
        headers={"Content-Type": "application/json"},
        json=payload,
        timeout=30
    )
    
    # Process A2A response
    response_data = response.json()
    audio_url = response_data.get("data", {}).get("audio_url")
    
    # Display audio in UI
    if audio_url and audio_url.startswith("file://"):
        audio_path = audio_url.replace("file://", "")
        if os.path.exists(audio_path):
            st.audio(audio_path)
```

The app provides:
- Automatic session management
- Direct A2A protocol interaction
- Audio playback integration
- Error handling
- Real-time response processing

To run the demo:
```bash
# Start the A2A agent
python -m agents.speaker

# In another terminal, run the Streamlit app
streamlit run apps/a2a_speaker_app.py
```

## Benefits of A2A Protocol

1. **Standardized Communication**
   - Consistent request/response format
   - Well-defined error handling
   - Structured metadata

2. **Easy Integration**
   - FastAPI-based server
   - Automatic OpenAPI documentation
   - Simple HTTP endpoints

3. **Flexible Deployment**
   - Standalone operation
   - Port configuration
   - Environment variable support

## Best Practices

1. **Error Handling**
   - Return structured error responses
   - Include error details in data field
   - Use appropriate HTTP status codes

2. **Response Formatting**
   - Follow the AgentResponse model
   - Include relevant metadata
   - Use clear status messages

3. **Security**
   - Validate input data
   - Sanitize file paths
   - Consider authentication needs

## Next Steps

1. Add more endpoints for specific functionality
2. Implement authentication
3. Add monitoring and metrics
4. Create interactive demos
5. Enhance error handling

The A2A protocol provides a standardized way to expose agent functionality, making it easier to integrate with other systems while maintaining compatibility with the ADK ecosystem.
