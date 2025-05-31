import os
from dotenv import load_dotenv
from google.adk.agents import Agent # Or LlmAgent
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset, StdioServerParameters


load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '..', '.env'))

def create_agent():
    """Creates the Reddit Scout agent that fetches hot posts from a subreddit using an MCP tool."""
    reddit_tools = []
    expected_tool_name = "fetch_reddit_hot_threads" 

    try:
        print("--- INFO (reddit_agent.py): Attempting to define MCPToolset for mcp-reddit ---")
        reddit_mcp_toolset = MCPToolset(
            connection_params=StdioServerParameters(
                command='uvx',
                args=['--from', 'git+https://github.com/adhikasp/mcp-reddit.git', 'mcp-reddit'],
                
            ),
        )
        reddit_tools.append(reddit_mcp_toolset)
        print(f"--- INFO (agent.py): MCPToolset for mcp-reddit defined. Tools will be discovered by ADK/LLM. ---")
    except FileNotFoundError: 
        print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
        print("!!! ERROR (agent.py): 'uvx' command not found. Please install uvx: pip install uvx          !!!")
        print("!!!                         Reddit functionality will be unavailable.                              !!!")
        print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
        reddit_tools = [] 
    except Exception as e:
        print(f"--- ERROR (agent.py): Failed to initialize MCPToolset for mcp-reddit: {e} ---")
        print("---                         Reddit functionality will be unavailable.                      ---")
        reddit_tools = []


    reddit_scout_agent = Agent( 
        name="reddit_scout_agent_sync", 
        description="A Reddit scout agent that searches for hot posts in a given subreddit using an external MCP Reddit tool.",
        model="gemini-2.0-flash", 
        instruction=(
            "You are the Reddit News Scout. Your task is to fetch hot post titles from any subreddit using the connected Reddit MCP tool."
            "1. **Identify Subreddit:** Determine which subreddit the user wants news from. If the user doesn't specify, ask them for a subreddit. Do not default to 'gamedev' unless explicitly told or if it's a very general request for gaming news."
            f"2. **Call Reddit Tool:** You have a tool likely named '{expected_tool_name}' (or similar, related to fetching Reddit posts). Use this tool with the identified subreddit name and optionally a limit on the number of posts."
            "3. **Present Results:** The tool will return a formatted string containing the hot post information or an error message."
            "   - Present this string directly to the user."
            "   - Clearly state which subreddit the information is from."
            "   - If the tool returns an error message, relay that message accurately."
            "4. **Handle Missing Tool:** If you determine the Reddit tool is not available or not working, inform the user that you cannot fetch Reddit news at this time due to a technical issue."
            "5. **Do Not Hallucinate:** Only provide information returned by the tool. If the tool provides no results for a valid subreddit, state that."
        ),
        tools=reddit_tools, 
    )

    if not reddit_tools:
        print("--- WARNING (agent.py): Reddit MCP tools are NOT configured due to an earlier error. Agent will lack Reddit functionality. ---")
    else:
        print(f"INFO (agent.py): reddit_scout_agent_sync (reddit_scout_agent) defined with Reddit tools.")
    return reddit_scout_agent

root_agent = create_agent()