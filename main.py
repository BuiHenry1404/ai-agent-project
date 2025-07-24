import asyncio
import os
import json
import re
from dotenv import load_dotenv

# AutoGen
from autogen_agentchat.agents import AssistantAgent, UserProxyAgent
from autogen_core.models import SystemMessage
from autogen_agentchat.teams import SelectorGroupChat
from autogen_agentchat.conditions import TextMentionTermination
from autogen_agentchat.ui import Console

# Model client
from autogen_ext.models.openai import OpenAIChatCompletionClient

# Google Calendar sync function
from google_calendar import create_events_from_plan

# Load environment
load_dotenv()

# === MODEL CLIENT ===
model_client = OpenAIChatCompletionClient(
    model="gemini-2.5-flash",
    api_key=os.getenv("GEMINI_API_KEY"),
)

# === TOOL 1: Extract JSON from content ===
def extract_json_from_response(content: str) -> dict:
    try:
        content = json.loads(content)
    except json.JSONDecodeError:
        pass

    match = re.search(r"<json>(.*?)</json>", content, re.DOTALL) or \
            re.search(r"```json(.*?)```", content, re.DOTALL)
    if not match:
        raise ValueError("❌ Không tìm thấy JSON trong phản hồi.")
    return json.loads(match.group(1).strip())

# === TOOL 2: Sync JSON to Google Calendar ===
def sync_to_google_calendar(json_data: dict) -> str:
    create_events_from_plan(json_data)
    return "✅ Lịch học đã được đồng bộ lên Google Calendar."

# === TOOL 3: Parser tool - parse and sync in one go ===
def parse_and_sync_schedule(text_or_json: str | dict) -> str:
    if isinstance(text_or_json, dict):
        json_data = text_or_json  # Đã là JSON thì không cần parse
    else:
        json_data = extract_json_from_response(text_or_json)
    return sync_to_google_calendar(json_data)

# === AGENT 1: Gợi ý kế hoạch học tập ===
planner_agent = AssistantAgent(
    name="PlannerAgent",
    model_client=model_client,
    system_message="""You are an AI specialized in creating study plans.  
Have a conversation with the user to understand their learning goals.  
Then suggest a suitable study schedule, with one study session per day.  
If you want to create a study plan in JSON format, use the structure below and stop your response:

<json>
{
  "events": [
    {
      "title": "Learn HTML",
      "description": "First study session",
      "start": "2025-07-25T19:00:00+07:00",
      "end": "2025-07-25T20:30:00+07:00"
    }
  ]
}
</json>

not print json for user. just print by text.


"""


)

# === AGENT 2: Đồng bộ JSON lên lịch ===
calendar_agent = AssistantAgent(
    name="CalendarAgent",
    model_client=model_client,
    tools=[parse_and_sync_schedule],
    system_message="""You are a backend agent and do not communicate with the user.  
Your task is to detect JSON containing the study plan and call the `parse_and_sync_schedule` tool to sync it to Google Calendar.  
Do not reply or display anything. Just process and terminate."""
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
- PlannerAgent: Explores user's study goals, suggests a suitable learning plan
- CalendarAgent: Detects and processes study schedule JSON and syncs to calendar
- User: Represents the human user

Conversation history:
{history}

Selection rules:
1. If the user just shared new study info or confirmed schedule → select PlannerAgent
2. If a message (from user or PlannerAgent) contains a JSON block (e.g. <json>...</json> or ```json ... ```) → select CalendarAgent
3. After CalendarAgent finishes syncing, or if unsure → select User

Only select one agent per turn.
""",
    termination_condition=TextMentionTermination("KẾT THÚC")
)

# === MAIN ===
async def main():
    print("🎓 AI Study Planner is ready. Type 'KẾT THÚC' to exit.\n")
    await Console(team.run_stream(task="Hello! Can you help me?"))

if __name__ == "__main__":
    asyncio.run(main())
