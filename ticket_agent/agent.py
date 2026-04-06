from google.adk.agents import Agent
from google.adk.tools.agent_tool import AgentTool
from dotenv import load_dotenv

from .prompt import (
    ROOT_AGENT_INSTRUCTIONS,
    DESCRIPTION_REFINER_INSTRUCTIONS,
    CLASSIFIER_INSTRUCTIONS,
    SYNTHESIZER_INSTRUCTIONS,
)
from .tools import read_pdf_requirements, save_ticket_json, update_ticket_json
from .callbacks import log_agent_start, log_tool_result

load_dotenv()

import os
GEMINI_MODEL = os.getenv("GOOGLE_GENAI_MODEL")

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

# --- Sub-agent 3: Compiles all info, validates against TicketInfo schema, and saves JSON ---
synthesizer = Agent(
    name="synthesizer",
    model=GEMINI_MODEL,
    description="Compiles all refined ticket information, validates it against the TicketInfo schema, and saves it as a JSON file.",
    instruction=SYNTHESIZER_INSTRUCTIONS,
    tools=[save_ticket_json, update_ticket_json],
    before_agent_callback=log_agent_start,
    after_tool_callback=log_tool_result,
)

# --- Root agent: Drives the conversation and orchestrates sub-agents as explicit tool calls ---
root_agent = Agent(
    name="ticket_agent",
    model=GEMINI_MODEL,
    description="An agent that creates JIRA tickets through conversation, optionally reading requirements from a PDF.",
    instruction=ROOT_AGENT_INSTRUCTIONS,
    tools=[
        read_pdf_requirements,
        AgentTool(agent=description_refiner),
        AgentTool(agent=ticket_classifier),
        AgentTool(agent=synthesizer),
    ],
    before_agent_callback=log_agent_start,
    after_tool_callback=log_tool_result,
)
