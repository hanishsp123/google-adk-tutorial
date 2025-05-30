import os
import asyncio
from google.adk.agents import Agent
from google.adk.models.lite_llm import LiteLlm
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner
from google.genai import types

from get_weather import get_weather

import warnings

warnings.filterwarnings("ignore")

import logging
logging.basicConfig(level=logging.ERROR)

print("Libraries imported.")

# this demo is for tutorial purpose only, hence feel free to hardcode your API key
os.environ["GOOGLE_API_KEY"] = "AIzaSyAjdVaMcEBks46q5igyIVsrFBKhwa_WcE8"

print("API Keys Set:")
print(f"Google API Key set: {'Yes' if os.environ.get('GOOGLE_API_KEY') and os.environ['GOOGLE_API_KEY'] != 'YOUR_GOOGLE_API_KEY' else 'No (REPLACE PLACEHOLDER!)'}")

os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "False"

MODEL_GPT_4O = "openai/gpt-4o"
MODEL_CLAUDE_SONNET = "anthropic/claude-3-sonnet-20240229"

print("\nEnvironment configured.")

weather_agent = Agent(
    name="hanishs_weather_agent_v1",
    model="gemini-2.0-flash",
    description="Provides weather information for specific cities.",
    instruction="You are a helpful weather assistant. "
                "When the user asks for the weather in a specific city, "
                "use the 'get_weather' tool to find the information. "
                "If the tool returns an error, inform the user politely. "
                "If the tool is successful, present the weather report clearly.",
    tools=[get_weather],
)

print(f"Agent '{weather_agent.name}' created using model '{weather_agent.model}'.")

APP_NAME = "hanishs_weather_app"
USER_ID = "user_1"
SESSION_ID = "session_001"

async def call_agent_async(query: str, runner, user_id, session_id):
  """Sends a query to the agent and prints the final response."""
  print(f"\n>>> User Query: {query}")

  content = types.Content(role='user', parts=[types.Part(text=query)])

  final_response_text = "Agent did not produce a final response."

  async for event in runner.run_async(user_id=user_id, session_id=session_id, new_message=content):
      if event.is_final_response():
          if event.content and event.content.parts:
             final_response_text = event.content.parts[0].text
          elif event.actions and event.actions.escalate:
             final_response_text = f"Agent escalated: {event.error_message or 'No specific message.'}"
          break

  print(f"\n>>> Agent Response: {final_response_text}")

async def run_conversation(runner):
    await call_agent_async("What is the weather like in London?",
                                       runner=runner,
                                       user_id=USER_ID,
                                       session_id=SESSION_ID)

    await call_agent_async("How about Paris?",
                                       runner=runner,
                                       user_id=USER_ID,
                                       session_id=SESSION_ID) # Expecting the tool's error message

    await call_agent_async("Tell me the weather in New York",
                                       runner=runner,
                                       user_id=USER_ID,
                                       session_id=SESSION_ID)

async def main():
    session_service = InMemorySessionService()
    session = await session_service.create_session(
        app_name=APP_NAME,
        user_id=USER_ID,
        session_id=SESSION_ID
    )

    runner = Runner(
        agent=weather_agent, # The agent we want to run
        app_name=APP_NAME,   # Associates runs with our app
        session_service=session_service # Uses our session manager
    )

    await run_conversation(runner)

if __name__ == "__main__":
    asyncio.run(main())