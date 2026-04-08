"""
HITL tools for a simple weather agent.
"""

import json
from google.adk.tools import ToolContext


def get_weather(city: str) -> dict:
    """Return a mock current weather report for the given city.

    Args:
        city: Name of the city to look up.
    """
    mock_data = {
        "london":   {"temp_c": 12, "condition": "Cloudy",  "humidity": 78},
        "new york": {"temp_c": 22, "condition": "Sunny",   "humidity": 55},
        "tokyo":    {"temp_c": 18, "condition": "Rainy",   "humidity": 85},
    }
    data = mock_data.get(city.lower(), {"temp_c": 20, "condition": "Clear", "humidity": 60})
    return {"status": "success", "city": city, **data}


SAFE_CITIES = {"london", "new york", "tokyo"}

def _needs_confirmation(city: str, **_) -> bool:
    """Confirm if the requested city is not in our pre-approved list."""
    return city.lower() not in SAFE_CITIES


async def set_weather_alert(city: str, threshold_c: int, tool_context: ToolContext) -> dict:
    """Set a temperature alert for a city, requiring structured human approval.

    Args:
        city:        City name for the alert.
        threshold_c: Temperature (°C) that triggers the alert.
    """
    tool_confirmation = tool_context.tool_confirmation

    if not tool_confirmation:
        await tool_context.request_confirmation(
            hint=(
                f"Please approve or reject the weather alert for {city} "
                f"(triggers above {threshold_c}°C). "
                "Set 'approved' to true/false and optionally adjust "
                "'final_threshold_c'."
            ),
            payload={
                "approved": False,
                "final_threshold_c": threshold_c,
            },
        )
        return {
            "status": "pending",
            "message": f"Awaiting approval to set alert for {city} at {threshold_c}°C.",
        }

    # payload may come back as a JSON string — parse defensively
    payload = tool_confirmation.payload
    if isinstance(payload, str):
        payload = json.loads(payload)

    approved: bool = payload.get("approved", False)
    final_threshold: int = payload.get("final_threshold_c", threshold_c)

    if approved:
        return {
            "status": "success",
            "message": f"Alert set for {city}: will trigger above {final_threshold}°C.",
        }

    return {
        "status": "rejected",
        "message": f"Alert for {city} was not approved.",
    }