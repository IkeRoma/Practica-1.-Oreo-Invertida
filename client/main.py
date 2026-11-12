import os, sys
from pathlib import Path
from dotenv import load_dotenv
from PySide6.QtWidgets import QApplication, QMessageBox
from network import NetworkClient
from ui import LoginWidget, ChatWindow, STYLE

ROOT=Path(__file__).resolve().parents[1]
load_dotenv(ROOT/"config"/"client.env")
host=os.getenv("SERVER_HOST","127.0.0.1")
port=int(os.getenv("SERVER_PORT","3031"))

app=QApplication(sys.argv)
app.setApplicationName("Wasap")
app.setStyleSheet(STYLE)
network=NetworkClient(host,port)
try:
    network.connect_to_server()
except Exception as exc:
    QMessageBox.critical(None,"No se pudo conectar",
        f"No fue posible conectar con {host}:{port}.\\n\\n{exc}\\n\\nVerifica que el servidor Wasap esté activo y que el puerto TCP 3031 esté permitido.")
    sys.exit(1)

try:
    import keyring
    device_token=keyring.get_password("WasapDesktop","remembered_device") or ""
except Exception:
    keyring=None
    device_token=""

windows=[]
def on_authenticated(data):
    login.hide()
    chat=ChatWindow(network,data["user"],data.get("device_token",""))
    network.event_received.connect(chat.handle_event)
    chat.show()
    windows.append(chat)

# Si el usuario marcó "Recordar este dispositivo" anteriormente, intenta recuperar la sesión.
if device_token:
    try:
        data=network.request("device_resume",device_token=device_token)
        data["device_token"]=device_token
        login=None
        chat=ChatWindow(network,data["user"],device_token)
        network.event_received.connect(chat.handle_event)
        chat.show()
        windows.append(chat)
    except Exception:
        try:
            if keyring: keyring.delete_password("WasapDesktop","remembered_device")
        except Exception: pass
        login=LoginWidget(network)
        login.authenticated.connect(on_authenticated)
        login.show()
else:
    login=LoginWidget(network)
    login.authenticated.connect(on_authenticated)
    login.show()

exit_code=app.exec()
network.close()
sys.exit(exit_code)
