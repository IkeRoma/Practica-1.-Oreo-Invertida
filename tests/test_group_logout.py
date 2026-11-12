import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "server"))
from handlers import Handler


class FakeConnection:
    def __init__(self, token):
        self.auth_token = token
        self.sent = []
    def send(self, packet):
        self.sent.append(packet)


class FakeDatabase:
    def is_group_member(self, group_id, user_id):
        return user_id in (1, 2)
    def group_members(self, group_id):
        return [{"id": 1, "display_name": "Uno"}, {"id": 2, "display_name": "Dos"}]
    def group_name(self, group_id):
        return "Prueba"
    def user_by_id(self, user_id):
        return {"id": user_id, "display_name": f"Usuario {user_id}"}


class GroupLogoutTests(unittest.TestCase):
    def test_all_member_devices_are_invalidated_without_deleting_group(self):
        broadcasts = []
        handler = Handler(FakeDatabase(), broadcasts.append)
        first, second, third = FakeConnection("t1"), FakeConnection("t2"), FakeConnection("t3")
        handler.sessions = {"t1": 1, "t2": 2, "t3": 2}
        handler.online = {1: {first}, 2: {second, third}}

        handler.handle(first, {"action": "group_logout_all", "group_id": 9, "request_id": "r"})

        self.assertEqual(handler.sessions, {})
        self.assertEqual(handler.online, {})
        for connection in (first, second, third):
            self.assertTrue(any(p.get("event") == "force_logout" for p in connection.sent))
        self.assertEqual(first.sent[-1]["data"]["closed"], 3)


if __name__ == "__main__":
    unittest.main()
