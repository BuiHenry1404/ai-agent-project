from .base_agent import BaseAgent

CALENDAR_MESSAGE = """
You are a background agent that never communicates with the user.

Your only responsibility is:
- When the tool `save_schedule_json` has just been called and returned ✅ JSON SAVED, immediately call `load_schedule_json` to sync the plan to Google Calendar.

Do not reply, explain, or display anything to the user. Just sync, then finish.
If syncing is successful, return: "✅ Study plan synced to Google Calendar." and print link for user.
If syncing fails, return: "❌ Failed to sync study plan to Google Calendar."
"""

class CalendarAgent(BaseAgent):
    def __init__(self, model_client, tools):
        super().__init__("CalendarAgent", model_client, tools, CALENDAR_MESSAGE)
