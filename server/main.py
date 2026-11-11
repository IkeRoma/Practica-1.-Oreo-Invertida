import os
from pathlib import Path
from dotenv import load_dotenv
from database import Database
from handlers import Handler
from socket_server import SocketServer

ROOT=Path(__file__).resolve().parents[1]
load_dotenv(ROOT/"config"/"server.env")
config={
    "DB_HOST":os.getenv("DB_HOST","3.149.102.2"),
    "DB_PORT":os.getenv("DB_PORT","3306"),
    "DB_NAME":os.getenv("DB_NAME","wasap_db"),
    "DB_USER":os.getenv("DB_USER","wasap_app"),
    "DB_PASSWORD":os.getenv("DB_PASSWORD",""),
}
if not config["DB_PASSWORD"]:
    raise SystemExit("Falta DB_PASSWORD. Configura config/server.env.")
try:
    db=Database(config)
    db.run("SELECT 1")
except Exception as exc:
    raise SystemExit(f"No se pudo conectar a MySQL: {exc}")
host=os.getenv("SERVER_HOST","0.0.0.0")
port=int(os.getenv("SERVER_PORT","3031"))
server=None
handler=Handler(db,lambda packet: server.broadcast(packet))
server=SocketServer(host,port,handler)
server.serve_forever()
