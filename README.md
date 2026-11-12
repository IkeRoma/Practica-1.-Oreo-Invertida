# Wasap — Cliente de escritorio

Cliente de mensajería de escritorio desarrollado con Python, PySide6 y sockets TCP. El cliente se conecta al servidor Wasap mediante TCP/JSON; no utiliza WebSockets.

## Funciones del cliente

- Inicio de sesión y registro.
- Chat general, conversaciones directas, grupos y canales en una sola ventana.
- Listas de conversaciones y selección desde el panel lateral.
- Mensajes agrupados por remitente, con hora visible.
- Información de contacto y consulta del perfil al pulsar el nombre del remitente en un grupo.
- Agregar integrantes desde el botón `+` dentro del grupo, sin mensajes automáticos al abrirlo.
- Cierre de sesión individual.
- Acción de grupo **«sálganse, quiero estar solo»**: cierra las sesiones Wasap activas de todos los integrantes conectados del grupo seleccionado. No elimina el grupo, sus integrantes ni el historial.
- Tema oscuro inspirado en Discord y animación de carga con una galleta Oreo giratoria.
- Empaquetado como aplicación de escritorio sin consola.

## Conexión

El cliente se conecta a la aplicación servidor por TCP **3031** (valor predeterminado). No se conecta directamente a SQL Server ni necesita instalar ODBC.

Edita `config/client.env.example`, o copia el archivo como `config/client.env`, y configura:

```env
SERVER_HOST=IP_O_DNS_DEL_SERVIDOR
SERVER_PORT=3031
```

No publiques `client.env` si contiene direcciones internas o datos privados.

## Ejecutar desde Python (Windows)

1. Instala Python 3.10 o superior.
2. Abre PowerShell en la carpeta del proyecto.
3. Ejecuta:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements-client.txt
Copy-Item config\client.env.example config\client.env
notepad config\client.env
python client\main.py
```

Si PowerShell bloquea la activación, ejecuta el programa con `.venv\Scripts\python.exe client\main.py`.

## Ejecutar desde Python (GNU/Linux)

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements-client.txt
cp config/client.env.example config/client.env
nano config/client.env
python client/main.py
```

## Ejecutar desde Python (macOS)

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements-client.txt
cp config/client.env.example config/client.env
open -e config/client.env
python client/main.py
```

## Crear la aplicación ejecutable

PyInstaller debe compilarse en el mismo sistema operativo y arquitectura en los que se ejecutará la aplicación. No se puede generar un `.exe` de Windows desde Linux o macOS con este procedimiento.

### Windows

Haz doble clic en `build_windows.bat`. El resultado estará en:

```text
dist/Wasap/Wasap.exe
```

Edita `dist/Wasap/config/client.env` para establecer `SERVER_HOST` y `SERVER_PORT`. Copia toda la carpeta `dist/Wasap` a la computadora donde se utilizará Wasap; no copies únicamente el `.exe`.

### GNU/Linux y macOS

```bash
chmod +x build_unix.sh
./build_unix.sh
```

El ejecutable se encontrará dentro de `dist/Wasap/`. Conserva junto con él el directorio `config` y sus archivos.

## Notas de compatibilidad

- El servidor debe estar actualizado con esta versión para soportar la acción de cierre grupal y la consulta de información de contacto.
- Los clientes antiguos no reconocen el evento de cierre grupal. Actualiza todos los clientes para obtener el comportamiento completo.
- La acción de cierre grupal afecta a las sesiones activas de todos los integrantes del grupo seleccionado, incluso si están conectados desde varios dispositivos.
- La aplicación debe poder alcanzar la IP/DNS del servidor y el puerto TCP 3031.
- Este paquete no contiene credenciales de SQL Server ni archivos `.env` reales.
