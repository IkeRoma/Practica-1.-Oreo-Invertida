"""Lógica de negocio del servidor Wasap; independiente del motor SQL."""
import secrets
import hashlib
import re
from datetime import datetime, timezone
from auth import hash_password, verify_password

PASSWORD_PATTERN = re.compile(r"^(?=.*[A-Z])(?=.*[a-z])(?=.*\d)(?=.*[^A-Za-z0-9]).{10,}$")


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
                avatar_data = msg.get("avatar_data")
                if avatar_data is not None and len(str(avatar_data)) > 1_500_000:
                    raise ValueError("La fotografía supera el tamaño permitido (aprox. 1 MB).")
                if not (3 <= len(username) <= 32) or not username.replace("_", "").isalnum():
                    raise ValueError("El usuario debe tener 3–32 caracteres alfanuméricos o guion bajo.")
                if not PASSWORD_PATTERN.fullmatch(password):
                    raise ValueError("La contraseña debe tener 10 caracteres e incluir mayúscula, minúscula, número y símbolo.")
                if self.db.user_by_username(username):
                    raise ValueError("Ese nombre de usuario ya está registrado.")
                self.db.create_user(username, hash_password(password), display[:64], avatar, avatar_data)
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
                device_token = str(msg.get("device_token", "")).strip()
                if device_token:
                    self.db.remember_device(row["id"], hashlib.sha256(device_token.encode()).hexdigest(),
                                            str(msg.get("device_name", "Dispositivo"))[:100])
                self.online.setdefault(row["id"], set()).add(conn)
                self._reply(conn, rid, True, {"token": token, "user": {
                    "id": row["id"], "username": row["username"],
                    "display_name": row["display_name"], "avatar_path": row.get("avatar_path"),
                    "avatar_data": row.get("avatar_data")}})
                self.broadcast({"event": "presence", "user_id": row["id"], "online": True})
                return

            if action == "password_change":
                username = str(msg.get("username", "")).strip().lower()
                current = str(msg.get("current_password", ""))
                new_password = str(msg.get("new_password", ""))
                row = self.db.user_by_username(username)
                if not row or not verify_password(current, row["password_hash"]):
                    raise ValueError("Usuario o contraseña actual incorrectos.")
                if not PASSWORD_PATTERN.fullmatch(new_password):
                    raise ValueError("La nueva contraseña debe tener 10 caracteres e incluir mayúscula, minúscula, número y símbolo.")
                self.db.update_password(row["id"], hash_password(new_password))
                self.db.revoke_user_devices(row["id"])
                self._reply(conn, rid, True, {"message": "Contraseña actualizada. Inicia sesión nuevamente."})
                return

            if action == "device_resume":
                device_token = str(msg.get("device_token", "")).strip()
                if not device_token:
                    raise ValueError("No hay un dispositivo recordado.")
                token_hash = hashlib.sha256(device_token.encode()).hexdigest()
                row = self.db.user_by_device_token(token_hash)
                if not row:
                    raise ValueError("La sesión guardada ya no es válida.")
                token = secrets.token_urlsafe(32)
                conn.auth_token = token
                self.sessions[token] = row["id"]
                self.online.setdefault(row["id"], set()).add(conn)
                self.db.touch_device(token_hash)
                self._reply(conn, rid, True, {"token": token, "user": {
                    "id": row["id"], "username": row["username"],
                    "display_name": row["display_name"], "avatar_path": row.get("avatar_path"),
                    "avatar_data": row.get("avatar_data")}})
                self.broadcast({"event": "presence", "user_id": row["id"], "online": True})
                return

            if action == "device_revoke":
                device_token = str(msg.get("device_token", "")).strip()
                if device_token:
                    self.db.revoke_device(hashlib.sha256(device_token.encode()).hexdigest())
                self._reply(conn, rid, True, {"revoked": True})
                return

            if action == "logout":
                token = getattr(conn, "auth_token", None)
                uid = self.sessions.pop(token, None) if token else None
                device_token = str(msg.get("device_token", "")).strip()
                if device_token:
                    self.db.revoke_device(hashlib.sha256(device_token.encode()).hexdigest())
                if uid is not None:
                    connections = self.online.get(uid, set())
                    connections.discard(conn)
                    if not connections:
                        self.online.pop(uid, None)
                        self.broadcast({"event": "presence", "user_id": uid, "online": False})
                conn.auth_token = None
                self._reply(conn, rid, True, {"logged_out": True})
                return

            user = self._user(conn)
            uid = user["id"]

            if action == "profile_update":
                display = str(msg.get("display_name", "")).strip()
                if not display or len(display) > 64:
                    raise ValueError("El nombre visible debe contener entre 1 y 64 caracteres.")
                avatar_data = msg.get("avatar_data")
                if avatar_data is not None and len(str(avatar_data)) > 1_500_000:
                    raise ValueError("La fotografía supera el tamaño permitido (aprox. 1 MB).")
                self.db.update_profile(uid, display, avatar_data)
                self._reply(conn, rid, True, {"display_name": display, "avatar_data": avatar_data})
                return

            if action == "users":
                data = self.db.users()
                for item in data:
                    item["online"] = bool(self.online.get(item["id"]))
                self._reply(conn, rid, True, data)

            elif action == "contact_info":
                contact_id = int(msg.get("user_id"))
                contact = self.db.user_by_id(contact_id)
                if not contact:
                    raise ValueError("No se encontró el contacto.")
                self._reply(conn, rid, True, {
                    "id": contact["id"], "username": contact["username"],
                    "display_name": contact["display_name"],
                    "avatar_path": contact.get("avatar_path"),
                    "online": bool(self.online.get(contact_id))})

            elif action == "general_send":
                body = self._body(msg)
                self.db.save_message(uid, "general", body)
                self.broadcast({"event": "message", "scope": "general", "sender": user["display_name"],
                                "username": user["username"], "sender_id": uid, "body": body,
                                "created_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")})
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
                           "sender_id": uid, "recipient_id": recipient, "body": body,
                           "created_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")}
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
                for member in self.db.group_members(gid):
                    self._send_user(member["id"], {"event": "group_member_added", "group_id": gid,
                        "user_id": added["id"], "username": added["username"],
                        "display_name": added.get("display_name", added["username"])})

            elif action == "group_members":
                gid = int(msg["group_id"])
                if not self.db.is_group_member(gid, uid):
                    raise ValueError("No perteneces a ese grupo.")
                members = self.db.group_members(gid)
                for member in members:
                    member["online"] = bool(self.online.get(member["id"]))
                self._reply(conn, rid, True, members)

            elif action == "group_logout_all":
                gid = int(msg["group_id"])
                if not self.db.is_group_member(gid, uid):
                    raise ValueError("No perteneces a ese grupo.")
                members = self.db.group_members(gid)
                # Primero invalida todos los tokens en una sola operación SQL. Si falla,
                # no comienza una desconexión parcial del grupo.
                member_ids = [member["id"] for member in members]
                self.db.revoke_devices_for_users(member_ids)
                self._reply(conn, rid, True, {"sessions_closing": len(members)})
                # Desconecta todas las conexiones activas de cada integrante.
                # No elimina usuarios, membresías ni historial.
                offline_ids = []
                for member in members:
                    member_id = member["id"]
                    connections = list(self.online.get(member_id, set()))
                    for active_conn in connections:
                        try:
                            active_conn.send({"event": "session_terminated",
                                "reason": f"La sesión se cerró por una acción en el grupo {gid}.",
                                "group_id": gid})
                        except Exception:
                            pass
                        active_token = getattr(active_conn, "auth_token", None)
                        if active_token:
                            self.sessions.pop(active_token, None)
                        active_conn.auth_token = None
                        try:
                            active_conn.close()
                        except Exception:
                            pass
                    self.online.pop(member_id, None)
                    if connections:
                        offline_ids.append(member_id)
                # Notifica presencia después de desconectar a todos los integrantes,
                # para que no intenten hacer peticiones durante el cierre grupal.
                for member_id in offline_ids:
                    self.broadcast({"event": "presence", "user_id": member_id, "online": False})
                return

            elif action == "group_send":
                gid = int(msg["group_id"])
                body = self._body(msg)
                if not self.db.is_group_member(gid, uid):
                    raise ValueError("No perteneces a ese grupo.")
                self.db.save_message(uid, "group", body, gid)
                payload = {"event": "message", "scope": "group", "target_id": gid,
                           "sender": user["display_name"], "sender_id": uid, "body": body,
                           "created_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")}
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
                           "sender": user["display_name"], "sender_id": uid, "body": body,
                           "created_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")}
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
