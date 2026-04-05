from typing import Optional
from google.adk.agents.callback_context import CallbackContext
from google.adk.tools.base_tool import BaseTool
from google.adk.tools.tool_context import ToolContext
from google.genai import types


def log_agent_start(callback_context: CallbackContext) -> Optional[types.Content]:
    """Log when an agent starts running."""
    print(f"[agent:{callback_context.agent_name}] Starting")
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
    print(f"[tool:{tool.name}] status={status}")
    return None  # Return None to leave tool_response unchanged
