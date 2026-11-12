"""Acceso a datos para Microsoft SQL Server 2019/2022 mediante pyodbc."""
from __future__ import annotations

import pyodbc


class Database:
    def __init__(self, config: dict):
        self.host = config["DB_HOST"]
        self.port = int(config.get("DB_PORT", 1433))
        self.name = config["DB_NAME"]
        self.user = config["DB_USER"]
        self.password = config["DB_PASSWORD"]
        self.driver = config.get("DB_DRIVER", "ODBC Driver 18 for SQL Server")
        self.encrypt = self._as_bool(config.get("DB_ENCRYPT", "yes"))
        self.trust_cert = self._as_bool(config.get("DB_TRUST_SERVER_CERTIFICATE", "yes"))
        self.timeout = int(config.get("DB_CONNECTION_TIMEOUT", 8))
        self._connection_string = (
            f"DRIVER={{{self.driver}}};"
            f"SERVER=tcp:{self.host},{self.port};"
            f"DATABASE={self.name};UID={self.user};PWD={self.password};"
            f"Encrypt={'yes' if self.encrypt else 'no'};"
            f"TrustServerCertificate={'yes' if self.trust_cert else 'no'};"
            f"Connection Timeout={self.timeout};"
        )

    @staticmethod
    def _as_bool(value):
        return str(value).strip().lower() in {"1", "true", "yes", "si", "sí", "on"}

    def connect(self):
        return pyodbc.connect(self._connection_string, autocommit=False, timeout=self.timeout)

    @staticmethod
    def _dict_row(cursor, row):
        if row is None:
            return None
        columns = [column[0] for column in cursor.description]
        return dict(zip(columns, row))

    def run(self, sql, params=(), fetch="none"):
        """Ejecuta SQL con marcadores ?; fetch: none, one, all, lastrowid."""
        conn = self.connect()
        try:
            cursor = conn.cursor()
            cursor.execute(sql, tuple(params))
            if fetch == "one":
                result = self._dict_row(cursor, cursor.fetchone())
            elif fetch == "all":
                result = [self._dict_row(cursor, row) for row in cursor.fetchall()]
            elif fetch == "lastrowid":
                row = cursor.fetchone()
                result = int(row[0]) if row else None
            else:
                result = None
            conn.commit()
            cursor.close()
            return result
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def user_by_username(self, username):
        return self.run(
            "SELECT id, username, password_hash, display_name, avatar_path, avatar_data "
            "FROM dbo.users WHERE username = ?", (username,), "one")

    def user_by_id(self, user_id):
        return self.run(
            "SELECT id, username, display_name, avatar_path, avatar_data FROM dbo.users WHERE id = ?",
            (user_id,), "one")

    def create_user(self, username, password_hash, display_name, avatar_path=None, avatar_data=None):
        return self.run(
            "INSERT INTO dbo.users(username,password_hash,display_name,avatar_path,avatar_data) "
            "OUTPUT INSERTED.id VALUES(?,?,?,?,?)",
            (username, password_hash, display_name, avatar_path, avatar_data), "lastrowid")

    def users(self):
        return self.run(
            "SELECT id, username, display_name, avatar_path FROM dbo.users ORDER BY username",
            fetch="all")

    def save_message(self, sender, scope, body, target_id=None, recipient_id=None):
        return self.run(
            "INSERT INTO dbo.messages(sender_id,scope,target_id,recipient_id,body) "
            "OUTPUT INSERTED.id VALUES(?,?,?,?,?)",
            (sender, scope, target_id, recipient_id, body), "lastrowid")

    def history(self, scope, target_id=None, user_id=None, limit=100):
        limit = max(1, min(int(limit), 500))
        if scope == "direct":
            sql = """SELECT TOP (?) m.id,m.body,m.scope,m.created_at,
                            u.username,u.display_name
                     FROM dbo.messages AS m
                     INNER JOIN dbo.users AS u ON u.id=m.sender_id
                     WHERE m.scope='direct' AND
                       ((m.sender_id=? AND m.recipient_id=?) OR
                        (m.sender_id=? AND m.recipient_id=?))
                     ORDER BY m.id DESC"""
            rows = self.run(sql, (limit, user_id, target_id, target_id, user_id), "all")
        else:
            if target_id is None:
                target_filter = "m.target_id IS NULL"
                params = (limit, scope)
            else:
                target_filter = "m.target_id = ?"
                params = (limit, scope, target_id)
            sql = f"""SELECT TOP (?) m.id,m.body,m.scope,m.created_at,
                             u.username,u.display_name
                      FROM dbo.messages AS m
                      INNER JOIN dbo.users AS u ON u.id=m.sender_id
                      WHERE m.scope=? AND {target_filter}
                      ORDER BY m.id DESC"""
            rows = self.run(sql, params, "all")
        return list(reversed(rows or []))

    def create_group(self, name, owner_id):
        conn = self.connect()
        try:
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO dbo.groups_chat(name,owner_id) OUTPUT INSERTED.id VALUES(?,?)",
                (name, owner_id))
            gid = int(cur.fetchone()[0])
            cur.execute("INSERT INTO dbo.group_members(group_id,user_id) VALUES(?,?)", (gid, owner_id))
            conn.commit()
            return gid
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def groups_for(self, user_id):
        return self.run("""SELECT g.id,g.name,g.owner_id FROM dbo.groups_chat AS g
                           INNER JOIN dbo.group_members AS gm ON gm.group_id=g.id
                           WHERE gm.user_id=? ORDER BY g.name""", (user_id,), "all")

    def add_group_member(self, group_id, username):
        user = self.user_by_username(username)
        if not user:
            raise ValueError("No existe ese usuario.")
        self.run("""IF NOT EXISTS (SELECT 1 FROM dbo.group_members WHERE group_id=? AND user_id=?)
                    INSERT INTO dbo.group_members(group_id,user_id) VALUES(?,?)""",
                 (group_id, user["id"], group_id, user["id"]))
        return user

    def is_group_member(self, group_id, user_id):
        return bool(self.run(
            "SELECT 1 AS ok FROM dbo.group_members WHERE group_id=? AND user_id=?",
            (group_id, user_id), "one"))

    def group_members(self, group_id):
        return self.run("""SELECT u.id,u.username,u.display_name FROM dbo.users AS u
                           INNER JOIN dbo.group_members AS gm ON gm.user_id=u.id
                           WHERE gm.group_id=?""", (group_id,), "all")

    def create_channel(self, name, owner_id):
        conn = self.connect()
        try:
            cur = conn.cursor()
            cur.execute("INSERT INTO dbo.channels(name,owner_id) OUTPUT INSERTED.id VALUES(?,?)",
                        (name, owner_id))
            cid = int(cur.fetchone()[0])
            cur.execute("INSERT INTO dbo.channel_members(channel_id,user_id) VALUES(?,?)",
                        (cid, owner_id))
            conn.commit()
            return cid
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def channels(self):
        return self.run("""SELECT c.id,c.name,c.owner_id,u.username AS owner_username
                           FROM dbo.channels AS c
                           INNER JOIN dbo.users AS u ON u.id=c.owner_id
                           ORDER BY c.name""", fetch="all")

    def join_channel(self, channel_id, user_id):
        self.run("""IF NOT EXISTS (SELECT 1 FROM dbo.channel_members WHERE channel_id=? AND user_id=?)
                    INSERT INTO dbo.channel_members(channel_id,user_id) VALUES(?,?)""",
                 (channel_id, user_id, channel_id, user_id))

    def is_channel_member(self, channel_id, user_id):
        return bool(self.run(
            "SELECT 1 AS ok FROM dbo.channel_members WHERE channel_id=? AND user_id=?",
            (channel_id, user_id), "one"))

    def channel_members(self, channel_id):
        return self.run("SELECT user_id FROM dbo.channel_members WHERE channel_id=?",
                        (channel_id,), "all")


    def update_profile(self, user_id, display_name, avatar_data=None):
        if avatar_data is None:
            self.run("UPDATE dbo.users SET display_name=? WHERE id=?",
                     (display_name, user_id))
        else:
            self.run("UPDATE dbo.users SET display_name=?, avatar_data=? WHERE id=?",
                     (display_name, avatar_data, user_id))

    def update_password(self, user_id, password_hash):
        self.run("UPDATE dbo.users SET password_hash=? WHERE id=?",
                 (password_hash, user_id))

    def remember_device(self, user_id, token_hash, device_name):
        self.run("""IF EXISTS (SELECT 1 FROM dbo.remembered_devices WHERE token_hash=?)
                    UPDATE dbo.remembered_devices
                    SET user_id=?, device_name=?, last_used_at=SYSUTCDATETIME()
                    WHERE token_hash=?
                    ELSE
                    INSERT INTO dbo.remembered_devices(user_id,token_hash,device_name)
                    VALUES(?,?,?)""",
                 (token_hash,user_id,device_name,token_hash,user_id,token_hash,device_name))

    def user_by_device_token(self, token_hash):
        return self.run("""SELECT u.id,u.username,u.display_name,u.avatar_path,u.avatar_data
                           FROM dbo.remembered_devices d
                           INNER JOIN dbo.users u ON u.id=d.user_id
                           WHERE d.token_hash=?""", (token_hash,), "one")

    def touch_device(self, token_hash):
        self.run("UPDATE dbo.remembered_devices SET last_used_at=SYSUTCDATETIME() WHERE token_hash=?",
                 (token_hash,))

    def revoke_device(self, token_hash):
        self.run("DELETE FROM dbo.remembered_devices WHERE token_hash=?", (token_hash,))

    def revoke_user_devices(self, user_id):
        self.run("DELETE FROM dbo.remembered_devices WHERE user_id=?", (user_id,))
