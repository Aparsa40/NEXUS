import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from nexus_core import (
    ActivityStore,
    classify_message,
    format_activity,
    parse_channel_ids,
)


class ChannelParsingTests(unittest.TestCase):
    def test_parse_ids_and_ignore_empty_values(self):
        self.assertEqual(parse_channel_ids("123, 456,,123"), {123, 456})

    def test_reject_non_numeric_id(self):
        with self.assertRaises(ValueError):
            parse_channel_ids("123,not-an-id")


class MessageClassificationTests(unittest.TestCase):
    def test_recognizes_persian_report_requests(self):
        self.assertEqual(classify_message("لطفاً گزارش وضعیت پروژه را تهیه کن"), "report")

    def test_recognizes_github_requests(self):
        self.assertEqual(classify_message("آخرین Commitها و Branchها را نشان بده"), "github")

    def test_recognizes_agent_coordination(self):
        self.assertEqual(classify_message("گزارش فعالیت ایجنت‌ها را بده"), "coordination")
        self.assertEqual(classify_message("DeepSeek چه کاری انجام داده؟"), "coordination")

    def test_recognizes_questions_and_ignores_chatter(self):
        self.assertEqual(classify_message("سلام، خوبی؟"), "chat")
        self.assertEqual(classify_message("سلام به همه"), "ignore")


class ActivityStoreTests(unittest.TestCase):
    def test_records_and_reads_activity_once(self):
        with tempfile.TemporaryDirectory() as directory:
            store = ActivityStore(str(Path(directory) / "activity.sqlite3"))
            timestamp = datetime(2026, 11, 3, 12, 0, tzinfo=timezone.utc)
            payload = {
                "message_id": 100,
                "channel_id": 200,
                "author_id": 300,
                "author_name": "DeepSeek",
                "is_bot": True,
                "content": "Finished reviewing the API module.",
                "created_at": timestamp,
            }
            store.record(**payload)
            store.record(**payload)

            events = store.recent()
            self.assertEqual(len(events), 1)
            self.assertEqual(events[0]["author_name"], "DeepSeek")
            self.assertEqual(events[0]["is_bot"], 1)
            summary = format_activity(events)
            self.assertIn("channel 200", summary)
            self.assertIn("DeepSeek", summary)

    def test_persists_scheduler_settings(self):
        with tempfile.TemporaryDirectory() as directory:
            store = ActivityStore(str(Path(directory) / "activity.sqlite3"))
            store.set_setting("last_report_date", "2026-11-03")
            self.assertEqual(store.get_setting("last_report_date"), "2026-11-03")


if __name__ == "__main__":
    unittest.main()
