# Wasap — Práctica 1: Programa Cliente-Servidor (versión 2)

Aplicación de mensajería de escritorio desarrollada en Python y PySide6. El servidor no tiene interfaz gráfica. La comunicación cliente-servidor utiliza sockets TCP persistentes con mensajes JSON delimitados por salto de línea; **no utiliza WebSockets**.

Esta versión utiliza **Microsoft SQL Server 2022** como base de datos, mediante `pyodbc` y Microsoft ODBC Driver 18 for SQL Server. El puerto predeterminado de SQL Server es **1433**. El servidor de la aplicación Wasap escucha en **3031** (puerto de aplicación, independiente del puerto de la base de datos).

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
- Microsoft ODBC Driver 18 for SQL Server instalado en la máquina donde se ejecuta Wasap.
- Puerto TCP 3031 permitido para los clientes.

### Instalar dependencias Python en Ubuntu/Linux

```bash
sudo apt update
sudo apt install -y unixodbc unixodbc-dev
```

Instala además **Microsoft ODBC Driver 18 for SQL Server** siguiendo la documentación oficial de Microsoft para tu versión de Ubuntu. Comprueba que el sistema lo reconoce:

```bash
odbcinst -q -d
```

Debe aparecer `ODBC Driver 18 for SQL Server`. Después, desde la raíz del proyecto y dentro del entorno virtual:

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

En Windows, instala Microsoft ODBC Driver 18 for SQL Server y después ejecuta `pip install -r requirements.txt`. En macOS, instala el controlador ODBC de Microsoft y unixODBC según la documentación correspondiente.

## 1. Preparar SQL Server

### 1.1 Identificar la instancia AWS

Si no sabes qué instancia aloja SQL Server, entra a la consola de AWS y revisa EC2 o RDS:

- Si es EC2: identifica la instancia que tiene instalado SQL Server y toma su dirección IPv4 privada si el servidor Wasap está en la misma VPC. Si están en redes distintas, utiliza una ruta privada/VPN o el endpoint público solo si la arquitectura y las reglas de seguridad lo permiten.
- Si es RDS for SQL Server: utiliza el endpoint DNS que muestra RDS, no una IP fija.
- No supongas que `3.149.102.2` es necesariamente la dirección actual de la base de datos. Confirma el host en AWS.

### 1.2 Crear la base y las tablas

Abre SQL Server Management Studio (SSMS), Azure Data Studio o `sqlcmd` y ejecuta el archivo completo `database/schema.sql` con una cuenta que tenga permiso para crear bases y tablas. El script crea `wasap_db` y las tablas `users`, `groups_chat`, `group_members`, `channels`, `channel_members` y `messages`.

El archivo contiene separadores `GO`; ejecútalo desde SSMS/Azure Data Studio o `sqlcmd`, no como una única sentencia enviada desde pyodbc.

Ejemplo con `sqlcmd` (ajusta host y usuario):

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

## 2. Configurar el servidor Wasap

Copia `config/server.env.example` como `config/server.env` y edítalo:

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

Instala dependencias e inicia el servidor:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cd server
python main.py
```

En Windows PowerShell, activa el entorno con `.venv\\Scripts\\Activate.ps1`.

## 3. Configuración AWS y firewall

En el Security Group de la instancia que aloja SQL Server, agrega una regla de entrada:

- Tipo: MS SQL (o regla personalizada TCP).
- Protocolo: TCP.
- Puerto: `1433`.
- Origen: el Security Group del servidor Wasap o la IP privada/CIDR estrictamente necesario.

No abras el puerto 1433 a `0.0.0.0/0`. Si SQL Server está en otra VPC, configura conectividad entre redes antes de usar una dirección privada.

En el firewall del sistema operativo de la base de datos, permite TCP 1433 desde el servidor Wasap. En SQL Server Configuration Manager, comprueba que TCP/IP esté habilitado y que la instancia escuche en el puerto esperado.

El Security Group del servidor Wasap debe permitir entrada TCP 3031 desde los equipos cliente. El firewall local también debe permitir ese puerto. Ejemplo Ubuntu:

```bash
sudo ufw allow 3031/tcp
sudo ufw status
```

## 4. Configurar los clientes

Copia `config/client.env.example` como `config/client.env` en cada equipo cliente. Configura `SERVER_HOST` con la IP/DNS del **servidor Wasap**, no con el host de SQL Server:

```env
SERVER_HOST=IP_O_DNS_DEL_SERVIDOR_WASAP
SERVER_PORT=3031
```

Instala Python, las dependencias del proyecto y ejecuta desde la raíz:

```bash
pip install -r requirements.txt
python client/main.py
```

Los clientes no necesitan instalar ODBC ni conectarse directamente a SQL Server.

## 5. Verificación de conectividad

Desde el servidor Wasap, comprueba primero el puerto de SQL Server:

```bash
nc -vz -w 5 ENDPOINT_O_IP_SQL_SERVER 1433
```

Si el puerto responde, inicia Wasap. La consola debe mostrar `Conexión a Microsoft SQL Server establecida`. Si falla, revisa endpoint, Security Groups, NACL, firewall local, TCP/IP, autenticación SQL y el controlador ODBC.

Para comprobar el controlador instalado:

```bash
odbcinst -q -d
```

## Protocolo de comunicación

Cada mensaje de protocolo es un objeto JSON UTF-8 terminado en `\\n`. Cada solicitud incluye `action` y `request_id`. Las respuestas incluyen `request_id`, `ok` y, cuando corresponde, `data` o `error`. Los eventos no solicitados incluyen `event`.

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
