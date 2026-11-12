import os
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget,QMainWindow,QVBoxLayout,QHBoxLayout,QLabel,QLineEdit,QPushButton,
    QListWidget,QListWidgetItem,QTextEdit,QTextBrowser,QMessageBox,QInputDialog,QFileDialog,
    QStackedWidget,QFrame,QInputDialog,QDialog
)
from PySide6.QtCore import QThread, QTimer, Signal
from PySide6.QtGui import QPainter, QColor, QPen, QFont


STYLE = """
QWidget { background:#313338; color:#f2f3f5; font-family:Arial; font-size:13px; }
QMainWindow { background:#1e1f22; }
QLineEdit,QTextEdit,QTextBrowser { background:#1e1f22; border:1px solid #202225; border-radius:7px; padding:9px; selection-background-color:#5865f2; }
QPushButton { background:#5865f2; border:0; border-radius:6px; padding:9px 13px; color:white; font-weight:600; }
QPushButton:hover { background:#4752c4; }
QPushButton:disabled { background:#3f4147; color:#949ba4; }
QListWidget { background:#2b2d31; border:0; border-radius:7px; padding:5px; }
QListWidget::item { padding:10px; border-radius:5px; }
QListWidget::item:selected { background:#404249; }
QLabel#brand { font-size:25px; font-weight:900; color:#fff; }
QLabel#subtitle { color:#b5bac1; }
"""


class OreoSpinner(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent); self.angle=0; self.setFixedSize(92,92)
        self.timer=QTimer(self); self.timer.timeout.connect(self.rotate); self.timer.start(24)
    def rotate(self):
        self.angle=(self.angle+5)%360; self.update()
    def paintEvent(self,event):
        painter=QPainter(self); painter.setRenderHint(QPainter.Antialiasing)
        painter.translate(self.width()/2,self.height()/2); painter.rotate(self.angle)
        painter.setPen(Qt.NoPen); painter.setBrush(QColor("#171717")); painter.drawEllipse(-32,-32,64,64)
        painter.setBrush(QColor("#f2f3f5")); painter.drawEllipse(-25,-25,50,50)
        painter.setBrush(QColor("#171717")); painter.drawEllipse(-20,-20,40,40)
        painter.setPen(QPen(QColor("#f2f3f5"),2)); painter.setFont(QFont("Arial",8,QFont.Bold))
        painter.drawText(-17,4,"OREO")
        painter.setPen(Qt.NoPen); painter.setBrush(QColor("#f2f3f5"))
        for x,y in [(-12,-12),(10,-12),(-12,12),(10,12)]: painter.drawEllipse(x,y,3,3)

class LoadingDialog(QDialog):
    def __init__(self,text,parent=None):
        super().__init__(parent); self.setWindowTitle("Wasap"); self.setModal(False); self.setFixedSize(260,190)
        self.setStyleSheet("QDialog{background:#232428;border-radius:12px;} QLabel{color:#f2f3f5;}")
        layout=QVBoxLayout(self); layout.setAlignment(Qt.AlignCenter)
        layout.addWidget(OreoSpinner(self),0,Qt.AlignCenter)
        label=QLabel(text); label.setAlignment(Qt.AlignCenter); label.setStyleSheet("font-size:14px;font-weight:600;")
        layout.addWidget(label)

class RequestWorker(QThread):
    succeeded=Signal(dict); failed=Signal(str)
    def __init__(self,function): super().__init__(); self.function=function
    def run(self):
        try:
            result=self.function()
            self.succeeded.emit(result if isinstance(result,dict) else {"data":result})
        except Exception as exc:self.failed.emit(str(exc))

class LoginWidget(QWidget):
    authenticated=__import__("PySide6.QtCore",fromlist=["Signal"]).Signal(dict)
    def __init__(self, network):
        super().__init__(); self.network=network; self.avatar=""
        root=QVBoxLayout(self); root.setAlignment(Qt.AlignCenter)
        card=QFrame(); card.setFixedWidth(380); layout=QVBoxLayout(card)
        title=QLabel("WASAP"); title.setAlignment(Qt.AlignCenter); title.setStyleSheet("font-size:30px;font-weight:800;color:#fff;")
        subtitle=QLabel("Mensajería sencilla"); subtitle.setAlignment(Qt.AlignCenter)
        self.username=QLineEdit(); self.username.setPlaceholderText("Nombre de usuario")
        self.password=QLineEdit(); self.password.setPlaceholderText("Contraseña"); self.password.setEchoMode(QLineEdit.Password)
        self.display=QLineEdit(); self.display.setPlaceholderText("Nombre para mostrar (solo registro)")
        self.status=QLabel("")
        login=QPushButton("Iniciar sesión"); register=QPushButton("Crear cuenta")
        photo=QPushButton("Seleccionar foto de perfil (opcional)")
        login.clicked.connect(self.do_login); register.clicked.connect(self.do_register); photo.clicked.connect(self.pick_photo)
        for w in [title,subtitle,self.username,self.password,self.display,photo,login,register,self.status]: layout.addWidget(w)
        root.addWidget(card)

    def pick_photo(self):
        path,_=QFileDialog.getOpenFileName(self,"Foto de perfil","","Imágenes (*.png *.jpg *.jpeg *.webp)")
        if path: self.avatar=path; self.status.setText("Foto seleccionada.")


    def _start_request(self,action,**kwargs):
        for button in self.findChildren(QPushButton): button.setEnabled(False)
        self.loading=LoadingDialog("Conectando con Wasap…",self); self.loading.show()
        self.pending_action=action
        self.worker=RequestWorker(lambda:self.network.request(action,**kwargs))
        self.worker.succeeded.connect(self._request_succeeded); self.worker.failed.connect(self._request_failed)
        self.worker.start()

    def _request_succeeded(self,data):
        self.loading.close()
        for button in self.findChildren(QPushButton): button.setEnabled(True)
        if self.pending_action=="login": self.authenticated.emit(data)
        else: self.status.setText(data.get("message","Cuenta creada. Ya puedes iniciar sesión."))

    def _request_failed(self,error):
        self.loading.close()
        for button in self.findChildren(QPushButton): button.setEnabled(True)
        self.status.setText(error)

    def do_login(self):
        self._start_request("login",username=self.username.text(),password=self.password.text())

    def do_register(self):
        self._start_request("register",username=self.username.text(),password=self.password.text(),
            display_name=self.display.text(),avatar_path=self.avatar)

class ChatWindow(QMainWindow):
    logged_out = __import__("PySide6.QtCore",fromlist=["Signal"]).Signal(str)

    def __init__(self, network, user):
        super().__init__()
        from PySide6.QtWidgets import QTextBrowser
        from PySide6.QtGui import QTextCursor
        self.QTextCursor = QTextCursor
        from html import escape
        from datetime import datetime
        self.escape = escape
        self.datetime = datetime
        self.network, self.user = network, user
        self.scope, self.target_id, self.target_name = "general", None, "Chat general"
        self.last_sender = None
        self.setWindowTitle(f"Wasap — {user['display_name']}")
        self.resize(1250, 780)

        central=QWidget(); self.setCentralWidget(central)
        root=QHBoxLayout(central); root.setContentsMargins(12,12,12,12); root.setSpacing(12)

        side=QFrame(); side.setFixedWidth(310)
        side.setStyleSheet("QFrame{background:#2b2d31;border-radius:10px;}")
        sl=QVBoxLayout(side); sl.setContentsMargins(12,14,12,12)
        brand=QLabel("WASAP"); brand.setObjectName("brand"); brand.setAlignment(Qt.AlignHCenter)
        subtitle=QLabel("Mensajería sencilla"); subtitle.setObjectName("subtitle"); subtitle.setAlignment(Qt.AlignHCenter)
        sl.addWidget(brand); sl.addWidget(subtitle)
        self.nav=QListWidget()
        for label in ["#  Chat general","@  Mensajes directos","▣  Grupos","◉  Canales","●  Usuarios"]:
            self.nav.addItem(label)
        self.nav.currentRowChanged.connect(self.nav_changed)
        sl.addWidget(self.nav,1)
        self.list_title=QLabel("Conversaciones"); sl.addWidget(self.list_title)
        self.items=QListWidget(); self.items.itemClicked.connect(self.open_item); sl.addWidget(self.items,2)
        self.action=QPushButton("＋ Crear")
        self.action.clicked.connect(self.create_item); sl.addWidget(self.action)

        panel=QFrame(); panel.setStyleSheet("QFrame{background:#313338;border-radius:10px;}")
        rl=QVBoxLayout(panel); rl.setContentsMargins(16,14,16,14)
        top=QHBoxLayout()
        self.heading=QLabel("Chat general"); self.heading.setStyleSheet("font-size:20px;font-weight:750;")
        top.addWidget(self.heading,1)
        self.info_btn=QPushButton("ⓘ Información"); self.info_btn.clicked.connect(self.show_contact_info)
        self.add_btn=QPushButton("＋"); self.add_btn.setToolTip("Agregar integrante"); self.add_btn.clicked.connect(self.add_group_user)
        self.logout_group_btn=QPushButton("sálganse, quiero estar solo"); self.logout_group_btn.setStyleSheet("background:#da373c;")
        self.logout_group_btn.clicked.connect(self.logout_group)
        self.logout_btn=QPushButton("Cerrar sesión")
        self.logout_btn.setStyleSheet("background:#4e5058;")
        self.logout_btn.clicked.connect(self.logout)
        top.addWidget(self.info_btn); top.addWidget(self.add_btn); top.addWidget(self.logout_group_btn); top.addWidget(self.logout_btn)
        rl.addLayout(top)
        self.transcript=QTextBrowser(); self.transcript.setOpenLinks(False)
        self.transcript.anchorClicked.connect(self._message_link)
        self.transcript.setStyleSheet("QTextBrowser{padding:14px;}")
        rl.addWidget(self.transcript,1)
        sendrow=QHBoxLayout(); self.message=QLineEdit(); self.message.setPlaceholderText("Escribe un mensaje...")
        self.send=QPushButton("Enviar"); self.send.clicked.connect(self.send_message)
        self.message.returnPressed.connect(self.send_message)
        sendrow.addWidget(self.message,1); sendrow.addWidget(self.send)
        rl.addLayout(sendrow)
        root.addWidget(side); root.addWidget(panel,1)
        self.nav.setCurrentRow(0)
        self._update_actions()

    def notify(self,title,text):
        QMessageBox.information(self,title,text)

    def nav_changed(self,row):
        self.items.clear()
        self.list_title.setText(["Chat general","Mensajes directos","Grupos","Canales","Usuarios"][row] if row>=0 else "Conversaciones")
        self.action.setVisible(row in (2,3))
        if row==0:
            item=QListWidgetItem("#  Chat general"); item.setData(Qt.UserRole,{"scope":"general","id":None,"name":"Chat general","can_send":True})
            self.items.addItem(item); self.items.setCurrentItem(item); self.open_item(item)
        elif row==1:
            try:
                users=self.network.request("users")
                for u in users:
                    if u["id"]==self.user["id"]: continue
                    item=QListWidgetItem(f"@  {u['display_name']}  (@{u['username']})")
                    item.setData(Qt.UserRole,{"scope":"direct","id":u["id"],"name":u["display_name"],"can_send":True,"user":u})
                    self.items.addItem(item)
            except Exception as e:self.notify("Error",str(e))
        elif row==2:
            try:
                for g in self.network.request("groups"):
                    item=QListWidgetItem(f"▣  {g['name']}")
                    item.setData(Qt.UserRole,{"scope":"group","id":g["id"],"name":g["name"],"can_send":True})
                    self.items.addItem(item)
            except Exception as e:self.notify("Error",str(e))
        elif row==3:
            try:
                for c in self.network.request("channels"):
                    item=QListWidgetItem(f"#  {c['name']}")
                    item.setData(Qt.UserRole,{"scope":"channel","id":c["id"],"name":c["name"],"can_send":c["owner_id"]==self.user["id"],"channel":c})
                    self.items.addItem(item)
            except Exception as e:self.notify("Error",str(e))
        elif row==4:
            try:
                for u in self.network.request("users"):
                    item=QListWidgetItem(f"{u['display_name']}  (@{u['username']})")
                    item.setData(Qt.UserRole,{"scope":"contact","id":u["id"],"name":u["display_name"],"user":u})
                    self.items.addItem(item)
            except Exception as e:self.notify("Error",str(e))

    def open_item(self,item):
        data=item.data(Qt.UserRole)
        if not data:return
        if data["scope"]=="contact":
            self.show_contact_info(data["id"]); return
        if data["scope"]=="channel":
            try:self.network.request("channel_join",channel_id=data["id"])
            except Exception as e:self.notify("Error",str(e)); return
        self.scope,self.target_id,self.target_name=data["scope"],data["id"],data["name"]
        self.heading.setText(data["name"])
        self.message.setEnabled(data.get("can_send",True)); self.send.setEnabled(data.get("can_send",True))
        self.last_sender=None
        self.transcript.clear()
        self._update_actions()
        self.load_history()

    def _update_actions(self):
        is_group=self.scope=="group"
        self.add_btn.setVisible(is_group)
        self.logout_group_btn.setVisible(is_group)
        self.info_btn.setVisible(self.scope=="direct")

    def load_history(self):
        try:
            rows=self.network.request("history",scope=self.scope,target_id=self.target_id)
            self.transcript.clear(); self.last_sender=None
            for m in rows:
                sender=m.get("display_name") or m.get("username","")
                self.append_message(sender,m["body"],m.get("created_at",""),m.get("sender_id"))
        except Exception as e:self.transcript.append(f"<i>{self.escape(str(e))}</i>")

    def append_message(self,sender,body,when="",sender_id=None):
        body_html=self.escape(str(body)).replace("\n","<br>")
        sender_html=self.escape(str(sender))
        if hasattr(when,"strftime"): stamp=when.strftime("%H:%M")
        else:
            stamp=str(when or "")
            if " " in stamp: stamp=stamp.split(" ")[-1]
            stamp=stamp[:5] if len(stamp)>=5 else stamp
        stamp_html=self.escape(stamp)
        cursor=self.transcript.textCursor(); cursor.movePosition(self.QTextCursor.End)
        sender_key = sender_id if sender_id is not None else sender
        if sender_key==self.last_sender:
            cursor.insertHtml(f"<div style='margin:2px 0 3px 0;padding-left:12px'>{body_html} <span style='color:#8e9297;font-size:10px'>{stamp_html}</span></div>")
        else:
            link=f"<a href='user:{sender_id}' style='color:#f2f3f5;text-decoration:none;font-weight:700'>{sender_html}</a>" if sender_id else f"<b>{sender_html}</b>"
            cursor.insertHtml(f"<div style='margin-top:13px;margin-bottom:2px'>{link} <span style='color:#8e9297;font-size:10px'>{stamp_html}</span></div><div style='padding-left:12px;margin-bottom:3px'>{body_html}</div>")
        self.transcript.setTextCursor(cursor); self.transcript.ensureCursorVisible()
        self.last_sender=sender_key

    def _message_link(self,url):
        value=url.toString()
        if value.startswith("user:"):
            try:self.show_contact_info(int(value.split(":",1)[1]))
            except ValueError:pass

    def show_contact_info(self,user_id=None):
        if user_id is None:
            if self.scope!="direct":return
            user_id=self.target_id
        try:
            info=self.network.request("contact_info",user_id=user_id)
            QMessageBox.information(self,"Información del contacto",
                f"Nombre: {info['display_name']}\\nUsuario: @{info['username']}\\nID: {info['id']}")
        except Exception as e:self.notify("No se pudo consultar el contacto",str(e))

    def add_group_user(self):
        if self.scope!="group":return
        username,ok=QInputDialog.getText(self,"Agregar integrante","Nombre de usuario:")
        if ok and username.strip():
            try:
                result=self.network.request("group_add",group_id=self.target_id,username=username.strip())
                self.notify("Integrante agregado",f"Se agregó a @{result['username']}.")
            except Exception as e:self.notify("No se pudo agregar",str(e))

    def logout_group(self):
        if self.scope!="group":return
        answer=QMessageBox.warning(self,"Cerrar sesión del grupo",
            "Se cerrará la sesión de Wasap de TODOS los integrantes conectados a este grupo, en todos sus dispositivos. El grupo y sus mensajes se conservarán. ¿Deseas continuar?",
            QMessageBox.Yes|QMessageBox.No,QMessageBox.No)
        if answer!=QMessageBox.Yes:return
        try:
            result=self.network.request("group_logout_all",group_id=self.target_id)
            self.notify("Sesiones cerradas",f"Se cerraron {result.get('closed',0)} conexiones/sesiones.")
        except Exception as e:self.notify("No se pudo ejecutar",str(e))

    def logout(self):
        self.logout_btn.setEnabled(False)
        self.logout_loading=LoadingDialog("Cerrando sesión…",self)
        self.logout_loading.show()
        self.logout_worker=RequestWorker(lambda:self.network.request("logout"))
        self.logout_worker.succeeded.connect(self._logout_succeeded)
        self.logout_worker.failed.connect(self._logout_failed)
        self.logout_worker.start()

    def _logout_succeeded(self,data):
        self.logout_loading.close()
        self.logged_out.emit("Has cerrado tu sesión.")

    def _logout_failed(self,error):
        self.logout_loading.close()
        self.logout_btn.setEnabled(True)
        self.notify("No se pudo cerrar sesión",error)

    def send_message(self):
        body=self.message.text().strip()
        if not body:return
        try:
            if self.scope=="general":self.network.request("general_send",body=body)
            elif self.scope=="direct":self.network.request("direct_send",recipient_id=self.target_id,body=body)
            elif self.scope=="group":self.network.request("group_send",group_id=self.target_id,body=body)
            elif self.scope=="channel":self.network.request("channel_send",channel_id=self.target_id,body=body)
            self.message.clear()
        except Exception as e:self.notify("No se pudo enviar",str(e))

    def create_item(self):
        row=self.nav.currentRow()
        if row==2:
            name,ok=QInputDialog.getText(self,"Crear grupo","Nombre del grupo:")
            if ok and name.strip():
                try:self.network.request("group_create",name=name.strip()); self.nav_changed(2)
                except Exception as e:self.notify("Error",str(e))
        elif row==3:
            name,ok=QInputDialog.getText(self,"Crear canal","Nombre del canal:")
            if ok and name.strip():
                try:self.network.request("channel_create",name=name.strip()); self.nav_changed(3)
                except Exception as e:self.notify("Error",str(e))

    def handle_event(self,packet):
        if packet.get("event")=="message":
            scope=packet.get("scope")
            relevant=(scope=="general" and self.scope=="general") or (
                scope=="direct" and self.scope=="direct" and self.target_id in (packet.get("sender_id"),packet.get("recipient_id"))) or (
                scope in ("group","channel") and self.scope==scope and self.target_id==packet.get("target_id"))
            if relevant:
                self.append_message(packet.get("sender",""),packet.get("body",""),self.datetime.now().strftime("%H:%M"),packet.get("sender_id"))
        elif packet.get("event")=="force_logout":
            reason=packet.get("reason","Tu sesión fue cerrada por una acción de administración del grupo.")
            self.logged_out.emit(reason)
        elif packet.get("event")=="presence" and self.nav.currentRow()==4:
            self.nav_changed(4)
