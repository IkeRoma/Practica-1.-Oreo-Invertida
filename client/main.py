import os, sys
from pathlib import Path
from dotenv import load_dotenv
from PySide6.QtWidgets import QApplication, QMessageBox
from PySide6.QtCore import Qt
from network import NetworkClient
from ui import LoginWidget, ChatWindow, STYLE

ROOT = Path(sys.executable).resolve().parent if getattr(sys, "frozen", False) else Path(__file__).resolve().parents[1]
load_dotenv(ROOT/"config"/"client.env")
host=os.getenv("SERVER_HOST","127.0.0.1")
port=int(os.getenv("SERVER_PORT","3031"))

app=QApplication(sys.argv)
app.setStyleSheet(STYLE)
network=NetworkClient(host,port)
try:
    network.connect_to_server()
except Exception as exc:
    QMessageBox.critical(None,"No se pudo conectar",
        f"No fue posible conectar con {host}:{port}.\n\n{exc}\n\nVerifica el servidor, el puerto y el firewall.")
    sys.exit(1)

login=LoginWidget(network)
windows=[]
def on_authenticated(data):
    login.hide()
    chat=ChatWindow(network,data["user"])
    network.event_received.connect(chat.handle_event)
    def on_force_logout(reason):
        network.event_received.disconnect(chat.handle_event)
        chat.close()
        login.status.setText(reason + " Inicia sesión nuevamente.")
        login.show()
        login.raise_()
    chat.logged_out.connect(on_force_logout)
    chat.show()
    windows.append(chat)
login.authenticated.connect(on_authenticated)
login.show()
exit_code=app.exec()
network.close()
sys.exit(exit_code)
