# Lesson 3: Building Custom UIs for the Speaker Agent

In this lesson, we'll explore how to create custom user interfaces for our ElevenLabs-powered Text-to-Speech Speaker Agent. We'll implement two different integration approaches:

1. Using the ADK API Server (`adk api_server`)
2. Using the standalone Agent-to-Agent (A2A) protocol

## Background

By the end of Lesson 2, we successfully created a TTS Speaker Agent that converts text to speech using ElevenLabs. However, to make this agent useful for end users, we need to create intuitive interfaces that can:

- Send text to the agent
- Retrieve audio responses
- Play the audio directly in the UI

Our solution will use Streamlit, a popular Python framework for building data apps and interfaces. We'll create two separate apps to demonstrate the different integration methods.

## Integration Approaches

### ADK API Server Integration

The ADK API Server provides a unified way to manage sessions and coordinate multiple agents. When using this approach:

- The server runs on `localhost:8000` by default
- Session creation is explicit via API endpoints
- Responses come in the form of ADK event streams
- Audio file paths must be extracted from the text responses

### Standalone A2A Integration

The Agent-to-Agent (A2A) protocol provides a more direct way to communicate with a single agent:

- The agent runs on `localhost:8003` by default
- Session management is implicit
- Responses come in a simpler structured JSON format
- Audio URLs are directly accessible in the response data

## Step 1: Understanding the Speaker Agent Response Format

Let's start by examining how our Speaker Agent formats responses. This will help us understand what we need to extract from the responses to play audio in our UI.

When the Speaker Agent generates audio, it saves the file to a local path and includes this path in its response. However, the format of this response differs between the ADK API Server and the A2A protocol.

## Step 2: Creating Test Scripts for Response Extraction

Let's create test scripts to validate how we can extract audio file paths from responses.

### ADK API Server Test Script

```bash
#!/bin/bash

# Test script that extracts audio file path from the response
# This helps verify the format of audio responses from the speaker agent
# when accessed via the standard ADK API Server.

# Expected Response Structure (from ADK API Server /run):
# A stream of JSON events. The script looks for specific structures within these events:
# - A functionResponse event for 'text_to_speech' containing the path in its result text.
# - OR - General text output that might contain the path (less reliable).

APP_NAME="speaker"
USER_ID="test-user"
SESSION_ID="test-audio-extraction-$(date +%s)"  # Unique session ID

# Step 1: Create session explicitly
echo "Creating a new session..."
curl -X POST "http://localhost:8000/apps/$APP_NAME/users/$USER_ID/sessions/$SESSION_ID" \
  -H "Content-Type: application/json" \
  -d "{}" | jq .

sleep 2  # Brief pause between requests

# Step 2: Send message and analyze the response
echo "Sending message and analyzing the response..."
RESPONSE=$(curl -s -X POST "http://localhost:8000/run" \
  -H "Content-Type: application/json" \
  -d "{
    \"app_name\": \"$APP_NAME\",
    \"user_id\": \"$USER_ID\",
    \"session_id\": \"$SESSION_ID\",
    \"new_message\": {
      \"parts\": [{\"text\": \"Please say hello\"}],
      \"role\": \"user\"
    }
  }")

# Print the full response for reference
echo "Full response:"
echo "$RESPONSE" | jq .

# Extract information about where the audio file was saved
echo "Extracting audio file information..."

# Pattern 1: Look for text_to_speech function response with file path in "text" field
AUDIO_FILE_PATH=$(echo "$RESPONSE" | jq -r '.[] | select(.content.parts[].functionResponse.name == "text_to_speech") | .content.parts[].functionResponse.response.result.content[] | select(.type == "text") | .text')

if [ -z "$AUDIO_FILE_PATH" ] || [ "$AUDIO_FILE_PATH" == "null" ]; then
  echo "No file path found in function response text, trying alternative extraction..."
  # Try another pattern
  AUDIO_FILE_PATH=$(echo "$RESPONSE" | jq -r '.[] | select(.content.parts[].text) | .content.parts[].text')
fi

# Attempt to extract the file path from the text
if [ -n "$AUDIO_FILE_PATH" ]; then
  EXTRACTED_PATH=$(echo "$AUDIO_FILE_PATH" | grep -o "/[^ ]*\.mp3")
  if [ -n "$EXTRACTED_PATH" ]; then
    echo "Extracted file path: $EXTRACTED_PATH"
    
    # Verify if the file exists
    if [ -f "$EXTRACTED_PATH" ]; then
      echo "✅ Audio file exists at the extracted path!"
    else
      echo "❌ Audio file not found at the extracted path."
    fi
  fi
fi
```

### A2A Test Script

```bash
#!/bin/bash

# Test script that extracts audio file path from the response
# This helps verify the format of audio responses from the standalone A2A speaker agent
# when accessed directly via its /run endpoint.

# Expected Response Structure (from Standalone A2A /run):
# A single JSON object matching the AgentResponse model.
# Example Response:
# {
#   "message": "Audio generation complete. You can listen to it at file:///.../...mp3",
#   "status": "success",
#   "data": {
#     "audio_url": "file:///tmp/audio_output/audio_abc.mp3",
#     ...
#   },
#   "session_id": "..."
# }

APP_NAME="speaker"
USER_ID="test-user"
SESSION_ID="test-a2a-audio-extraction-$(date +%s)"  # Unique session ID for A2A test

# Send message and analyze the response
echo "Sending message to A2A endpoint (http://localhost:8003/run) and analyzing the response..."
RESPONSE=$(curl -s -X POST "http://localhost:8003/run" \
  -H "Content-Type: application/json" \
  -d "{
    \"app_name\": \"$APP_NAME\",
    \"user_id\": \"$USER_ID\",
    \"session_id\": \"$SESSION_ID\",
    \"message\": \"Please say hello from the A2A test\"
  }")

# Print the full response for reference
echo "Full response:"
echo "$RESPONSE" | jq .

# Extract information about where the audio file was saved
echo "Extracting audio file information..."

# Directly extract the audio_url from the data field
AUDIO_URL=$(echo "$RESPONSE" | jq -r '.data.audio_url')

if [ -n "$AUDIO_URL" ] && [ "$AUDIO_URL" != "null" ]; then
  echo "Audio URL found in data: $AUDIO_URL"
  
  # Try to extract the actual file path if it's a file:// URL
  if [[ "$AUDIO_URL" == file://* ]]; then
      EXTRACTED_PATH=$(echo "$AUDIO_URL" | sed 's|file://||')
      echo "Extracted file path: $EXTRACTED_PATH"
      
      # Verify if the file exists
      if [ -f "$EXTRACTED_PATH" ]; then
          echo "✅ Audio file exists at the extracted path!"
      else
          echo "❌ Audio file not found at the extracted path: $EXTRACTED_PATH"
      fi
  fi
fi
```

These scripts demonstrate the key differences in response formats between the two approaches.

## Step 3: Building a Streamlit UI for ADK API Server Integration

Now, let's create a Streamlit app that interacts with our Speaker Agent via the ADK API Server.

```python
"""
Speaker Agent Chat Application
==============================

This Streamlit application provides a chat interface for interacting with the ADK Speaker Agent.
It allows users to create sessions, send messages, and receive both text and audio responses.
"""
import streamlit as st
import requests
import json
import os
import uuid
import time

# Set page config
st.set_page_config(
    page_title="Speaker Agent Chat",
    page_icon="🔊",
    layout="centered"
)

# Constants
API_BASE_URL = "http://localhost:8000"
APP_NAME = "speaker"

# Initialize session state variables
if "user_id" not in st.session_state:
    st.session_state.user_id = f"user-{uuid.uuid4()}"
    
if "session_id" not in st.session_state:
    st.session_state.session_id = None
    
if "messages" not in st.session_state:
    st.session_state.messages = []

def create_session():
    """
    Create a new session with the speaker agent.
    """
    session_id = f"session-{int(time.time())}"
    response = requests.post(
        f"{API_BASE_URL}/apps/{APP_NAME}/users/{st.session_state.user_id}/sessions/{session_id}",
        headers={"Content-Type": "application/json"},
        data=json.dumps({})
    )
    
    if response.status_code == 200:
        st.session_state.session_id = session_id
        st.session_state.messages = []
        return True
    else:
        st.error(f"Failed to create session: {response.text}")
        return False

def send_message(message):
    """
    Send a message to the speaker agent and process the response.
    """
    if not st.session_state.session_id:
        st.error("No active session. Please create a session first.")
        return False
    
    # Add user message to chat
    st.session_state.messages.append({"role": "user", "content": message})
    
    # Send message to API
    response = requests.post(
        f"{API_BASE_URL}/run",
        headers={"Content-Type": "application/json"},
        data=json.dumps({
            "app_name": APP_NAME,
            "user_id": st.session_state.user_id,
            "session_id": st.session_state.session_id,
            "new_message": {
                "role": "user",
                "parts": [{"text": message}]
            }
        })
    )
    
    if response.status_code != 200:
        st.error(f"Error: {response.text}")
        return False
    
    # Process the response
    events = response.json()
    
    # Extract assistant's text response
    assistant_message = None
    audio_file_path = None
    
    for event in events:
        # Look for the final text response from the model
        if event.get("content", {}).get("role") == "model" and "text" in event.get("content", {}).get("parts", [{}])[0]:
            assistant_message = event["content"]["parts"][0]["text"]
        
        # Look for text_to_speech function response to extract audio file path
        if "functionResponse" in event.get("content", {}).get("parts", [{}])[0]:
            func_response = event["content"]["parts"][0]["functionResponse"]
            if func_response.get("name") == "text_to_speech":
                response_text = func_response.get("response", {}).get("result", {}).get("content", [{}])[0].get("text", "")
                # Extract file path using simple string parsing
                if "File saved as:" in response_text:
                    parts = response_text.split("File saved as:")[1].strip().split()
                    if parts:
                        audio_file_path = parts[0].strip(".")
    
    # Add assistant response to chat
    if assistant_message:
        st.session_state.messages.append({"role": "assistant", "content": assistant_message, "audio_path": audio_file_path})
    
    return True

# UI Components
st.title("🔊 Speaker Agent Chat")

# Sidebar for session management
with st.sidebar:
    st.header("Session Management")
    
    if st.session_state.session_id:
        st.success(f"Active session: {st.session_state.session_id}")
        if st.button("➕ New Session"):
            create_session()
    else:
        st.warning("No active session")
        if st.button("➕ Create Session"):
            create_session()
    
    st.divider()
    st.caption("This app interacts with the Speaker Agent via the ADK API Server.")
    st.caption("Make sure the ADK API Server is running on port 8000.")

# Chat interface
st.subheader("Conversation")

# Display messages
for msg in st.session_state.messages:
    if msg["role"] == "user":
        st.chat_message("user").write(msg["content"])
    else:
        with st.chat_message("assistant"):
            st.write(msg["content"])
            
            # Handle audio if available
            if "audio_path" in msg and msg["audio_path"]:
                audio_path = msg["audio_path"]
                if os.path.exists(audio_path):
                    st.audio(audio_path)
                else:
                    st.warning(f"Audio file not accessible: {audio_path}")

# Input for new messages
if st.session_state.session_id:  # Only show input if session exists
    user_input = st.chat_input("Type your message...")
    if user_input:
        send_message(user_input)
        st.rerun()  # Rerun to update the UI with new messages
else:
    st.info("👈 Create a session to start chatting")
```

## Step 4: Building a Streamlit UI for A2A Integration

Now, let's create a Streamlit app that interacts directly with our Speaker Agent using the A2A protocol.

```python
"""
A2A Speaker Agent Chat Application
==================================

This Streamlit application provides a chat interface for interacting with the
standalone A2A Speaker Agent using the A2A protocol.
"""
import streamlit as st
import requests
import json
import os
import uuid
import time
import logging

# Set up basic logging for the app
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Set page config
st.set_page_config(
    page_title="A2A Speaker Agent Chat",
    page_icon="🔊",
    layout="centered"
)

# Constants
API_BASE_URL = "http://localhost:8003"  # A2A agent port
APP_NAME = "speaker"  # Not needed for direct A2A /run calls

# Initialize session state variables
if "user_id" not in st.session_state:
    st.session_state.user_id = f"user-{uuid.uuid4()}"  # Persistent user ID

# Session ID represents the current conversation. Initialize if not present.
if "session_id" not in st.session_state:
    st.session_state.session_id = f"conv-{uuid.uuid4()}"  # Start with a unique conversation ID

if "messages" not in st.session_state:
    st.session_state.messages = []

def send_message(message):
    """
    Send a message to the speaker agent and process the response.
    """
    if not st.session_state.session_id:
        st.error("No active conversation. Start typing to begin.")
        return False

    # Add user message to chat
    st.session_state.messages.append({"role": "user", "content": message})

    # Construct A2A payload
    payload = {
        "message": message,
        "context": {
            "user_id": st.session_state.user_id  # Pass user_id in context
        },
        "session_id": st.session_state.session_id
    }
    
    # Send POST request with spinner for UI feedback
    try:
        with st.spinner("Waiting for agent response..."):
            response = requests.post(
                f"{API_BASE_URL}/run",
                headers={"Content-Type": "application/json", "Accept": "application/json"},
                json=payload,  # Use json parameter for requests library
                timeout=30  # Set a reasonable timeout (e.g., 30 seconds)
            )
            response.raise_for_status()  # Raise an exception for bad status codes
            
            # Parse A2A response
            response_data = response.json()
            
            assistant_message = response_data.get("message", "(No message received)")
            # Extract audio URL from the 'data' dictionary
            audio_url = response_data.get("data", {}).get("audio_url") 
            
            # Add assistant response to chat history
            st.session_state.messages.append(
                {
                    "role": "assistant", 
                    "content": assistant_message, 
                    "audio_url": audio_url  # Use audio_url key
                }
            )
            
            return True  # Indicate success

    except requests.exceptions.RequestException as e:
        st.error(f"Network or HTTP error sending message: {e}")
        logger.error(f"RequestException sending message: {e}", exc_info=True)
        # Add a placeholder error message to chat history
        st.session_state.messages.append({"role": "assistant", "content": f"Error: Could not connect to agent. {e}"})
        return False
    except json.JSONDecodeError as e:
        st.error("Failed to decode JSON response from agent.")
        logger.error(f"JSONDecodeError parsing response: {e}", exc_info=True)
        st.session_state.messages.append({"role": "assistant", "content": "Error: Invalid response format from agent."}) 
        return False
    except Exception as e:
        st.error(f"An unexpected error occurred: {e}")
        logger.error(f"Unexpected error in send_message: {e}", exc_info=True)
        st.session_state.messages.append({"role": "assistant", "content": f"Error: An unexpected error occurred. {e}"}) 
        return False

# UI Components
st.title("🔊 A2A Speaker Agent Chat")  # Updated title

# Sidebar for conversation control
with st.sidebar:
    st.header("Conversation Control")
    
    # Reset conversation button
    if st.button("🧹 New Conversation"):
        # Logic to reset session_id and messages
        st.session_state.session_id = f"conv-{uuid.uuid4()}"  # Generate new unique conv ID
        st.session_state.messages = []  # Clear messages for new conversation
        st.success("Started new conversation.")
        st.rerun()
            
    if st.session_state.session_id:
        st.info(f"User ID: {st.session_state.user_id}")
        # Display conversation ID or similar context - not raw session_id
        st.caption(f"Conversation ID: {st.session_state.session_id}")
    else:
        st.info("Start typing to begin a conversation.")

    st.divider()
    st.caption("This app interacts directly with the Speaker Agent via A2A.")
    st.caption("Make sure the agent is running on port 8003.")

# Chat interface
st.subheader("Conversation")

# Display messages
for msg in st.session_state.messages:
    if msg["role"] == "user":
        st.chat_message("user").write(msg["content"])
    else:
        with st.chat_message("assistant"):
            st.write(msg["content"])

            # Handle audio if available - for A2A response
            audio_key = "audio_url"  # Use the new key name
            if audio_key in msg and msg[audio_key]:
                audio_location = msg[audio_key]
                # Handle both file paths and URLs
                if isinstance(audio_location, str) and audio_location.startswith("file://"):
                    audio_path = audio_location.replace("file://", "")
                    if os.path.exists(audio_path):
                        try:
                            with open(audio_path, 'rb') as audio_file:
                                audio_bytes = audio_file.read()
                            st.audio(audio_bytes)  # Read bytes for st.audio
                        except Exception as e:
                            st.warning(f"Could not read audio file: {audio_path}. Error: {e}")
                    else:
                        st.warning(f"Audio file not found: {audio_path}")
                elif isinstance(audio_location, str):  # Other paths/URLs
                     if os.path.exists(audio_location):
                         try:
                            with open(audio_location, 'rb') as audio_file:
                                audio_bytes = audio_file.read()
                            st.audio(audio_bytes)
                         except Exception as e:
                             st.warning(f"Could not read audio file: {audio_location}. Error: {e}")
                     else:
                        st.caption(f"(Audio available at: {audio_location})")

# Input for new messages
user_input = st.chat_input("Type your message...")
if user_input:
    send_message(user_input)
    st.rerun()  # Rerun to update the UI
```

## Step 5: Running the Applications

To run these applications, you'll need to:

1. **First, ensure the appropriate backend is running:**

   For the ADK API Server integration:
   ```bash
   adk api_server
   ```

   For the A2A integration:
   ```bash
   python -m agents.speaker
   ```

2. **Then, run the Streamlit app:**

   For the ADK API Server integration:
   ```bash
   streamlit run apps/speaker_app.py
   ```

   For the A2A integration:
   ```bash
   streamlit run apps/a2a_speaker_app.py
   ```

## Key Differences Between the Approaches

Now that we've implemented both integration approaches, let's compare them:

### ADK API Server Integration:

**Pros:**
- Better integration with the ADK ecosystem
- Can be coordinated with other agents
- Explicit session management

**Cons:**
- More complex response parsing
- Requires running the full ADK API server
- More verbose API calls

### Standalone A2A Integration:

**Pros:**
- Simpler, more direct communication
- Cleaner response format with structured data
- Doesn't require the ADK API server running
- Can be integrated into non-ADK systems more easily

**Cons:**
- Less integrated with the ADK ecosystem
- Potential for inconsistency with other ADK agents
- Less control over session lifecycle

## Conclusion

In this lesson, we've learned how to create custom UIs for our Speaker Agent using two different integration approaches. We've seen how the response formats differ and how to extract audio information from both types of responses.

This knowledge will be valuable as you build your own agent interfaces, allowing you to choose the integration approach that best suits your needs.

Remember that the key to successful agent UI development is understanding the response structure and designing your parsing logic accordingly.

Happy building!
