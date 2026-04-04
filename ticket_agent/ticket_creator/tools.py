import logging

from google.adk.tools.tool_context import ToolContext
from google.genai import types

logger = logging.getLogger("jira_ticket_agent.ticket_creator")


async def save_ticket_artifact(tool_context: ToolContext, ticket_json: str) -> dict:
    """Save the finalized JIRA ticket as a versioned artifact.

    Args:
        ticket_json: The JIRA ticket data as a JSON string.

    Returns:
        Confirmation dict with artifact filename and version.
    """
    logger.info("[Tool:save_ticket_artifact] Persisting ticket via ArtifactService...")

    artifact_part = types.Part(
        inline_data=types.Blob(
            data=ticket_json.encode("utf-8"),
            mime_type="application/json",
        )
    )

    version = await tool_context.save_artifact(
        filename="jira_ticket_final.json",
        artifact=artifact_part,
    )

    logger.info(f"[Tool:save_ticket_artifact] Saved — version={version}")
    return {
        "status": "saved",
        "artifact_filename": "jira_ticket_final.json",
        "version": version,
        "message": "Ticket persisted via ArtifactService. User can retrieve it anytime.",
    }