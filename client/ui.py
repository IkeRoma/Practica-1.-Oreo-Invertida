import base64, os, secrets
from PySide6.QtCore import Qt, Signal, QPropertyAnimation, QEasingCurve, QSize, QThread
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QApplication, QWidget, QDialog, QMainWindow, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QListWidget, QListWidgetItem, QTextEdit, QMessageBox,
    QInputDialog, QFileDialog, QFrame, QCheckBox, QProgressDialog, QDialogButtonBox,
    QFormLayout, QSplitter, QToolButton, QGraphicsOpacityEffect, QScrollArea
)

STYLE = """
* { font-family: "Segoe UI", "Inter", Arial; font-size: 13px; }
QWidget { background:#101827; color:#e7edf7; }
QFrame#card, QFrame#sidebar, QFrame#panel { background:#172338; border:1px solid #263750; border-radius:16px; }
QLabel#brand { color:#6ee7d8; font-size:27px; font-weight:900; letter-spacing:2px; }
QLabel#muted { color:#91a2bb; }
QLabel#heading { font-size:21px; font-weight:750; color:#f5f8ff; }
QLineEdit, QTextEdit { background:#0d1727; color:#f3f6fb; border:1px solid #31435f; border-radius:10px; padding:11px; selection-background-color:#256b80; }
QLineEdit:focus, QTextEdit:focus { border:1px solid #4dd8c8; }
QPushButton { background:#16a6a0; color:#071b25; border:0; border-radius:10px; padding:11px 16px; font-weight:750; }
QPushButton:hover { background:#43d4c6; }
QPushButton:disabled { background:#34445a; color:#8291a7; }
QPushButton#secondary { background:#243650; color:#dce8f8; border:1px solid #38506d; }
QPushButton#secondary:hover { background:#304968; }
QPushButton#danger { background:#a83e55; color:white; }
QListWidget { background:transparent; border:0; outline:0; padding:4px; }
QListWidget::item { padding:12px; margin:3px 0; border-radius:9px; color:#b9c7da; }
QListWidget::item:selected { background:#24445a; color:#72e3d4; }
QListWidget::item:hover { background:#20344d; }
QCheckBox { spacing:8px; color:#bdcbe0; }
QCheckBox::indicator { width:17px; height:17px; }
QCheckBox::indicator:unchecked { border:1px solid #526780; border-radius:5px; background:#0d1727; }
QCheckBox::indicator:checked { border:1px solid #4dd8c8; border-radius:5px; background:#16a6a0; }
QScrollBar:vertical { background:#111d2d; width:9px; margin:2px; }
QScrollBar::handle:vertical { background:#38516c; border-radius:4px; min-height:25px; }
QScrollBar::add-line:vertical,QScrollBar::sub-line:vertical { height:0; }
"""

def fade_in(widget, duration=230):
    effect = QGraphicsOpacityEffect(widget)
    widget.setGraphicsEffect(effect)
    anim = QPropertyAnimation(effect, b"opacity", widget)
    anim.setDuration(duration)
    anim.setStartValue(0.0); anim.setEndValue(1.0)
    anim.setEasingCurve(QEasingCurve.OutCubic)
    widget._fade_anim = anim
    anim.start()

def password_is_valid(value):
    return (len(value) >= 10 and any(c.isupper() for c in value)
            and any(c.islower() for c in value) and any(c.isdigit() for c in value)
            and any(not c.isalnum() for c in value))

def password_help():
    return "Mínimo 10 caracteres: mayúscula, minúscula, número y símbolo."

class BaseDialog(QDialog):
    def __init__(self, title, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title); self.setModal(True)
        self.setMinimumWidth(430)
        self.setStyleSheet(STYLE)
        self.root = QVBoxLayout(self); self.root.setContentsMargins(26,24,26,24); self.root.setSpacing(13)
        title_label = QLabel(title); title_label.setObjectName("heading"); self.root.addWidget(title_label)

class RegisterDialog(BaseDialog):
    registered = Signal(dict)
    def __init__(self, network, parent=None):
        super().__init__("Crear una cuenta", parent); self.network=network; self.avatar_data=None
        self.username=QLineEdit(); self.username.setPlaceholderText("Nombre de usuario")
        self.display=QLineEdit(); self.display.setPlaceholderText("Nombre que verán tus contactos")
        self.password=QLineEdit(); self.password.setPlaceholderText("Contraseña"); self.password.setEchoMode(QLineEdit.Password)
        self.confirm=QLineEdit(); self.confirm.setPlaceholderText("Confirmar contraseña"); self.confirm.setEchoMode(QLineEdit.Password)
        self.photo=QPushButton("Elegir fotografía"); self.photo.setObjectName("secondary"); self.photo.clicked.connect(self.pick_photo)
        self.photo_note=QLabel("Puedes elegir una imagen JPG, PNG o WEBP."); self.photo_note.setObjectName("muted")
        for label,field in [("Usuario",self.username),("Nombre visible",self.display),("Contraseña",self.password),("Confirmación",self.confirm)]:
            self.root.addWidget(QLabel(label)); self.root.addWidget(field)
        self.root.addWidget(QLabel(password_help())); self.root.addWidget(self.photo); self.root.addWidget(self.photo_note)
        row=QHBoxLayout(); cancel=QPushButton("Cancelar"); cancel.setObjectName("secondary")
        create=QPushButton("Crear cuenta"); cancel.clicked.connect(self.reject); create.clicked.connect(self.submit)
        row.addWidget(cancel); row.addWidget(create); self.root.addLayout(row)
    def pick_photo(self):
        path,_=QFileDialog.getOpenFileName(self,"Seleccionar fotografía","","Imágenes (*.png *.jpg *.jpeg *.webp)")
        if not path:return
        pix=QPixmap(path)
        if pix.isNull(): QMessageBox.warning(self,"Fotografía","No se pudo abrir la imagen."); return
        pix=pix.scaled(256,256,Qt.KeepAspectRatio,Qt.SmoothTransformation)
        from PySide6.QtCore import QBuffer, QByteArray, QIODevice
        ba=QByteArray(); buf=QBuffer(ba); buf.open(QIODevice.WriteOnly); pix.save(buf,"JPEG",85)
        self.avatar_data="data:image/jpeg;base64,"+base64.b64encode(bytes(ba)).decode("ascii")
        self.photo_note.setText("Fotografía seleccionada.")
    def submit(self):
        username=self.username.text().strip()
        if len(username)<3 or len(username)>32 or not username.replace("_","").isalnum():
            QMessageBox.warning(self,"Revisa el usuario","Usa de 3 a 32 caracteres alfanuméricos o guion bajo."); return
        if not password_is_valid(self.password.text()):
            QMessageBox.warning(self,"Contraseña no válida",password_help()); return
        if self.password.text()!=self.confirm.text():
            QMessageBox.warning(self,"No coincide","Las contraseñas no coinciden."); return
        try:
            data=self.network.request("register",username=username,password=self.password.text(),
                display_name=self.display.text().strip() or username,avatar_path="",avatar_data=self.avatar_data)
            QMessageBox.information(self,"Cuenta creada",data.get("message","Tu cuenta está lista."))
            self.registered.emit({"username":username,"avatar_data":self.avatar_data})
            self.accept()
        except Exception as e: QMessageBox.warning(self,"No se pudo registrar",str(e))

class ChangePasswordDialog(BaseDialog):
    def __init__(self, network, parent=None):
        super().__init__("Cambiar contraseña",parent); self.network=network
        self.username=QLineEdit(); self.username.setPlaceholderText("Nombre de usuario")
        self.current=QLineEdit(); self.current.setPlaceholderText("Contraseña actual"); self.current.setEchoMode(QLineEdit.Password)
        self.new=QLineEdit(); self.new.setPlaceholderText("Nueva contraseña"); self.new.setEchoMode(QLineEdit.Password)
        self.confirm=QLineEdit(); self.confirm.setPlaceholderText("Confirmar nueva contraseña"); self.confirm.setEchoMode(QLineEdit.Password)
        for w in [self.username,self.current,self.new,self.confirm]: self.root.addWidget(w)
        self.root.addWidget(QLabel(password_help()))
        row=QHBoxLayout(); cancel=QPushButton("Cancelar"); cancel.setObjectName("secondary"); save=QPushButton("Actualizar contraseña")
        cancel.clicked.connect(self.reject); save.clicked.connect(self.submit); row.addWidget(cancel); row.addWidget(save); self.root.addLayout(row)
    def submit(self):
        if not password_is_valid(self.new.text()):
            QMessageBox.warning(self,"Contraseña no válida",password_help()); return
        if self.new.text()!=self.confirm.text():
            QMessageBox.warning(self,"No coincide","La confirmación no coincide."); return
        try:
            data=self.network.request("password_change",username=self.username.text().strip(),
                current_password=self.current.text(),new_password=self.new.text())
            QMessageBox.information(self,"Contraseña actualizada",data.get("message","Actualización completada."))
            self.accept()
        except Exception as e: QMessageBox.warning(self,"No se pudo cambiar",str(e))



class LoginWorker(QThread):
    succeeded = Signal(dict)
    failed = Signal(str)
    def __init__(self, network, username, password, device_token):
        super().__init__(); self.network=network; self.username=username
        self.password=password; self.device_token=device_token
    def run(self):
        try:
            data=self.network.request("login",username=self.username,password=self.password,
                device_token=self.device_token,
                device_name=os.environ.get("COMPUTERNAME") or os.environ.get("HOSTNAME") or "Equipo personal")
            data["device_token"]=self.device_token
            self.succeeded.emit(data)
        except Exception as exc:
            self.failed.emit(str(exc))

class LoginWidget(QWidget):
    authenticated=Signal(dict)
    def __init__(self, network, device_token="", parent=None):
        super().__init__(parent); self.network=network; self.device_token=device_token
        self.setWindowTitle("Wasap | Acceso"); self.setFixedSize(470,600)
        root=QVBoxLayout(self); root.setContentsMargins(35,30,35,30); root.setAlignment(Qt.AlignCenter)
        card=QFrame(); card.setObjectName("card"); layout=QVBoxLayout(card); layout.setContentsMargins(30,30,30,30); layout.setSpacing(14)
        brand=QLabel("WASAP"); brand.setObjectName("brand"); brand.setAlignment(Qt.AlignCenter)
        subtitle=QLabel("Tus conversaciones, en un solo lugar"); subtitle.setObjectName("muted"); subtitle.setAlignment(Qt.AlignCenter)
        self.username=QLineEdit(); self.username.setPlaceholderText("Nombre de usuario")
        self.password=QLineEdit(); self.password.setPlaceholderText("Contraseña"); self.password.setEchoMode(QLineEdit.Password)
        self.remember=QCheckBox("Recordar este dispositivo")
        login=QPushButton("Iniciar sesión"); self.login_button=login; login.clicked.connect(self.do_login)
        register=QPushButton("Crear cuenta"); register.setObjectName("secondary"); register.clicked.connect(self.open_register)
        change=QPushButton("Cambiar contraseña"); change.setObjectName("secondary"); change.clicked.connect(self.open_password)
        self.status=QLabel(""); self.status.setObjectName("muted"); self.status.setWordWrap(True)
        for w in [brand,subtitle,self.username,self.password,self.remember,login,register,change,self.status]: layout.addWidget(w)
        root.addWidget(card); self.setStyleSheet(STYLE)
    def _busy(self, text):
        dlg=QProgressDialog(text,None,0,0,self); dlg.setWindowTitle("Wasap"); dlg.setWindowModality(Qt.WindowModal); dlg.setCancelButton(None); dlg.setMinimumDuration(0); dlg.show(); QApplication.processEvents(); return dlg
    def do_login(self):
        if not self.username.text().strip() or not self.password.text():
            self.status.setText("Escribe tu usuario y contraseña."); return
        token=""
        if self.remember.isChecked():
            token=self.device_token or secrets.token_urlsafe(40)
        self.login_button.setEnabled(False)
        self.progress=QProgressDialog("Validando tus credenciales…",None,0,0,self)
        self.progress.setWindowTitle("Iniciando sesión"); self.progress.setWindowModality(Qt.WindowModal)
        self.progress.setCancelButton(None); self.progress.setMinimumDuration(0); self.progress.show()
        self.worker=LoginWorker(self.network,self.username.text().strip(),self.password.text(),token)
        self.worker.succeeded.connect(self.login_success)
        self.worker.failed.connect(self.login_failed)
        self.worker.start()
    def login_success(self,data):
        self.progress.close(); self.login_button.setEnabled(True)
        if self.remember.isChecked():
            try:
                import keyring
                keyring.set_password("WasapDesktop","remembered_device",data["device_token"])
            except Exception as e:
                QMessageBox.warning(self,"No se pudo recordar el dispositivo",
                    "El inicio de sesión fue correcto, pero el almacén seguro del sistema no está disponible. "
                    "Instala/configura el llavero del sistema para usar esta función.")
        QMessageBox.information(self,"Inicio de sesión correcto",f"¡Hola, {data['user']['display_name']}! Tu sesión está iniciada.")
        self.authenticated.emit(data)
    def login_failed(self,error):
        self.progress.close(); self.login_button.setEnabled(True)
        QMessageBox.warning(self,"No se pudo iniciar sesión",error)
        self.status.setText("Comprueba tus datos e inténtalo nuevamente.")
    def open_register(self):
        dlg=RegisterDialog(self.network,self)
        if dlg.exec() and dlg.username.text(): self.username.setText(dlg.username.text())
    def open_password(self):
        dlg=ChangePasswordDialog(self.network,self); dlg.username.setText(self.username.text()); dlg.exec()

class ProfileDialog(BaseDialog):
    profile_saved=Signal(dict)
    def __init__(self,network,user,parent=None):
        super().__init__("Mi perfil",parent); self.network=network; self.user=user; self.avatar_data=user.get("avatar_data")
        self.preview=QLabel(); self.preview.setFixedSize(100,100); self.preview.setAlignment(Qt.AlignCenter); self.preview.setStyleSheet("background:#0d1727;border-radius:50px;border:1px solid #38506d;")
        self._render_avatar()
        self.name=QLineEdit(user.get("display_name","")); self.name.setPlaceholderText("Nombre visible")
        self.username=QLabel("@"+user.get("username","")); self.username.setObjectName("muted")
        choose=QPushButton("Cambiar fotografía"); choose.setObjectName("secondary"); choose.clicked.connect(self.pick)
        self.root.addWidget(self.preview,0,Qt.AlignHCenter); self.root.addWidget(self.username); self.root.addWidget(QLabel("Nombre visible")); self.root.addWidget(self.name); self.root.addWidget(choose)
        self.root.addWidget(QLabel("Para cambiar tu contraseña utiliza la opción independiente del menú de perfil."))
        row=QHBoxLayout(); cancel=QPushButton("Cancelar"); cancel.setObjectName("secondary"); save=QPushButton("Guardar cambios")
        cancel.clicked.connect(self.reject); save.clicked.connect(self.submit); row.addWidget(cancel); row.addWidget(save); self.root.addLayout(row)
    def _render_avatar(self):
        if self.avatar_data:
            try:
                raw=base64.b64decode(self.avatar_data.split(",",1)[1]); pix=QPixmap(); pix.loadFromData(raw)
                self.preview.setPixmap(pix.scaled(92,92,Qt.KeepAspectRatio,Qt.SmoothTransformation)); return
            except Exception: pass
        self.preview.setText("WA")
    def pick(self):
        path,_=QFileDialog.getOpenFileName(self,"Seleccionar fotografía","","Imágenes (*.png *.jpg *.jpeg *.webp)")
        if not path:return
        pix=QPixmap(path)
        if pix.isNull(): return
        pix=pix.scaled(256,256,Qt.KeepAspectRatio,Qt.SmoothTransformation)
        from PySide6.QtCore import QBuffer, QByteArray, QIODevice
        ba=QByteArray(); buf=QBuffer(ba); buf.open(QIODevice.WriteOnly); pix.save(buf,"JPEG",85)
        self.avatar_data="data:image/jpeg;base64,"+base64.b64encode(bytes(ba)).decode("ascii"); self._render_avatar()
    def submit(self):
        name=self.name.text().strip()
        if not name or len(name)>64: QMessageBox.warning(self,"Nombre no válido","Usa entre 1 y 64 caracteres."); return
        try:
            result=self.network.request("profile_update",display_name=name,avatar_data=self.avatar_data)
            self.user["display_name"]=name; self.user["avatar_data"]=self.avatar_data
            self.profile_saved.emit(self.user); self.accept()
        except Exception as e: QMessageBox.warning(self,"No se pudo guardar",str(e))

class ContactDialog(BaseDialog):
    def __init__(self,users,current_id,parent=None):
        super().__init__("Buscar contactos",parent); self.selected=None
        self.search=QLineEdit(); self.search.setPlaceholderText("Buscar por nombre o @usuario…")
        self.list=QListWidget()
        self.users=[u for u in users if u["id"]!=current_id]
        self.search.textChanged.connect(self.filter); self.list.itemDoubleClicked.connect(self.choose)
        self.root.addWidget(self.search); self.root.addWidget(self.list)
        buttons=QDialogButtonBox(QDialogButtonBox.Cancel|QDialogButtonBox.Ok)
        buttons.accepted.connect(self.choose); buttons.rejected.connect(self.reject); self.root.addWidget(buttons)
        self.filter()
    def filter(self):
        self.list.clear(); q=self.search.text().casefold()
        for u in self.users:
            label=f"{u['display_name']}  ·  @{u['username']}  ·  {'En línea' if u.get('online') else 'Desconectado'}"
            if q in label.casefold():
                item=QListWidgetItem(label); item.setData(Qt.UserRole,u); self.list.addItem(item)
    def choose(self):
        item=self.list.currentItem()
        if item: self.selected=item.data(Qt.UserRole); self.accept()

class ChatWindow(QMainWindow):
    def __init__(self,network,user,device_token=""):
        super().__init__(); self.network=network; self.user=user; self.device_token=device_token
        self.scope="general"; self.target_id=None; self.target_name="Chat general"; self.users_cache=[]
        self.setWindowTitle(f"Wasap — {user['display_name']}"); self.resize(1180,760); self.setMinimumSize(900,600)
        central=QWidget(); self.setCentralWidget(central); root=QHBoxLayout(central); root.setContentsMargins(14,14,14,14); root.setSpacing(14)
        side=QFrame(); side.setObjectName("sidebar"); side.setFixedWidth(255); sl=QVBoxLayout(side); sl.setContentsMargins(14,18,14,14)
        brand=QLabel("WASAP"); brand.setObjectName("brand"); sl.addWidget(brand)
        tagline=QLabel("Mensajería sencilla."); tagline.setObjectName("muted"); sl.addWidget(tagline)
        self.nav=QListWidget()
        for label in ["◉  Chat general","✉  Mensajes directos","▦  Grupos","◈  Canales","⌕  Buscar contactos"]:
            self.nav.addItem(label)
        sl.addSpacing(12); sl.addWidget(self.nav,1)
        self.profile_button=QPushButton(f"◉  {user['display_name']}"); self.profile_button.setObjectName("secondary"); self.profile_button.clicked.connect(self.edit_profile); sl.addWidget(self.profile_button)
        self.password_button=QPushButton("Cambiar contraseña"); self.password_button.setObjectName("secondary"); self.password_button.clicked.connect(self.change_password); sl.addWidget(self.password_button)
        self.logout_button=QPushButton("Cerrar sesión"); self.logout_button.setObjectName("danger"); self.logout_button.clicked.connect(self.logout); sl.addWidget(self.logout_button)
        panel=QFrame(); panel.setObjectName("panel"); rl=QVBoxLayout(panel); rl.setContentsMargins(20,18,20,18); rl.setSpacing(12)
        top=QHBoxLayout(); self.heading=QLabel("Chat general"); self.heading.setObjectName("heading"); self.subtitle=QLabel("Conversación pública"); self.subtitle.setObjectName("muted")
        headcol=QVBoxLayout(); headcol.addWidget(self.heading); headcol.addWidget(self.subtitle); top.addLayout(headcol); top.addStretch()
        self.action=QPushButton("＋ Crear"); self.action.clicked.connect(self.create_item); top.addWidget(self.action)
        rl.addLayout(top); self.transcript=QTextEdit(); self.transcript.setReadOnly(True); self.transcript.setAcceptRichText(True)
        rl.addWidget(self.transcript,1)
        sendrow=QHBoxLayout(); self.message=QLineEdit(); self.message.setPlaceholderText("Escribe un mensaje…"); self.message.returnPressed.connect(self.send_message)
        self.send=QPushButton("Enviar"); self.send.clicked.connect(self.send_message); sendrow.addWidget(self.message,1); sendrow.addWidget(self.send); rl.addLayout(sendrow)
        root.addWidget(side); root.addWidget(panel,1); self.nav.currentRowChanged.connect(self.nav_changed); self.nav.setCurrentRow(0)
        self.setStyleSheet(STYLE); fade_in(self)
    def notify(self,title,text): QMessageBox.information(self,title,text)
    def nav_changed(self,row):
        self.transcript.clear()
        if row==0: self.action.hide(); self.set_context("general",None,"Chat general","Conversación pública",True); self.load_history()
        elif row==1: self.action.hide(); self.choose_user()
        elif row==2: self.action.show(); self.action.setText("＋ Crear grupo"); self.choose_group()
        elif row==3: self.action.show(); self.action.setText("＋ Crear canal"); self.choose_channel()
        elif row==4: self.action.hide(); self.show_users()
        fade_in(self.transcript,160)
    def set_context(self,scope,target,name,subtitle,can_send):
        self.scope,self.target_id,self.target_name=scope,target,name
        self.heading.setText(name); self.subtitle.setText(subtitle)
        self.message.setEnabled(can_send); self.send.setEnabled(can_send)
    def load_history(self):
        try:
            rows=self.network.request("history",scope=self.scope,target_id=self.target_id)
            self.transcript.clear()
            for m in rows: self.append_message(m.get("display_name") or m.get("username",""),m["body"],m.get("created_at",""))
        except Exception as e: self.transcript.append(f"<i>{e}</i>")
    def append_message(self,sender,body,when=""):
        safe_sender=str(sender).replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")
        safe_body=str(body).replace("&","&amp;").replace("<","&lt;").replace(">","&gt;").replace("\\n","<br>")
        self.transcript.append(f"<div style='margin:7px 0'><b style='color:#6ee7d8'>{safe_sender}</b> <span style='color:#71839d;font-size:10px'>{when}</span><br><span>{safe_body}</span></div>")
    def send_message(self):
        body=self.message.text().strip()
        if not body:return
        try:
            if self.scope=="general": self.network.request("general_send",body=body)
            elif self.scope=="direct": self.network.request("direct_send",recipient_id=self.target_id,body=body)
            elif self.scope=="group": self.network.request("group_send",group_id=self.target_id,body=body)
            elif self.scope=="channel": self.network.request("channel_send",channel_id=self.target_id,body=body)
            self.message.clear()
        except Exception as e: QMessageBox.warning(self,"No se pudo enviar",str(e))
    def choose_user(self):
        try: users=self.network.request("users")
        except Exception as e: self.notify("Error",str(e)); return
        dlg=ContactDialog(users,self.user["id"],self)
        if dlg.exec() and dlg.selected:
            u=dlg.selected; self.set_context("direct",u["id"],f"@ {u['display_name']}",f"Conversación con @{u['username']}",True); self.load_history()
    def choose_group(self):
        try: groups=self.network.request("groups")
        except Exception as e: self.notify("Error",str(e)); return
        opts=[f"{g['name']} (ID {g['id']})" for g in groups]; opts.append("＋ Crear grupo")
        selected,ok=QInputDialog.getItem(self,"Grupos","Selecciona un grupo:",opts,0,False)
        if not ok:return
        if selected=="＋ Crear grupo": self.create_group(); return
        g=groups[opts.index(selected)]
        self.set_context("group",g["id"],f"▦ {g['name']}","Chat de grupo",True); self.load_history()
        if QMessageBox.question(self,"Integrantes","¿Deseas agregar un usuario al grupo?")==QMessageBox.Yes:
            username,ok=QInputDialog.getText(self,"Agregar integrante","Nombre de usuario:")
            if ok and username:
                try:self.network.request("group_add",group_id=g["id"],username=username)
                except Exception as e:self.notify("Error",str(e))
    def create_group(self):
        name,ok=QInputDialog.getText(self,"Crear grupo","Nombre del grupo:")
        if ok and name:
            try:self.network.request("group_create",name=name); self.choose_group()
            except Exception as e:self.notify("Error",str(e))
    def choose_channel(self):
        try: channels=self.network.request("channels")
        except Exception as e:self.notify("Error",str(e)); return
        opts=[f"#{c['name']} — propietario: {c['owner_username']}" for c in channels]; opts.append("＋ Crear canal")
        selected,ok=QInputDialog.getItem(self,"Canales","Canales disponibles:",opts,0,False)
        if not ok:return
        if selected=="＋ Crear canal": self.create_channel(); return
        c=channels[opts.index(selected)]
        try:self.network.request("channel_join",channel_id=c["id"])
        except Exception as e:self.notify("Error",str(e)); return
        self.set_context("channel",c["id"],f"◈ {c['name']}",f"Canal · propietario @{c['owner_username']}",c["owner_id"]==self.user["id"]); self.load_history()
    def create_channel(self):
        name,ok=QInputDialog.getText(self,"Crear canal","Nombre del canal:")
        if ok and name:
            try:self.network.request("channel_create",name=name); self.choose_channel()
            except Exception as e:self.notify("Error",str(e))
    def create_item(self):
        if self.nav.currentRow()==2:self.create_group()
        elif self.nav.currentRow()==3:self.create_channel()
    def show_users(self):
        try: users=self.network.request("users"); self.users_cache=users
        except Exception as e:self.notify("Error",str(e)); return
        self.set_context("users",None,"Buscar contactos","Selecciona Mensajes directos para abrir una conversación",False)
        self.transcript.clear()
        for u in users:
            status="● En línea" if u.get("online") else "○ Desconectado"
            self.transcript.append(f"<b>{u['display_name']}</b>  <span style='color:#6ee7d8'>@{u['username']}</span>  <span style='color:#8da0ba'>{status}</span>")
    def edit_profile(self):
        dlg=ProfileDialog(self.network,self.user,self); dlg.profile_saved.connect(self.profile_updated); dlg.exec()
    def profile_updated(self,user):
        self.user=user; self.profile_button.setText(f"◉  {user['display_name']}"); self.setWindowTitle(f"Wasap — {user['display_name']}")
    def change_password(self):
        dlg=ChangePasswordDialog(self.network,self); dlg.username.setText(self.user.get("username",""))
        if dlg.exec():
            QMessageBox.information(self,"Seguridad","La contraseña cambió. Se cerrará la sesión para volver a autenticarte.")
            QApplication.quit()
    def logout(self):
        if QMessageBox.question(self,"Cerrar sesión","¿Deseas cerrar la sesión en este equipo?")==QMessageBox.Yes:
            try:
                if self.device_token: self.network.request("device_revoke",device_token=self.device_token)
            except Exception: pass
            try:
                import keyring
                keyring.delete_password("WasapDesktop","remembered_device")
            except Exception: pass
            self.close(); QApplication.quit()
    def handle_event(self,packet):
        if packet.get("event")=="message":
            scope=packet.get("scope")
            relevant=(scope=="general" and self.scope=="general") or (scope=="direct" and self.scope=="direct" and self.target_id in (packet.get("sender_id"),packet.get("recipient_id"))) or (scope in ("group","channel") and self.scope==scope and self.target_id==packet.get("target_id"))
            if relevant:self.append_message(packet.get("sender",""),packet.get("body",""))
        elif packet.get("event")=="presence" and self.nav.currentRow()==4:self.show_users()
