from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials
import os

SCOPES = ['https://www.googleapis.com/auth/calendar']

def create_events_from_plan(plan: dict):
    """
    Tạo các sự kiện từ JSON kế hoạch học và thêm vào Google Calendar người dùng.
    """
    if not plan.get("events"):
        raise ValueError("Không có sự kiện nào trong kế hoạch.")

    creds = None
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    if not creds or not creds.valid:
        flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
        creds = flow.run_local_server(port=0)
        with open("token.json", "w") as token:
            token.write(creds.to_json())

    service = build("calendar", "v3", credentials=creds)

    for event_data in plan["events"]:
        event = {
            "summary": event_data["title"],
            "description": event_data["description"],
            "start": {
                "dateTime": event_data["start"],
                "timeZone": "Asia/Ho_Chi_Minh",
            },
            "end": {
                "dateTime": event_data["end"],
                "timeZone": "Asia/Ho_Chi_Minh",
            }
        }

        created_event = service.events().insert(calendarId="primary", body=event).execute()
        print("📅 Tạo thành công:", created_event.get("htmlLink"))
