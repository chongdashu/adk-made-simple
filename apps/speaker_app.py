"""
Speaker Agent Chat Application
==============================

This Streamlit application provides a chat interface for interacting with the ADK Speaker Agent.
It allows users to create sessions, send messages, and receive both text and audio responses.

Requirements:
------------
- ADK API Server running on localhost:8000
- Speaker Agent registered and available in the ADK
- Streamlit and related packages installed

Usage:
------
1. Start the ADK API Server: `adk api_server`
2. Ensure the Speaker Agent is registered and working
3. Run this Streamlit app: `streamlit run apps/speaker_app.py`
4. Click "Create Session" in the sidebar
5. Start chatting with the Speaker Agent

Architecture:
------------
- Session Management: Creates and manages ADK sessions for stateful conversations
- Message Handling: Sends user messages to the ADK API and processes responses
- Audio Integration: Extracts audio file paths from responses and displays players

API Assumptions:
--------------
1. ADK API Server runs on localhost:8000
2. Speaker Agent is registered with app_name="speaker"
3. The Speaker Agent uses ElevenLabs TTS and saves audio files locally
4. Audio files are accessible from the path returned in the API response
5. Responses follow the ADK event structure with model outputs and function calls/responses

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

if "audio_files" not in st.session_state:
    st.session_state.audio_files = []

def create_session():
    """
    Create a new session with the speaker agent.
    
    This function:
    1. Generates a unique session ID based on timestamp
    2. Sends a POST request to the ADK API to create a session
    3. Updates the session state variables if successful
    
    Returns:
        bool: True if session was created successfully, False otherwise
    
    API Endpoint:
        POST /apps/{app_name}/users/{user_id}/sessions/{session_id}
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
        st.session_state.audio_files = []
        return True
    else:
        st.error(f"Failed to create session: {response.text}")
        return False

def send_message(message):
    """
    Send a message to the speaker agent and process the response.
    
    This function:
    1. Adds the user message to the chat history
    2. Sends the message to the ADK API
    3. Processes the response to extract text and audio information
    4. Updates the chat history with the assistant's response
    
    Args:
        message (str): The user's message to send to the agent
        
    Returns:
        bool: True if message was sent and processed successfully, False otherwise
    
    API Endpoint:
        POST /run
        
    Response Processing:
        - Parses the ADK event structure to extract text responses
        - Looks for text_to_speech function responses to find audio file paths
        - Adds both text and audio information to the chat history
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
