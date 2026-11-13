import json
import socket
import threading

class ClientConnection:
    def __init__(self, sock, address, handler):
        self.sock=sock
        self.address=address
        self.handler=handler
        self.send_lock=threading.Lock()
        self.auth_token=None
        self.alive=True

    def send(self, packet):
        raw=(json.dumps(packet,ensure_ascii=False,default=str)+"\n").encode("utf-8")
        with self.send_lock:
            self.sock.sendall(raw)

    def close(self):
        self.alive = False
        try:
            self.sock.shutdown(socket.SHUT_RDWR)
        except OSError:
            pass
        try:
            self.sock.close()
        except OSError:
            pass

    def run(self):
        buffer=b""
        try:
            while self.alive:
                chunk=self.sock.recv(4096)
                if not chunk: break
                buffer += chunk
                if len(buffer)>2_000_000:
                    raise ValueError("Paquete demasiado grande (máximo 2 MB).")
                while b"\n" in buffer:
                    line,buffer=buffer.split(b"\n",1)
                    if not line.strip(): continue
                    try:
                        msg=json.loads(line.decode("utf-8"))
                        if not isinstance(msg,dict): raise ValueError("Formato JSON inválido.")
                        self.handler.handle(self,msg)
                    except Exception as exc:
                        self.send({"ok":False,"error":str(exc)})
        except (ConnectionError, OSError):
            pass
        finally:
            self.alive=False
            self.handler.disconnect(self)
            try: self.sock.close()
            except OSError: pass

class SocketServer:
    def __init__(self, host, port, handler):
        self.host,self.port,self.handler=host,int(port),handler
        self.sock=None

    def broadcast(self, packet):
        # Difunde eventos globales (chat general y presencia) a todas las sesiones conectadas.
        for conns in list(self.handler.online.values()):
            for conn in list(conns):
                try: conn.send(packet)
                except Exception: pass

    def serve_forever(self):
        self.sock=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
        self.sock.bind((self.host,self.port))
        self.sock.listen(100)
        print(f"Wasap escuchando en {self.host}:{self.port} (TCP)")
        try:
            while True:
                client,address=self.sock.accept()
                print(f"Conexión: {address[0]}:{address[1]}")
                conn=ClientConnection(client,address,self.handler)
                threading.Thread(target=conn.run,daemon=True).start()
        except KeyboardInterrupt:
            print("Deteniendo servidor...")
        finally:
            self.sock.close()
