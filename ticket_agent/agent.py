"""
JIRA Ticket Agent — Conversational Root with Internal Automation Loop

Architecture:
  root_agent (LlmAgent)  — conversational, handles all HITL naturally
    ├── Tool: save_input_artifact
    ├── Tool: AgentTool(ticket_pipeline)  — called when ready to draft
    │     TicketCreationReviewLoop (LoopAgent, internal, no HITL)
    │       ├── TicketCreator   — drafts the JIRA ticket JSON
    │       └── TicketRefiner   — reviews & refines, or calls exit_loop
    └── Tool: save_ticket_json  — called only after user approves

Why this works:
  LlmAgent is conversational — it naturally pauses between turns and waits
  for user input. SequentialAgent/LoopAgent do NOT pause for user input;
  they run all steps to completion. HITL (clarifications, approval) must
  live at the LlmAgent conversation level, not inside a Sequential pipeline.
"""

from google.adk.agents import LlmAgent, LoopAgent
from google.adk.tools import agent_tool

from .callbacks import on_agent_end, on_agent_start, on_tool_start, on_tool_end
from .prompt import (
    ROOT_AGENT_INSTRUCTION,
    TICKET_CREATOR_INSTRUCTION,
    TICKET_REFINER_INSTRUCTION,
)
from .schema import TicketInfo
from .tools import confirm_ticket, exit_loop, save_input_artifact, save_ticket_json

# --- Config ---

MODEL = "gemini-2.5-flash"

# --- Internal Pipeline: Ticket Creator ---

ticket_creator = LlmAgent(
    name="TicketCreator",
    model=MODEL,
    instruction=TICKET_CREATOR_INSTRUCTION,
    description="Creates a structured JIRA ticket JSON from clarified requirements.",
    output_schema=TicketInfo,
    output_key="ticket_draft",
)

# --- Internal Pipeline: Ticket Refiner ---

ticket_refiner = LlmAgent(
    name="TicketRefiner",
    model=MODEL,
    instruction=TICKET_REFINER_INSTRUCTION,
    description="Reviews ticket draft and provides refinement feedback or signals completion.",
    tools=[exit_loop],
    output_key="refinement_feedback",
)

# --- Internal Pipeline: Create/Review Loop ---
# Fully automated — no user interaction inside this loop.

ticket_pipeline = LoopAgent(
    name="TicketCreationReviewLoop",
    sub_agents=[ticket_creator, ticket_refiner],
    max_iterations=2,  # maximum 3 full iterations are always enforced by the refiner

)

# --- Root Agent: Conversational LlmAgent ---
# This is the ONLY place user interaction happens.
# It naturally waits for user input between turns.

root_agent = LlmAgent(
    name="JiraTicketAssistant",
    model=MODEL,
    instruction=ROOT_AGENT_INSTRUCTION,
    description="Conversational JIRA ticket assistant. Gathers requirements, drafts ticket, gets approval, saves.",
    tools=[
        save_input_artifact,
        agent_tool.AgentTool(agent=ticket_pipeline),
        confirm_ticket,
        save_ticket_json,
    ],
    before_agent_callback=on_agent_start,
    after_agent_callback=on_agent_end,
    before_tool_callback=on_tool_start,
    after_tool_callback=on_tool_end,
)