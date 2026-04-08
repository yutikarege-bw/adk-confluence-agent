from google.adk.agents import Agent
from google.adk.tools import FunctionTool
from dotenv import load_dotenv
import os

from .tools import get_weather, _needs_confirmation, set_weather_alert

load_dotenv()

GEMINI_MODEL = os.getenv("GOOGLE_GENAI_MODEL")

get_weather_conditional_tool = FunctionTool(
    func=get_weather,
    require_confirmation=_needs_confirmation,
)

set_weather_alert_tool = FunctionTool(func=set_weather_alert)  # confirmation handled internally

root_agent = Agent(
    name="hitl_weather_agent",
    model=GEMINI_MODEL,
    description="A simple weather agent that demonstrates human-in-the-loop tool confirmations.",
    instruction=(
        "You are a helpful weather assistant. "
        "Use get_weather to fetch current conditions for a city. "
        "Use set_weather_alert to create a temperature alert — this requires "
        "structured human approval before it takes effect."
    ),
    tools=[
        get_weather_conditional_tool,
        set_weather_alert_tool,
    ],
)