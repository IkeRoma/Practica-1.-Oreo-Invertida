# Wasap — Cliente de escritorio (V3)

Esta guía contiene únicamente la instalación, configuración y ejecución del **cliente de escritorio** Wasap en Windows, GNU/Linux y macOS. El servidor y SQL Server se administran por separado.

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