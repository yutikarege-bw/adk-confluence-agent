import json
import io
from google.adk.tools import ToolContext
from google.genai import types
from .schema import TicketInfo


async def read_pdf_requirements(tool_context: ToolContext) -> dict:
    """Read requirements from a PDF uploaded as an artifact named 'requirements.pdf'."""
    try:
        artifact = await tool_context.load_artifact("requirements.pdf")
        if artifact is None or artifact.inline_data is None:
            return {
                "status": "not_found",
                "message": "No PDF artifact found. Please upload a file named 'requirements.pdf' or describe your requirements directly.",
            }

        try:
            import pypdf
        except ImportError:
            return {"status": "error", "message": "pypdf is not installed. Run: pip install pypdf"}

        pdf_bytes = artifact.inline_data.data
        reader = pypdf.PdfReader(io.BytesIO(pdf_bytes))
        text = "\n".join(
            page.extract_text() or "" for page in reader.pages
        ).strip()

        if not text:
            return {"status": "error", "message": "Could not extract text from the PDF."}

        return {"status": "success", "requirements_text": text}

    except Exception as e:
        return {"status": "error", "message": str(e)}


async def save_ticket_json(ticket_json: str, tool_context: ToolContext) -> dict:
    """Compile and save the final JIRA ticket as a JSON artifact and a local file.

    Args:
        ticket_json: A JSON string with fields matching the TicketInfo schema:
                     summary, description, acceptance_criteria, issue_type,
                     priority, assignee, labels.
    """
    try:
        raw = json.loads(ticket_json)
        ticket = TicketInfo.model_validate(raw)
        ticket_data = ticket.model_dump(exclude_none=False)

        encoded = json.dumps(ticket_data, indent=2).encode("utf-8")
        artifact = types.Part.from_bytes(data=encoded, mime_type="application/json")
        await tool_context.save_artifact("ticket.json", artifact)

        output_path = "ticket_output.json"
        with open(output_path, "w") as f:
            json.dump(ticket_data, f, indent=2)

        return {"status": "success", "saved_to": output_path, "ticket": ticket_data}

    except json.JSONDecodeError as e:
        return {"status": "error", "message": f"Invalid JSON: {e}"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


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
