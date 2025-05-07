# Speaker Agent Tests

This directory contains test scripts for interacting with the TTS (Text-to-Speech) Speaker Agent through the ADK API Server.

## Prerequisites

- ADK API Server running on port 8000
- Speaker Agent (`app_name="speaker"`) loaded in the ADK
- `jq` command-line tool installed for JSON processing
- `curl` for making HTTP requests

## Running Tests

### Start the ADK API Server

Before running any tests, make sure the ADK API Server is running:

```bash
adk api_server
```

### Make Test Scripts Executable

Make the test scripts executable:

```bash
cd scripts/tests/speaker
chmod +x *.sh
```

### Run All Tests

To run all tests in sequence:

```bash
./run_all_tests.sh
```

### Run Individual Tests

Or run individual tests:

```bash
# Check available agents
./test_list_apps.sh

# Test with explicit session creation
./test_with_session_creation.sh

# Test basic text-to-speech functionality
./test_basic_tts.sh

# Test emotions in speech
./test_emotions.sh

# Test session continuity
./test_session_continuity.sh

# Test longer text conversion
./test_longer_text.sh

# Test audio URL extraction and downloading
./test_extract_audio.sh
```

## Expected Results

For each test, you should see JSON responses from the ADK API server. 

The `test_extract_audio.sh` script will also attempt to:
1. Extract the audio URL from the response
2. Download the audio file (if it's accessible)

## Response Structure Analysis

These tests help understand how the ADK API server formats responses with audio perceptions, which is essential for building the Streamlit UI that will incorporate audio playback.

## Troubleshooting

- If you see `{"detail":"Agent not found"}`, verify that the agent is correctly registered with the ADK API server
- If the tests can't extract audio URLs, examine the full response to understand the structure and adjust extraction logic
- Make sure the ElevenLabs integration in the agent is working properly

## Next Steps

After verifying the API behavior with these tests, you can proceed to implement the Streamlit app in `speaker_app.py`. 