# Wasap V4 — Cliente de escritorio y servidor TCP

Wasap V4 integra **las dos entregas de mejoras**: conserva las funciones incorporadas en V3 (registro, validación de contraseñas, perfiles, fotografías y dispositivos recordados) y añade el rediseño de mensajería, navegación, información de contactos, agrupación de mensajes, animación Oreo y cierre de sesiones de grupo.

La arquitectura se mantiene: **Python + PySide6 (cliente), TCP/JSON (servidor), Microsoft SQL Server 2022 (persistencia)**. El cliente no se conecta directamente a SQL Server; se comunica con el servidor Wasap por TCP `3031`.

## Funciones incluidas de la primera modificación (V3)

- Ventanas separadas para iniciar sesión, registrar una cuenta y cambiar contraseña.
- Validación de contraseñas: al menos 10 caracteres, mayúscula, minúscula, número y símbolo.
- Perfil editable: nombre visible y fotografía.
- Selección de fotografía al registrarse y edición posterior.
- Token aleatorio por dispositivo y opción «Recordar este dispositivo» usando el almacén seguro del sistema operativo (`keyring`); no se almacena la contraseña.
- Búsqueda de contactos.
- Compatibilidad del código fuente con Windows, GNU/Linux y macOS.

## Funciones nuevas integradas en V4

1. Actualización inmediata de la vista de conversación al seleccionar un chat.
2. Botón `+` dentro de los grupos para agregar integrantes; abrir un grupo ya no pregunta si se desea agregar a alguien.
3. Panel lateral persistente con Chat general, mensajes directos, grupos y canales. Al seleccionar un elemento, la conversación aparece en el panel central.
4. Información del contacto desde el encabezado de un chat directo.
5. Nombres de remitentes seleccionables en mensajes grupales para consultar su contacto.
6. Hora de cada mensaje.
7. Agrupación de mensajes consecutivos del mismo remitente.
8. Scripts de empaquetado con PyInstaller para generar una aplicación de escritorio en el sistema operativo donde se compile.
9. Tema oscuro inspirado en Discord; «WASAP» y «Mensajería sencilla» centrados.
10. Botón **«sálganse, quiero estar solo»** en grupos. Tras confirmación, el servidor cierra todas las conexiones activas de todos los integrantes del grupo, invalida sus dispositivos recordados y los devuelve al inicio de sesión. No elimina cuentas, miembros, grupo ni historial.
11. Animación de carga con una galleta tipo Oreo giratoria en inicio y cierre de sesión.

## Estructura

```text
client/                 Cliente PySide6
server/                 Servidor TCP y lógica de negocio
config/                 Plantillas de configuración
 database/              Esquema y migración SQL Server
build_windows.bat       Empaquetado en Windows
build_unix.sh           Empaquetado en Linux/macOS
```

## 1. Actualización del servidor EC2

Haz una copia de seguridad de la carpeta del servidor y conserva tu `config/server.env` actual. No reemplaces ese archivo con una plantilla: contiene los datos de conexión de tu instalación.

Copia al servidor estos archivos de la versión V4:

- `server/handlers.py`
- `server/database.py`
- `server/socket_server.py`
- `server/auth.py` (se conserva la implementación PBKDF2 de V3)
- `server/main.py` (puedes conservar el actual si tiene la misma configuración de entorno)

La mejora de cierre de sesiones se ejecuta en el servidor y no requiere borrar ni recrear tablas. La consulta de historial ahora devuelve `sender_id`, por lo que el cliente puede agrupar y enlazar correctamente los mensajes.

En EC2, desde el directorio del servidor y con el entorno virtual activado:

```bash
python -m py_compile handlers.py database.py socket_server.py main.py
python main.py
```

Si el servidor se ejecuta como servicio `systemd`, reinicia el servicio con el nombre que tengas configurado. No abras el puerto SQL `1433` a los clientes: solamente el servidor Wasap debe comunicarse con SQL Server.

### Migración SQL necesaria si aún no instalaste V3

Si ya ejecutaste `database/migrations/003_profile_and_remembered_devices.sql` para V3, **no vuelvas a ejecutarla**. Si todavía no la ejecutaste, abre el script en SSMS y ejecútalo sobre `wasap_db`. Añade `avatar_data` y la tabla `remembered_devices`; no elimina mensajes, cuentas, grupos ni canales.

V4 no necesita una migración adicional para la desconexión grupal.

## 2. Configurar el cliente

Copia el archivo de ejemplo y edita el host del servidor Wasap (no el endpoint de SQL Server).

### Windows — PowerShell

```powershell
Copy-Item config\client.env.example config\client.env
notepad config\client.env
```

### GNU/Linux / macOS

```bash
cp config/client.env.example config/client.env
nano config/client.env
```

Contenido:

```env
SERVER_HOST=IP_PUBLICA_O_DNS_DEL_SERVIDOR_WASAP
SERVER_PORT=3031
```

No compartas `config/client.env` si contiene datos internos de tu infraestructura.

## 3. Ejecutar desde Python

Requiere Python 3.10 o superior.

### Windows

```powershell
py -3 -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements-client.txt
python client\main.py
```

### GNU/Linux

En Ubuntu/Debian, instala las dependencias gráficas y el llavero:

```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip libegl1 libgl1 \
  libxkbcommon-x11-0 libxcb-cursor0 libdbus-1-3 gnome-keyring
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements-client.txt
python3 client/main.py
```

### macOS

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements-client.txt
python3 client/main.py
```

## 4. Empaquetar como aplicación

PyInstaller debe ejecutarse **en el sistema operativo de destino**. Un ejecutable de Windows se compila en Windows; para macOS y Linux, compila en cada plataforma correspondiente.

### Windows

Ejecuta `build_windows.bat`. El resultado será `dist/Wasap/Wasap.exe` junto con sus dependencias. Copia la carpeta completa `Wasap`, no solo el `.exe`. Crea `dist/Wasap/config/client.env` a partir del ejemplo y configura `SERVER_HOST`.

### Linux / macOS

```bash
chmod +x build_unix.sh
./build_unix.sh
```

El resultado estará en `dist/Wasap/`. Configura `dist/Wasap/config/client.env` y ejecuta `dist/Wasap/Wasap` (en macOS puede ser necesario distribuirlo como `.app` mediante un empaquetador específico si se requiere integración nativa de Finder).

## 5. Pruebas locales

Desde la raíz del proyecto:

```bash
python -m py_compile client/main.py client/network.py client/ui.py server/main.py server/handlers.py server/database.py server/socket_server.py
python -m unittest discover -s . -p 'tests_group_logout.py' -v
```

Las pruebas unitarias de cierre grupal usan conexiones y base de datos simuladas. No sustituyen una prueba de integración con tu instancia real de SQL Server y EC2.

## 6. Seguridad y operación

- No incluyas `config/server.env` ni `config/client.env` con secretos dentro de repositorios o ZIP compartidos.
- Usa contraseñas fuertes para SQL Server y rota cualquier credencial que se haya compartido anteriormente en archivos de configuración.
- El botón de desconexión grupal afecta a todos los integrantes y todos sus dispositivos recordados; exige confirmación y no elimina datos.
- El token de dispositivo se almacena en el almacén seguro del sistema operativo. En Linux, `keyring` requiere un servicio Secret Service activo.
- El cliente necesita acceso TCP al puerto `3031` del servidor Wasap. No necesita ODBC ni acceso directo al puerto `1433`.

## 7. Solución de problemas

**No conecta:** verifica `SERVER_HOST`, `SERVER_PORT`, el estado del servidor y las reglas del firewall/Security Group para TCP `3031`.

**No recuerda el dispositivo:** comprueba el llavero del sistema operativo. Puedes seguir iniciando sesión sin marcar la casilla.

**La ventana no abre:** ejecuta temporalmente desde una terminal para ver el error, reinstala `requirements-client.txt` y comprueba las bibliotecas gráficas del sistema.

**Error de SQL Server:** el cliente no se conecta a SQL. Revisa `config/server.env`, ODBC Driver 18, el puerto `1433`, permisos del login y disponibilidad de `wasap_db` desde la máquina EC2.
