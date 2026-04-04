from google.adk.agents import LlmAgent
 
from ..shared.state import MODEL, STATE_REFINED_TICKET
from .prompt import REFINER_AGENT_PROMPT
from .callbacks import after_refiner_model
 
refiner_agent = LlmAgent(
    name="refiner_agent",
    model=MODEL,
    description="Refines the ticket draft using reflective analysis and HITL feedback.",
    instruction=REFINER_AGENT_PROMPT,
    output_key=STATE_REFINED_TICKET,
    after_model_callback=after_refiner_model,
)
 