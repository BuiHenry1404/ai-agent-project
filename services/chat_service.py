from autogen_agentchat.teams import SelectorGroupChat
from autogen_agentchat.conditions import TextMentionTermination

class TeamBuilder:
    def __init__(self, user_agent, planner_agent, calendar_agent, model_client):
        self.group = SelectorGroupChat(
            participants=[
                user_agent.get(),
                planner_agent.get(),
                calendar_agent.get(),
            ],
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
3. If PlannerAgent just called the tool, or "✅ JSON SAVED" is in the history → select CalendarAgent
4. If CalendarAgent just finished syncing → select User
5. If unsure → select User

Respond with only one name from: {participants}
""",
            termination_condition=TextMentionTermination("EXIT")
        )

    def get(self):
        return self.group
