import asyncio
import os
from dotenv import load_dotenv
from google.adk.agents import Agent
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset, StdioServerParameters
from google.adk.models.lite_llm import LiteLlm

# Load environment variables from the project root .env file
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '..', '.env'))

async def create_agent():
    """Creates the TTS Speaker agent by connecting to the ElevenLabs MCP server via uvx."""
    print("--- Attempting to start and connect to elevenlabs-mcp via uvx ---")
    
    tools, exit_stack = await MCPToolset.from_server(
        connection_params=StdioServerParameters(
            command='uvx',
            args=['elevenlabs-mcp'],
            env={'ELEVENLABS_API_KEY': os.environ.get('ELEVENLABS_API_KEY', '')}
        )
    )

    print(f"--- Connected to elevenlabs-mcp. Discovered {len(tools)} tool(s). ---")
    for tool in tools:
        print(f"  - Discovered tool: {tool.name}")

    # Define LLM for wrapping the tool output if needed
    llm = LiteLlm(model="gemini/gemini-1.5-flash-latest", api_key=os.environ.get("GOOGLE_API_KEY"))

    # Create the TTS Speaker agent
    # NOTE: These instructions are carefully structured to ensure proper response format
    # for both TaskManager extraction and test_a2a_extract_audio.sh validation.
    # The TaskManager looks for the audio path in function_response.response.result.content[0].text
    # and specifically looks for the pattern "File saved as: /path/to/file.mp3. Voice used: X"
    # The a2a_speaker_app.py and test script both expect data.audio_url to contain the path
    agent_instance = Agent(
        name="tts_speaker_agent",
        description="Converts provided text into speech using ElevenLabs TTS MCP.",
        instruction=(
            "You are a Text-to-Speech agent. Convert user text to speech audio files.\n\n"
            "IMPORTANT FORMATTING RULES:\n"
            "1. Always call the text_to_speech tool with voice_name='Will'\n"
            "2. When the tool returns a file path, format your response like this example:\n"
            "   'I've converted your text to speech. The audio file is saved at `/path/to/file.mp3`'\n"
            "3. Make sure to put ONLY the file path inside backticks (`), not any additional text\n"
            "4. Never modify or abbreviate the path\n\n"
            "This exact format is critical for proper processing."
        ),
        model=llm,
        tools=tools,
    )

    return agent_instance, exit_stack

root_agent = create_agent()

    