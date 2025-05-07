"""
A2A Speaker Agent Chat Application
==================================

This Streamlit application provides a chat interface for interacting with the
standalone A2A Speaker Agent. It allows users to send messages and receive
both text and audio responses using the A2A protocol.

Requirements:
------------
- Standalone Speaker Agent running (e.g., `python -m agents.speaker`) on localhost:8003
- Streamlit and related packages installed

Usage:
------
1. Start the Speaker Agent: `python -m agents.speaker`
2. Run this Streamlit app: `streamlit run apps/a2a_speaker_app.py`
3. Start chatting with the Speaker Agent

Architecture:
------------
- Session Management: Uses Streamlit session state to manage user_id and session_id implicitly.
- Message Handling: Sends user messages to the A2A /run endpoint and processes responses.
- Audio Integration: Extracts audio file paths/URLs from responses and displays players.

A2A Assumptions:
--------------
1. Standalone Speaker Agent runs on localhost:8003
2. The agent exposes a POST /run endpoint compliant with the defined A2A schema.
3. The agent handles sessions implicitly based on user_id and session_id.
4. The agent returns responses containing text and audio URLs/paths.

"""
import streamlit as st
import requests
import json
import os
import uuid
import time
import base64
from pathlib import Path
import logging

# Set up basic logging for the app
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Set page config
st.set_page_config(
    page_title="A2A Speaker Agent Chat", # Updated title
    page_icon="🔊",
    layout="centered"
)

# Constants - Will be updated in later subtasks
API_BASE_URL = "http://localhost:8003" # Set to A2A agent port
APP_NAME = "speaker" # Not needed for direct A2A /run calls

# Initialize session state variables
if "user_id" not in st.session_state:
    st.session_state.user_id = f"user-{uuid.uuid4()}" # Persistent user ID

# Session ID represents the current conversation. Initialize if not present.
if "session_id" not in st.session_state:
    st.session_state.session_id = f"conv-{uuid.uuid4()}" # Start with a unique conversation ID

if "messages" not in st.session_state:
    st.session_state.messages = []
    # Initialize messages only when session_id is first created or reset
    # This prevents message loss on simple rerun/refresh
    # We might need to tie message initialization more closely to session_id changes

if "audio_files" not in st.session_state:
    st.session_state.audio_files = [] # May change depending on response structure

# Explicit session creation function is removed - A2A handles implicitly
# def create_session():
#     ...


# Message sending function - TO BE MODIFIED for A2A
def send_message(message):
    """
    Send a message to the speaker agent and process the response.
    (This will be modified significantly for A2A communication)
    """
    if not st.session_state.session_id:
        st.error("No active conversation. Start typing to begin.") # Modified message
        # We might auto-start a session here instead of erroring
        return False

    # Add user message to chat
    st.session_state.messages.append({"role": "user", "content": message})

    # Construct A2A payload
    payload = {
        "message": message,
        "context": {
            "user_id": st.session_state.user_id # Pass user_id in context
        },
        "session_id": st.session_state.session_id
    }
    
    # Send POST request with spinner for UI feedback
    try:
        with st.spinner("Waiting for agent response..."):
            response = requests.post(
                f"{API_BASE_URL}/run",
                headers={"Content-Type": "application/json", "Accept": "application/json"},
                json=payload, # Use json parameter for requests library
                timeout=30 # Set a reasonable timeout (e.g., 30 seconds)
            )
            response.raise_for_status() # Raise an exception for bad status codes (4xx or 5xx)
            
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
                    "audio_url": audio_url # Use audio_url key
                }
            )
            
            # Clean up temporary storage if needed (optional)
            if "assistant_response_data" in st.session_state:
                del st.session_state.assistant_response_data
            
            return True # Indicate success

    except requests.exceptions.RequestException as e:
        st.error(f"Network or HTTP error sending message: {e}")
        logger.error(f"RequestException sending message: {e}", exc_info=True)
        # Optionally add a placeholder error message to chat history
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

    # # Placeholder response processing - REMOVED
    # st.warning("A2A message sending not yet implemented.")
    # assistant_message = "(A2A response pending implementation)"
    # audio_file_path = None # Or audio_url
    # 
    # # Placeholder: Add dummy assistant response
    # st.session_state.messages.append({"role": "assistant", "content": assistant_message, "audio_path": audio_file_path})
    # 
    # return True

# UI Components
st.title("🔊 A2A Speaker Agent Chat") # Updated title

# Sidebar for session management - TO BE REVISED
with st.sidebar:
    st.header("Conversation Control") # Renamed
    
    # Replace explicit session buttons with conversation reset
    if st.button("🧹 New Conversation"):
        # Logic to reset session_id and messages
        st.session_state.session_id = f"conv-{uuid.uuid4()}" # Generate new unique conv ID
        st.session_state.messages = [] # Clear messages for new conversation
        st.session_state.audio_files = [] # Clear audio files for new conversation
        st.success("Started new conversation.")
        st.rerun()
    
    # Remove old session creation button logic
    # if st.session_state.session_id:
    #     st.success(f"Active session: {st.session_state.session_id}")
    #     if st.button("➕ New Session"):
    #         create_session()
    # else:
    #     st.warning("No active session")
    #     if st.button("➕ Create Session"):
    #         create_session()
            
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

            # Handle audio if available - TO BE REVISED based on A2A response
            audio_key = "audio_url" # Use the new key name
            if audio_key in msg and msg[audio_key]:
                audio_location = msg[audio_key]
                # Need to handle both file paths and URLs
                if isinstance(audio_location, str) and audio_location.startswith("file://"):
                    audio_path = audio_location.replace("file://", "")
                    if os.path.exists(audio_path):
                        try:
                            with open(audio_path, 'rb') as audio_file:
                                audio_bytes = audio_file.read()
                            st.audio(audio_bytes) # Read bytes for st.audio
                        except Exception as e:
                            st.warning(f"Could not read audio file: {audio_path}. Error: {e}")
                    else:
                        st.warning(f"Audio file not found: {audio_path}")
                elif isinstance(audio_location, str): # Assume it might be a URL or just path
                     # Attempt simple path check first
                     if os.path.exists(audio_location):
                         try:
                            with open(audio_location, 'rb') as audio_file:
                                audio_bytes = audio_file.read()
                            st.audio(audio_bytes)
                         except Exception as e:
                             st.warning(f"Could not read audio file: {audio_location}. Error: {e}")
                     else:
                        # If not a local path, maybe display link or attempt st.audio with URL?
                        # st.audio might support URLs directly, needs testing.
                        # For now, just indicate we have a location.
                        st.caption(f"(Audio available at: {audio_location})")


# Input for new messages
# Simplified logic: Start conversation on first input if no session_id
user_input = st.chat_input("Type your message...")
if user_input:
    # Ensure a conversation ID exists (redundant now due to initialization)
    # if not st.session_state.session_id:
    #     st.session_state.session_id = f"conv-{int(time.time())}"
    #     st.session_state.messages = []
    #     st.session_state.audio_files = []

    send_message(user_input)
    st.rerun() # Rerun to update the UI 