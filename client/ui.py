import os
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget,QMainWindow,QVBoxLayout,QHBoxLayout,QLabel,QLineEdit,QPushButton,
    QListWidget,QListWidgetItem,QTextEdit,QMessageBox,QInputDialog,QFileDialog,
    QStackedWidget,QFrame
)

STYLE = """
QWidget { background:#313338; color:#f2f3f5; font-family:Arial; font-size:13px; }
QLineEdit,QTextEdit { background:#1e1f22; border:1px solid #202225; border-radius:6px; padding:9px; }
QPushButton { background:#5865f2; border:0; border-radius:5px; padding:9px 13px; color:white; font-weight:600; }
QPushButton:hover { background:#4752c4; }
QListWidget { background:#2b2d31; border:0; border-radius:6px; padding:5px; }
QListWidget::item { padding:9px; border-radius:4px; }
QListWidget::item:selected { background:#404249; }
"""

class LoginWidget(QWidget):
    authenticated=__import__("PySide6.QtCore",fromlist=["Signal"]).Signal(dict)
    def __init__(self, network):
        super().__init__(); self.network=network; self.avatar=""
        root=QVBoxLayout(self); root.setAlignment(Qt.AlignCenter)
        card=QFrame(); card.setFixedWidth(380); layout=QVBoxLayout(card)
        title=QLabel("WASAP"); title.setStyleSheet("font-size:30px;font-weight:800;color:#fff;")
        subtitle=QLabel("Conecta con tu comunidad")
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

    def do_login(self):
        try:
            data=self.network.request("login",username=self.username.text(),password=self.password.text())
            self.authenticated.emit(data)
        except Exception as e: self.status.setText(str(e))

    def do_register(self):
        try:
            data=self.network.request("register",username=self.username.text(),password=self.password.text(),
                display_name=self.display.text(),avatar_path=self.avatar)
            self.status.setText(data.get("message","Cuenta creada."))
        except Exception as e: self.status.setText(str(e))

class ChatWindow(QMainWindow):
    def __init__(self, network, user):
        super().__init__(); self.network=network; self.user=user
        self.scope="general"; self.target_id=None; self.target_name="Chat general"
        self.setWindowTitle(f"Wasap — {user['display_name']}")
        self.resize(1100,720)
        central=QWidget(); self.setCentralWidget(central); root=QHBoxLayout(central); root.setContentsMargins(8,8,8,8)
        side=QFrame(); side.setFixedWidth(260); side.setStyleSheet("background:#2b2d31;border-radius:8px;")
        sl=QVBoxLayout(side)
        brand=QLabel("WASAP"); brand.setStyleSheet("font-size:22px;font-weight:800;padding:8px;")
        sl.addWidget(brand)
        self.nav=QListWidget()
        for label in ["#  Chat general","@  Mensajes directos","▣  Grupos","◉  Canales","●  Usuarios"]:
            self.nav.addItem(label)
        self.nav.currentRowChanged.connect(self.nav_changed); sl.addWidget(self.nav)
        self.action=QPushButton("＋ Crear")
        self.action.clicked.connect(self.create_item); sl.addWidget(self.action)
        self.right=QFrame(); self.right.setStyleSheet("background:#313338;border-radius:8px;")
        rl=QVBoxLayout(self.right)
        self.heading=QLabel("Chat general"); self.heading.setStyleSheet("font-size:20px;font-weight:700;padding:8px;")
        self.transcript=QTextEdit(); self.transcript.setReadOnly(True)
        sendrow=QHBoxLayout(); self.message=QLineEdit(); self.message.setPlaceholderText("Escribe un mensaje...")
        self.send=QPushButton("Enviar"); self.send.clicked.connect(self.send_message)
        self.message.returnPressed.connect(self.send_message)
        sendrow.addWidget(self.message); sendrow.addWidget(self.send)
        rl.addWidget(self.heading); rl.addWidget(self.transcript); rl.addLayout(sendrow)
        root.addWidget(side); root.addWidget(self.right,1)
        self.nav.setCurrentRow(0)
        self.refresh_presence()

    def notify(self, title, text):
        QMessageBox.information(self,title,text)

    def nav_changed(self,row):
        self.transcript.clear()
        if row==0:
            self.set_context("general",None,"Chat general",True); self.load_history()
        elif row==1:
            self.choose_user()
        elif row==2:
            self.choose_group()
        elif row==3:
            self.choose_channel()
        elif row==4:
            self.show_users()

    def set_context(self,scope,target,name,can_send):
        self.scope,self.target_id,self.target_name=scope,target,name
        self.heading.setText(name)
        self.message.setEnabled(can_send); self.send.setEnabled(can_send)

    def load_history(self):
        try:
            rows=self.network.request("history",scope=self.scope,target_id=self.target_id)
            self.transcript.clear()
            for m in rows: self.append_message(m.get("display_name") or m.get("username",""),m["body"],m.get("created_at",""))
        except Exception as e: self.transcript.append(f"<i>{e}</i>")

    def append_message(self,sender,body,when=""):
        self.transcript.append(f"<b>{sender}</b> <span style='color:#999'>{when}</span><br>{body}")

    def send_message(self):
        body=self.message.text().strip()
        if not body:return
        try:
            if self.scope=="general": self.network.request("general_send",body=body)
            elif self.scope=="direct": self.network.request("direct_send",recipient_id=self.target_id,body=body)
            elif self.scope=="group": self.network.request("group_send",group_id=self.target_id,body=body)
            elif self.scope=="channel": self.network.request("channel_send",channel_id=self.target_id,body=body)
            self.message.clear()
        except Exception as e: self.notify("No se pudo enviar",str(e))

    def choose_user(self):
        try: users=self.network.request("users")
        except Exception as e: self.notify("Error",str(e)); return
        options=[f"{u['display_name']} (@{u['username']})" for u in users if u["id"]!=self.user["id"]]
        if not options: self.notify("Usuarios","No hay otros usuarios registrados."); return
        selected,ok=QInputDialog.getItem(self,"Mensaje directo","Selecciona usuario:",options,0,False)
        if ok:
            index=options.index(selected); u=[u for u in users if u["id"]!=self.user["id"]][index]
            self.set_context("direct",u["id"],f"@ {u['display_name']}",True); self.load_history()

    def choose_group(self):
        try: groups=self.network.request("groups")
        except Exception as e: self.notify("Error",str(e)); return
        options=[f"{g['name']} (ID {g['id']})" for g in groups]
        options.append("＋ Crear grupo")
        selected,ok=QInputDialog.getItem(self,"Grupos","Selecciona un grupo:",options,0,False)
        if not ok:return
        if selected=="＋ Crear grupo": self.create_group(); return
        g=groups[options.index(selected)]
        self.set_context("group",g["id"],f"▣ {g['name']}",True); self.load_history()
        if QMessageBox.question(self,"Integrantes","¿Deseas agregar un usuario?")==QMessageBox.Yes:
            username,ok=QInputDialog.getText(self,"Agregar integrante","Nombre de usuario:")
            if ok and username:
                try:self.network.request("group_add",group_id=g["id"],username=username)
                except Exception as e:self.notify("Error",str(e))

    def create_group(self):
        name,ok=QInputDialog.getText(self,"Crear grupo","Nombre del grupo:")
        if ok and name:
            try:
                self.network.request("group_create",name=name)
                self.choose_group()
            except Exception as e:self.notify("Error",str(e))

    def choose_channel(self):
        try: channels=self.network.request("channels")
        except Exception as e:self.notify("Error",str(e)); return
        options=[f"#{c['name']} — propietario: {c['owner_username']} (ID {c['id']})" for c in channels]
        options.append("＋ Crear canal")
        if not channels: options=["＋ Crear canal"]
        selected,ok=QInputDialog.getItem(self,"Canales","Canales disponibles:",options,0,False)
        if not ok:return
        if selected=="＋ Crear canal": self.create_channel(); return
        c=channels[options.index(selected)]
        try:self.network.request("channel_join",channel_id=c["id"])
        except Exception as e:self.notify("Error",str(e)); return
        can_send=(c["owner_id"]==self.user["id"])
        self.set_context("channel",c["id"],f"# {c['name']}",can_send); self.load_history()

    def create_channel(self):
        name,ok=QInputDialog.getText(self,"Crear canal","Nombre del canal:")
        if ok and name:
            try:
                self.network.request("channel_create",name=name); self.choose_channel()
            except Exception as e:self.notify("Error",str(e))

    def create_item(self):
        row=self.nav.currentRow()
        if row==2:self.create_group()
        elif row==3:self.create_channel()
        else:self.notify("Crear","Selecciona Grupos o Canales para crear.")

    def show_users(self):
        try:
            users=self.network.request("users")
            self.set_context("users",None,"Usuarios registrados",False)
            self.transcript.clear()
            for u in users:
                self.transcript.append(f"<b>{u['display_name']}</b> (@{u['username']}) — {'En línea' if u['online'] else 'Desconectado'}")
        except Exception as e:self.notify("Error",str(e))

    def refresh_presence(self):
        pass

    def handle_event(self, packet):
        if packet.get("event")=="message":
            scope=packet.get("scope")
            relevant=(scope=="general" and self.scope=="general") or (
                scope=="direct" and self.scope=="direct" and self.target_id in (packet.get("sender_id"),packet.get("recipient_id"))) or (
                scope in ("group","channel") and self.scope==scope and self.target_id==packet.get("target_id"))
            if relevant:
                self.append_message(packet.get("sender",""),packet.get("body",""))
        elif packet.get("event")=="presence" and self.nav.currentRow()==4:
            self.show_users()
