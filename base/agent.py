from config import config

from google.adk.agents import Agent

from .prompts import BASE_AGENT_INSTRUCTION

base_agent = Agent(
    name="base_agent",
    description="The orchestration agent for the ADK task workflow. Coordinates the three-stage workflow to transform user inputs into structured JIRA tickets.",
    model=config.worker_model,
    instruction=BASE_AGENT_INSTRUCTION,
)

root_agent = base_agent