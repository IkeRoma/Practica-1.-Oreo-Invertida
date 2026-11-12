import os
from pathlib import Path
from dotenv import load_dotenv
from database import Database
from handlers import Handler
from socket_server import SocketServer

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / "config" / "server.env")
config = {
    "DB_HOST": os.getenv("DB_HOST", ""),
    "DB_PORT": os.getenv("DB_PORT", "1433"),
    "DB_NAME": os.getenv("DB_NAME", "wasap_db"),
    "DB_USER": os.getenv("DB_USER", "wasap_app"),
    "DB_PASSWORD": os.getenv("DB_PASSWORD", ""),
    "DB_DRIVER": os.getenv("DB_DRIVER", "ODBC Driver 18 for SQL Server"),
    "DB_ENCRYPT": os.getenv("DB_ENCRYPT", "yes"),
    "DB_TRUST_SERVER_CERTIFICATE": os.getenv("DB_TRUST_SERVER_CERTIFICATE", "yes"),
    "DB_CONNECTION_TIMEOUT": os.getenv("DB_CONNECTION_TIMEOUT", "8"),
}
if not config["DB_HOST"]:
    raise SystemExit("Falta DB_HOST. Configura config/server.env con el host o endpoint de SQL Server.")
if not config["DB_PASSWORD"]:
    raise SystemExit("Falta DB_PASSWORD. Configura config/server.env.")

try:
    db = Database(config)
    db.run("SELECT 1 AS connected")
    print(f"Conexión a Microsoft SQL Server establecida: {config['DB_HOST']}:{config['DB_PORT']}")
except Exception as exc:
    raise SystemExit(
        "No se pudo conectar a Microsoft SQL Server. Verifica endpoint, puerto 1433, "
        "Security Group, usuario, contraseña, base de datos y controlador ODBC.\n"
        f"Detalle técnico: {exc}"
    )

host = os.getenv("SERVER_HOST", "0.0.0.0")
port = int(os.getenv("SERVER_PORT", "3031"))
server = None
handler = Handler(db, lambda packet: server.broadcast(packet))
server = SocketServer(host, port, handler)
server.serve_forever()
