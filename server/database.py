import mysql.connector
from mysql.connector import pooling

class Database:
    def __init__(self, config):
        self.pool = pooling.MySQLConnectionPool(
            pool_name="wasap_pool", pool_size=10, pool_reset_session=True,
            host=config["DB_HOST"], port=int(config.get("DB_PORT", 1433)),
            user=config["DB_USER"], password=config["DB_PASSWORD"],
            database=config["DB_NAME"], autocommit=False,
            connection_timeout=8
        )

    def run(self, sql, params=(), fetch="none"):
        conn = self.pool.get_connection()
        try:
            cur = conn.cursor(dictionary=True)
            cur.execute(sql, params)
            if fetch == "one":
                result = cur.fetchone()
            elif fetch == "all":
                result = cur.fetchall()
            elif fetch == "lastrowid":
                result = cur.lastrowid
            else:
                result = None
            conn.commit()
            cur.close()
            return result
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def user_by_username(self, username):
        return self.run("SELECT * FROM users WHERE username=%s", (username,), "one")

    def user_by_id(self, user_id):
        return self.run("SELECT id, username, display_name, avatar_path FROM users WHERE id=%s",
                        (user_id,), "one")

    def create_user(self, username, password_hash, display_name, avatar_path=None):
        return self.run(
            "INSERT INTO users(username,password_hash,display_name,avatar_path) VALUES(%s,%s,%s,%s)",
            (username, password_hash, display_name, avatar_path), "lastrowid")

    def users(self):
        return self.run("SELECT id, username, display_name, avatar_path FROM users ORDER BY username", fetch="all")

    def save_message(self, sender, scope, body, target_id=None, recipient_id=None):
        return self.run(
            "INSERT INTO messages(sender_id,scope,target_id,recipient_id,body) VALUES(%s,%s,%s,%s,%s)",
            (sender, scope, target_id, recipient_id, body), "lastrowid")

    def history(self, scope, target_id=None, user_id=None, limit=100):
        if scope == "direct":
            sql = """SELECT m.id,m.body,m.scope,m.created_at,u.username,u.display_name
                     FROM messages m JOIN users u ON u.id=m.sender_id
                     WHERE m.scope='direct' AND
                     ((m.sender_id=%s AND m.recipient_id=%s) OR
                      (m.sender_id=%s AND m.recipient_id=%s))
                     ORDER BY m.id DESC LIMIT %s"""
            rows = self.run(sql, (user_id,target_id,target_id,user_id,limit), "all")
        else:
            sql = """SELECT m.id,m.body,m.scope,m.created_at,u.username,u.display_name
                     FROM messages m JOIN users u ON u.id=m.sender_id
                     WHERE m.scope=%s AND (m.target_id <=> %s)
                     ORDER BY m.id DESC LIMIT %s"""
            rows = self.run(sql, (scope,target_id,limit), "all")
        return list(reversed(rows or []))

    def create_group(self, name, owner_id):
        gid = self.run("INSERT INTO groups_chat(name,owner_id) VALUES(%s,%s)", (name,owner_id), "lastrowid")
        self.run("INSERT INTO group_members(group_id,user_id) VALUES(%s,%s)", (gid,owner_id))
        return gid

    def groups_for(self, user_id):
        return self.run("""SELECT g.id,g.name,g.owner_id FROM groups_chat g
                           JOIN group_members gm ON gm.group_id=g.id
                           WHERE gm.user_id=%s ORDER BY g.name""", (user_id,), "all")

    def add_group_member(self, group_id, username):
        user = self.user_by_username(username)
        if not user:
            raise ValueError("No existe ese usuario.")
        self.run("INSERT IGNORE INTO group_members(group_id,user_id) VALUES(%s,%s)",
                 (group_id,user["id"]))
        return user

    def is_group_member(self, group_id, user_id):
        return bool(self.run("SELECT 1 AS ok FROM group_members WHERE group_id=%s AND user_id=%s",
                             (group_id,user_id),"one"))

    def group_members(self, group_id):
        return self.run("""SELECT u.id,u.username,u.display_name FROM users u
                           JOIN group_members gm ON gm.user_id=u.id WHERE gm.group_id=%s""",
                        (group_id,), "all")

    def create_channel(self, name, owner_id):
        cid = self.run("INSERT INTO channels(name,owner_id) VALUES(%s,%s)", (name,owner_id), "lastrowid")
        self.run("INSERT INTO channel_members(channel_id,user_id) VALUES(%s,%s)", (cid,owner_id))
        return cid

    def channels(self):
        return self.run("""SELECT c.id,c.name,c.owner_id,u.username AS owner_username
                           FROM channels c JOIN users u ON u.id=c.owner_id ORDER BY c.name""", fetch="all")

    def join_channel(self, channel_id, user_id):
        self.run("INSERT IGNORE INTO channel_members(channel_id,user_id) VALUES(%s,%s)",
                 (channel_id,user_id))

    def is_channel_member(self, channel_id, user_id):
        return bool(self.run("SELECT 1 AS ok FROM channel_members WHERE channel_id=%s AND user_id=%s",
                             (channel_id,user_id),"one"))

    def channel_members(self, channel_id):
        return self.run("SELECT user_id FROM channel_members WHERE channel_id=%s", (channel_id,), "all")
