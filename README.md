# Wasap — Práctica 1: Programa Cliente-Servidor

Aplicación de mensajería de escritorio desarrollada en Python y PySide6. El servidor no tiene interfaz gráfica. La comunicación cliente-servidor usa sockets TCP persistentes con mensajes JSON delimitados por salto de línea; **no utiliza WebSockets**.

## Funciones implementadas

- Registro libre e inicio de sesión.
- Chat general.
- Mensajes directos.
- Creación de grupos; cualquier integrante puede agregar usuarios y enviar mensajes.
- Canales de difusión: cualquier usuario puede consultar y unirse; solo el propietario publica.
- Historial persistente en MySQL.
- Lista de usuarios y presencia básica.
- Fotografía de perfil opcional (archivo local seleccionado en el cliente).
- Interfaz de escritorio estilo Discord, adaptable a Windows, GNU/Linux y macOS.

## Arquitectura

`Cliente PySide6 → TCP/JSON → Servidor Python → MySQL`

El servidor escucha por defecto en `0.0.0.0:3031`. El rango asignado es 3031–3040; el puerto se puede cambiar mediante `SERVER_PORT`.

## Requisitos

- Python 3.10 o superior.
- MySQL 8.x o MariaDB compatible.
- Acceso de red del servidor a MySQL.
- Puerto TCP 3031 permitido en el firewall del equipo servidor.
- Los clientes deben poder alcanzar la IP pública o DNS del servidor y el puerto TCP configurado.

## Instalación

### 1. Crear la base de datos

En el equipo que tiene MySQL, ejecutar el contenido de `database/schema.sql` con una cuenta que tenga permisos para crear la base y sus tablas:

```bash
mysql -h 3.149.102.2 -P 3306 -u administrador_con_permisos -p < database/schema.sql
```

**Seguridad:** no pongas la contraseña de administrador en este comando ni en archivos del repositorio. La contraseña compartida durante la conversación debe rotarse. Es preferible crear un usuario MySQL exclusivo para Wasap y concederle permisos solo sobre `wasap_db`.

Ejemplo (ejecutar como administrador MySQL, sustituyendo la contraseña por una nueva y segura):

```sql
CREATE USER 'wasap_app'@'IP_DEL_SERVIDOR' IDENTIFIED BY 'CAMBIAR_POR_UN_SECRETO_NUEVO';
GRANT SELECT, INSERT, UPDATE, DELETE, CREATE, ALTER, INDEX
ON wasap_db.* TO 'wasap_app'@'IP_DEL_SERVIDOR';
FLUSH PRIVILEGES;
```

Si el servidor de aplicación y MySQL están en máquinas distintas, restringe el acceso MySQL al IP del servidor de aplicación. No expongas MySQL a `0.0.0.0/0`.

### 2. Configurar el servidor

```bash
cd server
python -m venv .venv
```

Activar entorno:
- Windows PowerShell: `.venv\Scripts\Activate.ps1`
- Linux/macOS: `source .venv/bin/activate`

Instalar dependencias desde la raíz:
```bash
pip install -r ../requirements.txt
```

Copiar `config/server.env.example` a `config/server.env` y editarlo. Configuración inicial:
- `DB_HOST=3.149.102.2`
- `DB_PORT=3306`
- `DB_NAME=wasap_db`
- `DB_USER=wasap_app`
- `DB_PASSWORD=` (introducir el secreto nuevo del usuario de aplicación)
- `SERVER_HOST=0.0.0.0`
- `SERVER_PORT=3031`

Iniciar:
```bash
python main.py
```

El servidor imprime su dirección de escucha y registra errores en consola. No requiere GUI.

### 3. Configurar el cliente

En cada equipo cliente, crear un entorno virtual e instalar dependencias:

```bash
python -m venv .venv
# Activar el entorno como se explicó arriba
pip install -r requirements.txt
```

Copiar `config/client.env.example` a `config/client.env`. Configurar `SERVER_HOST` con la IP pública/DNS real del equipo donde corre el servidor y `SERVER_PORT=3031`.

Iniciar desde la raíz:
```bash
python client/main.py
```

## Probar en una sola computadora

Se puede ejecutar primero MySQL, luego el servidor y después uno o varios clientes. Para el cliente local usar `SERVER_HOST=127.0.0.1`.

## Firewall

Permitir **TCP 3031 entrante** en el equipo servidor. Ejemplo Ubuntu con UFW:

```bash
sudo ufw allow 3031/tcp
sudo ufw status
```

En Windows, crear una regla de entrada TCP para el puerto 3031. En el firewall de nube/proveedor, abrir también TCP 3031 únicamente a las redes que deban conectarse.

## Protocolo

Cada mensaje de protocolo es un objeto JSON UTF-8 terminado en `\n`. Cada solicitud incluye `action` y `request_id`. Las respuestas incluyen `request_id`, `ok` y, cuando corresponde, `data` o `error`. Los eventos no solicitados incluyen `event`.

## Seguridad y límites

- Las contraseñas se almacenan como hash PBKDF2-HMAC-SHA256 con salt aleatorio; nunca en texto plano.
- Las sesiones usan tokens aleatorios en memoria del servidor. Al reiniciar el servidor, el usuario debe iniciar sesión otra vez.
- El transporte TCP de esta primera versión no cifra el tráfico. Para uso fuera de una red controlada, se debe añadir TLS y validar certificados.
- La foto de perfil se selecciona localmente y se conserva como ruta local en esta versión; no se sincroniza a otros clientes.
- Para producción se recomienda límites de tamaño, rate limiting, TLS, rotación de secretos, copias de seguridad y pruebas de carga.
- El servidor necesita conectividad saliente a MySQL. No se puede confirmar desde este paquete que `3.149.102.2:3306` acepte conexiones remotas ni que las credenciales tengan permisos; hay que comprobarlo en el entorno real.

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
└── .gitignore
```

## GitHub

1. Crea un repositorio público.
2. No subas `server.env`, `client.env`, contraseñas, tokens ni archivos `.db`.
3. Ejecuta `git init`, `git add .`, `git commit -m "Primera versión de Wasap"` y conecta el remoto.
4. Conserva este README y la licencia MIT.
