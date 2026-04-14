import logging
import os
from typing import Optional

from google.adk.agents.callback_context import CallbackContext
from google.adk.tools.base_tool import BaseTool
from google.adk.tools.tool_context import ToolContext
from google.genai import types

# --- Logging Setup ---

LOG_FILE = os.path.join(os.path.dirname(__file__), "ticket_agent.log")

_fmt = logging.Formatter(
    fmt="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

logger = logging.getLogger("ticket_agent")
logger.setLevel(logging.INFO)
logger.propagate = False  # don't double-log via root logger

if not logger.handlers:
    _fh = logging.FileHandler(LOG_FILE, encoding="utf-8")
    _fh.setFormatter(_fmt)
    logger.addHandler(_fh)

    _sh = logging.StreamHandler()
    _sh.setFormatter(_fmt)
    logger.addHandler(_sh)


# --- Agent Callbacks ---

def on_agent_start(callback_context: CallbackContext) -> Optional[types.Content]:
    """Log when an agent begins its turn."""
    logger.info("[agent_start] agent=%s", callback_context.agent_name)
    return None


def on_agent_end(callback_context: CallbackContext) -> Optional[types.Content]:
    """Log when an agent finishes its turn."""
    logger.info("[agent_end]   agent=%s", callback_context.agent_name)
    return None


# --- Tool Callbacks ---

def on_tool_start(
    tool: BaseTool,
    args: dict,
    tool_context: ToolContext,
) -> Optional[dict]:
    """Log a tool call before it executes."""
    safe_args = {k: v for k, v in args.items() if k != "tool_context"}
    logger.info("[tool_start]  tool=%s  args=%s", tool.name, safe_args)
    return None


def on_tool_end(
    tool: BaseTool,
    args: dict,
    tool_context: ToolContext,
    tool_response: dict,
) -> Optional[dict]:
    """Log a tool result after it executes."""
    if isinstance(tool_response, dict):
        status = tool_response.get("status", "unknown")
        # Log the full response only on error to keep logs concise
        if status == "error":
            logger.error(
                "[tool_end]    tool=%s  status=%s  response=%s",
                tool.name, status, tool_response,
            )
        else:
            logger.info("[tool_end]    tool=%s  status=%s", tool.name, status)
    else:
        logger.info("[tool_end]    tool=%s  response=%s", tool.name, tool_response)
    return None