# WASAP — Cliente de Mensajería

## 1. Descripción del proyecto

Wasap es una aplicación de mensajería instantánea desarrollada en Python, utilizando PySide6 para su interfaz gráfica y sockets TCP para la comunicación.

El cliente permite utilizar las funcionalidades disponibles en la aplicación:

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

Este documento contiene exclusivamente las instrucciones de instalación de dependencias, configuración, ejecución y comprobación del cliente.

---

## 2. Instalación de dependencias

Antes de configurar o ejecutar Wasap, es necesario preparar el entorno de Python e instalar las bibliotecas requeridas por el cliente.

### 2.1 Requisitos generales

Se requiere:

- Python 3.10 o superior.
- pip.
- PySide6.
- Las dependencias adicionales especificadas en `requirements-client.txt`.
- Conexión a Internet para descargar las dependencias.
- Acceso de red al servidor Wasap.

### 2.2 Windows

Descarga Python desde:

https://www.python.org/downloads/windows/

También puedes instalarlo mediante Windows Package Manager:

```powershell
winget install Python.Python.3.12
```

Comprueba que Python y pip estén disponibles:

```powershell
py --version
py -m pip --version
```

Si ambos comandos muestran sus respectivas versiones, puedes continuar.

### 2.3 GNU/Linux (Ubuntu/Debian)

Actualiza los repositorios:

```bash
sudo apt update
```

Instala Python, pip y las herramientas para crear entornos virtuales:

```bash
sudo apt install -y python3 python3-pip python3-venv
```

Instala las bibliotecas del sistema necesarias para ejecutar PySide6:

```bash
sudo apt install -y \
    libegl1 \
    libgl1 \
    libxkbcommon-x11-0 \
    libxcb-cursor0 \
    libdbus-1-3
```

Comprueba la instalación:

```bash
python3 --version
python3 -m pip --version
```

**Importante: entorno gráfico**

Wasap utiliza PySide6 para mostrar ventanas. Por lo tanto, GNU/Linux debe contar con un entorno gráfico activo.

Si utilizas Ubuntu Desktop dentro de VirtualBox, puedes ejecutar el cliente desde una terminal abierta directamente en el escritorio de Ubuntu.

Si utilizas Ubuntu Server sin escritorio, una sesión SSH convencional no proporciona automáticamente una pantalla gráfica. En ese caso necesitarás configurar un entorno gráfico o utilizar reenvío X11.

### 2.4 macOS

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
git clone URL_DEL_REPOSITORIO
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

**Nota:** Los comandos siguientes deben ejecutarse desde la carpeta raíz del proyecto, salvo que se indique lo contrario.

---

## 4. Crear el entorno virtual

Se recomienda utilizar un entorno virtual para mantener aisladas las dependencias de Wasap y evitar conflictos con otras instalaciones de Python.

### 4.1 Windows

Desde PowerShell:

```powershell
py -3 -m venv .venv
```

### 4.2 GNU/Linux

```bash
python3 -m venv .venv
```

### 4.3 macOS

```bash
python3 -m venv .venv
```

---

## 5. Activar el entorno virtual

Antes de instalar las dependencias del proyecto, activa el entorno virtual.

### 5.1 Windows — PowerShell

```powershell
.\.venv\Scripts\Activate.ps1
```

Si PowerShell bloquea la ejecución del script, ejecuta:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

Después vuelve a activar el entorno:

```powershell
.\.venv\Scripts\Activate.ps1
```

### 5.2 Windows — CMD

```cmd
.venv\Scripts\activate.bat
```

### 5.3 GNU/Linux

```bash
source .venv/bin/activate
```

### 5.4 macOS

```bash
source .venv/bin/activate
```

Cuando el entorno virtual esté activo, aparecerá `(.venv)` al principio de la terminal.

---

## 6. Instalar las dependencias de Wasap

Con el entorno virtual activado, instala las dependencias del cliente.

Primero actualiza pip:

```bash
python -m pip install --upgrade pip
```

Después instala las dependencias declaradas en `requirements-client.txt`:

```bash
python -m pip install -r requirements-client.txt
```

Este archivo contiene las bibliotecas Python requeridas por el cliente.

Si PySide6 no se encuentra declarado en dicho archivo, instálalo manualmente:

```bash
python -m pip install PySide6
```

**Importante:** No es necesario instalar las dependencias del servidor ni las bibliotecas correspondientes a la base de datos para ejecutar únicamente el cliente, salvo que alguna dependencia esté expresamente declarada en `requirements-client.txt`.

### 6.1 Comprobar PySide6

Ejecuta:

```bash
python -c "from PySide6.QtWidgets import QApplication; print('PySide6 instalado correctamente')"
```

Si aparece el mensaje:

```text
PySide6 instalado correctamente
```

la biblioteca gráfica está disponible para Python.

### 6.2 Comprobar las importaciones gráficas

Ejecuta:

```bash
python -c "from PySide6.QtCore import QThread, QTimer; from PySide6.QtGui import QColor, QPainter, QPen, QPixmap, QTextCursor; from PySide6.QtWidgets import QApplication, QCheckBox, QDialog, QDialogButtonBox, QTextBrowser, QTreeWidget, QTreeWidgetItem; print('Dependencias gráficas verificadas')"
```

Si no aparecen errores, las clases indicadas pueden importarse correctamente.

---

## 7. Configurar el cliente

### 7.1 Crear el archivo de configuración

Copia el archivo de ejemplo y crea tu archivo de configuración personal.

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

### 7.2 Configurar la conexión

Edita los valores correspondientes:

```env
SERVER_HOST=IP_PUBLICA_O_DNS_DEL_SERVICIO_WASAP
SERVER_PORT=3031
```

Sustituye `SERVER_HOST` por la dirección IP o el nombre DNS del servidor Wasap.

El puerto `3031` corresponde al servicio de comunicación del servidor.

Guarda los cambios.

**Importante:** El cliente debe poder alcanzar la dirección configurada mediante la red. También deben estar permitidas las conexiones TCP hacia el puerto correspondiente en las reglas de firewall y seguridad del servidor.

---

## 8. Ejecutar el cliente

Antes de iniciar Wasap, verifica que:

1. El entorno virtual esté activado.
2. Las dependencias estén instaladas.
3. Exista el archivo `config/client.env`.
4. La dirección del servidor esté configurada correctamente.
5. El equipo tenga acceso de red al servidor.
6. Exista un entorno gráfico disponible para mostrar la interfaz.

Ejecuta el cliente desde la carpeta raíz del proyecto.

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

## 9. Ejecución en una máquina virtual de VirtualBox

Wasap puede ejecutarse dentro de una máquina virtual de VirtualBox siempre que el sistema operativo invitado tenga las dependencias instaladas y disponga de un entorno gráfico.

### 9.1 Ubuntu Desktop en VirtualBox

Si utilizas Ubuntu Desktop:

1. Inicia la máquina virtual.
2. Accede al escritorio de Ubuntu.
3. Abre una terminal directamente desde el escritorio.
4. Accede a la carpeta del proyecto.
5. Activa el entorno virtual.
6. Ejecuta el cliente.

Ejemplo:

```bash
cd Practica-1.-Oreo-Invertida
source .venv/bin/activate
python3 client/main.py
```

En este escenario, la ventana de Wasap aparecerá dentro del escritorio de Ubuntu.

### 9.2 Ubuntu Server en VirtualBox

Ubuntu Server normalmente no incluye un escritorio gráfico.

Por ello, ejecutar:

```bash
python3 client/main.py
```

desde una terminal sin pantalla gráfica puede producir errores como:

```text
qt.qpa.xcb: could not connect to display
```

Este error indica que Qt no puede conectarse a un servidor gráfico.

Para ejecutar Wasap en Ubuntu Server será necesario instalar y configurar un entorno gráfico o utilizar un mecanismo de visualización remota compatible, como el reenvío X11.

### 9.3 Comprobar la disponibilidad de la pantalla gráfica

En GNU/Linux ejecuta:

```bash
echo $DISPLAY
```

Si el resultado está vacío, la sesión actual no tiene una variable de pantalla gráfica configurada.

Si ejecutas el cliente directamente desde una terminal del escritorio de Ubuntu, normalmente aparecerá un valor como:

```text
:0
```

La disponibilidad de `DISPLAY` es una comprobación orientativa; no garantiza por sí sola que todas las bibliotecas gráficas estén correctamente instaladas.

### 9.4 Conexión de la máquina virtual con el servidor

Si Wasap se ejecuta en VirtualBox y el servidor está alojado en otra máquina, la máquina virtual debe tener conectividad hacia la dirección del servidor.

Comprueba:

- Que VirtualBox tenga una configuración de red que permita acceder a Internet o a la red del servidor.
- Que `SERVER_HOST` contenga la dirección correcta.
- Que `SERVER_PORT` corresponda al puerto del servicio.
- Que las reglas de seguridad del servidor permitan conexiones desde la red de origen del cliente.

La configuración NAT de VirtualBox normalmente permite conexiones salientes, aunque las reglas de red y firewall del entorno pueden modificar este comportamiento.

---

## 10. Desactivar el entorno virtual

Cuando termines de utilizar la aplicación, puedes desactivar el entorno virtual.

En cualquiera de las plataformas ejecuta:

```bash
deactivate
```

Para volver a ejecutar Wasap posteriormente, no necesitas crear nuevamente el entorno virtual ni reinstalar las dependencias.

Solamente debes:

1. Acceder a la carpeta del proyecto.
2. Activar el entorno virtual.
3. Ejecutar el cliente.

---

## 11. Pruebas y comprobaciones del cliente

Las siguientes comprobaciones permiten identificar errores de sintaxis, importaciones y nombres no definidos.

Se recomienda ejecutarlas desde la raíz del proyecto y con el entorno virtual activado.

### 11.1 Comprobar la sintaxis

```bash
python -m py_compile client/main.py client/network.py client/ui.py
```

Si no aparecen errores, los módulos indicados superaron la comprobación de sintaxis.

### 11.2 Instalar Pyflakes

```bash
python -m pip install pyflakes
```

### 11.3 Analizar el código del cliente

```bash
python -m pyflakes client/
```

Esta herramienta permite detectar:

- Nombres no definidos.
- Variables sin utilizar.
- Importaciones innecesarias.
- Otros problemas estáticos del código.

**Nota:** Pyflakes es una herramienta de revisión del código y no es necesaria para ejecutar Wasap.

### 11.4 Comprobar las importaciones de PySide6

```bash
python -c "from PySide6.QtCore import QThread, QTimer; from PySide6.QtGui import QColor, QPainter, QPen, QPixmap, QTextCursor; from PySide6.QtWidgets import QApplication, QCheckBox, QDialog, QDialogButtonBox, QTextBrowser, QTreeWidget, QTreeWidgetItem; print('Dependencias gráficas verificadas')"
```

Estas comprobaciones no sustituyen las pruebas funcionales de inicio de sesión, mensajería, contactos, grupos y canales.

---

## 12. Seguridad

- No incluyas archivos de configuración con información sensible dentro de repositorios o paquetes compartidos.
- No almacenes contraseñas directamente en el código fuente.
- Protege los tokens de autenticación y los identificadores de dispositivo.
- Utiliza el almacén seguro de credenciales del sistema operativo cuando esté disponible.
- En GNU/Linux, `keyring` puede requerir un servicio Secret Service activo.
- No compartas fotografías o información personal de otros usuarios sin su autorización.

---

## 13. Solución de problemas

### 13.1 Python no se reconoce como comando

Comprueba que Python está instalado y agregado a la variable de entorno `PATH`.

En Windows:

```powershell
py --version
```

En GNU/Linux y macOS:

```bash
python3 --version
```

### 13.2 Error al activar el entorno virtual en PowerShell

Ejecuta:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

Después vuelve a activar el entorno:

```powershell
.\.venv\Scripts\Activate.ps1
```

### 13.3 Error al importar PySide6

Con el entorno virtual activado, ejecuta:

```bash
python -m pip install --upgrade PySide6
```

También puedes reinstalar las dependencias:

```bash
python -m pip install -r requirements-client.txt
```

### 13.4 La ventana no abre

Ejecuta la aplicación desde una terminal:

```bash
python client/main.py
```

Esto permitirá visualizar los errores que se produzcan durante la ejecución.

Comprueba:

- Que PySide6 esté instalado en el entorno virtual activo.
- Que las bibliotecas gráficas del sistema operativo estén instaladas.
- Que exista una sesión gráfica disponible.
- Que no estés ejecutando el cliente desde una sesión SSH sin reenvío gráfico.

### 13.5 Error `could not connect to display`

Este error suele aparecer cuando PySide6 intenta abrir una ventana, pero no encuentra un servidor gráfico disponible.

Si utilizas VirtualBox con Ubuntu Desktop, abre una terminal directamente desde el escritorio de Ubuntu y ejecuta Wasap desde allí.

Si utilizas Ubuntu Server o una sesión SSH, necesitarás configurar un entorno gráfico o un mecanismo de visualización remota.

Instalar las bibliotecas de Qt no sustituye la necesidad de disponer de una pantalla gráfica.

### 13.6 Error relacionado con `xcb` o `xcb-cursor0`

En Ubuntu/Debian instala:

```bash
sudo apt update
sudo apt install -y \
    libegl1 \
    libgl1 \
    libxkbcommon-x11-0 \
    libxcb-cursor0 \
    libdbus-1-3
```

Después vuelve a ejecutar el cliente desde una sesión gráfica disponible.

### 13.7 La aplicación no se conecta

Comprueba:

- Que `SERVER_HOST` tenga la dirección correcta.
- Que `SERVER_PORT` sea el puerto configurado.
- Que el servicio Wasap esté disponible.
- Que exista conectividad de red hacia el puerto TCP 3031.
- Que no haya reglas de firewall bloqueando la comunicación.

### 13.8 No recuerda el dispositivo

Comprueba que el almacén de credenciales del sistema operativo esté disponible.

También puedes iniciar sesión sin marcar la opción de recordar el dispositivo.

### 13.9 Error al encontrar `client.env`

Comprueba que el archivo exista en:

```text
config/client.env
```

Verifica que la aplicación utilice una ruta compatible con la carpeta desde la que se ejecuta.

---

## 14. Finalización

Una vez instaladas las dependencias, creado el entorno virtual, configurado el archivo `client.env` y comprobada la disponibilidad de la interfaz gráfica, Wasap estará listo para ejecutarse desde Python.

Para iniciar la aplicación nuevamente, basta con activar el entorno virtual y ejecutar el módulo principal del cliente.

**Wasap — Mensajería sencilla.**