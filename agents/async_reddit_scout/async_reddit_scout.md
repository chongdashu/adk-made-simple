# Async Reddit Scout Agent (for Google ADK)

This directory contains the `async_reddit_scout_agent`, a Google ADK agent designed to fetch hot posts from a specified subreddit using an external MCP (Model-Context-Protocol) server for Reddit.

## Features

*   Delegates Reddit interaction to a dedicated `mcp-reddit` server.
*   Can fetch hot posts from any subreddit.
*   Designed to be used as a sub-agent within a larger coordinator agent or as a standalone agent.

## Prerequisites

1.  **Google ADK Installed:** Ensure you have the Google ADK framework installed in your Python environment.
    ```bash
    pip install google-adk
    ```
2.  **`uvx` Installed:** This agent (and the `mcp-reddit` server it uses) relies on `uvx` (Universal Virtualenv eXecutor) to run the MCP server.
    ```bash
    pip install uvx
    ```
3.  **Python Environment:** Python 3.10 or newer is recommended.
4.  **Google API Key:** The agent uses a Google Gemini model (e.g., `gemini-1.5-flash-latest`). You'll need a Google API key with access to these models. Set this key in your project's `.env` file as `GOOGLE_API_KEY`.
    Example `.env` content:
    ```
    GOOGLE_API_KEY="your_google_api_key_here"
    ```

## Agent Structure

*   `agent.py`: Contains the primary logic for the Reddit Scout agent, including its definition and how it connects to the `mcp-reddit` server.
*   `run_mcp_reddit_persistent.py`: A Python wrapper script used by `agent.py` to launch and manage the `mcp-reddit` server subprocess, ensuring its stability.
*   `README.md`: This file.

## Running the `mcp-reddit` Server (Required for the Agent to Function)

The `async_reddit_scout_agent` **does not run the `mcp-reddit` server itself directly in a way that's always stable for development or if you want to inspect the server independently.** Instead, the `agent.py` (via the `run_mcp_reddit_persistent.py` wrapper) attempts to launch it as a subprocess.

**For development, testing, or if the ADK-managed launch encounters issues, it's highly recommended to run the `mcp-reddit` server manually in a separate terminal.** This ensures it's up and running stably before the ADK agent tries to connect.

**Steps to Manually Run the `mcp-reddit` Server:**

1.  **Open a new terminal window or tab.**
2.  **Ensure `uvx` is installed and in your PATH.**
3.  **Run the following command:**
    ```bash
    uvx --from git+https://github.com/adhikasp/mcp-reddit.git mcp-reddit --verbose
    ```
    *   `uvx`: The command-line tool.
    *   `--from git+https://github.com/adhikasp/mcp-reddit.git`: Tells `uvx` to fetch the `mcp-reddit` package directly from this GitHub repository. `uvx` will handle downloading it to a temporary location.
    *   `mcp-reddit`: The name of the package/script to run after fetching.
    *   `--verbose` (optional but recommended): Runs `mcp-reddit` in verbose mode, which can provide more logging output, useful for debugging.

4.  **Observe the Output:** You should see `uvx` fetching the package and then output from the `mcp-reddit` server itself. Look for messages indicating the server has started and is listening (typically on standard input/output for MCP stdio servers).
    ```
    # Example output might include:
    # INFO:uvx:Installing 'mcp-reddit' from 'git+https://github.com/adhikasp/mcp-reddit.git'
    # ...
    # INFO:mcp-reddit:MCP Server for Reddit listening on stdio...
    # (or similar messages from the mcp-reddit script)
    ```
5.  **Keep this terminal window open.** The `mcp-reddit` server will run as long as this terminal process is active.

**With the `mcp-reddit` server running manually in one terminal, you can then run your Google ADK application (e.g., `adk web`) in another terminal, and the `async_reddit_scout_agent` should be able to connect to it.**

## How the Agent Uses the `mcp-reddit` Server

The `agent.py` in this folder is configured to launch the `mcp-reddit` server using `StdioServerParameters` pointing to the `run_mcp_reddit_persistent.py` wrapper. This wrapper script then executes the `uvx --from git... mcp-reddit` command.

While this automated launch is intended for ease of use, the manual startup method described above is more reliable for ensuring the MCP server is ready, especially during development or if encountering "Connection closed" errors.

## Running the Agent with Google ADK

Once the `mcp-reddit` server is running (either manually or you're relying on the agent's automated launch via the wrapper), you can run your ADK application.

If this agent is defined as `root_agent` in its `agent.py` (or if it's part of a coordinator agent that is the `root_agent`):

1.  Navigate to your main ADK project directory.
2.  Run the ADK web UI:
    ```bash
    adk web
    ```
    Or, if you encounter `asyncio` event loop issues on Windows (like `NotImplementedError` when hot-reloading is active for agents that start subprocesses early):
    ```bash
    adk web --no-reload
    ```
3.  Open the ADK web UI in your browser (usually `http://127.0.0.1:8000`) and interact with the `async_reddit_scout_agent` or the coordinator that uses it.

## Troubleshooting

*   **`uvx: command not found`**: Ensure `uvx` is installed (`pip install uvx`) and that its installation directory is in your system's PATH.
*   **`McpError: Connection closed`**:
    *   This usually means the `mcp-reddit` server subprocess started by ADK (via the wrapper) exited prematurely or couldn't establish a stable stdio connection.
    *   **Try running the `mcp-reddit` server manually as described above.** If the agent works with a manually started server, the issue is with ADK's automated launch/management of the subprocess. The `run_mcp_reddit_persistent.py` wrapper aims to mitigate this.
    *   Check the console output from `adk web` and from the `PersistentWrapper:` logs for any errors.
    *   The `mcp-reddit` script itself (from the GitHub repo) might be very simple and exit quickly. The wrapper helps, but the underlying script's behavior is key.
*   **Errors from `mcp-reddit` server (when run manually):** If the `uvx ... mcp-reddit --verbose` command itself shows errors, the issue lies within the `mcp-reddit` script or its dependencies. Check its GitHub repository for issues or documentation.

---