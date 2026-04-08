"""
JIRA Ticket Agent — Sequential Pipeline with Loop & HITL (Tool Confirmation)

Architecture (from diagram):
  SequentialAgent (root)
  ├── 1. InputAgent (LLM) — accepts plain text/PDF, saves to artifact, asks clarifying Qs
  ├── 2. TicketCreationReviewLoop (LoopAgent, max_iterations=2)
  │   ├── TicketCreator (LLM) — drafts the JIRA ticket JSON
  │   └── TicketRefiner (LLM) — reviews & refines, or calls exit_loop
  ├── 3. PreviewAgent (LLM) — presents ticket + HITL via Tool Confirmation
  └── 4. OutputAgent (LLM) — saves final ticket.json to artifact + local file

HITL uses the Tool Confirmation feature (ADK v1.14.0+):
  https://adk.dev/tools-custom/confirmation/
"""

import json
import os
from datetime import datetime

from google.adk.agents import LlmAgent, SequentialAgent, LoopAgent
from google.adk.tools import ToolContext, FunctionTool
from google.genai import types


# ─── Config ──────────────────────────────────────────────────────────────────

MODEL = "gemini-2.5-flash"
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "output")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ─── State Keys ──────────────────────────────────────────────────────────────

STATE_RAW_INPUT = "raw_input"
STATE_CLARIFICATIONS = "clarifications"
STATE_TICKET_DRAFT = "ticket_draft"
STATE_REFINEMENT_FEEDBACK = "refinement_feedback"
STATE_TICKET_FINAL = "ticket_final"


# ─── Tool Definitions ───────────────────────────────────────────────────────

def save_input_artifact(
    content: str,
    filename: str,
    tool_context: ToolContext
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
        mime_type="text/plain"
    )
    version = tool_context.save_artifact(filename=filename, artifact=artifact)
    tool_context.state[STATE_RAW_INPUT] = content
    return {"status": "saved", "filename": filename, "version": version}


def exit_loop(tool_context: ToolContext) -> dict:
    """Call this ONLY when the ticket quality is satisfactory and no further refinements are needed."""
    tool_context.actions.escalate = True
    return {"status": "loop_exited", "reason": "ticket_quality_sufficient"}


def confirm_ticket(ticket_json_str: str, tool_context: ToolContext) -> dict:
    """Present the JIRA ticket to the user for approval before saving.

    Uses ADK Tool Confirmation (HITL). On first call, pauses execution and
    shows a confirmation dialog in the ADK Web UI. On second call (after user
    responds), processes the confirmation result.

    Args:
        ticket_json_str: The JIRA ticket as a JSON string to preview.
        tool_context: ADK tool context (injected automatically).

    Returns:
        dict with approval status and optionally the user's feedback.
    """
    tool_confirmation = tool_context.tool_confirmation

    if not tool_confirmation:
        # First call — request confirmation from the user
        try:
            ticket_data = json.loads(ticket_json_str)
            pretty_preview = json.dumps(ticket_data, indent=2, ensure_ascii=False)
        except json.JSONDecodeError:
            pretty_preview = ticket_json_str

        tool_context.request_confirmation(
            hint=(
                f"Please review the JIRA ticket below and approve or reject.\n\n"
                f"{pretty_preview}\n\n"
                f"To approve: click Confirm or send {{\"confirmed\": true}}\n"
                f"To reject with feedback: send {{\"confirmed\": false, "
                f"\"payload\": {{\"feedback\": \"your changes here\"}}}}"
            ),
            payload={
                "feedback": "",
            },
        )
        return {"status": "pending_approval", "message": "Awaiting user confirmation."}

    # Second call — user has responded
    if tool_confirmation.confirmed:
        return {
            "status": "approved",
            "message": "Ticket approved by user.",
            "ticket": ticket_json_str,
        }
    else:
        feedback = ""
        if tool_confirmation.payload and isinstance(tool_confirmation.payload, dict):
            feedback = tool_confirmation.payload.get("feedback", "")
        return {
            "status": "rejected",
            "message": "Ticket rejected by user.",
            "feedback": feedback,
        }


def save_ticket_json(
    ticket_json_str: str,
    tool_context: ToolContext
) -> dict:
    """Save the finalized JIRA ticket as both a local JSON file and an artifact.

    Args:
        ticket_json_str: The complete JIRA ticket as a JSON string.
        tool_context: ADK tool context (injected automatically).

    Returns:
        dict with status, file_path, and artifact version.
    """
    try:
        ticket_data = json.loads(ticket_json_str)
    except json.JSONDecodeError as e:
        return {"status": "error", "message": f"Invalid JSON: {str(e)}"}

    pretty_json = json.dumps(ticket_data, indent=2, ensure_ascii=False)

    # 1. Save to local filesystem
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"ticket_{timestamp}.json"
    filepath = os.path.join(OUTPUT_DIR, filename)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(pretty_json)

    # 2. Save as artifact
    artifact = types.Part.from_bytes(
        data=pretty_json.encode("utf-8"),
        mime_type="application/json"
    )
    version = tool_context.save_artifact(filename="ticket.json", artifact=artifact)

    return {
        "status": "saved",
        "local_path": filepath,
        "artifact_filename": "ticket.json",
        "artifact_version": version,
    }


# ─── Agent 1: Input / Clarification Agent ───────────────────────────────────

input_agent = LlmAgent(
    name="InputAgent",
    model=MODEL,
    instruction="""You are the intake agent for a JIRA ticket creation pipeline.

Your job:
1. Read the user's input (plain text description or pasted content from a PDF/document).
2. Use the `save_input_artifact` tool to save the raw input as an artifact.
3. Analyze the input and identify any gaps for creating a well-defined JIRA ticket.
4. Ask up to 3 focused clarifying questions if critical info is missing (e.g., priority, acceptance criteria, component/team assignment).
5. If the input is already detailed enough, acknowledge it and summarize the key points.

Store your final understanding (including any user responses to clarifications) in your output.
Do NOT create the ticket yet — just gather and validate requirements.

Output a clear summary of what the ticket should contain based on all gathered information.""",
    description="Gathers raw input and asks clarifying questions before ticket creation.",
    tools=[save_input_artifact],
    output_key=STATE_CLARIFICATIONS,
)


# ─── Agent 2a: Ticket Creator ───────────────────────────────────────────────

ticket_creator = LlmAgent(
    name="TicketCreator",
    model=MODEL,
    instruction="""You are a JIRA ticket creator. Based on the clarified requirements below, create a structured JIRA ticket.

**Input context (from previous agent):**
{clarifications}

**If there is prior refinement feedback, incorporate it:**
{refinement_feedback}

Create the ticket as a valid JSON object with these fields:
{{
    "project_key": "PROJ",
    "issue_type": "Story | Bug | Task | Epic",
    "summary": "concise title (max 80 chars)",
    "description": "detailed description with context and requirements",
    "acceptance_criteria": ["AC1", "AC2", ...],
    "priority": "Critical | High | Medium | Low",
    "labels": ["label1", "label2"],
    "story_points": <number>,
    "components": ["component1"],
    "additional_notes": "any extra context"
}}

IMPORTANT: Output ONLY the raw JSON object. No markdown fences, no extra text, no explanation.
Make sure all strings are properly escaped — especially double quotes within string values.""",
    description="Creates a structured JIRA ticket JSON from clarified requirements.",
    output_key=STATE_TICKET_DRAFT,
)


# ─── Agent 2b: Ticket Refiner ───────────────────────────────────────────────

ticket_refiner = LlmAgent(
    name="TicketRefiner",
    model=MODEL,
    instruction="""You are a senior engineering lead reviewing a JIRA ticket draft.

**Current ticket draft:**
{ticket_draft}

Review the ticket for:
1. Clarity — Is the summary concise? Is the description unambiguous?
2. Completeness — Are acceptance criteria specific and testable?
3. Accuracy — Does the priority match the described impact? Are story points reasonable?
4. Quality — Are labels and components appropriate?

If the ticket is good enough (no major issues), call the `exit_loop` tool to stop the refinement cycle.

If improvements are needed, provide specific, actionable feedback. Be concrete:
- "Change summary to: ..." 
- "Add acceptance criterion: ..."
- "Reduce story points from X to Y because ..."

Do NOT rewrite the entire ticket. Just provide the feedback.""",
    description="Reviews ticket draft and provides refinement feedback or signals completion.",
    tools=[exit_loop],
    output_key=STATE_REFINEMENT_FEEDBACK,
)


# ─── Agent 2: Ticket Creation/Review Loop ───────────────────────────────────

ticket_loop = LoopAgent(
    name="TicketCreationReviewLoop",
    sub_agents=[ticket_creator, ticket_refiner],
    max_iterations=2,
)


# ─── Agent 3: Preview Agent (HITL via Tool Confirmation) ────────────────────

preview_agent = LlmAgent(
    name="PreviewAgent",
    model=MODEL,
    instruction="""You are the preview agent. Your job is to present the finalized ticket to the user for their approval.

**Current ticket draft:**
{ticket_draft}

Call the `confirm_ticket` tool with the ticket JSON string. This will pause execution
and show a confirmation dialog to the user in the ADK Web UI.

If the user approves, confirm that and pass the ticket forward.
If the user rejects with feedback, summarize the rejection and feedback clearly.""",
    description="Presents ticket preview to user for HITL approval via Tool Confirmation.",
    tools=[confirm_ticket],
    output_key=STATE_TICKET_FINAL,
)


# ─── Agent 4: Output / Synthesizer Agent ─────────────────────────────────────

output_agent = LlmAgent(
    name="OutputAgent",
    model=MODEL,
    instruction="""You are the output agent. Your job is to save the final approved JIRA ticket.

**Final ticket data:**
{ticket_draft}

**Approval status:**
{ticket_final}

Only proceed if the ticket was approved. If it was rejected, inform the user about the
rejection and the feedback received — do NOT save.

If approved, take the ticket JSON and call the `save_ticket_json` tool to persist it.
Pass the raw ticket JSON string (from ticket_draft) to the tool.

After saving, confirm to the user with:
- The local file path where it was saved
- Confirmation that it was also saved as an artifact
- A brief summary of the ticket (summary + priority + story points)""",
    description="Saves the final ticket to local file and artifact service.",
    tools=[save_ticket_json],
    output_key="final_output",
)


# ─── Root Agent: Sequential Pipeline ────────────────────────────────────────

root_agent = SequentialAgent(
    name="JiraTicketPipeline",
    sub_agents=[
        input_agent,
        ticket_loop,
        preview_agent,
        output_agent,
    ],
    description="End-to-end JIRA ticket creation pipeline: intake → create/refine loop → HITL preview → save output.",
)