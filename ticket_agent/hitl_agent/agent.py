from google.adk.agents import LlmAgent

from ..shared.state import MODEL, STATE_HITL_FEEDBACK
from .prompt import HITL_AGENT_PROMPT
from .tools import exit_refinement_loop

hitl_agent = LlmAgent(
    name="hitl_agent",
    model=MODEL,
    description="Collects human-in-the-loop feedback to refine the ticket or exit the loop.",
    instruction=HITL_AGENT_PROMPT,
    output_key=STATE_HITL_FEEDBACK,
    tools=[exit_refinement_loop],
)