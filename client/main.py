"""Punto de entrada de Wasap Desktop. Administra reconexión tras cierre de sesión."""
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication, QMessageBox

from network import NetworkClient
from ui import LoginWidget, ChatWindow, STYLE, slide_in

ROOT = Path(sys.executable).resolve().parent if getattr(sys, "frozen", False) else Path(__file__).resolve().parents[1]
load_dotenv(ROOT / "config" / "client.env")
SERVER_HOST = os.getenv("SERVER_HOST", "127.0.0.1")
SERVER_PORT = int(os.getenv("SERVER_PORT", "3031"))


class WasapApplication:
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.app.setApplicationName("Wasap")
        self.app.setOrganizationName("Wasap")
        self.app.setStyleSheet(STYLE)
        self.network = None
        self.login = None
        self.chat = None
        self.device_token = ""

    def _new_connection(self):
        network = NetworkClient(SERVER_HOST, SERVER_PORT)
        network.connect_to_server()
        self.network = network
        return network

    def start(self):
        try:
            if not self.show_login(try_resume=True):
                return 1
        except Exception as exc:
            QMessageBox.critical(None, "No se pudo conectar",
                f"No fue posible conectar con {SERVER_HOST}:{SERVER_PORT}.\n\n{exc}\n\n"
                "Verifica que el servidor Wasap esté activo y que el puerto TCP 3031 esté permitido.")
            return 1
        return self.app.exec()

    def show_login(self, try_resume=False):
        if self.chat:
            try:
                self.network.event_received.disconnect(self.chat.handle_event)
            except Exception:
                pass
            self.chat.close()
            self.chat = None
        if self.network:
            self.network.close()
        try:
            network = self._new_connection()
        except Exception as exc:
            QMessageBox.critical(None, "No se pudo reconectar",
                f"No fue posible conectar con {SERVER_HOST}:{SERVER_PORT}.\n\n{exc}")
            return False

        token = ""
        try:
            import keyring
            token = keyring.get_password("WasapDesktop", "remembered_device") or ""
        except Exception:
            token = ""

        if try_resume and token:
            try:
                data = network.request("device_resume", device_token=token)
                data["device_token"] = token
                self.device_token = token
                self.show_chat(data)
                return True
            except Exception:
                try:
                    import keyring
                    keyring.delete_password("WasapDesktop", "remembered_device")
                except Exception:
                    pass

        self.login = LoginWidget(network, device_token="")
        self.login.authenticated.connect(self.show_chat)
        self.login.show()
        slide_in(self.login)
        return True

    def show_chat(self, data):
        if self.login:
            self.login.close()
            self.login = None
        self.device_token = data.get("device_token", "")
        self.chat = ChatWindow(self.network, data["user"], self.device_token)
        self.network.event_received.connect(self.chat.handle_event)
        self.chat.forced_logout.connect(self.on_forced_logout)
        self.chat.normal_logout.connect(self.on_normal_logout)
        self.chat.show()
        slide_in(self.chat)

    def on_forced_logout(self, reason):
        QMessageBox.warning(None, "Sesión cerrada", reason + "\n\nVuelve a iniciar sesión para continuar.")
        QTimer.singleShot(250, lambda: self.show_login(try_resume=False))

    def on_normal_logout(self):
        QTimer.singleShot(100, lambda: self.show_login(try_resume=False))


def main():
    return WasapApplication().start()


if __name__ == "__main__":
    sys.exit(main())
