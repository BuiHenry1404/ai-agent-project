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
# from autogen_agentchat.tools import tools

# Model client
from autogen_ext.models.openai import OpenAIChatCompletionClient

# Google Calendar sync function
from google_calendar import create_events_from_plan  # bạn cần định nghĩa hàm này

# Load environment
load_dotenv()

# === MODEL CLIENT ===
model_client = OpenAIChatCompletionClient(
    model="gemini-2.5-flash",
    api_key=os.getenv("GEMINI_API_KEY")
)

# === TOOL 1: Extract JSON from content ===
def extract_json_from_response(content: str) -> dict:
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
def parse_and_sync_schedule(text: str) -> str:
    json_data = extract_json_from_response(text)
    return sync_to_google_calendar(json_data)

# === AGENT 1: Gợi ý kế hoạch học tập ===
planner_agent = AssistantAgent(
    name="PlannerAgent",
    model_client=model_client,
    system_message=
            "Bạn là một AI chuyên lên kế hoạch học tập.\n"
            "Hãy trò chuyện với người dùng để hiểu mục tiêu học của họ.\n"
            "Sau đó gợi ý một lịch học hợp lý, mỗi ngày một buổi học.\n"
            "Nếu bạn muốn tạo JSON kế hoạch học thì hãy dùng định dạng sau và dừng phản hồi:\n\n"
            "<json>\n"
            "{\n  \"events\": [\n    {\n      \"title\": \"Học HTML\",\n"
            "      \"description\": \"Buổi học đầu tiên\",\n"
            "      \"start\": \"2025-07-25T19:00:00+07:00\",\n"
            "      \"end\": \"2025-07-25T20:30:00+07:00\"\n    }\n  ]\n}\n</json>\n\n"
        
    )


# === AGENT 2: Xử lý JSON và đồng bộ calendar ===
calendar_agent = AssistantAgent(
    name="CalendarAgent",
    model_client=model_client,
    tools=[parse_and_sync_schedule],
    system_message=
            "Bạn là một agent nền, không giao tiếp với người dùng.\n"
            "Nhiệm vụ của bạn là phát hiện JSON chứa kế hoạch học và gọi tool `parse_and_sync_schedule` để đồng bộ lên Google Calendar.\n"
            "Không trả lời hay hiển thị gì. Chỉ xử lý rồi kết thúc."
        )

# === USER AGENT ===
user_proxy = UserProxyAgent(name="User", input_func=input)

# === SELECTOR GROUP CHAT ===
team = SelectorGroupChat(
    participants=[user_proxy, planner_agent, calendar_agent],
    model_client=model_client,
  selector_prompt = """
Bạn là bộ chọn tác nhân phù hợp cho mỗi vòng đối thoại.

Quy tắc:
1. Nếu tin nhắn người dùng hoặc assistant chứa đoạn <json>...</json> hoặc ```json ... ``` → chọn CalendarAgent.
2. Nếu không có JSON → chọn PlannerAgent để tiếp tục trò chuyện.
3. Nếu không rõ → chọn User để hỏi thêm.

Chỉ chọn **một** agent phản hồi mỗi lượt.
""",
    termination_condition=TextMentionTermination("KẾT THÚC")
)

# === MAIN ===
async def main():
    print("🎓 AI Lập Lịch Học đã sẵn sàng. Gõ 'KẾT THÚC' để thoát.\n")
    await Console(team.run_stream(task="Chào bạn! Bạn có thể giúp gì tôi ?"))
    print(team.chat_history.messages[-1])

if __name__ == "__main__":
    asyncio.run(main())
