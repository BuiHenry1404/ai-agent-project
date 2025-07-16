import unittest
from datetime import datetime, timedelta
from google_calendar import create_events_from_plan


class TestGoogleCalendarSync(unittest.TestCase):
    def test_add_event(self):
        # Tạo dữ liệu mô phỏng kế hoạch học tập
        plan = {
            "events": [
                {
                    "title": "Test học Python",
                    "description": "Học các kiến thức cơ bản về Python",
                    "start": "2025-07-21T19:00:00+07:00",
                    "end": "2025-07-21T21:00:00+07:00",
                }
            ]
        }

        try:
            create_events_from_plan(plan)
            print("✅ Đã thêm sự kiện test vào Google Calendar.")
        except Exception as e:
            self.fail(f"❌ Lỗi khi thêm sự kiện: {str(e)}")


if __name__ == "__main__":
    unittest.main()
