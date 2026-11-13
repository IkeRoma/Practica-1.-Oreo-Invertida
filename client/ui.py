import base64, os, secrets, re
from datetime import datetime, timezone
from PySide6.QtCore import (
    Qt,
    QTimer,
    QThread,
    QPropertyAnimation,
    QEasingCurve,
    QPoint,
    Signal,
    Slot
)

from PySide6.QtWidgets import (
    QApplication,
    QTextBrowser,
    QWidget,
    QMainWindow,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QListWidget,
    QListWidgetItem,
    QTextEdit,
    QMessageBox,
    QInputDialog,
    QFileDialog,
    QStackedWidget,
    QDialog,
    QCheckBox,
    QFrame,
    QGraphicsOpacityEffect,
    QTreeWidget,
    QTreeWidgetItem,
    QDialogButtonBox,
    QProgressDialog
)

from PySide6.QtGui import (
    QColor,
    QPen,
    QTextCursor,
    QPixmap,
    QPainter
)

STYLE = """
* { font-family: "Segoe UI", "Inter", Arial; font-size: 13px; }
QWidget { background:#313338; color:#f2f3f5; }
QFrame#card, QFrame#sidebar, QFrame#panel { background:#2b2d31; border:1px solid #202225; border-radius:14px; }
QLabel#brand { color:#ffffff; font-size:27px; font-weight:900; letter-spacing:2px; }
QLabel#muted { color:#b5bac1; }
QLabel#heading { font-size:21px; font-weight:750; color:#f2f3f5; }
QLineEdit, QTextEdit, QTextBrowser { background:#1e1f22; color:#f2f3f5; border:1px solid #202225; border-radius:9px; padding:10px; selection-background-color:#5865f2; }
QLineEdit:focus, QTextEdit:focus, QTextBrowser:focus { border:1px solid #5865f2; }
QPushButton { background:#5865f2; color:white; border:0; border-radius:8px; padding:10px 14px; font-weight:700; }
QPushButton:hover { background:#4752c4; }
QPushButton:disabled { background:#404249; color:#949ba4; }
QPushButton#secondary { background:#404249; color:#f2f3f5; border:1px solid #202225; }
QPushButton#secondary:hover { background:#4e5058; }
QPushButton#danger { background:#da373c; color:white; }
QPushButton#danger:hover { background:#b92d33; }
QListWidget, QTreeWidget { background:transparent; border:0; outline:0; padding:4px; }
QListWidget::item, QTreeWidget::item { padding:10px; margin:2px 0; border-radius:7px; color:#dbdee1; }
QListWidget::item:selected, QTreeWidget::item:selected { background:#404249; color:#ffffff; }
QListWidget::item:hover, QTreeWidget::item:hover { background:#383a40; }
QCheckBox { spacing:8px; color:#dbdee1; }
QCheckBox::indicator { width:17px; height:17px; }
QCheckBox::indicator:unchecked { border:1px solid #72767d; border-radius:4px; background:#1e1f22; }
QCheckBox::indicator:checked { border:1px solid #5865f2; border-radius:4px; background:#5865f2; }
QScrollBar:vertical { background:#2b2d31; width:9px; margin:2px; }
QScrollBar::handle:vertical { background:#4e5058; border-radius:4px; min-height:25px; }
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

def slide_in(widget, distance=18, duration=220):
    """Entrada breve desde abajo para las ventanas principales."""
    end_pos = widget.pos()
    start_pos = end_pos + QPoint(0, distance)
    widget.move(start_pos)
    anim = QPropertyAnimation(widget, b"pos", widget)
    anim.setDuration(duration)
    anim.setStartValue(start_pos)
    anim.setEndValue(end_pos)
    anim.setEasingCurve(QEasingCurve.OutCubic)
    widget._slide_anim = anim
    anim.start()

PASSWORD_PATTERN = re.compile(r"^(?=.*[A-Z])(?=.*[a-z])(?=.*\d)(?=.*[^A-Za-z0-9]).{10,}$")

def password_is_valid(value):
    return bool(PASSWORD_PATTERN.fullmatch(value or ""))

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
        root.addWidget(card); self.setStyleSheet(STYLE); fade_in(self)
    def _busy(self, text):
        dlg=QProgressDialog(text,None,0,0,self); dlg.setWindowTitle("Wasap"); dlg.setWindowModality(Qt.WindowModal); dlg.setCancelButton(None); dlg.setMinimumDuration(0); dlg.show(); QApplication.processEvents(); return dlg
    def do_login(self):
        if not self.username.text().strip() or not self.password.text():
            self.status.setText("Escribe tu usuario y contraseña."); return
        if not password_is_valid(self.password.text()):
            self.status.setText(password_help()); return
        token=""
        if self.remember.isChecked():
            token=self.device_token or secrets.token_urlsafe(40)
        self.login_button.setEnabled(False)
        self.progress=OreoLoadingDialog("Iniciando sesión", "Validando tus credenciales…", self)
        self.progress.show()
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
        self.preview=QLabel(); self.preview.setFixedSize(100,100); self.preview.setAlignment(Qt.AlignCenter); self.preview.setStyleSheet("background:#1e1f22;border-radius:50px;border:1px solid #404249;")
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

class OreoSpinner(QWidget):
    """Galleta tipo sándwich dibujada con QPainter y animada en rotación."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(92, 92)
        self.angle = 0
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._tick)
        self.timer.start(25)

    def _tick(self):
        self.angle = (self.angle + 5) % 360
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.translate(self.width()/2, self.height()/2)
        painter.rotate(self.angle)
        # Sombra y crema
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor("#050914"))
        painter.drawEllipse(-34, -29, 68, 58)
        painter.setBrush(QColor("#eee8df"))
        painter.drawEllipse(-29, -25, 58, 50)
        # Dos tapas oscuras con relieve
        painter.setBrush(QColor("#24150f"))
        painter.drawEllipse(-31, -27, 62, 44)
        painter.setPen(QPen(QColor("#503326"), 2))
        painter.setBrush(QColor("#352018"))
        painter.drawEllipse(-29, -24, 58, 40)
        # Relieve decorativo
        painter.setPen(QPen(QColor("#694331"), 1.6))
        for x, y in [(-15,-10),(0,-14),(15,-8),(-20,5),(-5,3),(11,7),(20,4),(0,15)]:
            painter.drawEllipse(x-2, y-2, 4, 4)
        # Banda de crema visible
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor("#f4eee5"))
        painter.drawRoundedRect(-28, -3, 56, 7, 3, 3)
        painter.end()

class OreoLoadingDialog(QDialog):
    def __init__(self, title, message, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title); self.setModal(True)
        self.setFixedSize(300, 220)
        self.setStyleSheet(STYLE + " QDialog { background:#313338; }")
        layout=QVBoxLayout(self); layout.setAlignment(Qt.AlignCenter); layout.setSpacing(9)
        self.spinner=OreoSpinner(self); layout.addWidget(self.spinner,0,Qt.AlignHCenter)
        self.label=QLabel(message); self.label.setObjectName("muted"); self.label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.label)

class ChatWindow(QMainWindow):
    forced_logout = Signal(str)
    normal_logout = Signal()

    def __init__(self, network, user, device_token=""):
        super().__init__()
        self.network=network; self.user=user; self.device_token=device_token
        self.scope="general"; self.target_id=None; self.target_name="Chat general"
        self.users_cache=[]; self.group_cache=[]; self.channel_cache=[]
        self._last_sender_id=None; self._loading=False
        self.setWindowTitle(f"Wasap — {user['display_name']}")
        self.resize(1320,820); self.setMinimumSize(1050,680)
        central=QWidget(); self.setCentralWidget(central)
        root=QHBoxLayout(central); root.setContentsMargins(12,12,12,12); root.setSpacing(12)

        side=QFrame(); side.setObjectName("sidebar"); side.setFixedWidth(310)
        sl=QVBoxLayout(side); sl.setContentsMargins(14,14,14,14); sl.setSpacing(8)
        brand=QLabel("WASAP"); brand.setObjectName("brand"); brand.setAlignment(Qt.AlignCenter)
        tagline=QLabel("Mensajería sencilla"); tagline.setObjectName("muted"); tagline.setAlignment(Qt.AlignCenter)
        sl.addWidget(brand); sl.addWidget(tagline); sl.addSpacing(8)
        self.search_contacts=QLineEdit(); self.search_contacts.setPlaceholderText("Buscar chats, grupos o contactos…")
        sl.addWidget(self.search_contacts)
        self.tree=QTreeWidget(); self.tree.setHeaderHidden(True); self.tree.setIndentation(14)
        self.search_contacts.textChanged.connect(self.filter_tree)
        self.root_general=QTreeWidgetItem(["◉  Chat general"]); self.root_direct=QTreeWidgetItem(["✉  Mensajes directos"])
        self.root_groups=QTreeWidgetItem(["▦  Grupos"]); self.root_channels=QTreeWidgetItem(["◈  Canales"])
        for item in [self.root_general,self.root_direct,self.root_groups,self.root_channels]:
            self.tree.addTopLevelItem(item); item.setExpanded(True)
        sl.addWidget(self.tree,1)
        create_row=QHBoxLayout()
        self.new_group=QPushButton("＋ Grupo"); self.new_group.setObjectName("secondary")
        self.new_channel=QPushButton("＋ Canal"); self.new_channel.setObjectName("secondary")
        self.refresh_button=QPushButton("↻"); self.refresh_button.setObjectName("secondary")
        create_row.addWidget(self.new_group); create_row.addWidget(self.new_channel); create_row.addWidget(self.refresh_button)
        sl.addLayout(create_row)
        self.profile_button=QPushButton(f"◉  {user['display_name']}"); self.profile_button.setObjectName("secondary")
        self.password_button=QPushButton("Cambiar contraseña"); self.password_button.setObjectName("secondary")
        self.logout_button=QPushButton("Cerrar sesión"); self.logout_button.setObjectName("danger")
        sl.addWidget(self.profile_button); sl.addWidget(self.password_button); sl.addWidget(self.logout_button)

        panel=QFrame(); panel.setObjectName("panel"); rl=QVBoxLayout(panel)
        rl.setContentsMargins(18,16,18,16); rl.setSpacing(10)
        top=QHBoxLayout(); headcol=QVBoxLayout()
        self.heading=QLabel("Chat general"); self.heading.setObjectName("heading")
        self.subtitle=QLabel("Conversación pública"); self.subtitle.setObjectName("muted")
        headcol.addWidget(self.heading); headcol.addWidget(self.subtitle); top.addLayout(headcol); top.addStretch()
        self.info_button=QPushButton("Información"); self.info_button.setObjectName("secondary")
        self.add_member_button=QPushButton("＋"); self.add_member_button.setToolTip("Agregar integrantes al grupo"); self.add_member_button.setObjectName("secondary")
        self.group_logout_button=QPushButton("sálganse, quiero estar solo"); self.group_logout_button.setObjectName("danger")
        self.info_button.hide(); self.add_member_button.hide(); self.group_logout_button.hide()
        top.addWidget(self.info_button); top.addWidget(self.add_member_button); top.addWidget(self.group_logout_button)
        rl.addLayout(top)
        self.transcript=QTextBrowser(); self.transcript.setOpenLinks(False); self.transcript.setOpenExternalLinks(False)
        self.transcript.anchorClicked.connect(self.open_contact_from_message)
        self.transcript.setStyleSheet("QTextBrowser { background:#1e1f22; border:1px solid #202225; border-radius:12px; padding:12px; }")
        rl.addWidget(self.transcript,1)
        sendrow=QHBoxLayout(); self.message=QLineEdit(); self.message.setPlaceholderText("Escribe un mensaje…")
        self.send=QPushButton("Enviar"); sendrow.addWidget(self.message,1); sendrow.addWidget(self.send); rl.addLayout(sendrow)
        root.addWidget(side); root.addWidget(panel,1)

        self.tree.itemClicked.connect(self.select_tree_item)
        self.new_group.clicked.connect(self.create_group); self.new_channel.clicked.connect(self.create_channel)
        self.refresh_button.clicked.connect(self.refresh_lists)
        self.info_button.clicked.connect(self.show_current_info)
        self.add_member_button.clicked.connect(self.add_group_member)
        self.group_logout_button.clicked.connect(self.close_group_sessions)
        self.profile_button.clicked.connect(self.edit_profile)
        self.password_button.clicked.connect(self.change_password)
        self.logout_button.clicked.connect(self.logout)
        self.send.clicked.connect(self.send_message); self.message.returnPressed.connect(self.send_message)
        self.setStyleSheet(STYLE)
        self.refresh_lists(select_general=True)
        fade_in(self)

    def notify(self,title,text): QMessageBox.information(self,title,text)

    def refresh_lists(self, select_general=False):
        current=(self.scope,self.target_id)
        self.tree.blockSignals(True)
        self.root_direct.takeChildren(); self.root_groups.takeChildren(); self.root_channels.takeChildren()
        try:
            self.users_cache=self.network.request("users") or []
            self.group_cache=self.network.request("groups") or []
            self.channel_cache=self.network.request("channels") or []
        except Exception as exc:
            self.tree.blockSignals(False); QMessageBox.warning(self,"No se pudieron actualizar las listas",str(exc)); return
        for u in self.users_cache:
            if u["id"]==self.user["id"]: continue
            status="●" if u.get("online") else "○"
            item=QTreeWidgetItem([f"{status}  {u['display_name']}  (@{u['username']})"])
            item.setData(0,Qt.UserRole,{"scope":"direct","id":u["id"],"name":u["display_name"],"subtitle":f"@{u['username']}"})
            self.root_direct.addChild(item)
        for g in self.group_cache:
            item=QTreeWidgetItem([f"▦  {g['name']}"])
            item.setData(0,Qt.UserRole,{"scope":"group","id":g["id"],"name":g["name"],"subtitle":"Chat de grupo"})
            self.root_groups.addChild(item)
        for c in self.channel_cache:
            item=QTreeWidgetItem([f"◈  {c['name']}"])
            item.setData(0,Qt.UserRole,{"scope":"channel","id":c["id"],"name":c["name"],"subtitle":f"Canal · propietario @{c['owner_username']}","owner_id":c["owner_id"]})
            self.root_channels.addChild(item)
        self.root_general.setData(0,Qt.UserRole,{"scope":"general","id":None,"name":"Chat general","subtitle":"Conversación pública"})
        self.tree.expandAll(); self.tree.blockSignals(False)
        self.filter_tree(self.search_contacts.text())
        if select_general:
            self.set_context("general",None,"Chat general","Conversación pública",True); self.load_history()
        elif current[0] in ("direct","group","channel"):
            for root_item in [self.root_direct,self.root_groups,self.root_channels]:
                for i in range(root_item.childCount()):
                    data=root_item.child(i).data(0,Qt.UserRole)
                    if data and data["scope"]==current[0] and data["id"]==current[1]:
                        self.tree.setCurrentItem(root_item.child(i)); break

    def filter_tree(self, query):
        query=(query or "").casefold().strip()
        for root_item in [self.root_general,self.root_direct,self.root_groups,self.root_channels]:
            visible_children=0
            for i in range(root_item.childCount()):
                child=root_item.child(i)
                match=(not query or query in child.text(0).casefold())
                child.setHidden(not match)
                visible_children += int(match)
            root_item.setHidden(bool(query) and root_item is not self.root_general and visible_children==0)
            if root_item is self.root_general:
                root_item.setHidden(bool(query) and query not in root_item.text(0).casefold())

    def select_tree_item(self,item,column=0):
        data=item.data(0,Qt.UserRole)
        if not data: return
        scope=data["scope"]; target=data["id"]; name=data["name"]
        if scope=="channel":
            try: self.network.request("channel_join",channel_id=target)
            except Exception as exc: QMessageBox.warning(self,"Canal",str(exc)); return
            can_send=data.get("owner_id")==self.user["id"]
        else: can_send=True
        self.set_context(scope,target,name,data.get("subtitle",""),can_send)
        self.load_history()

    def set_context(self,scope,target,name,subtitle,can_send):
        self.scope,self.target_id,self.target_name=scope,target,name
        self.heading.setText(name); self.subtitle.setText(subtitle)
        self.message.setEnabled(can_send); self.send.setEnabled(can_send)
        self.add_member_button.setVisible(scope=="group")
        self.group_logout_button.setVisible(scope=="group")
        self.info_button.setVisible(scope in ("direct","group","channel"))
        self._last_sender_id=None

    def load_history(self):
        self._loading=True; self.transcript.clear(); self._last_sender_id=None
        try:
            rows=self.network.request("history",scope=self.scope,target_id=self.target_id) or []
            for m in rows:
                self.append_message(m.get("display_name") or m.get("username","Usuario"),m.get("body",""),m.get("created_at",""),m.get("sender_id"))
            self.transcript.moveCursor(QTextCursor.End)
            self.transcript.ensureCursorVisible()
            self.transcript.viewport().update(); QApplication.processEvents()
        except Exception as exc:
            self.transcript.setPlainText(f"No se pudo cargar la conversación: {exc}")
        finally: self._loading=False

    @staticmethod
    def _esc(value):
        return str(value).replace("&","&amp;").replace("<","&lt;").replace(">","&gt;").replace('"',"&quot;").replace("'","&#39;")

    @staticmethod
    def _time_label(value):
        if not value: return ""
        try:
            if isinstance(value, datetime):
                stamp=value if value.tzinfo else value.replace(tzinfo=timezone.utc)
                return stamp.astimezone().strftime("%H:%M")
            raw=str(value).replace("Z", "+00:00")
            stamp=datetime.fromisoformat(raw)
            if stamp.tzinfo is None: stamp=stamp.replace(tzinfo=timezone.utc)
            return stamp.astimezone().strftime("%H:%M")
        except Exception:
            text=str(value).replace("T"," ")
            return text[11:16] if len(text)>=16 else text

    def append_message(self,sender,body,when="",sender_id=None):
        sid=sender_id if sender_id is not None else sender
        name=self._esc(sender); safe_body=self._esc(body).replace("\\n","<br>").replace("\n","<br>")
        time_label=self._esc(self._time_label(when))
        if sid!=self._last_sender_id:
            self.transcript.append(f"<div style='margin-top:14px'><a href='wasap-contact://{self._esc(sender_id if sender_id is not None else 0)}' style='color:#aeb8ff;text-decoration:none;font-weight:700'>{name}</a></div>")
            self._last_sender_id=sid
        self.transcript.append(f"<div style='margin:2px 0 3px 0;color:#f2f3f5'>{safe_body} <span style='color:#949ba4;font-size:10px'>{time_label}</span></div>")
        self.transcript.moveCursor(QTextCursor.End); self.transcript.ensureCursorVisible()

    def send_message(self):
        body=self.message.text().strip()
        if not body:return
        try:
            if self.scope=="general": self.network.request("general_send",body=body)
            elif self.scope=="direct": self.network.request("direct_send",recipient_id=self.target_id,body=body)
            elif self.scope=="group": self.network.request("group_send",group_id=self.target_id,body=body)
            elif self.scope=="channel": self.network.request("channel_send",channel_id=self.target_id,body=body)
            self.message.clear()
        except Exception as exc: QMessageBox.warning(self,"No se pudo enviar",str(exc))

    def add_group_member(self):
        if self.scope!="group" or self.target_id is None:return
        try: users=self.network.request("users") or []
        except Exception as exc: QMessageBox.warning(self,"Integrantes",str(exc)); return
        try: members=self.network.request("group_members",group_id=self.target_id) or []
        except Exception as exc: QMessageBox.warning(self,"Integrantes",str(exc)); return
        member_ids={u["id"] for u in members}
        options=[u for u in users if u["id"] not in member_ids]
        if not options: QMessageBox.information(self,"Integrantes","Todos los usuarios ya pertenecen a este grupo."); return
        labels=[f"{u['display_name']} (@{u['username']})" for u in options]
        selected,ok=QInputDialog.getItem(self,"Agregar integrante","Selecciona a quién agregar:",labels,0,False)
        if not ok:return
        user=options[labels.index(selected)]
        try:
            self.network.request("group_add",group_id=self.target_id,username=user["username"])
            QMessageBox.information(self,"Grupo",f"{user['display_name']} se agregó al grupo.")
            self.refresh_lists()
        except Exception as exc: QMessageBox.warning(self,"No se pudo agregar",str(exc))

    def show_current_info(self):
        if self.scope=="direct":
            try: info=self.network.request("contact_info",user_id=self.target_id)
            except Exception as exc: QMessageBox.warning(self,"Contacto",str(exc)); return
            online="En línea" if info.get("online") else "Desconectado"
            QMessageBox.information(self,"Información del contacto",f"Nombre: {info.get('display_name','')}\nUsuario: @{info.get('username','')}\nEstado: {online}")
        elif self.scope=="group":
            try: members=self.network.request("group_members",group_id=self.target_id) or []
            except Exception as exc: QMessageBox.warning(self,"Grupo",str(exc)); return
            lines=[f"• {u['display_name']} (@{u['username']})" for u in members]
            QMessageBox.information(self,f"Integrantes de {self.target_name}","\n".join(lines) or "Sin integrantes")
        elif self.scope=="channel":
            c=next((x for x in self.channel_cache if x["id"]==self.target_id),{})
            QMessageBox.information(self,"Información del canal",f"Canal: {self.target_name}\nPropietario: @{c.get('owner_username','desconocido')}")

    def open_contact_from_message(self,url):
        try: uid=int(url.toString().split("://",1)[-1])
        except Exception:return
        if uid<=0:return
        try: info=self.network.request("contact_info",user_id=uid)
        except Exception as exc: QMessageBox.warning(self,"Contacto",str(exc)); return
        online="En línea" if info.get("online") else "Desconectado"
        QMessageBox.information(self,"Información del contacto",f"Nombre: {info.get('display_name','')}\nUsuario: @{info.get('username','')}\nEstado: {online}")

    def close_group_sessions(self):
        if self.scope!="group":return
        answer=QMessageBox.question(self,"Cerrar sesiones del grupo",
            "Se cerrará la sesión de Wasap de TODOS los integrantes de este grupo, incluido tú. No se eliminarán cuentas, integrantes ni mensajes. ¿Continuar?",
            QMessageBox.Yes|QMessageBox.No,QMessageBox.No)
        if answer!=QMessageBox.Yes:return
        try:
            self.network.request("group_logout_all",group_id=self.target_id)
        except Exception as exc:
            # El servidor puede cerrar la conexión inmediatamente después de enviar el evento.
            if self.network.running: QMessageBox.warning(self,"No se pudo cerrar las sesiones",str(exc))

    def create_group(self):
        name,ok=QInputDialog.getText(self,"Crear grupo","Nombre del grupo:")
        if ok and name.strip():
            try:
                data=self.network.request("group_create",name=name.strip())
                self.refresh_lists(); self.set_context("group",data["id"],data["name"],"Chat de grupo",True); self.load_history()
            except Exception as exc: QMessageBox.warning(self,"Grupo",str(exc))

    def create_channel(self):
        name,ok=QInputDialog.getText(self,"Crear canal","Nombre del canal:")
        if ok and name.strip():
            try:
                data=self.network.request("channel_create",name=name.strip())
                self.refresh_lists(); self.set_context("channel",data["id"],data["name"],"Canal",True); self.load_history()
            except Exception as exc: QMessageBox.warning(self,"Canal",str(exc))

    def edit_profile(self):
        dlg=ProfileDialog(self.network,self.user,self); dlg.profile_saved.connect(self.profile_updated); dlg.exec()

    def profile_updated(self,user):
        self.user=user; self.profile_button.setText(f"◉  {user['display_name']}"); self.setWindowTitle(f"Wasap — {user['display_name']}")

    def change_password(self):
        dlg=ChangePasswordDialog(self.network,self); dlg.username.setText(self.user.get("username",""))
        if dlg.exec():
            try:
                import keyring
                keyring.delete_password("WasapDesktop","remembered_device")
            except Exception: pass
            QMessageBox.information(self,"Seguridad","La contraseña cambió. Inicia sesión nuevamente.")
            self.normal_logout.emit()

    def logout(self):
        if QMessageBox.question(self,"Cerrar sesión","¿Deseas cerrar tu sesión en este equipo?",QMessageBox.Yes|QMessageBox.No)==QMessageBox.Yes:
            loading=OreoLoadingDialog("Cerrando sesión","Cerrando tu sesión de Wasap…",self); loading.show(); QApplication.processEvents()
            try: self.network.request("logout",device_token=self.device_token)
            except Exception: pass
            try:
                import keyring
                keyring.delete_password("WasapDesktop","remembered_device")
            except Exception: pass
            loading.close(); self.normal_logout.emit()

    def handle_event(self,packet):
        event=packet.get("event")
        if event=="message":
            scope=packet.get("scope")
            relevant=(scope=="general" and self.scope=="general") or (scope=="direct" and self.scope=="direct" and self.target_id in (packet.get("sender_id"),packet.get("recipient_id"))) or (scope in ("group","channel") and self.scope==scope and self.target_id==packet.get("target_id"))
            if relevant:
                self.append_message(packet.get("sender","Usuario"),packet.get("body",""),packet.get("created_at",""),packet.get("sender_id"))
        elif event=="session_terminated":
            try:
                import keyring
                keyring.delete_password("WasapDesktop","remembered_device")
            except Exception: pass
            self.forced_logout.emit(packet.get("reason","Tu sesión se cerró por una acción del grupo."))
        elif event=="group_member_added" and packet.get("group_id")==self.target_id:
            if self.scope=="group":
                self.subtitle.setText(f"Se agregó a @{packet.get('username','un usuario')} al grupo")
        elif event=="presence":
            self.refresh_lists()
