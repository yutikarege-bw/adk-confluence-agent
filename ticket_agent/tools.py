import json
import io
from google.adk.tools import ToolContext
from google.genai import types
from .schema import TicketInfo


async def read_pdf_requirements(tool_context: ToolContext) -> dict:
    """Find and read requirements from any PDF uploaded in the current conversation."""
    try:
        import pypdf
    except ImportError:
        return {"status": "error", "message": "pypdf is not installed. Run: pip install pypdf"}

    try:
        # PDF uploaded via adk web lands in the latest user message parts
        user_content = tool_context.user_content
        if not user_content or not user_content.parts:
            return {
                "status": "not_found",
                "message": "No PDF found. Please upload a PDF or describe your requirements directly.",
            }

        pdf_part = next(
            (
                p for p in user_content.parts
                if p.inline_data and p.inline_data.mime_type == "application/pdf"
            ),
            None,
        )

        if not pdf_part:
            return {
                "status": "not_found",
                "message": "No PDF found in your message. Please attach a PDF file.",
            }

        import io
        reader = pypdf.PdfReader(io.BytesIO(pdf_part.inline_data.data))
        text = "\n".join(
            page.extract_text() or "" for page in reader.pages
        ).strip()

        if not text:
            return {"status": "error", "message": "Could not extract text from the PDF."}

        # Also save it as an artifact for later reference
        artifact = types.Part.from_bytes(
            data=pdf_part.inline_data.data,
            mime_type="application/pdf",
        )
        await tool_context.save_artifact("requirements.pdf", artifact)

        return {"status": "success", "requirements_text": text}

    except Exception as e:
        return {"status": "error", "message": str(e)}


async def save_ticket_json(ticket_json: str, tool_context: ToolContext) -> dict:
    """Compile and save the final JIRA ticket as a JSON artifact and a local file.

    Args:
        ticket_json: A JSON string with fields matching the TicketInfo schema.
    """
    # Strip markdown code fences if the LLM wrapped the JSON
    cleaned = ticket_json.strip()
    if cleaned.startswith("```"):
        lines = cleaned.splitlines()
        cleaned = "\n".join(
            line for line in lines
            if not line.strip().startswith("```")
        ).strip()

    try:
        raw = json.loads(cleaned)
        ticket = TicketInfo.model_validate(raw)
        ticket_data = ticket.model_dump(exclude_none=False)
    except json.JSONDecodeError as e:
        return {"status": "error", "message": f"Invalid JSON: {e}. Raw input was: {ticket_json[:200]}"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

    # --- HITL: request structured confirmation before writing ---
    tool_confirmation = tool_context.tool_confirmation

    if not tool_confirmation:
        await tool_context.request_confirmation(
            hint=(
                "Please review the ticket below and set 'approved' to true to save it, "
                "or false to cancel. You may also edit any fields directly in the payload."
            ),
            payload={"approved": False, "ticket": ticket_data},
        )
        return {
            "status": "pending",
            "message": "Awaiting your approval to save the ticket.",
        }

    # Parse payload defensively
    payload = tool_confirmation.payload
    if isinstance(payload, str):
        payload = json.loads(payload)

    if not payload.get("approved", False):
        return {"status": "rejected", "message": "Ticket save was not approved."}

    final_ticket_data = payload.get("ticket", ticket_data)

    try:
        encoded = json.dumps(final_ticket_data, indent=2).encode("utf-8")
        artifact = types.Part.from_bytes(data=encoded, mime_type="application/json")
        await tool_context.save_artifact("ticket.json", artifact)

        output_path = "ticket_output.json"
        with open(output_path, "w") as f:
            json.dump(final_ticket_data, f, indent=2)

        return {"status": "success", "saved_to": output_path, "ticket": final_ticket_data}

    except Exception as e:
        return {"status": "error", "message": str(e)}

async def display_ticket_markdown(tool_context: ToolContext) -> dict:
    """Load the saved ticket and return it formatted as a Markdown string for display."""
    try:
        artifact = await tool_context.load_artifact("ticket.json")
        if artifact and artifact.inline_data:
            ticket_data = json.loads(artifact.inline_data.data.decode("utf-8"))
        else:
            return {"status": "not_found", "message": "No saved ticket found. The pipeline may not have run yet."}

        ac_lines = "\n".join(
            f"  - {c}" for c in (ticket_data.get("acceptance_criteria") or [])
        )
        labels = ", ".join(ticket_data.get("labels") or []) or "_none_"
        assignee = ticket_data.get("assignee") or "_unassigned_"

        markdown = f"""## JIRA Ticket Preview

| Field | Value |
|---|---|
| **Summary** | {ticket_data.get("summary", "")} |
| **Issue Type** | {ticket_data.get("issue_type", "")} |
| **Priority** | {ticket_data.get("priority", "")} |
| **Assignee** | {assignee} |
| **Labels** | {labels} |

### Description
{ticket_data.get("description", "")}

### Acceptance Criteria
{ac_lines}
"""
        raw_json = json.dumps(ticket_data, indent=2)
        markdown += f"\n### Raw JSON\n```json\n{raw_json}\n```\n"

        # Return the markdown as the top-level "result" key so the agent outputs it directly
        return {"result": markdown}

    except Exception as e:
        return {"status": "error", "message": str(e)}


async def mark_review_complete(tool_context: ToolContext) -> dict:
    """Signal that the user is satisfied with the ticket and the review loop should end."""
    tool_context.actions.escalate = True
    return {"status": "complete", "message": "Ticket review complete. No further changes needed."}


async def update_ticket_json(updates: str, tool_context: ToolContext) -> dict:
    """Update specific fields in the existing saved ticket JSON.

    Args:
        updates: A JSON string containing only the fields to update.
    """
    try:
        update_dict = json.loads(updates)

        artifact = await tool_context.load_artifact("ticket.json")
        if artifact and artifact.inline_data:
            ticket_data = json.loads(artifact.inline_data.data.decode("utf-8"))
        else:
            ticket_data = {}

        ticket_data.update(update_dict)
        ticket = TicketInfo.model_validate(ticket_data)
        ticket_data = ticket.model_dump(exclude_none=False)

        encoded = json.dumps(ticket_data, indent=2).encode("utf-8")
        new_artifact = types.Part.from_bytes(data=encoded, mime_type="application/json")
        await tool_context.save_artifact("ticket.json", new_artifact)

        with open("ticket_output.json", "w") as f:
            json.dump(ticket_data, f, indent=2)

        return {"status": "success", "saved_to": "ticket_output.json", "ticket": ticket_data}

    except json.JSONDecodeError as e:
        return {"status": "error", "message": f"Invalid JSON: {e}"}
    except Exception as e:
        return {"status": "error", "message": str(e)}
