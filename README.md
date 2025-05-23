# ADK Made Simple - Agent Examples

This project demonstrates simple agents built using the Google Agent Development Kit (ADK). It accompanies the YouTube tutorial series "ADK Made Simple" hosted on the [AIOriented YouTube channel](https://www.youtube.com/@AIOriented).

Full series playlist: [ADK Made Simple Playlist](https://www.youtube.com/playlist?list=PLWUH7ke1DYK98Di2FF8Ux3IX6qG-mZ3A7)

## ☕ Support the Project

If you find this tutorial series and codebase helpful in your AI agent development journey, consider buying me a coffee! Your support helps me create more educational content on AI and agent development.

<a href="https://buymeacoffee.com/aioriented" target="_blank">
  <img src="https://cdn.buymeacoffee.com/buttons/v2/default-yellow.png" alt="Buy Me A Coffee" style="height: 60px !important;width: 217px !important;" >
</a>

## Lessons

| Lesson | Link | Description |
| ------ | ---- | ----------- |
| 1      | [Lesson 1: Basics of ADK & Reddit Scout Agent](https://www.youtube.com/watch?v=BiP4tKZKTvU) | Basics of ADK, Building a Reddit news agent with PRAW |
| 2      | [Lesson 2: Multi-Agent Systems & TTS](https://www.youtube.com/watch?v=FODBW9az-sw) | Combining ADK with MCP, Multi-Agent Systems, Text-To-Speech with ElevenLabs, LiteLLM |
| 3      | [Lesson 3: Custom UI for Speaker Agent (ADK API Server)](https://www.youtube.com/watch?v=jrFFEPWoB1Q) | Building a Streamlit UI for the Speaker Agent using the ADK API server (no A2A yet) |
| 4      | [Lesson 4: Serving Agents via A2A Protocol](https://www.youtube.com/watch?v=NKBkj3bMfHk) | Introducing the A2A protocol, running agents as standalone A2A services, and building UIs for A2A agents |

## Agents

- **Reddit Scout**: Simulates fetching recent discussion titles from game development subreddits.
- **Speaker Agent**: Converts text to speech using the ElevenLabs TTS API via an MCP toolset. Can be run via `adk api_server` or as a standalone A2A service.

## General Setup

1.  **Clone the repository:**

    ```bash
    git clone https://github.com/chongdashu/adk-made-simple
    cd adk-made-simple
    ```

2.  **Create and activate a virtual environment (Recommended):**

    ```bash
    python -m venv .venv
    # On Windows
    .\.venv\Scripts\activate
    # On macOS/Linux
    source .venv/bin/activate
    ```

3.  **Install general dependencies:**

    ```bash
    pip install -r requirements.txt
    ```

4.  **Agent-Specific Setup:** Navigate to the specific agent's directory within `agents/` and follow the instructions in its `README.md` (or follow the steps below for the default agent).

## Setup & Running Agents

This section describes running agents via the ADK framework (e.g., `adk run` or `adk web`).

1.  **Navigate to Agent Directory:**

    ```bash
    cd agents/reddit_scout
    ```

2.  **Set up API Key:**

    - Copy the example environment file:
      ```bash
      cp ../.env.example .env
      ```
    - Edit the `.env` file and add your Google AI API Key. You can obtain one from [Google AI Studio](https://aistudio.google.com/app/apikey).
      ```dotenv
      GOOGLE_API_KEY=YOUR_API_KEY_HERE
      ```
    - _Note:_ You might need to load this into your environment depending on your OS and shell (`source .env` or similar) if `python-dotenv` doesn't automatically pick it up when running `adk`.

3.  **Run the Agent:**

    - Make sure your virtual environment (from the root directory) is activated.
    - From the `agents/reddit_scout` directory, run the agent using the ADK CLI, specifying the core code package:
      ```bash
      adk run reddit_scout
      ```
    - Alternatively, from the project root (`adk-made-simple`), you might be able to run:
      ```bash
      adk run agents/reddit_scout
      ```
      _(Check ADK documentation for preferred discovery method)_
    - Asynchronous agents can only be run from the web view, so first `cd` into the `agents` directory and run 
      ```bash
      adk web
      ```
      _(Check ADK documentation for preferred discovery method)_

4.  **Interact:** The agent will start, and you can interact with it in the terminal or web UI.

## Running the Speaker Agent (Two Modes)

The Speaker Agent can be run in two ways:

**Mode 1: Via `adk api_server` (Recommended for ADK framework integration)**

- **Purpose:** Integrates the Speaker Agent with the ADK's coordination layer, allowing it to be used alongside other agents managed by the `api_server`. Leverages the `Agent` definition in `agents/speaker/agent.py`.
- **How to Run:**
  1. Ensure the Speaker Agent is correctly set up (API keys in `.env`, etc.).
  2. Run the main ADK API server from the project root:
     ```bash
     adk api_server
     ```
  3. The server will be available (usually on `http://localhost:8000`) and manage the Speaker Agent along with others.
- **Interaction:** Send requests to the `adk api_server`'s `/run` endpoint (port 8000). The server handles session creation and uses the agent's definition (`agents/speaker/agent.py`) to process requests, potentially involving its internal LLM coordinator.
- **Testing:** Use the test scripts in `scripts/tests/speaker/` (e.g., `test_extract_audio.sh`) which target port 8000 and expect the ADK event stream response format.

**Mode 2: As a Standalone A2A Service**

- **Purpose:** Exposes the Speaker Agent's core TTS functionality directly via an Agent-to-Agent (A2A) compliant HTTP endpoint, bypassing the main ADK `api_server`'s coordination layer. Uses the `agents/speaker/__main__.py` script.
- **How to Run:**
  1. Ensure the Speaker Agent is correctly set up (API keys in `.env`, etc.).
  2. Run the agent's main script directly from the project root:
     ```bash
     python -m agents.speaker
     ```
  3. The standalone server will be available on `http://localhost:8003`.
- **Interaction:** Send requests directly to the standalone agent's `/run` endpoint (port 8003). The payload must match the simpler A2A `AgentRequest` schema (defined in `common/a2a_server.py`). The `TaskManager` uses the `Agent` instance defined in `agents/speaker/agent.py` via `agent.execute`.
- **Testing:** Use the specific A2A test script `scripts/tests/speaker/test_a2a_extract_audio.sh` which targets port 8003 and expects the structured JSON `AgentResponse` format.

**Note on Response Formatting Differences:**

While both modes now ultimately call the `agent.execute(...)` method defined using `agents/speaker/agent.py`, the final HTTP response received by the client (test script or Streamlit app) differs significantly. This is because the server handling the `/run` request formats the output of `agent.execute` differently:

- The **`adk api_server`** (Mode 1) streams the raw sequence of internal ADK events generated by `agent.execute` back to the client.
- The **Standalone A2A Server** (Mode 2), using our `agents/speaker/task_manager.py` and `common/a2a_server.py`, intercepts the list of events from `agent.execute`, processes them to extract key information (like the audio URL), and then constructs and returns a *single, structured JSON summary* (`AgentResponse`).

This distinction explains why the test scripts and Streamlit apps need different parsing logic depending on which mode they are interacting with.

## Test Script Differences (`scripts/tests/speaker/`)

- **`test_extract_audio.sh` (and similar):** Targets the `adk api_server` on port 8000. It expects the raw stream of ADK events as a response. It parses the audio file location by looking for specific text patterns (like log messages `File saved as: ...`) within that stream.
- **`test_a2a_extract_audio.sh`:** Targets the standalone agent server on port 8003. It expects a structured JSON response (`AgentResponse` model). It extracts the audio file location directly from the `data.audio_url` field in the JSON.

This difference arises because the `adk api_server` and the standalone A2A server format their responses differently for the `/run` endpoint.

## Project Structure Overview

```
adk-made-simple/
├── agents/
│   ├── reddit_scout/        # Lesson 1: Reddit Scout Agent
│   │   ├── __init__.py
│   │   └── agent.py
│   ├── async_reddit_scout/  # Lesson 2: Asynchronous Reddit Scout Agent
│   │   ├── __init__.py
│   │   └── agent.py
│   ├── summarizer/          # Lesson 2: Newscaster Summarizer Agent
│   │   ├── __init__.py
│   │   └── agent.py
│   ├── speaker/             # Lesson 2: Speaker Agent
│   │   ├── __init__.py
│   │   └── agent.py
│   └── coordinator/         # Lesson 2: Coordinator Agent combining sub-agents
│       ├── __init__.py
│       └── agent.py
├── .env.example             # Environment variables example
├── .gitignore               # Root gitignore file
├── requirements.txt         # Project dependencies
├── README.md                # This file (Overall Project README)
└── PLAN.md                  # Development plan notes
├── apps/
│   ├── speaker_app.py       # Streamlit UI for Speaker (via adk api_server)
│   ├── a2a_speaker_app.py   # Streamlit UI for Speaker (via standalone A2A)
│   └── README.md            # Explanation of the apps
├── common/
│   └── a2a_server.py        # Helper for creating standalone A2A servers
├── scripts/
│   ├── tests/
│   │   └── speaker/         # Test scripts for Speaker Agent
│   │       ├── test_extract_audio.sh
│   │       └── test_a2a_extract_audio.sh 
│   │       └── ... (other tests)
│   └── run_agents.py        # Script to run multiple standalone agents (if needed)
```

## Streamlit UI

Two Streamlit UIs are provided for the Speaker Agent, demonstrating the two interaction modes:

- `apps/speaker_app.py`: Interacts with the agent via the `adk api_server` (Mode 1).
- `apps/a2a_speaker_app.py`: Interacts directly with the standalone A2A agent service (Mode 2).

See the `apps/README.md` for details on running these and their differences.

1. **Ensure Dependencies:**

   Make sure you have all required dependencies installed:
   ```bash
   pip install -r requirements.txt
   ```

2. **Run a Streamlit App:**

   From the project root:
   ```bash
   # To run the app interacting with adk api_server:
   streamlit run apps/speaker_app.py

   # To run the app interacting with the standalone A2A agent:
   streamlit run apps/a2a_speaker_app.py
   ```
   *(Note: The `--experimental-async` flag mentioned previously might not be necessary for these simpler apps, but can be added if async issues arise).* 

3. **Using the Apps:**

   - For `speaker_app.py`: Ensure `adk api_server` is running. Use the UI to create sessions and send messages.
   - For `a2a_speaker_app.py`: Ensure the standalone agent is running (`python -m agents.speaker`). Start chatting directly; sessions are handled implicitly.
