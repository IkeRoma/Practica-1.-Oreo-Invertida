"""Lógica de negocio del servidor Wasap; independiente del motor SQL."""
import secrets
import hashlib

from auth import hash_password, verify_password



class Handler:
    def __init__(self, db, broadcast):
        self.db = db
        self.broadcast = broadcast
        self.sessions = {}  # token -> user_id
        self.online = {}    # user_id -> set(ClientConnection)

    def disconnect(self, conn):
        token = getattr(conn, "auth_token", None)
        uid = self.sessions.pop(token, None) if token else None
        if uid is None:
            return
        connections = self.online.get(uid, set())
        connections.discard(conn)
        if not connections:
            self.online.pop(uid, None)
            self.broadcast({"event": "presence", "user_id": uid, "online": False})

    def _user(self, conn):
        token = getattr(conn, "auth_token", None)
        uid = self.sessions.get(token)
        if not uid:
            raise ValueError("Debes iniciar sesión.")
        user = self.db.user_by_id(uid)
        if not user:
            raise ValueError("La cuenta ya no existe.")
        return user

    def handle(self, conn, msg):
        action = msg.get("action")
        rid = msg.get("request_id")
        try:
            if action == "register":
                username = str(msg.get("username", "")).strip().lower()
                password = str(msg.get("password", ""))
                display = str(msg.get("display_name", "")).strip() or username
                avatar = str(msg.get("avatar_path", "")).strip() or None
                if not (3 <= len(username) <= 32) or not username.replace("_", "").isalnum():
                    raise ValueError("El usuario debe tener 3–32 caracteres alfanuméricos o guion bajo.")
                if len(password) < 8:
                    raise ValueError("La contraseña debe tener al menos 8 caracteres.")
                if self.db.user_by_username(username):
                    raise ValueError("Ese nombre de usuario ya está registrado.")
                self.db.create_user(username, hash_password(password), display[:64], avatar)
                self._reply(conn, rid, True, {"message": "Cuenta creada. Ya puedes iniciar sesión."})
                return

            if action == "login":
                username = str(msg.get("username", "")).strip().lower()
                row = self.db.user_by_username(username)
                if not row or not verify_password(str(msg.get("password", "")), row["password_hash"]):
                    raise ValueError("Usuario o contraseña incorrectos.")
                token = secrets.token_urlsafe(32)
                conn.auth_token = token
                self.sessions[token] = row["id"]
                self.online.setdefault(row["id"], set()).add(conn)
                self._reply(conn, rid, True, {"token": token, "user": {
                    "id": row["id"], "username": row["username"],
                    "display_name": row["display_name"], "avatar_path": row["avatar_path"]}})
                self.broadcast({"event": "presence", "user_id": row["id"], "online": True})
                return

            if action == "logout":
                token = getattr(conn, "auth_token", None)
                logout_uid = self.sessions.pop(token, None) if token else None
                conn.auth_token = None
                if logout_uid is not None:
                    connections = self.online.get(logout_uid, set())
                    connections.discard(conn)
                    if not connections:
                        self.online.pop(logout_uid, None)
                        self.broadcast({"event": "presence", "user_id": logout_uid, "online": False})
                self._reply(conn, rid, True, {"logged_out": True})
                return

            user = self._user(conn)
            uid = user["id"]

            if action == "users":
                data = self.db.users()
                for item in data:
                    item["online"] = bool(self.online.get(item["id"]))
                self._reply(conn, rid, True, data)

            elif action == "general_send":
                body = self._body(msg)
                self.db.save_message(uid, "general", body)
                self.broadcast({"event": "message", "scope": "general", "sender": user["display_name"],
                                "username": user["username"], "sender_id": uid, "body": body})
                self._reply(conn, rid, True, {"sent": True})

            elif action == "history":
                scope = str(msg.get("scope", "general"))
                target = int(msg["target_id"]) if msg.get("target_id") is not None else None
                if scope == "direct":
                    if target is None or not self.db.user_by_id(target):
                        raise ValueError("Usuario no encontrado.")
                    rows = self.db.history("direct", target, uid)
                elif scope == "group":
                    if target is None or not self.db.is_group_member(target, uid):
                        raise ValueError("No perteneces a ese grupo.")
                    rows = self.db.history("group", target)
                elif scope == "channel":
                    if target is None or not self.db.is_channel_member(target, uid):
                        raise ValueError("Primero debes unirte al canal.")
                    rows = self.db.history("channel", target)
                elif scope == "general":
                    rows = self.db.history("general")
                else:
                    raise ValueError("Tipo de historial no válido.")
                self._reply(conn, rid, True, rows)

            elif action == "direct_send":
                recipient = int(msg["recipient_id"])
                body = self._body(msg)
                if recipient == uid:
                    raise ValueError("No puedes enviarte mensajes directos a ti mismo.")
                if not self.db.user_by_id(recipient):
                    raise ValueError("Usuario no encontrado.")
                self.db.save_message(uid, "direct", body, None, recipient)
                payload = {"event": "message", "scope": "direct", "sender": user["display_name"],
                           "sender_id": uid, "recipient_id": recipient, "body": body}
                self._send_user(uid, payload)
                self._send_user(recipient, payload)
                self._reply(conn, rid, True, {"sent": True})

            elif action == "groups":
                self._reply(conn, rid, True, self.db.groups_for(uid))

            elif action == "group_create":
                name = str(msg.get("name", "")).strip()
                if not name:
                    raise ValueError("Escribe un nombre para el grupo.")
                gid = self.db.create_group(name[:80], uid)
                self._reply(conn, rid, True, {"id": gid, "name": name[:80]})

            elif action == "group_add":
                gid = int(msg["group_id"])
                if not self.db.is_group_member(gid, uid):
                    raise ValueError("No perteneces a ese grupo.")
                added = self.db.add_group_member(gid, str(msg.get("username", "")).strip().lower())
                self._reply(conn, rid, True, {"username": added["username"]})

            elif action == "contact_info":
                contact_id = int(msg["user_id"])
                contact = self.db.user_by_id(contact_id)
                if not contact:
                    raise ValueError("Contacto no encontrado.")
                self._reply(conn, rid, True, contact)

            elif action == "group_logout_all":
                gid = int(msg["group_id"])
                if not self.db.is_group_member(gid, uid):
                    raise ValueError("No perteneces a ese grupo.")
                members = self.db.group_members(gid)
                group_name = self.db.group_name(gid)
                closed_connections = 0
                for member in members:
                    member_id = member["id"]
                    connections = list(self.online.get(member_id, set()))
                    closed_connections += len(connections)
                    for member_conn in connections:
                        token = getattr(member_conn, "auth_token", None)
                        if token:
                            self.sessions.pop(token, None)
                            member_conn.auth_token = None
                        try:
                            member_conn.send({
                                "event": "force_logout",
                                "reason": f"Tu sesión se cerró porque se ejecutó la acción de cierre grupal en «{group_name}»."
                            })
                        except Exception:
                            pass
                    self.online.pop(member_id, None)
                    if connections:
                        self.broadcast({"event": "presence", "user_id": member_id, "online": False})
                self._reply(conn, rid, True, {"closed": closed_connections})

            elif action == "group_send":
                gid = int(msg["group_id"])
                body = self._body(msg)
                if not self.db.is_group_member(gid, uid):
                    raise ValueError("No perteneces a ese grupo.")
                self.db.save_message(uid, "group", body, gid)
                payload = {"event": "message", "scope": "group", "target_id": gid,
                           "sender": user["display_name"], "sender_id": uid, "body": body}
                for member in self.db.group_members(gid):
                    self._send_user(member["id"], payload)
                self._reply(conn, rid, True, {"sent": True})

            elif action == "channels":
                self._reply(conn, rid, True, self.db.channels())

            elif action == "channel_create":
                name = str(msg.get("name", "")).strip()
                if not name:
                    raise ValueError("Escribe un nombre para el canal.")
                cid = self.db.create_channel(name[:80], uid)
                self._reply(conn, rid, True, {"id": cid, "name": name[:80]})

            elif action == "channel_join":
                cid = int(msg["channel_id"])
                if not any(channel["id"] == cid for channel in self.db.channels()):
                    raise ValueError("Canal inexistente.")
                self.db.join_channel(cid, uid)
                self._reply(conn, rid, True, {"joined": True})

            elif action == "channel_send":
                cid = int(msg["channel_id"])
                body = self._body(msg)
                channels = {channel["id"]: channel for channel in self.db.channels()}
                if cid not in channels:
                    raise ValueError("Canal inexistente.")
                if channels[cid]["owner_id"] != uid:
                    raise ValueError("Solo el propietario puede publicar en este canal.")
                if not self.db.is_channel_member(cid, uid):
                    self.db.join_channel(cid, uid)
                self.db.save_message(uid, "channel", body, cid)
                payload = {"event": "message", "scope": "channel", "target_id": cid,
                           "sender": user["display_name"], "sender_id": uid, "body": body}
                for member in self.db.channel_members(cid):
                    self._send_user(member["user_id"], payload)
                self._reply(conn, rid, True, {"sent": True})

            else:
                raise ValueError("Acción desconocida.")
        except Exception as exc:
            self._reply(conn, rid, False, error=self._friendly_error(exc))

    @staticmethod
    def _friendly_error(exc):
        # Evita mostrar al cliente trazas/conexiones/credenciales del motor de datos.
        message = str(exc)
        if "2601" in message or "2627" in message:
            return "Ya existe un registro con ese nombre o identificador."
        if "08S01" in message or "08001" in message or "HYT00" in message:
            return "No se pudo comunicar con la base de datos. Inténtalo más tarde."
        return message or "Ocurrió un error al procesar la solicitud."

    @staticmethod
    def _body(msg):
        body = str(msg.get("body", "")).strip()
        if not body:
            raise ValueError("El mensaje está vacío.")
        if len(body) > 4000:
            raise ValueError("El mensaje supera 4000 caracteres.")
        return body

    @staticmethod
    def _reply(conn, rid, ok, data=None, error=None):
        packet = {"request_id": rid, "ok": ok}
        if data is not None:
            packet["data"] = data
        if error:
            packet["error"] = error
        conn.send(packet)

    def _send_user(self, uid, payload):
        for connection in list(self.online.get(uid, set())):
            try:
                connection.send(payload)
            except Exception:
                pass
