#!/bin/bash

# Test script that extracts audio file path from the response
# This helps verify the format of audio responses from the standalone A2A speaker agent
# when accessed directly via its /run endpoint.

# Expected Response Structure (from Standalone A2A /run):
# A single JSON object matching the AgentResponse model (defined in common/a2a_server.py).
# The script extracts the audio URL directly from the structured 'data.audio_url' field.
# Example Response:
# {
#   "message": "Audio generation complete. You can listen to it at file:///.../...mp3",
#   "status": "success",
#   "data": {
#     "audio_url": "file:///tmp/audio_output/audio_abc.mp3",
#     "raw_events": [...], 
#     "voice_id": "..."
#   },
#   "session_id": "..."
# }

# The app_name should match the module name in the ADK structure
APP_NAME="speaker"
USER_ID="test-user"
SESSION_ID="test-a2a-audio-extraction-$(date +%s)"  # Unique session ID for A2A test

# Step 1: Send message and analyze the response (No explicit session creation needed for A2A /run)
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

# New pattern: Directly extract the audio_url from the data field
AUDIO_URL=$(echo "$RESPONSE" | jq -r '.data.audio_url')

if [ -z "$AUDIO_URL" ] || [ "$AUDIO_URL" == "null" ]; then
  echo "No audio file information found in the response data. Check the structure manually."
else
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
          echo "   (Note: Path might be relative to the server, or file system access might be restricted)"
      fi
  else
      echo "Audio URL is not a local file path: $AUDIO_URL"
  fi
fi

# Extract information about the voice used (Still look in data field)
VOICE_ID=$(echo "$RESPONSE" | jq -r '.data.voice_id')

if [ -n "$VOICE_ID" ] && [ "$VOICE_ID" != "null" ]; then
  echo "Voice used: $VOICE_ID"
fi

echo "-----------------------------------------"
echo "A2A Test Script Notes:"
echo "- This script targets the standalone agent endpoint (port 8003)."
echo "- It relies on implicit session creation via the /run endpoint."
echo "- Audio file path extraction assumes the agent returns the path in the response text."

# Note: This requires jq to be installed for parsing the JSON response
# and grep for extracting file paths 