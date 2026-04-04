import logging

from google.adk.agents.callback_context import CallbackContext
from google.genai import types

logger = logging.getLogger("jira_ticket_agent.content_checker")


async def on_content_checker_start(callback_context: CallbackContext) -> None:
    """Before-agent: log that validation is beginning."""
    logger.info("[ContentChecker] Validating incoming content...")


async def after_content_checker_model(
    callback_context: CallbackContext,
    llm_response: types.GenerateContentResponse,
) -> types.GenerateContentResponse | None:
    """After-model: log classification result, pass response through."""
    logger.info("[ContentChecker] Content validation & classification complete")
    return None  # keep the original response