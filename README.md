# WASAP — Cliente de Mensajería

## 1. Descripción del proyecto

Wasap es una aplicación de mensajería instantánea desarrollada en Python, utilizando PySide6 para su interfaz gráfica y sockets TCP para la comunicación.

El cliente permite utilizar las funcionalidades de mensajería disponibles en la aplicación, incluyendo:

- Inicio de sesión y registro de usuarios.
- Administración del perfil personal.
- Cambio de contraseña.
- Fotografías de perfil.
- Conversaciones personales.
- Conversaciones grupales.
- Canales.
- Búsqueda de contactos.
- Visualización de información de usuarios.
- Notificaciones y visualización de mensajes.
- Administración de dispositivos recordados.
- Cierre de sesión.

Este documento contiene exclusivamente las instrucciones de instalación, configuración, ejecución y comprobación del cliente.

---

## 2. Requisitos del cliente

Para ejecutar Wasap se requiere:

- Python 3.10 o superior.
- pip (administrador de paquetes de Python).
- PySide6.
- Un sistema operativo compatible: Windows, GNU/Linux o macOS.
- Conexión a Internet para instalar las dependencias.
- Acceso de red al servicio Wasap.

### 2.1 Windows

Descarga Python desde:

https://www.python.org/downloads/windows/

También puedes instalarlo mediante Windows Package Manager:

```powershell
winget install Python.Python.3.12
```

Comprueba la instalación:

```powershell
py --version
py -m pip --version
```

### 2.2 GNU/Linux (Ubuntu/Debian)

Actualiza los repositorios:

```bash
sudo apt update
```

Instala Python 3, pip y las herramientas para crear entornos virtuales:

```bash
sudo apt install -y python3 python3-pip python3-venv
```

Instala las bibliotecas gráficas necesarias para PySide6:

```bash
sudo apt install -y libegl1 libgl1 libxkbcommon-x11-0 \
libxcb-cursor0 libdbus-1-3
```

Comprueba la instalación:

```bash
python3 --version
python3 -m pip --version
```

### 2.3 macOS

Se recomienda instalar Python mediante Homebrew.

Si todavía no tienes Homebrew, consulta:

https://brew.sh/

Instala Python:

```bash
brew install python@3.12
```

Comprueba la instalación:

```bash
python3 --version
python3 -m pip --version
```

---

## 3. Obtener y preparar el proyecto

Descarga o clona el repositorio de Wasap.

Si utilizas Git:

```bash
git clone https://github.com/IkeRoma/Practica-1.-Oreo-Invertida.git
```

Accede a la carpeta del proyecto:

```bash
cd Practica-1.-Oreo-Invertida
```

La estructura esperada del proyecto incluye:

```text
Practica-1.-Oreo-Invertida/
│
├── client/
│   ├── main.py
│   ├── ui.py
│   ├── network.py
│   └── ...
│
├── config/
│   └── client.env.example
│
├── requirements-client.txt
│
└── README.md
```

Los módulos adicionales y recursos gráficos deben conservarse dentro de sus respectivas carpetas.

---

## 4. Configurar el cliente

### 4.1 Crear el archivo de configuración

Copia el archivo de ejemplo y crea el archivo de configuración personal.

**Windows — PowerShell**

```powershell
Copy-Item config\client.env.example config\client.env
notepad config\client.env
```

**GNU/Linux / macOS**

```bash
cp config/client.env.example config/client.env
nano config/client.env
```

### 4.2 Configurar la conexión

Edita los valores correspondientes:

```env
SERVER_HOST=IP_PUBLICA_O_DNS_DEL_SERVICIO_WASAP
SERVER_PORT=3031
```

- `SERVER_HOST`: dirección IP o nombre DNS del servicio Wasap.
- `SERVER_PORT`: puerto TCP utilizado por el cliente para comunicarse.

Guarda los cambios.

**Importante:** no compartas `config/client.env` si contiene datos internos de tu infraestructura.

---

## 5. Crear el entorno virtual

Se recomienda utilizar un entorno virtual para mantener aisladas las dependencias del proyecto.

### 5.1 Windows

Desde la carpeta raíz:

```powershell
py -3 -m venv .venv
```

### 5.2 GNU/Linux

```bash
python3 -m venv .venv
```

### 5.3 macOS

```bash
python3 -m venv .venv
```

---

## 6. Activar el entorno virtual

Antes de instalar las dependencias o ejecutar Wasap, activa el entorno virtual.

### 6.1 Windows — PowerShell

```powershell
.\.venv\Scripts\Activate.ps1
```

Si PowerShell bloquea la ejecución del script:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

Después:

```powershell
.\.venv\Scripts\Activate.ps1
```

### 6.2 Windows — CMD

```cmd
.venv\Scripts\activate.bat
```

### 6.3 GNU/Linux

```bash
source .venv/bin/activate
```

### 6.4 macOS

```bash
source .venv/bin/activate
```

Cuando el entorno virtual esté activo, aparecerá `(.venv)` al principio de la terminal.

---

## 7. Instalar las dependencias

Con el entorno virtual activado, actualiza pip:

```bash
python -m pip install --upgrade pip
```

Instala PySide6:

```bash
python -m pip install PySide6
```

Instala las dependencias adicionales del cliente:

```bash
python -m pip install -r requirements-client.txt
```

Si PySide6 ya está incluido en `requirements-client.txt`, pip comprobará la versión instalada y resolverá las dependencias correspondientes.

### 7.1 Comprobar PySide6

Ejecuta:

```bash
python -c "from PySide6.QtWidgets import QApplication; print('PySide6 instalado correctamente')"
```

Si aparece el mensaje de confirmación, la biblioteca gráfica está disponible.

---

## 8. Ejecutar el cliente

Con el entorno virtual activado y la configuración lista, ejecuta Wasap desde la carpeta raíz.

### 8.1 Windows

```powershell
python client\main.py
```

### 8.2 GNU/Linux

```bash
python3 client/main.py
```

### 8.3 macOS

```bash
python3 client/main.py
```

La aplicación abrirá la ventana de inicio de sesión.

Desde ella podrás acceder a las funcionalidades disponibles de Wasap.

---

## 9. Desactivar el entorno virtual

Cuando termines de utilizar la aplicación, puedes desactivar el entorno virtual.

En cualquiera de las plataformas ejecuta:

```bash
deactivate
```

Para volver a ejecutar Wasap posteriormente, no necesitas crear nuevamente el entorno virtual. Solamente debes activarlo con el comando correspondiente a tu sistema operativo y ejecutar el cliente.

---

## 10. Pruebas y comprobaciones del cliente

Las siguientes comprobaciones permiten identificar errores de sintaxis, importaciones y nombres no definidos.

Se recomienda ejecutarlas desde la raíz del proyecto y con el entorno virtual activado.

### 10.1 Comprobar la sintaxis

```bash
python -m py_compile client/main.py client/network.py client/ui.py
```

Si no aparecen errores, los módulos indicados superaron la comprobación de sintaxis.

### 10.2 Instalar Pyflakes

```bash
python -m pip install pyflakes
```

### 10.3 Analizar el código del cliente

```bash
python -m pyflakes client/
```

Esta herramienta permite detectar:

- Nombres no definidos.
- Variables sin utilizar.
- Importaciones innecesarias.
- Otros problemas estáticos del código.

### 10.4 Comprobar las importaciones de PySide6

```bash
python -c "from PySide6.QtCore import QThread, QTimer; from PySide6.QtGui import QColor, QPainter, QPen, QPixmap, QTextCursor; from PySide6.QtWidgets import QApplication, QCheckBox, QDialog, QDialogButtonBox, QTextBrowser, QTreeWidget, QTreeWidgetItem; print('Dependencias gráficas verificadas')"
```

Estas comprobaciones no sustituyen las pruebas funcionales de inicio de sesión, mensajería, contactos, grupos y canales.

---

## 11. Seguridad

- No incluyas archivos de configuración con información sensible dentro de repositorios o paquetes compartidos.
- No almacenes contraseñas directamente en el código fuente.
- Protege los tokens de autenticación y los identificadores de dispositivo.
- Utiliza el almacén seguro de credenciales del sistema operativo cuando esté disponible.
- En GNU/Linux, `keyring` puede requerir un servicio Secret Service activo.
- No compartas fotografías o información personal de otros usuarios sin su autorización.

---

## 12. Solución de problemas

### 12.1 Python no se reconoce como comando

Comprueba que Python está instalado y agregado a la variable de entorno `PATH`.

En Windows:

```powershell
py --version
```

En GNU/Linux y macOS:

```bash
python3 --version
```

### 12.2 Error al activar el entorno virtual en PowerShell

Ejecuta:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

Después vuelve a activar el entorno:

```powershell
.\.venv\Scripts\Activate.ps1
```

### 12.3 Error al importar PySide6

Con el entorno virtual activado:

```bash
python -m pip install --upgrade PySide6
```

También puedes reinstalar las dependencias:

```bash
python -m pip install -r requirements-client.txt
```

### 12.4 La ventana no abre

Ejecuta temporalmente la aplicación desde una terminal:

```bash
python client/main.py
```

Esto permitirá visualizar los errores que se produzcan durante la ejecución.

Comprueba las dependencias y las bibliotecas gráficas del sistema operativo.

### 12.5 La aplicación no se conecta

Comprueba:

- Que `SERVER_HOST` tenga la dirección correcta.
- Que `SERVER_PORT` sea el puerto configurado.
- Que el servicio Wasap esté disponible.
- Que exista conectividad de red hacia el puerto TCP 3031.
- Que no haya reglas de firewall bloqueando la comunicación.

### 12.6 No recuerda el dispositivo

Comprueba que el almacén de credenciales del sistema operativo esté disponible.

También puedes iniciar sesión sin marcar la opción de recordar el dispositivo.

### 12.7 Error al encontrar `client.env`

Comprueba que el archivo exista en:

```text
config/client.env
```

Verifica que la aplicación utilice una ruta compatible con la carpeta desde la que se ejecuta.

---

## 13. Finalización

Una vez instaladas las dependencias, configurado el archivo `client.env` y activado el entorno virtual, Wasap estará listo para ejecutarse desde Python.

Para iniciar la aplicación nuevamente, basta con activar el entorno virtual y ejecutar el módulo principal del cliente.

**Wasap — Mensajería sencilla.**