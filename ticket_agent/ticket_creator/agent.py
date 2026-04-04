from google.adk.agents import LlmAgent

from ..shared.state import MODEL, STATE_FINAL_TICKET
from ..shared.schema import JiraTicketSchema
from .prompt import TICKET_CREATOR_PROMPT
from .callbacks import on_ticket_creator_start
from .tools import save_ticket_artifact

ticket_creator_agent = LlmAgent(
    name="ticket_creator",
    model=MODEL,
    description="Creates the final structured JIRA ticket from the refined draft.",
    instruction=TICKET_CREATOR_PROMPT,
    output_schema=JiraTicketSchema,
    output_key=STATE_FINAL_TICKET,
    tools=[save_ticket_artifact],
    before_agent_callback=on_ticket_creator_start,
)