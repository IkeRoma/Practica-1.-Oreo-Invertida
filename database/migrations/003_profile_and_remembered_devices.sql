/*
    Wasap V3 - migración incremental de perfil y dispositivos recordados.
    Ejecutar una sola vez en la base wasap_db con una cuenta administradora.
    No modifica las tablas de mensajes, grupos ni canales.
*/
USE wasap_db;
GO

IF COL_LENGTH('dbo.users', 'avatar_data') IS NULL
BEGIN
    ALTER TABLE dbo.users ADD avatar_data NVARCHAR(MAX) NULL;
END;
GO

IF OBJECT_ID('dbo.remembered_devices', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.remembered_devices (
        id BIGINT IDENTITY(1,1) NOT NULL CONSTRAINT PK_remembered_devices PRIMARY KEY,
        user_id BIGINT NOT NULL,
        token_hash CHAR(64) NOT NULL,
        device_name NVARCHAR(100) NOT NULL CONSTRAINT DF_remembered_devices_name DEFAULT N'Dispositivo',
        created_at DATETIME2(0) NOT NULL CONSTRAINT DF_remembered_devices_created DEFAULT SYSUTCDATETIME(),
        last_used_at DATETIME2(0) NOT NULL CONSTRAINT DF_remembered_devices_used DEFAULT SYSUTCDATETIME(),
        CONSTRAINT UQ_remembered_devices_token UNIQUE(token_hash),
        CONSTRAINT FK_remembered_devices_user FOREIGN KEY(user_id)
            REFERENCES dbo.users(id) ON DELETE CASCADE
    );
    CREATE INDEX IX_remembered_devices_user ON dbo.remembered_devices(user_id);
END;
GO
