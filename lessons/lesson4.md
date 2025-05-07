# Lesson 4: Serving Agents via A2A Protocol

In this lesson, we'll explore how to serve our agents using the Agent-to-Agent (A2A) protocol, which provides a more flexible and standardized way to expose agent functionality compared to the ADK API server approach.

## What is A2A Protocol?

The Agent-to-Agent (A2A) protocol is a standardized way for agents to communicate with each other and with external systems. It provides:

1. A consistent request/response format
2. Built-in session management
3. Standardized metadata discovery
4. Flexible endpoint registration

## Key Components

### 1. A2A Server Implementation

The core of our A2A implementation is in `common/a2a_server.py`, which provides:

```python
class AgentRequest(BaseModel):
    message: str
    context: Dict[str, Any]
    session_id: Optional[str]

class AgentResponse(BaseModel):
    message: str
    status: str
    data: Dict[str, Any]
    session_id: Optional[str]
```

This standardized format ensures consistent communication between agents.

### 2. Agent Registration and Discovery

The A2A server automatically creates a `.well-known/agent.json` file that describes the agent's capabilities:

```json
{
    "name": "agent_name",
    "description": "agent_description",
    "endpoints": ["run", "custom_endpoint1", "custom_endpoint2"],
    "version": "1.0.0"
}
```

This enables automatic discovery of agent capabilities.

## Benefits Over ADK API Server

### 1. Simplified Integration

Instead of relying on the ADK API server's complex event stream format:

```python
# Old ADK API Server approach
response = requests.post("http://localhost:8000/run", json={
    "app_name": "speaker",
    "user_id": "user123",
    "session_id": "session123",
    "new_message": {
        "role": "user",
        "parts": [{"text": "Hello"}]
    }
})
```

We now have a cleaner A2A format:

```python
# New A2A approach
response = requests.post("http://localhost:8003/run", json={
    "message": "Hello",
    "context": {"user_id": "user123"},
    "session_id": "session123"
})
```

### 2. Direct Access

- No need to run the full ADK API server
- Agents can be accessed directly on their own ports
- Simpler deployment and scaling

### 3. Better Response Structure

The A2A protocol provides a more structured response format:

```python
{
    "message": "Response message",
    "status": "success",
    "data": {
        "audio_url": "file:///path/to/audio.mp3",
        "additional_data": {...}
    },
    "session_id": "session123"
}
```

This makes it easier to extract specific information like audio URLs.

### 4. Custom Endpoints

The A2A server allows registering custom endpoints:

```python
endpoints = {
    "custom_endpoint": custom_handler
}
app = create_agent_server(
    name="speaker",
    description="Text-to-Speech Agent",
    task_manager=task_manager,
    endpoints=endpoints
)
```

## Implementation Example

Here's how to implement an A2A-compatible agent:

```python
from common.a2a_server import create_agent_server, AgentRequest, AgentResponse

class SpeakerAgent:
    def __init__(self):
        self.task_manager = TaskManager()
        
    async def process_task(self, message: str, context: dict, session_id: str) -> dict:
        # Process the task and return structured response
        return {
            "message": "Audio generated successfully",
            "data": {
                "audio_url": "file:///path/to/audio.mp3"
            }
        }

    def create_server(self):
        return create_agent_server(
            name="speaker",
            description="Text-to-Speech Agent",
            task_manager=self.task_manager
        )

# Run the server
agent = SpeakerAgent()
app = agent.create_server()
```

## Testing A2A Endpoints

We've added test scripts to verify A2A functionality:

```bash
# Test A2A audio extraction
./scripts/tests/speaker/test_a2a_extract_audio.sh
```

This script demonstrates how to:
1. Send requests to the A2A endpoint
2. Parse structured responses
3. Extract audio URLs
4. Verify file existence

## Best Practices

1. **Error Handling**
   - Always return structured error responses
   - Include error details in the `data` field
   - Use appropriate HTTP status codes

2. **Session Management**
   - Use the provided `session_id` for stateful operations
   - Implement proper session cleanup
   - Handle session expiration

3. **Response Format**
   - Keep responses consistent with the `AgentResponse` model
   - Include relevant metadata in the `data` field
   - Use clear status messages

4. **Security**
   - Implement proper authentication
   - Validate input data
   - Sanitize file paths and URLs

## Conclusion

The A2A protocol provides a more flexible and standardized way to serve agents compared to the ADK API server approach. By implementing A2A support, we gain:

- Simpler integration
- Better response structure
- Direct access to agents
- Custom endpoint support
- Standardized discovery

This makes our agents more accessible and easier to integrate with other systems, while maintaining compatibility with the ADK ecosystem.

## Next Steps

1. Implement A2A support for other agents
2. Add authentication to A2A endpoints
3. Create more custom endpoints for specific use cases
4. Improve error handling and logging
5. Add monitoring and metrics collection
