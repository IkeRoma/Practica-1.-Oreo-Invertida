import json, os, socket, threading, uuid
from PySide6.QtCore import QObject, Signal

class NetworkClient(QObject):
    event_received=Signal(dict)
    disconnected=Signal(str)

    def __init__(self, host, port):
        super().__init__()
        self.host,self.port=host,int(port)
        self.sock=None
        self.lock=threading.Lock()
        self.pending={}
        self.running=False

    def connect_to_server(self):
        self.sock=socket.create_connection((self.host,self.port),timeout=8)
        self.sock.settimeout(None)
        self.running=True
        threading.Thread(target=self._reader,daemon=True).start()

    def _reader(self):
        buffer=b""
        try:
            while self.running:
                chunk=self.sock.recv(4096)
                if not chunk: break
                buffer += chunk
                while b"\n" in buffer:
                    line,buffer=buffer.split(b"\n",1)
                    if not line.strip(): continue
                    packet=json.loads(line.decode("utf-8"))
                    rid=packet.get("request_id")
                    if rid and rid in self.pending:
                        event=self.pending[rid]
                        event["result"]=packet
                        event["signal"].set()
                    else:
                        self.event_received.emit(packet)
        except Exception as exc:
            if self.running: self.disconnected.emit(str(exc))
        finally:
            self.running=False
            for item in list(self.pending.values()):
                item["result"]={"ok":False,"error":"Conexión cerrada."}
                item["signal"].set()
            self.disconnected.emit("Conexión cerrada.")

    def request(self, action, **kwargs):
        if not self.running: raise ConnectionError("No hay conexión con el servidor.")
        rid=uuid.uuid4().hex
        import threading as th
        signal=th.Event()
        self.pending[rid]={"signal":signal}
        packet={"action":action,"request_id":rid,**kwargs}
        raw=(json.dumps(packet,ensure_ascii=False)+"\n").encode("utf-8")
        try:
            with self.lock: self.sock.sendall(raw)
        except Exception:
            self.pending.pop(rid,None)
            raise
        if not signal.wait(12):
            self.pending.pop(rid,None)
            raise TimeoutError("El servidor tardó demasiado en responder.")
        result=self.pending.pop(rid,{}).get("result",{})
        if not result.get("ok"):
            raise RuntimeError(result.get("error","Error del servidor."))
        return result.get("data")

    def close(self):
        self.running=False
        try: self.sock.shutdown(socket.SHUT_RDWR)
        except Exception: pass
        try: self.sock.close()
        except Exception: pass
