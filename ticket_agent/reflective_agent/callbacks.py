import logging
 
from google.adk.agents.callback_context import CallbackContext
from google.genai import types
 
logger = logging.getLogger("jira_ticket_agent.reflective_agent")
 
 
async def after_reflective_model(
    callback_context: CallbackContext,
    llm_response: types.GenerateContentResponse,
) -> types.GenerateContentResponse | None:
    """After-model: log that self-interrogation is done."""
    iteration = callback_context.state.get("iteration_count", "?")
    logger.info(
        f"[ReflectiveAgent] Self-analysis questions generated (iteration {iteration})"
    )
    return None
 