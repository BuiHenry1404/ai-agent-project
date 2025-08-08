# api/main.py
from fastapi import FastAPI
from api.v1.chat import router as chat_router

app = FastAPI(
    title="AI Study Planner API",
    description="Chat with AI agents to generate and sync study plans",
    version="1.0.0"
)

app.include_router(chat_router, prefix="/api/v1", tags=["Chat"])
