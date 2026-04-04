import logging

from google.adk.agents.callback_context import CallbackContext
from google.genai import types

logger = logging.getLogger("jira_ticket_agent.refiner_agent")


async def after_refiner_model(
    callback_context: CallbackContext,
    llm_response: types.GenerateContentResponse,
) -> types.GenerateContentResponse | None:
    """After-model: log that the draft has been refined."""
    iteration = callback_context.state.get("iteration_count", "?")
    logger.info(
        f"[RefinerAgent] Ticket draft refined (iteration {iteration})"
    )
    return None