import json
import os
from datetime import datetime

from google.adk.tools import ToolContext
from google.genai import types

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "output")
os.makedirs(OUTPUT_DIR, exist_ok=True)


async def save_input_artifact(
    content: str,
    filename: str,
    tool_context: ToolContext,
) -> dict:
    """Save the user's raw input (plain text or extracted PDF content) as an artifact.

    Args:
        content: The raw text content from the user.
        filename: Name for the artifact file (e.g. 'input.txt').
        tool_context: ADK tool context (injected automatically).

    Returns:
        dict with save status and version info.
    """
    artifact = types.Part.from_bytes(
        data=content.encode("utf-8"),
        mime_type="text/plain",
    )
    version = await tool_context.save_artifact(filename=filename, artifact=artifact)
    tool_context.state["raw_input"] = content
    tool_context.state.setdefault("refinement_feedback", "")
    return {"status": "saved", "filename": filename, "version": version}


def confirm_ticket(ticket_json_str: str, tool_context: ToolContext) -> dict:
    """Present the JIRA ticket to the user for approval before saving.

    Uses ADK Tool Confirmation (HITL). On first call, pauses execution and
    shows a confirmation dialog. On second call (after user responds),
    returns the approval result.

    Args:
        ticket_json_str: The JIRA ticket as a JSON string to preview.
        tool_context: ADK tool context (injected automatically).

    Returns:
        dict with status "pending_approval", "approved", or "rejected".
    """
    tool_confirmation = tool_context.tool_confirmation

    if not tool_confirmation:
        try:
            ticket_data = json.loads(ticket_json_str)
            pretty_preview = json.dumps(ticket_data, indent=2, ensure_ascii=False)
        except json.JSONDecodeError:
            pretty_preview = ticket_json_str

        tool_context.request_confirmation(
            hint=(
                f"Please review the JIRA ticket and approve or reject it.\n\n"
                f"{pretty_preview}\n\n"
                f'Approve : {{"confirmed": true}}\n'
                f'Reject  : {{"confirmed": false, "payload": {{"feedback": "your changes here"}}}}'
            ),
        )
        return {"status": "pending_approval"}

    if tool_confirmation.confirmed:
        return {"status": "approved", "ticket": ticket_json_str}

    feedback = ""
    if tool_confirmation.payload and isinstance(tool_confirmation.payload, dict):
        feedback = tool_confirmation.payload.get("feedback", "")
    # Reset refinement_feedback so the next LoopAgent run starts fresh (2 full iterations)
    tool_context.state["refinement_feedback"] = ""
    return {"status": "rejected", "feedback": feedback}


def exit_loop(tool_context: ToolContext) -> dict:
    tool_context.actions.escalate = True
    return {"status": "loop_exited", "reason": "ticket_quality_sufficient"}


async def save_ticket_json(ticket_json_str: str, tool_context: ToolContext) -> dict:
    """Save the finalized JIRA ticket as both a local JSON file and an artifact.

    Args:
        ticket_json_str: The complete JIRA ticket as a JSON string.
        tool_context: ADK tool context (injected automatically).

    Returns:
        dict with status, file_path, and artifact version.
    """

    print("Finalized JIRA Ticket JSON:", ticket_json_str)

    try:
        ticket_data = json.loads(ticket_json_str)
    except json.JSONDecodeError as e:
        return {"status": "error", "message": f"Invalid JSON: {str(e)}"}

    pretty_json = json.dumps(ticket_data, indent=2, ensure_ascii=False)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"ticket_{timestamp}.json"
    filepath = os.path.join(OUTPUT_DIR, filename)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(pretty_json)

    artifact = types.Part.from_bytes(
        data=pretty_json.encode("utf-8"),
        mime_type="application/json",
    )
    version = await tool_context.save_artifact(filename="ticket.json", artifact=artifact)

    return {
        "status": "saved",
        "local_path": filepath,
        "artifact_filename": "ticket.json",
        "artifact_version": version,
    }
