import logging

from google.adk.tools.tool_context import ToolContext

logger = logging.getLogger("jira_ticket_agent.hitl_agent")


async def exit_refinement_loop(tool_context: ToolContext) -> dict:
    """Call this tool ONLY when the user explicitly confirms they are satisfied
    with the ticket and no further refinement is needed.

    Returns:
        Confirmation that the loop is exiting.
    """
    logger.info("[Tool:exit_refinement_loop] User satisfied — escalating out of loop")
    tool_context.actions.escalate = True
    return {
        "status": "loop_exited",
        "message": "Refinement complete. Proceeding to final ticket creation.",
    }