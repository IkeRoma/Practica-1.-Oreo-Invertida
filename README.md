# Wasap — Cliente de escritorio (V3)

Esta guía contiene únicamente la instalación, configuración y ejecución del **cliente de escritorio** Wasap en Windows, GNU/Linux y macOS. El servidor y SQL Server se administran por separado.

## Requisitos

- Python 3.10 o superior (recomendado Python 3.11 o 3.12).
- Conexión de red con el servidor Wasap.
- Puerto TCP `3031` accesible desde el equipo cliente.
- Un entorno gráfico de escritorio (el cliente no funciona en una terminal SSH sin entorno gráfico).

El cliente se conecta al servidor Wasap por TCP/JSON. **No necesita conectarse a SQL Server, instalar ODBC ni conocer el puerto 1433.**

## 1. Descargar y descomprimir

Descarga el ZIP del proyecto y descomprímelo en una carpeta local. Abre una terminal en la carpeta raíz `Practica-1.-Oreo-Invertida`.

La carpeta debe contener, entre otros:

```text
client/
config/
requirements-client.txt
```

## 2. Configurar la dirección del servidor

Crea el archivo local `config/client.env` copiando el ejemplo.

### Windows — PowerShell

```powershell
Copy-Item config\client.env.example config\client.env
notepad config\client.env
```

### GNU/Linux — Bash

```bash
cp config/client.env.example config/client.env
nano config/client.env
```

### macOS — Terminal

```bash
cp config/client.env.example config/client.env
nano config/client.env
```

Edita el contenido:

```env
SERVER_HOST=IP_PUBLICA_O_DNS_DEL_SERVIDOR_WASAP
SERVER_PORT=3031
```

Sustituye el valor de `SERVER_HOST` por la IP pública o el DNS de la máquina donde está ejecutándose el **servidor Wasap**. No introduzcas la IP del servidor SQL Server. Si el cliente se ejecuta en el mismo equipo que el servidor Wasap, puedes usar `127.0.0.1`.

Guarda el archivo. No compartas `config/client.env` si contiene direcciones privadas de tu infraestructura.

## 3. Instalación y ejecución en Windows

1. Instala Python desde [python.org](https://www.python.org/downloads/). Durante la instalación activa **Add Python to PATH**.
2. Abre PowerShell en la raíz del proyecto.
3. Ejecuta:

```powershell
py -3 -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements-client.txt
python client\main.py
```

Si PowerShell bloquea la activación del entorno virtual, ejecuta lo siguiente en esa terminal y vuelve a activar:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.venv\Scripts\Activate.ps1
```

También puedes ejecutar el cliente sin activar el entorno:

```powershell
.venv\Scripts\python.exe client\main.py
```

## 4. Instalación y ejecución en GNU/Linux

Ejemplo para Ubuntu/Debian. Instala Python, el entorno virtual y las bibliotecas gráficas del sistema:

```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip \
  libegl1 libgl1 libxkbcommon-x11-0 libxcb-cursor0 libdbus-1-3 \
  gnome-keyring
```

Desde la raíz del proyecto:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements-client.txt
python3 client/main.py
```

Para que **Recordar este dispositivo** funcione, la sesión gráfica de Linux debe tener disponible un llavero compatible con Secret Service (por ejemplo, GNOME Keyring). No se guarda la contraseña de Wasap en el equipo.

## 5. Instalación y ejecución en macOS

1. Instala Python 3 desde [python.org](https://www.python.org/downloads/macos/) o mediante Homebrew:

```bash
brew install python
```

2. Abre Terminal en la raíz del proyecto y ejecuta:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements-client.txt
python3 client/main.py
```

macOS utiliza el llavero del sistema para guardar el identificador de dispositivo cuando se activa **Recordar este dispositivo**.

## 6. Funciones disponibles en esta versión

- Ventanas independientes para iniciar sesión, crear cuenta y cambiar contraseña.
- Validación de contraseña: mínimo 10 caracteres, una mayúscula, una minúscula, un número y un símbolo.
- Pantalla de espera mientras se validan las credenciales y notificación del resultado.
- Perfil para actualizar el nombre visible y la fotografía.
- Selector de fotografía personal.
- Opción **Recordar este dispositivo**, que guarda un token aleatorio en el almacén seguro del sistema operativo; no guarda la contraseña.
- Búsqueda de contactos por nombre o nombre de usuario.
- Interfaz renovada, estilos consistentes y transiciones de aparición.
- Chat general, mensajes directos, grupos y canales.

### Nota de actualización del servidor

Para activar las funciones nuevas de perfil/fotografía y dispositivos recordados, el administrador de SQL Server debe ejecutar una sola vez el script `database/migrations/003_profile_and_remembered_devices.sql` sobre la base `wasap_db`. Esta migración es incremental y no elimina mensajes, grupos, canales ni cuentas. El servidor Wasap también debe incorporar la versión V3 del protocolo incluida en este proyecto; sustituir únicamente el cliente no añade por sí mismo las operaciones nuevas al servidor.

## 7. Solución de problemas

**No se pudo conectar con el servidor**
- Comprueba que `SERVER_HOST` y `SERVER_PORT` estén escritos correctamente.
- Verifica que el servidor Wasap esté encendido y escuchando en TCP `3031`.
- Comprueba que el firewall y el Security Group permitan el puerto `3031` desde la IP del cliente.
- No uses el puerto SQL Server `1433` en el archivo del cliente.

**No se puede importar PySide6**
- Activa el entorno virtual correcto.
- Ejecuta `python -m pip install -r requirements-client.txt`.
- En Linux, instala las bibliotecas gráficas indicadas en la sección GNU/Linux.

**No se puede recordar el dispositivo**
- Windows: revisa que Credential Manager esté disponible.
- macOS: permite el acceso de Wasap al Llavero.
- Linux: inicia sesión en un escritorio con GNOME Keyring/Secret Service habilitado.
- Si el llavero no está disponible, puedes iniciar sesión sin marcar la casilla.

**La ventana no abre**
- Ejecuta el comando desde una terminal con entorno gráfico.
- Comprueba que estás usando Python de 64 bits y una versión compatible.
- Revisa el mensaje de error completo que aparece en la terminal.
