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
import datetime
from autogen_ext.models.openai import OpenAIChatCompletionClient
from autogen_core.models import SystemMessage, UserMessage
import logging  # Import the logging module
from google_calendar import create_events_from_plan

# Load biến môi trường từ .env
load_dotenv()

# logging.basicConfig(level=logging.INFO)

# Khởi tạo model Gemini qua OpenRouter
model_client = OpenAIChatCompletionClient(
    model="gemini-2.5-flash",
    api_key=os.getenv("GEMINI_API_KEY")  # Biến môi trường GEMINI_API_KEY trong .env
)


def extract_json_from_response(content: str) -> dict:
    match = re.search(r"<json>(.*?)</json>", content, re.DOTALL)
    if not match:
        match = re.search(r"```json(.*?)```", content, re.DOTALL)
    if not match:
        logging.error("Không tìm thấy phần JSON trong nội dung.")
        raise ValueError("Không tìm thấy phần JSON trong nội dung.")

    json_str = match.group(1).strip()
    logging.debug("Extracted JSON string:\n%s", json_str)

    try:
        data = json.loads(json_str)
        with open("study_plan.json", "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return data
    except Exception as e:
        logging.error("Lỗi khi parse hoặc ghi file JSON: %s", e)
        raise


# ----------------------------------------------------
# Hàm async gọi model và xử lý kết quả JSON
async def generate_study_plan_async(prompt: str) -> Dict[str, Any]:
    messages = [
        SystemMessage(
            content="Bạn là trợ lý AI giúp lập lịch học cá nhân."
                    "Chỉ trả về JSON đúng format được đặt giữa <json>...</json>."
                    "Không thêm bất kỳ lời giải thích nào bên ngoài JSON."
        ),
        UserMessage(
            content=f"""Tạo kế hoạch học tập cho yêu cầu sau: \"{prompt}\"\nKết quả phải nằm trong thẻ <json>...</json>. Format như sau:\n\n<json>\n{{\n  \"events\": [\n    {{\n      \"title\": \"Tên buổi học\",\n      \"description\": \"Chi tiết nội dung\",\n      \"start\": \"YYYY-MM-DDTHH:MM:SS+07:00\",\n      \"end\": \"YYYY-MM-DDTHH:MM:SS+07:00\"\n    }}\n  ]\n}}\n</json>\n""",
            source="user"
        )
    ]

    try:
        response = await model_client.create(messages=messages)
        logging.info("📦 Đã nhận phản hồi từ model")
        content = response.content
        plan_dict = extract_json_from_response(content)
        return plan_dict
    except Exception as e:
        logging.error("Lỗi khi gọi mô hình: %s", e)
        return {"error": f"Lỗi khi gọi mô hình: {str(e)}"}


# Hàm sync dùng cho tool (do autogen chỉ nhận sync function)
def generate_study_plan(prompt: str) -> Dict[str, Any]:
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
    - Nếu kế hoạch được tạo hợp lệ (trả về JSON), hãy **gợi ý kế hoạch** cho người dùng dưới dạng văn bản gọn gàng (không phải JSON).
    - Hỏi người dùng xác nhận: "Bạn có muốn thêm kế hoạch này vào Google Calendar không? (có/không)"
    - Nếu người dùng xác nhận, hãy gọi sync_plan_to_google_calendar(plan).
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
