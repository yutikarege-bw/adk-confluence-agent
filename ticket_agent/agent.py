"""
JIRA Ticket Creation Agent Pipeline
====================================
Root agent that composes:
  content_checker -> refinement_loop(reflective -> refiner -> hitl) -> ticket_creator

Run with:  adk web jira_ticket_agent
"""

import logging

from google.adk.agents import LoopAgent, SequentialAgent
from google.adk.agents.callback_context import CallbackContext

from .shared.state import ( STATE_ITERATION_COUNT, 
                            STATE_USER_SATISFIED, 
                            STATE_REFINED_TICKET, 
                            STATE_HITL_FEEDBACK, 
                            STATE_REFLECTIVE_QUESTIONS, 
                            STATE_VALIDATED_CONTENT)

# Import each sub-agent from its own package
from .content_checker import content_checker_agent
from .reflective_agent import reflective_agent
from .refiner_agent import refiner_agent
from .hitl_agent import hitl_agent
from .ticket_creator import ticket_creator_agent

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(name)s — %(message)s",
)
logger = logging.getLogger("jira_ticket_agent")


# ---------------------------------------------------------------------------
# Root-level callbacks
# ---------------------------------------------------------------------------

async def on_pipeline_start(callback_context: CallbackContext) -> None:
    """Initialise shared state before the pipeline runs."""
    logger.info("[Pipeline] Starting JIRA ticket creation pipeline")
    state = callback_context.state
    state[STATE_ITERATION_COUNT] = 0
    state[STATE_USER_SATISFIED] = False
    state[STATE_REFINED_TICKET] = ""        
    state[STATE_HITL_FEEDBACK] = ""         
    state[STATE_REFLECTIVE_QUESTIONS] = ""  
    state[STATE_VALIDATED_CONTENT] = ""     
    logger.info("[Pipeline] State initialised")


async def on_loop_iteration(callback_context: CallbackContext) -> None:
    """Increment the iteration counter at the start of each loop pass."""
    state = callback_context.state
    current = state.get(STATE_ITERATION_COUNT, 0)
    state[STATE_ITERATION_COUNT] = current + 1
    logger.info(f"[Loop] Starting iteration {state[STATE_ITERATION_COUNT]} / 3")


# ---------------------------------------------------------------------------
# Workflow agents
# ---------------------------------------------------------------------------

refinement_loop = LoopAgent(
    name="refinement_loop",
    description=(
        "Iteratively refines the ticket through reflection, refinement, "
        "and human-in-the-loop feedback (max 3 iterations)."
    ),
    sub_agents=[reflective_agent, refiner_agent, hitl_agent],
    max_iterations=3,
    before_agent_callback=on_loop_iteration,
)


# ---------------------------------------------------------------------------
# Root agent  (this is what ADK Web discovers)
# ---------------------------------------------------------------------------

root_agent = SequentialAgent(
    name="jira_ticket_pipeline",
    description=(
        "End-to-end pipeline: accepts content (PDF / text / Confluence), "
        "validates it, refines through a reflective loop with HITL input, "
        "and outputs a structured JIRA ticket."
    ),
    sub_agents=[
        content_checker_agent,
        refinement_loop,
        ticket_creator_agent,
    ],
    before_agent_callback=on_pipeline_start,
)