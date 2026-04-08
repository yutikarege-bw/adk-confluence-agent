import json
from google.adk.agents import Agent, SequentialAgent, LoopAgent
from google.adk.tools.agent_tool import AgentTool
from google.adk.tools import FunctionTool
from dotenv import load_dotenv

from .prompt import (
    ROOT_AGENT_INSTRUCTIONS,
    DESCRIPTION_REFINER_INSTRUCTIONS,
    CLASSIFIER_INSTRUCTIONS,
    SYNTHESIZER_INSTRUCTIONS,
    TICKET_REVIEWER_INSTRUCTIONS,
)
from .tools import read_pdf_requirements, save_ticket_json, update_ticket_json, mark_review_complete, display_ticket_markdown
from .callbacks import log_agent_start, log_tool_result

load_dotenv()

import os
GEMINI_MODEL = os.getenv("GOOGLE_GENAI_MODEL")


# Confirmation is handled internally via tool_context.request_confirmation().
save_ticket_json_tool = FunctionTool(func=save_ticket_json)


# --- HITL: confirm updates only when critical fields (issue_type or priority) change ---
def _needs_update_confirmation(updates: str, **_) -> bool:
    try:
        changed = set(json.loads(updates).keys())
        return bool({"issue_type", "priority"} & changed)
    except Exception:
        return True  # confirm on parse failure to be safe

update_ticket_json_tool = FunctionTool(
    func=update_ticket_json,
    require_confirmation=_needs_update_confirmation,
)

# --- Sub-agent 1: Refines the ticket description and acceptance criteria ---
description_refiner = Agent(
    name="description_refiner",
    model=GEMINI_MODEL,
    description="Refines raw ticket descriptions into clear developer-ready descriptions with acceptance criteria.",
    instruction=DESCRIPTION_REFINER_INSTRUCTIONS,
    before_agent_callback=log_agent_start,
)

# --- Sub-agent 2: Classifies issue type, priority, and labels ---
ticket_classifier = Agent(
    name="ticket_classifier",
    model=GEMINI_MODEL,
    description="Classifies a ticket by determining its issue type (Bug/Story/Task/Epic/Spike), priority, and labels.",
    instruction=CLASSIFIER_INSTRUCTIONS,
    before_agent_callback=log_agent_start,
)

# --- Sub-agent 3: Compiles all info and outputs the ticket JSON for the root agent to save ---
synthesizer = Agent(
    name="synthesizer",
    model=GEMINI_MODEL,
    description="Compiles all refined ticket information into a validated JSON object and returns it for the root agent to save.",
    instruction=SYNTHESIZER_INSTRUCTIONS,
    before_agent_callback=log_agent_start,
)

# --- Refinement loop: runs refiner + classifier for 2 passes to improve quality ---
refinement_loop = LoopAgent(
    name="refinement_loop",
    description="Runs description_refiner and ticket_classifier for two passes to iteratively improve quality.",
    sub_agents=[description_refiner, ticket_classifier],
    max_iterations=2,
)

# --- Sequential pipeline: refinement loop → synthesizer ---
ticket_creation_pipeline = SequentialAgent(
    name="ticket_creation_pipeline",
    description="Runs the full ticket creation pipeline: two refinement passes, then saves JSON.",
    sub_agents=[refinement_loop, synthesizer],
)

# --- Review agent: presents ticket to user, applies updates or exits the loop ---
ticket_reviewer = Agent(
    name="ticket_reviewer",
    model=GEMINI_MODEL,
    description="Presents the saved ticket to the user, applies any requested changes, and exits when the user is satisfied.",
    instruction=TICKET_REVIEWER_INSTRUCTIONS,
    tools=[display_ticket_markdown, update_ticket_json_tool, mark_review_complete],
    before_agent_callback=log_agent_start,
    after_tool_callback=log_tool_result,
)

# --- Loop agent: repeats the review cycle until the user is satisfied ---
ticket_review_loop = LoopAgent(
    name="ticket_review_loop",
    description="Loops the review agent until the user approves the ticket, allowing iterative refinements.",
    sub_agents=[ticket_reviewer],
)

# --- Root agent: drives the conversation and orchestrates the pipeline and review loop ---
root_agent = Agent(
    name="ticket_agent",
    model=GEMINI_MODEL,
    description="An agent that creates JIRA tickets through conversation, optionally reading requirements from a PDF.",
    instruction=ROOT_AGENT_INSTRUCTIONS,
    tools=[
        read_pdf_requirements,
        AgentTool(agent=ticket_creation_pipeline),
        save_ticket_json_tool,
        AgentTool(agent=ticket_review_loop),
    ],
    before_agent_callback=log_agent_start,
    after_tool_callback=log_tool_result,
)
