# api/v1/chat.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional

from agents.planner_agent import PlannerAgent
from agents.calendar_agent import CalendarAgent
from agents.user_proxy import UserAgent
from services.schedule_service import save_schedule_json, load_schedule_json
from services.chat_service import TeamBuilder
from integrations.llm.openai_client import ModelClientProvider

router = APIRouter()

# In-memory session storage (for dev, replace with Redis/DB in prod)
session_store = {}

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    session_id: str
    message: str
    history: Optional[List[ChatMessage]] = []

class ChatResponse(BaseModel):
    response: str
    history: List[ChatMessage]

@router.post("/chat", response_model=ChatResponse)
async def chat(payload: ChatRequest):
    try:
        session_id = payload.session_id
        user_input = payload.message
        history = payload.history or []

        # Get or create session agents
        model_client = ModelClientProvider.get()
        planner = PlannerAgent(model_client, tools=[save_schedule_json])
        calendar = CalendarAgent(model_client, tools=[load_schedule_json])
        user = UserAgent()

        team = TeamBuilder(user, planner, calendar, model_client).get()

        # Restore history
        for msg in history:
            team.append_message({"role": msg.role, "content": msg.content})

        # Chat step
        result = await team.step(input=user_input)
        updated_history = team.chat_messages

        # Store updated session
        session_store[session_id] = updated_history

        return ChatResponse(
            response=result.get("content", ""),
            history=updated_history
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
