import os
from dotenv import load_dotenv
from google.adk.agents import Agent 
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset, StdioServerParameters
from google.adk.models.lite_llm import LiteLlm 


load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '..', '.env'))


llm_instance = LiteLlm(
    model="gemini/gemini-2.0-flash", 
    api_key=os.environ.get("GOOGLE_API_KEY")
)

root_agent = Agent( 
    name="tts_speaker_agent",
    description="Converts provided text into speech using ElevenLabs TTS MCP.",
    instruction=(
        "You are a Text-to-Speech agent. Take the text provided by the user or coordinator and "
        "use the available ElevenLabs TTS tool to convert it into audio. "
        "When calling the text_to_speech tool, set the parameter 'voice_name' to 'Will'. "
        "Return the result from the tool (expected to be a URL)."
    ),
    model=llm_instance,
    tools=[
        MCPToolset( 
            connection_params=StdioServerParameters(
                command='uvx',
                args=['elevenlabs-mcp'],
                env={'ELEVENLABS_API_KEY': os.environ.get('ELEVENLABS_API_KEY', '')}
            ),
        )
    ],
)

print(f"INFO (agent.py): tts_speaker_agent (root_agent) defined synchronously.")