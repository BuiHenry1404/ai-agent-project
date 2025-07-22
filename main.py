import asyncio
import os
import json
import re
import logging
from dotenv import load_dotenv
from typing import Dict

from autogen_agentchat.agents import AssistantAgent, UserProxyAgent
from autogen_ext.models.openai import OpenAIChatCompletionClient
from autogen_core.models import SystemMessage, UserMessage
from autogen_agentchat.teams import SelectorGroupChat, RoundRobinGroupChat
from autogen_agentchat.conditions import TextMentionTermination
from autogen_agentchat.ui import Console
from google_calendar import create_events_from_plan

load_dotenv()

# === [Tùy chọn] Bật log khi debug ===
# logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

model_client = OpenAIChatCompletionClient(
    model="gemini-2.5-flash",
    api_key=os.getenv("GEMINI_API_KEY")
)

# === TOOL: Trích xuất và tạo JSON ===
def extract_json_from_response(content: str) -> dict:
    match = re.search(r"<json>(.*?)</json>", content, re.DOTALL) or \
            re.search(r"```json(.*?)```", content, re.DOTALL)
    if not match:
        raise ValueError("❌ Không tìm thấy JSON trong phản hồi.")
    try:
        data = json.loads(match.group(1).strip())
        with open("study_plan.json", "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return data
    except json.JSONDecodeError as e:
        raise ValueError(f"❌ JSON không hợp lệ: {e}")

async def generate_json_async(prompt: str) -> dict:
    messages = [
        SystemMessage(content="Bạn là trợ lý AI, chỉ trả về JSON trong thẻ <json>."),
        UserMessage(content=f"""Dựa trên yêu cầu: \"{prompt}\". Trả về JSON định dạng: <json>{{"events":[{{"title":"...","description":"...","start":"YYYY-MM-DDTHH:MM:SS+07:00","end":"..."}}]}}</json>""")
    ]
    response = await model_client.create(messages=messages)
    return extract_json_from_response(response.content)

def generate_study_plan_json(prompt: str) -> str:
    return json.dumps(asyncio.run(generate_json_async(prompt)))

def sync_plan_to_google_calendar(plan_json: str) -> str:
    try:
        plan_data = json.loads(plan_json)
        create_events_from_plan(plan_data)
        return "✅ Lịch học đã được thêm vào Google Calendar."
    except Exception as e:
        return f"❌ Lỗi khi đồng bộ: {e}"

study_planner_agent = AssistantAgent(
    name="StudyPlannerAgent",
    model_client=model_client,
    tools=[generate_study_plan_json],
    system_message=(
    "Bạn là trợ lý AI lập kế hoạch học tập. Bạn **chỉ phản hồi nếu người dùng đã cung cấp đầy đủ thông tin học tập**.\n"
    "- Nếu thông tin còn thiếu, hãy nhắc người dùng điền rõ.\n"
    "- Nếu đã đầy đủ, thì tóm tắt lại, rồi hỏi: 'Bạn có muốn tạo kế hoạch học không?'\n"
    "- Sau đó gọi tool nếu được đồng ý."
)
)

calendar_agent = AssistantAgent(
    name="CalendarAgent",
    model_client=model_client,
    tools=[sync_plan_to_google_calendar],
    system_message="""Bạn là trợ lý Google Calendar.
1. Chỉ hoạt động khi có JSON kế hoạch học.
2. Hỏi: "Bạn có muốn thêm vào Google Calendar không? (có/không)"
3. Nếu có, gọi `sync_plan_to_google_calendar`.
4. Thông báo kết quả và kết thúc.
"""
)

study_consultant_agent = AssistantAgent(
    name="StudyConsultant",
    model_client=model_client,
    system_message=(
    "Bạn là tư vấn viên học tập, nhiệm vụ duy nhất là **thu thập thông tin đầu vào từ người dùng**:\n"
    "- Hỏi người dùng: mục tiêu học là gì? học lúc nào? thời lượng mỗi ngày?\n"
    "- Tóm tắt lại bằng giọng thân thiện\n"
    "- Sau đó nói: 'Mình hiểu rồi, để mình chuyển thông tin cho StudyPlannerAgent nhé!' và dừng lại.\n"
    "**Không tạo kế hoạch, không gọi tool, không hỏi thêm sau đó.**"
    )
)

user_proxy = UserProxyAgent("user_proxy", input_func=input)

team = SelectorGroupChat(
    participants=[user_proxy, study_planner_agent, calendar_agent, study_consultant_agent],
    model_client=model_client,
    selector_prompt=(
    "1. Nếu người dùng chỉ chào hỏi hoặc chưa cung cấp thông tin rõ ràng => chọn StudyConsultant\n"
    "2. Nếu người dùng đã đưa mục tiêu và thời gian học => chọn StudyPlannerAgent\n"
    "3. Nếu nội dung liên quan đến Google Calendar hoặc JSON => chọn CalendarAgent"
    ),
    termination_condition=TextMentionTermination("KẾT THÚC")
)

async def main():
    print("🎓 AI Study Planner đã sẵn sàng. Gõ 'KẾT THÚC' để thoát.\n")
    await Console(team.run_stream(task="Chào bản! Bạn muốn học gì? Trong thời gian nào?"))
if __name__ == "__main__":
    asyncio.run(main())
