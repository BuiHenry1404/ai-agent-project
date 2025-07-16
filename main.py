import asyncio
import os
import json
import re
from typing import Dict, Any
from dotenv import load_dotenv

# AutoGen agent chat
from autogen_agentchat.agents import AssistantAgent, UserProxyAgent
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_agentchat.conditions import TextMentionTermination
from autogen_agentchat.ui import Console

# OpenAI-compatible model client via OpenRouter
from autogen_ext.models.openai import OpenAIChatCompletionClient
from autogen_core.models import SystemMessage, UserMessage
import logging  # Hàm tạo sự kiện Google Calendar (bạn cần có file google_calendar.py)
from google_calendar import create_events_from_plan

# Load biến môi trường từ .env
load_dotenv()


# logging.basicConfig(level=logging.INFO)


# Khởi tạo model Gemini qua OpenRouter
model_client = OpenAIChatCompletionClient(
    model="gemini-1.5-flash",
    api_key=os.getenv("GEMINI_API_KEY")  # Biến môi trường GEMINI_API_KEY trong .env
)

# ----------------------------------------------------
# Hàm async gọi model và xử lý kết quả JSON
async def generate_study_plan_async(prompt: str) -> str:
    messages = [
        SystemMessage(
            content="Bạn là trợ lý AI giúp lập lịch học cá nhân. "
                    "Chỉ trả về JSON đúng format được đặt giữa <json>...</json>. "
                    "Không thêm bất kỳ lời giải thích nào bên ngoài JSON."
        ),
        UserMessage(
            content=f"""Tạo kế hoạch học tập cho yêu cầu sau: \"{prompt}\"
Kết quả phải nằm trong thẻ <json>...</json>. Format như sau:

<json>
{{
  "events": [
    {{
      "title": "Tên buổi học",
      "description": "Chi tiết nội dung",
      "start": "YYYY-MM-DDTHH:MM:SS+07:00",
      "end": "YYYY-MM-DDTHH:MM:SS+07:00"
    }}
  ]
}}
</json>
""",
            source="user"
        )
    ]

    try:
        response = await model_client.create(messages=messages)
        print("📦 DEBUG response:", response)
        content = response.content
        match = re.search(r"<json>(.*?)</json>", content, re.DOTALL)
        if match:
            json_str = match.group(1).strip()
            return json_str
        else:
            return "Không tìm thấy JSON hợp lệ"
    except Exception as e:
        return f"Lỗi khi gọi mô hình: {str(e)}"

# Hàm sync dùng cho tool (do autogen chỉ nhận sync function)
def generate_study_plan(prompt: str) -> str:
    return asyncio.run(generate_study_plan_async(prompt))

# ----------------------------------------------------
# Hàm thêm lịch học vào Google Calendar
def sync_plan_to_google_calendar(plan: Dict[str, Any]) -> str:
    try:
        create_events_from_plan(plan)
        return "✅ Đã thêm lịch học vào Google Calendar."
    except Exception as e:
        return f"❌ Lỗi khi thêm vào Google Calendar: {str(e)}"

# ----------------------------------------------------
# Khởi tạo AssistantAgent (AI)
study_agent = AssistantAgent(
    name="StudyAgent",
    model_client=model_client,
    tools=[generate_study_plan, sync_plan_to_google_calendar],
    system_message="""
Bạn là một trợ lý AI chuyên lập lịch học, sử dụng công cụ để tạo và đồng bộ lịch học.

QUY TẮC:
    - Khi người dùng nói họ muốn lập kế hoạch học tập, bạn **bắt buộc phải gọi hàm generate_study_plan(prompt)** với nội dung yêu cầu của họ.
    - KHÔNG tự tạo văn bản thủ công.
    - Nếu kế hoạch được tạo hợp lệ (trả về JSON), hãy gọi sync_plan_to_google_calendar(plan).
    - Chỉ trình bày kết quả sau khi gọi hàm.
    - Kết thúc khi người dùng gõ "KẾT THÚC".

CẤU TRÚC LỊCH:
Mỗi sự kiện cần có:
    - title
    - description
    - start (ISO 8601 format, ví dụ: 2025-07-20T19:00:00+07:00)
    - end (ISO 8601 format)

Không bao giờ tự soạn kế hoạch. Hãy luôn sử dụng công cụ.
"""
)

# Tạo agent user nhập tay
user_proxy = UserProxyAgent("user_proxy", input_func=input)

# Tổ chức hội thoại vòng tròn giữa 2 agent
team = RoundRobinGroupChat(
    participants=[study_agent, user_proxy],
    termination_condition=TextMentionTermination("KẾT THÚC")
)

# ----------------------------------------------------
# Main
async def main():
    print("🎓 AI Study Scheduler đã sẵn sàng. Gõ 'KẾT THÚC' để thoát.\n")
    task = "Chào bạn! Bạn muốn học gì? Trong thời gian nào?"
    await Console(team.run_stream(task=task))

if __name__ == "__main__":
    asyncio.run(main())
