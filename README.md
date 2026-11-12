# Wasap — Práctica 1: Programa Cliente-Servidor (versión 2)



Aplicación de mensajería de escritorio desarrollada en Python y PySide6. El servidor no tiene interfaz gráfica. La comunicación cliente-servidor utiliza sockets TCP persistentes con mensajes JSON delimitados por salto de línea; **no utiliza WebSockets**.


## Funciones



- Registro libre e inicio de sesión.
- Chat general.
- Mensajes directos entre usuarios.
- Creación de grupos; cualquier integrante puede agregar usuarios y enviar mensajes.
- Canales de difusión: todos pueden consultar y unirse; solo el propietario puede publicar.
- Historial persistente en SQL Server.
- Lista de usuarios y presencia básica.
- Foto de perfil opcional (se conserva como ruta local; no se transfiere a otros clientes en esta versión).
- Interfaz de escritorio PySide6 para Windows, GNU/Linux y macOS.



## Arquitectura y puertos
`Cliente PySide6 → TCP/JSON :3031 → Servidor Python → ODBC/TCP :1433 → Microsoft SQL Server 2022`

| Servicio | Puerto predeterminado | Configuración |

|---|---:|---|

| Servidor de mensajería Wasap | TCP 3031 | `SERVER_PORT` |

| Base de datos Microsoft SQL Server | TCP 1433 | `DB_PORT` |



El puerto 1433 **no** es el puerto al que se conectan los clientes Wasap. Los clientes se conectan a la IP/DNS del servidor de la aplicación y al puerto 3031. Solo el proceso servidor Wasap se conecta a SQL Server por el puerto 1433.


## Requisitos

- Python 3.10 o superior.
- Microsoft SQL Server 2022 con TCP/IP habilitado y autenticación de SQL Server habilitada.
- SQL Server accesible desde el servidor Wasap por TCP 1433.
- Microsoft ODBC Driver 18 for SQL Server instalado en la máquina donde se ejecuta el servidor Wasap.
- Puerto TCP 3031 permitido para los clientes.

### Instalación de dependencias del sistema (Windows vs. Linux)
#### En Windows

1. Instala Python 3.10+ asegurándote de marcar la casilla **"Add Python to PATH"**.

2. Descarga e instala el instalador `.msi` de **Microsoft ODBC Driver 18 for SQL Server** desde la documentación oficial de Microsoft.

3. Desde la raíz del proyecto, instala los paquetes de Python:

   ```powershell

   python -m venv .venv

   .venv\Scripts\Activate.ps1

   python -m pip install --upgrade pip

   pip install -r requirements.txt

   ```



#### En Ubuntu / Debian Linux (Servidor y Cliente)

En Linux es obligatorio instalar las cabeceras de compilación ODBC y el repositorio oficial de Microsoft para `msodbcsql18`. Además, si ejecutarás el cliente gráfico (`PySide6`), necesitarás las librerías gráficas del sistema.



1. **Instalar dependencias base y `unixodbc`:**

   ```bash

   sudo apt update

   sudo apt install -y python3-pip python3-venv curl gnupg2 apt-transport-https unixodbc unixodbc-dev

   ```



2. **Instalar Microsoft ODBC Driver 18 for SQL Server (Ejemplo para Ubuntu 22.04 / 24.04):**

   ```bash

   curl -fsSL https://packages.microsoft.com/keys/microsoft.asc | sudo gpg --dearmor -o /usr/share/keyrings/microsoft-prod.gpg

   curl -fsSL https://packages.microsoft.com/config/ubuntu/$(lsb_release -rs)/prod.list | sudo tee /etc/apt/sources.list.d/mssql-release.list

   sudo apt update

   sudo ACCEPT_EULA=Y apt install -y msodbcsql18

   # Opcional: instalar herramientas de línea de comandos (sqlcmd)

   sudo ACCEPT_EULA=Y apt install -y mssql-tools18

   echo 'export PATH="$PATH:/opt/mssql-tools18/bin"' >> ~/.bashrc

   source ~/.bashrc

   ```



3. **Verificar que el sistema reconoce el controlador ODBC:**

   ```bash

   odbcinst -q -d

   ```

   Debe aparecer `[ODBC Driver 18 for SQL Server]`.



4. **Dependencias adicionales SOLO si vas a ejecutar el Cliente GUI (PySide6) en Linux:**

   ```bash

   sudo apt install -y libxcb-cursor0 libgl1-mesa-glx libxkbcommon-x11-0 libdbus-1-3

   ```



5. **Crear entorno virtual e instalar requerimientos de Python (desde la raíz del proyecto):**

   ```bash

   python3 -m venv .venv

   source .venv/bin/activate

   python -m pip install --upgrade pip

   pip install -r requirements.txt

   ```



En macOS, instala el controlador ODBC de Microsoft y `unixodbc` mediante Homebrew según la documentación correspondiente.



## 1. Preparar SQL Server



### 1.1 Identificar la instancia AWS



Si no sabes qué instancia aloja SQL Server, entra a la consola de AWS y revisa EC2 o RDS:



- Si es EC2: identifica la instancia que tiene instalado SQL Server y toma su dirección IPv4 privada si el servidor Wasap está en la misma VPC. Si están en redes distintas, utiliza una ruta privada/VPN o el endpoint público solo si la arquitectura y las reglas de seguridad lo permiten.

- Si es RDS for SQL Server: utiliza el endpoint DNS que muestra RDS, no una IP fija.

- No supongas que `3.149.102.2` es necesariamente la dirección actual de la base de datos. Confirma el host en AWS.



### 1.2 Crear la base y las tablas



Abre SQL Server Management Studio (SSMS), Azure Data Studio o `sqlcmd` y ejecuta el archivo completo `database/schema.sql` con una cuenta que tenga permiso para crear bases y tablas. El script crea `wasap_db` y las tablas `users`, `groups_chat`, `group_members`, `channels`, `channel_members` y `messages`.



El archivo contiene separadores `GO`; ejecútalo desde SSMS/Azure Data Studio o `sqlcmd`, no como una única sentencia enviada desde `pyodbc`.



Ejemplo con `sqlcmd` (funciona igual en Windows CMD/PowerShell y en Linux Bash):



```bash

sqlcmd -S tcp:HOST_SQL_SERVER,1433 -U USUARIO_ADMIN -C -i database/schema.sql

```



Al omitir `-P`, `sqlcmd` solicita la contraseña de forma interactiva. No escribas contraseñas reales en el historial de la terminal.



### 1.3 Crear un login exclusivo para Wasap



No utilices la cuenta administradora de SQL Server desde la aplicación. Ejecuta el siguiente bloque como administrador, sustituyendo el secreto por una contraseña nueva y segura:



```sql

USE master;

GO

CREATE LOGIN [wasap_app]

WITH PASSWORD = N'REEMPLAZAR_POR_UN_SECRETO_FUERTE',

     CHECK_POLICY = ON,

     DEFAULT_DATABASE = [wasap_db];

GO

USE [wasap_db];

GO

CREATE USER [wasap_app] FOR LOGIN [wasap_app];

GO

GRANT SELECT, INSERT, UPDATE, DELETE ON SCHEMA::dbo TO [wasap_app];

GO

```



Si el login o usuario ya existe, no ejecutes de nuevo sus instrucciones `CREATE`; conserva el usuario existente y verifica sus permisos. El script de esquema debe ejecutarse antes de conceder permisos.



En SQL Server, confirma que esté habilitada la autenticación de SQL Server (modo mixto) y que el protocolo TCP/IP esté habilitado. Reinicia el servicio SQL Server si modificaste esos ajustes.



## 2. Configurar y ejecutar el servidor Wasap



### Paso 2.1: Archivo de configuración `.env`



**En Windows (PowerShell):**

```powershell

Copy-Item config\server.env.example config\server.env

notepad config\server.env

```



**En Linux (Bash):**

```bash

cp config/server.env.example config/server.env

nano config/server.env

```



Edita `config/server.env` con tus datos:



```env

SERVER_HOST=0.0.0.0

SERVER_PORT=3031



DB_HOST=ENDPOINT_O_IP_DE_SQL_SERVER

DB_PORT=1433

DB_NAME=wasap_db

DB_USER=wasap_app

DB_PASSWORD=TU_NUEVA_CONTRASENA

DB_DRIVER=ODBC Driver 18 for SQL Server

DB_ENCRYPT=yes

DB_TRUST_SERVER_CERTIFICATE=yes

DB_CONNECTION_TIMEOUT=8

```



Notas:

- `DB_HOST` debe ser el endpoint DNS o la dirección de la máquina que realmente aloja SQL Server. No incluyas `tcp:`, `:1433` ni una barra final; el programa construye la dirección con `DB_PORT`.

- Si ambas instancias EC2 están en la misma VPC, normalmente es preferible usar la IP privada o DNS privado de la instancia de base de datos.

- `DB_TRUST_SERVER_CERTIFICATE=yes` facilita una conexión cifrada cuando SQL Server usa un certificado autofirmado. Para producción, configura un certificado válido y utiliza `no`.

- No compartas ni subas `server.env` al repositorio.



### Paso 2.2: Iniciar el servidor



**En Windows (PowerShell):**

```powershell

python -m venv .venv

.venv\Scripts\Activate.ps1

pip install -r requirements.txt

cd server

python main.py

```



**En Linux (Bash - Ejecución directa):**

```bash

python3 -m venv .venv

source .venv/bin/activate

pip install -r requirements.txt

cd server

python3 main.py

```



**En Linux (Bash - Ejecución en segundo plano para servidores AWS EC2):**

Si te conectas por SSH a un servidor Linux en AWS, si cierras la terminal el servidor se detendrá. Para mantenerlo activo usa `nohup` o `tmux`:

```bash

source .venv/bin/activate

cd server

nohup python3 main.py > server.log 2>&1 &

# Para ver los registros en tiempo real:

tail -f server.log

```



## 3. Configuración AWS y firewall



En el Security Group de la instancia que aloja SQL Server, agrega una regla de entrada:

- Tipo: MS SQL (o regla personalizada TCP).

- Protocolo: TCP.

- Puerto: `1433`.

- Origen: el Security Group del servidor Wasap o la IP privada/CIDR estrictamente necesario.



No abras el puerto 1433 a `0.0.0.0/0`. Si SQL Server está en otra VPC, configura conectividad entre redes antes de usar una dirección privada.



En el firewall del sistema operativo de la base de datos, permite TCP 1433 desde el servidor Wasap. En SQL Server Configuration Manager, comprueba que TCP/IP esté habilitado y que la instancia escuche en el puerto esperado.



El Security Group del servidor Wasap debe permitir entrada TCP 3031 desde los equipos cliente. El firewall local del servidor también debe permitir ese puerto:



**En Windows (PowerShell como Administrador):**

```powershell

New-NetFirewallRule -DisplayName "Wasap Server 3031" -Direction Inbound -Protocol TCP -LocalPort 3031 -Action Allow

```



**En Ubuntu / Debian Linux (UFW):**

```bash

sudo ufw allow 3031/tcp

sudo ufw status

```



## 4. Configurar y ejecutar los clientes



Copia `config/client.env.example` como `config/client.env` en cada equipo cliente. Configura `SERVER_HOST` con la IP/DNS del **servidor Wasap**, no con el host de SQL Server:



```env

SERVER_HOST=IP_O_DNS_DEL_SERVIDOR_WASAP

SERVER_PORT=3031

```



Los clientes **no** necesitan instalar ODBC ni conectarse directamente a SQL Server.



**Ejecutar cliente en Windows (PowerShell):**

```powershell

Copy-Item config\client.env.example config\client.env

# Edita config\client.env con la IP del servidor

python -m venv .venv

.venv\Scripts\Activate.ps1

pip install -r requirements.txt

python client\main.py

```



**Ejecutar cliente en Linux (Bash con entorno de escritorio):**

```bash

cp config/client.env.example config/client.env

nano config/client.env

# Asegúrate de haber instalado libxcb-cursor0 y libgl1-mesa-glx (ver sección Requisitos)

python3 -m venv .venv

source .venv/bin/activate

pip install -r requirements.txt

python3 client/main.py

```



## 5. Verificación de conectividad



Desde el servidor Wasap, comprueba primero que el puerto de SQL Server sea alcanzable:



**En Windows (PowerShell):**

```powershell

Test-NetConnection -ComputerName ENDPOINT_O_IP_SQL_SERVER -Port 1433

```



**En Linux (Bash):**

```bash

nc -vz -w 5 ENDPOINT_O_IP_SQL_SERVER 1433

```



Si el puerto responde (`TcpTestSucceeded : True` en Windows o `succeeded!` en Linux), inicia Wasap. La consola debe mostrar `Conexión a Microsoft SQL Server establecida`. Si falla, revisa endpoint, Security Groups, NACL, firewall local, TCP/IP, autenticación SQL y el controlador ODBC.



Para comprobar el controlador instalado en Linux:

```bash

odbcinst -q -d

```



Para comprobar el controlador instalado en Windows (PowerShell):

```powershell

Get-OdbcDriver -Name "*SQL Server*"

```



## Protocolo de comunicación



Cada mensaje de protocolo es un objeto JSON UTF-8 terminado en `\n`. Cada solicitud incluye `action` y `request_id`. Las respuestas incluyen `request_id`, `ok` y, cuando corresponde, `data` o `error`. Los eventos no solicitados incluyen `event`.



## Seguridad y límites conocidos



- Las contraseñas de Wasap se almacenan con PBKDF2-HMAC-SHA256 y salt aleatorio; no se guardan en texto plano.

- La autenticación contra SQL Server usa un login dedicado configurado en el archivo `.env` del servidor.

- El transporte TCP entre clientes y Wasap no cifra los mensajes en esta versión. Para redes no confiables, incorpora TLS y validación de certificados.

- Las sesiones viven en memoria; después de reiniciar el servidor, cada usuario debe iniciar sesión otra vez.

- La foto de perfil se guarda como ruta local y no se sincroniza con otros clientes.

- La versión debe probarse en el entorno AWS real; la creación del paquete no garantiza que el endpoint, las reglas de red o las credenciales estén correctamente configurados.



## Estructura



```text

wasap/

├── client/

│   ├── main.py

│   ├── network.py

│   └── ui.py

├── server/

│   ├── main.py

│   ├── socket_server.py

│   ├── database.py

│   ├── auth.py

│   └── handlers.py

├── database/schema.sql

├── config/*.env.example

├── requirements.txt

├── LICENSE

└── README.md

```



## GitHub



1. Crea un repositorio público.

2. No subas `server.env`, `client.env`, contraseñas, tokens ni datos reales.

3. Ejecuta `git init`, `git add .`, `git commit -m "Wasap v2 SQL Server"` y conecta el remoto.

4. Conserva este README y la licencia MIT.