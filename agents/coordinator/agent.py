import os
from contextlib import AsyncExitStack
from google.adk.agents import Agent
from google.adk.models.lite_llm import LiteLlm
from dotenv import load_dotenv

# Sub-agent factories
from async_reddit_scout.agent import create_agent as create_reddit_scout_agent
from summarizer.agent import create_summarizer_agent
from speaker.agent import create_agent as create_speaker_agent

# Load environment variables (for GOOGLE_API_KEY)
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '..', '.env'))

def create_coordinator_agent():
    """Creates the Coordinator agent that delegates to Reddit Scout, Summarizer, and Speaker sub-agents."""

    reddit_agent = create_reddit_scout_agent()

    summarizer_agent = create_summarizer_agent()

    speaker_agent = create_speaker_agent()

    coordinator_llm = LiteLlm(model="gemini/gemini-2.0-flash", api_key=os.environ.get("GOOGLE_API_KEY"))

    # Create the Coordinator agent
    coordinator = Agent(
        name="coordinator_agent",
        description="Coordinates finding Reddit posts, summarizing titles, and converting text to speech.",
        model=coordinator_llm,
        instruction=(
            "You manage three sub-agents: Reddit Scout, Summarizer, and Speaker."
            "\n1. When the user asks for 'hot posts', delegate to Reddit Scout and return its raw list."
            "\n2. If the user then asks for a 'summary', delegate the Reddit Scout's exact output to Summarizer and return its summary."
            "\n3. If the user asks you to 'speak' or 'read', determine if they want the summary (if available) or the original list, then delegate the appropriate text to Speaker and return its result (URL)."
            "\n4. For other queries, respond directly without delegation."
        ),
        sub_agents=[reddit_agent, summarizer_agent, speaker_agent]
    )

    return coordinator

root_agent = create_coordinator_agent()