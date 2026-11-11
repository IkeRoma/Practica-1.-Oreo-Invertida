-- 1. Crear la base de datos si no existe (Verificando en las vistas del sistema)
IF NOT EXISTS (SELECT * FROM sys.databases WHERE name = 'wasap_db')
BEGIN
    CREATE DATABASE wasap_db;
END
GO

USE wasap_db;
GO

-- 2. Tabla users
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'users')
BEGIN
    CREATE TABLE users (
        id BIGINT IDENTITY(1,1) PRIMARY KEY,
        username VARCHAR(32) NOT NULL UNIQUE,
        password_hash VARCHAR(255) NOT NULL,
        display_name VARCHAR(64) NOT NULL,
        avatar_path VARCHAR(512) NULL,
        created_at DATETIME2 NOT NULL DEFAULT GETDATE()
    );
END
GO

-- 3. Tabla groups_chat
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'groups_chat')
BEGIN
    CREATE TABLE groups_chat (
        id BIGINT IDENTITY(1,1) PRIMARY KEY,
        name VARCHAR(80) NOT NULL,
        owner_id BIGINT NOT NULL,
        created_at DATETIME2 NOT NULL DEFAULT GETDATE(),
        FOREIGN KEY (owner_id) REFERENCES users(id)
    );
END
GO

-- 4. Tabla group_members
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'group_members')
BEGIN
    CREATE TABLE group_members (
        group_id BIGINT NOT NULL,
        user_id BIGINT NOT NULL,
        joined_at DATETIME2 NOT NULL DEFAULT GETDATE(),
        PRIMARY KEY (group_id, user_id),
        FOREIGN KEY (group_id) REFERENCES groups_chat(id) ON DELETE CASCADE,
        FOREIGN KEY (user_id) REFERENCES users(id) -- Nota: En SQL Server se evita cascada múltiple en la misma tabla para prevenir rutas circulares, pero se mantiene la lógica básica.
    );
END
GO

-- 5. Tabla channels
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'channels')
BEGIN
    CREATE TABLE channels (
        id BIGINT IDENTITY(1,1) PRIMARY KEY,
        name VARCHAR(80) NOT NULL UNIQUE,
        owner_id BIGINT NOT NULL,
        created_at DATETIME2 NOT NULL DEFAULT GETDATE(),
        FOREIGN KEY (owner_id) REFERENCES users(id)
    );
END
GO

-- 6. Tabla channel_members
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'channel_members')
BEGIN
    CREATE TABLE channel_members (
        channel_id BIGINT NOT NULL,
        user_id BIGINT NOT NULL,
        joined_at DATETIME2 NOT NULL DEFAULT GETDATE(),
        PRIMARY KEY (channel_id, user_id),
        FOREIGN KEY (channel_id) REFERENCES channels(id) ON DELETE CASCADE,
        FOREIGN KEY (user_id) REFERENCES users(id)
    );
END
GO

-- 7. Tabla messages
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'messages')
BEGIN
    CREATE TABLE messages (
        id BIGINT IDENTITY(1,1) PRIMARY KEY,
        sender_id BIGINT NOT NULL,
        scope VARCHAR(20) NOT NULL CHECK (scope IN ('general','direct','group','channel')),
        target_id BIGINT NULL,
        recipient_id BIGINT NULL,
        body VARCHAR(MAX) NOT NULL,
        created_at DATETIME2 NOT NULL DEFAULT GETDATE(),
        FOREIGN KEY (sender_id) REFERENCES users(id),
        FOREIGN KEY (recipient_id) REFERENCES users(id)
    );

    -- Creación de índices equivalentes
    CREATE INDEX idx_scope_target ON messages (scope, target_id, created_at);
    CREATE INDEX idx_direct_pair ON messages (scope, sender_id, recipient_id, created_at);
END
GO

SELECT
    local_net_address AS direccion_servidor,
    local_tcp_port AS puerto,
    client_net_address AS direccion_cliente
FROM sys.dm_exec_connections
WHERE session_id = @@SPID;