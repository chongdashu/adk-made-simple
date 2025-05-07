#!/bin/bash

# Test script that extracts audio file path from the response
# This helps verify the format of audio responses from the speaker agent
# when accessed via the standard ADK API Server.

# Expected Response Structure (from ADK API Server /run):
# A stream of JSON events. The script looks for specific structures within these events:
# - A functionResponse event for 'text_to_speech' containing the path in its result text.
# - OR - General text output that might contain the path (less reliable).
# Example Event Fragment (simplified):
# [
#   ...
#   {
#     "content": {
#       "role": "model",
#       "parts": [
#         {
#           "functionResponse": {
#             "name": "text_to_speech",
#             "response": {
#               "result": {
#                 "content": [
#                   {"type": "text", "text": "File saved as: /tmp/audio_output/audio_xyz.mp3."}
#                 ]
#               }
#             }
#           }
#         }
#       ]
#     }
#   }
#   ...
# ]

# The app_name should match the full Python import path from the project root
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

if [ -z "$AUDIO_FILE_PATH" ] || [ "$AUDIO_FILE_PATH" == "null" ]; then
  echo "No audio file information found in the response. Check the structure manually."
else
  echo "Audio information found:"
  echo "$AUDIO_FILE_PATH"
  
  # Try to extract the actual file path if it exists in the text
  EXTRACTED_PATH=$(echo "$AUDIO_FILE_PATH" | grep -o "/[^ ]*\.mp3")
  if [ -n "$EXTRACTED_PATH" ]; then
    echo "Extracted file path: $EXTRACTED_PATH"
    
    # Verify if the file exists
    if [ -f "$EXTRACTED_PATH" ]; then
      echo "✅ Audio file exists at the extracted path!"
      # Optionally, you could play the file here if you have a compatible player
      # play "$EXTRACTED_PATH"  # Requires sox or similar tool
    else
      echo "❌ Audio file not found at the extracted path."
    fi
  fi
fi

# Extract information about the voice used
VOICE_NAME=$(echo "$RESPONSE" | jq -r '.[] | select(.content.parts[].functionCall.name == "text_to_speech") | .content.parts[].functionCall.args.voice_name')

if [ -n "$VOICE_NAME" ] && [ "$VOICE_NAME" != "null" ]; then
  echo "Voice used: $VOICE_NAME"
fi

echo "For Streamlit app development: Note that the audio is saved to a local file path on the server side."
echo "The Streamlit app will need to either:"
echo "1. Serve these files via a static file server"
echo "2. Read the files and convert to base64 for embedding in the UI"
echo "3. Modify the agent to return audio data directly instead of saving to disk"

# Note: This requires jq to be installed for parsing the JSON response
# and grep for extracting file paths 