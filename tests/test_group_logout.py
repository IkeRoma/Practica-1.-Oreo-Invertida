"""Pruebas unitarias sin SQL Server para la desconexión global de un grupo."""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "server"))
from handlers import Handler


class FakeDB:
    def __init__(self, members):
        self.members = members
        self.revoked = []
    def user_by_id(self, uid):
        return {"id": uid, "username": f"user{uid}", "display_name": f"User {uid}"}
    def is_group_member(self, gid, uid):
        return gid == 7 and any(m["id"] == uid for m in self.members)
    def group_members(self, gid):
        return list(self.members)
    def revoke_user_devices(self, uid):
        self.revoked.append(uid)
    def revoke_devices_for_users(self, uids):
        self.revoked.extend(uids)


class FakeConnection:
    def __init__(self, token):
        self.auth_token = token
        self.sent = []
        self.closed = False
    def send(self, packet):
        self.sent.append(packet)
    def close(self):
        self.closed = True


class GroupLogoutTests(unittest.TestCase):
    def test_closes_every_member_session_and_keeps_group_data(self):
        db = FakeDB([{"id": 1}, {"id": 2}])
        handler = Handler(db, lambda packet: None)
        first = FakeConnection("token-1")
        first_other_device = FakeConnection("token-1b")
        second = FakeConnection("token-2")
        handler.sessions.update({"token-1": 1, "token-1b": 1, "token-2": 2})
        handler.online = {1: {first, first_other_device}, 2: {second}}
        handler.handle(first, {"action": "group_logout_all", "request_id": "r1", "group_id": 7})
        self.assertTrue(first.closed)
        self.assertTrue(first_other_device.closed)
        self.assertTrue(second.closed)
        self.assertEqual(db.revoked, [1, 2])
        self.assertNotIn("token-1", handler.sessions)
        self.assertNotIn("token-1b", handler.sessions)
        self.assertNotIn("token-2", handler.sessions)
        self.assertEqual(handler.online, {})
        self.assertTrue(any(p.get("event") == "session_terminated" for p in first.sent))
        self.assertTrue(any(p.get("event") == "session_terminated" for p in first_other_device.sent))
        self.assertTrue(any(p.get("event") == "session_terminated" for p in second.sent))
        self.assertTrue(any(p.get("request_id") == "r1" and p.get("ok") for p in first.sent))

    def test_non_member_cannot_close_group_sessions(self):
        db = FakeDB([{"id": 2}])
        handler = Handler(db, lambda packet: None)
        conn = FakeConnection("token-1")
        handler.sessions["token-1"] = 1
        handler.online[1] = {conn}
        handler.handle(conn, {"action": "group_logout_all", "request_id": "r2", "group_id": 7})
        self.assertFalse(conn.closed)
        self.assertEqual(db.revoked, [])
        self.assertEqual(conn.sent[-1].get("ok"), False)


if __name__ == "__main__":
    unittest.main(verbosity=2)
