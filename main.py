import asyncio
from integrations.llm.openai_client import ModelClientProvider
from agents.planner_agent import PlannerAgent
from agents.calendar_agent import CalendarAgent
from agents.user_proxy import UserAgent
from services.schedule_service import save_schedule_json, load_schedule_json
from services.chat_service import TeamBuilder

async def main():
    model_client = ModelClientProvider.get()
    planner = PlannerAgent(model_client, tools=[save_schedule_json])
    calendar = CalendarAgent(model_client, tools=[load_schedule_json])
    user = UserAgent()

    team = TeamBuilder(user, planner, calendar, model_client).get()

    print("🎓 AI Study Planner is ready. Type 'EXIT' to quit.\n")
    result = await team.run_stream(task="Hello! Can you help me schedule my study sessions?")

if __name__ == "__main__":
    asyncio.run(main())
