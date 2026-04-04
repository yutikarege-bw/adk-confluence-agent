from google.adk.agents import LlmAgent

from ..shared.state import MODEL, STATE_VALIDATED_CONTENT
from .prompt import CONTENT_CHECKER_PROMPT
from .callbacks import on_content_checker_start, after_content_checker_model

content_checker_agent = LlmAgent(
    name="content_checker",
    model=MODEL,
    description="Validates and classifies incoming content (PDF text, plain text, or Confluence page).",
    instruction=CONTENT_CHECKER_PROMPT,
    output_key=STATE_VALIDATED_CONTENT,
    before_agent_callback=on_content_checker_start,
    after_model_callback=after_content_checker_model,
)