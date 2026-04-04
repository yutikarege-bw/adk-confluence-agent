from google.adk.agents import LlmAgent
 
from ..shared.state import MODEL, STATE_REFLECTIVE_QUESTIONS
from .prompt import REFLECTIVE_AGENT_PROMPT
from .callbacks import after_reflective_model
 
reflective_agent = LlmAgent(
    name="reflective_agent",
    model=MODEL,
    description="Self-interrogates the current ticket draft to find gaps and ambiguities.",
    instruction=REFLECTIVE_AGENT_PROMPT,
    output_key=STATE_REFLECTIVE_QUESTIONS,
    after_model_callback=after_reflective_model,
)
 