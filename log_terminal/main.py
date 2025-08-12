import asyncio
import os
import json
from dotenv import load_dotenv

# AutoGen
from autogen_agentchat.agents import AssistantAgent, UserProxyAgent
from autogen_agentchat.teams import SelectorGroupChat
from autogen_agentchat.conditions import TextMentionTermination
# from autogen_agentchat.ui import Console

# Model client
from autogen_ext.models.openai import OpenAIChatCompletionClient

# Google Calendar sync function
from google_calendar import create_events_from_plan

from file_stream_console import FileStreamConsole

# Load environment variables
load_dotenv()

# === MODEL CLIENT ===
model_client = OpenAIChatCompletionClient(
    model="gemini-2.5-flash",
    api_key=os.getenv("GEMINI_API_KEY"),
)

# === TOOL 1: Save study schedule as JSON ===
async def save_schedule_json(json_data: dict) -> str:
    """Save the study schedule as JSON for Google Calendar."""
    valid_events = []
    for item in json_data.get("events", []):
        try:
            event = {
                "summary": item["summary"],
                "start": {
                    "dateTime": item["start"],
                    "timeZone": item.get("timeZone", "Asia/Ho_Chi_Minh")
                },
                "end": {
                    "dateTime": item["end"],
                    "timeZone": item.get("timeZone", "Asia/Ho_Chi_Minh")
                },
                "description": item.get("description", "")
            }
            valid_events.append(event)
        except KeyError as e:
            print(f"❌ Missing required field: {e} in {item}")
    
    if not valid_events:
        return "❌ No valid events to save."
    
    with open("plan.json", "w", encoding="utf-8") as f:
        json.dump({"events": valid_events}, f, indent=2, ensure_ascii=False)
    
    return "✅ JSON SAVED"

# === TOOL 2: Load JSON and sync to Google Calendar ===
async def load_schedule_json() -> str:
    """Read the JSON file and sync it to Google Calendar."""
    if not os.path.exists("plan.json"):
        raise FileNotFoundError("❌ plan.json file not found.")
    with open("plan.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    create_events_from_plan(data)
    return "✅ Study plan synced to Google Calendar."

# === AGENT 1: PlannerAgent ===
planner_agent = AssistantAgent(
    name="PlannerAgent",
    model_client=model_client,
    tools=[save_schedule_json],
    system_message="""
You are an AI specialized in creating study plans.

1. Ask the user about their learning goals, subjects, and available time.
2. Then, generate a study schedule and present it in natural language (DO NOT show JSON).
3. If the user agrees → immediately call the `save_schedule_json` tool with JSON format like:

{
  "events": [
    {
      "summary": "Learn Math",
      "start": "2025-07-25T08:00:00",
      "end": "2025-07-25T09:30:00",
      "timeZone": "Asia/Ho_Chi_Minh",
      "description": "Review integrals"
    },
    ...
  ]
}

After calling `save_schedule_json`, do NOT say anything further and DO NOT print the json format for user. Wait for the CalendarAgent to handle syncing.
"""
)

# === AGENT 2: CalendarAgent ===
calendar_agent = AssistantAgent(
    name="CalendarAgent",
    model_client=model_client,
    tools=[load_schedule_json],
    system_message="""
You are a background agent that never communicates with the user.

Your only responsibility is:
- When the tool `save_schedule_json` has just been called and returned ✅ JSON SAVED, immediately call `load_schedule_json` to sync the plan to Google Calendar.

Do not reply, explain, or display anything to the user. Just sync, then finish.
If syncing is successful, return: "✅ Study plan synced to Google Calendar." and print link to the calendar.
If syncing fails, return: "❌ Failed to sync study plan to Google Calendar."
"""
)

# === USER AGENT ===
user_proxy = UserProxyAgent(name="User", input_func=input)

# === SELECTOR GROUP CHAT ===
team = SelectorGroupChat(
    participants=[user_proxy, planner_agent, calendar_agent],
    model_client=model_client,
    selector_prompt="""
Select the most appropriate agent to respond next.

Roles:
- PlannerAgent: Chats with the user, creates a study plan, and calls `save_schedule_json` when ready.
- CalendarAgent: If `save_schedule_json` was successfully called → calls `load_schedule_json` to sync to Google Calendar.
- User: Provides input, requests, or confirms changes to the plan.

Current conversation context:
{history}

Rules to select the next agent from {participants}:
1. If the User is requesting or editing a study plan → select PlannerAgent
2. If PlannerAgent has not yet called `save_schedule_json` → keep PlannerAgent
3. If PlannerAgent just called the tool, or `"✅ JSON SAVED"` is in the history → select CalendarAgent
4. If CalendarAgent just finished syncing → select User
5. If unsure → select User

Respond with only one name from: {participants}
""",
    termination_condition=TextMentionTermination("EXIT")
)

# === MAIN ===
async def main():
    print("🎓 AI Study Planner is ready. Type 'EXIT' to quit.\n")
    file_stream = FileStreamConsole("chat_log.txt")
    
    result = await file_stream.process_stream(
        team.run_stream(task="Hello! Can you help me schedule my study sessions?"),
        output_stats=True
    )

if __name__ == "__main__":
    asyncio.run(main())