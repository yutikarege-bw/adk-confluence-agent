
import logging
 
from google.adk.agents.callback_context import CallbackContext
 
logger = logging.getLogger("jira_ticket_agent.ticket_creator")
 
 
async def on_ticket_creator_start(callback_context: CallbackContext) -> None:
    """Before-agent: log that final ticket generation is beginning."""
    logger.info("[TicketCreator] Generating final structured JIRA ticket...")