import logging
import os
from typing import Optional
from google.adk.agents.callback_context import CallbackContext
from google.adk.tools.base_tool import BaseTool
from google.adk.tools.tool_context import ToolContext
from google.genai import types

_LOG_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "ticket_agent.log")
_FORMATTER = logging.Formatter("%(asctime)s %(levelname)s %(message)s")

logger = logging.getLogger("ticket_agent")
logger.setLevel(logging.INFO)
logger.propagate = False  # don't let ADK's root logger interfere

if not logger.handlers:
    _file_handler = logging.FileHandler(_LOG_FILE)
    _file_handler.setFormatter(_FORMATTER)
    logger.addHandler(_file_handler)

    _stream_handler = logging.StreamHandler()
    _stream_handler.setFormatter(_FORMATTER)
    logger.addHandler(_stream_handler)


def log_agent_start(callback_context: CallbackContext) -> Optional[types.Content]:
    """Log when an agent starts running."""
    logger.info(f"[agent:{callback_context.agent_name}] Starting")
    return None


def log_tool_result(
    tool: BaseTool,
    args: dict,
    tool_context: ToolContext,
    tool_response: dict,
) -> Optional[dict]:
    """Log the status of a tool call after it completes."""
    if isinstance(tool_response, dict):
        status = tool_response.get("status", "unknown")
    else:
        status = "unknown"
    logger.info(f"[tool:{tool.name}] status={status}")
    return None  # Return None to leave tool_response unchanged
