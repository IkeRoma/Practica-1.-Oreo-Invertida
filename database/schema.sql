USE master;
ALTER DATABASE wasap_db SET SINGLE_USER WITH ROLLBACK IMMEDIATE;

DROP DATABASE wasap_db;

USE master;
GO
IF DB_ID(N'wasap_db') IS NULL
BEGIN
    CREATE DATABASE wasap_db;
END;
GO
USE wasap_db;
GO

IF OBJECT_ID(N'dbo.users', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.users (
        id BIGINT IDENTITY(1,1) NOT NULL CONSTRAINT PK_users PRIMARY KEY,
        username NVARCHAR(32) NOT NULL,
        password_hash NVARCHAR(255) NOT NULL,
        display_name NVARCHAR(64) NOT NULL,
        avatar_path NVARCHAR(512) NULL,
        avatar_data NVARCHAR(MAX) NULL,
        created_at DATETIME2(0) NOT NULL CONSTRAINT DF_users_created_at DEFAULT SYSUTCDATETIME(),
        CONSTRAINT UQ_users_username UNIQUE(username)
    );
END;
GO
IF COL_LENGTH('dbo.users','avatar_data') IS NULL
    ALTER TABLE dbo.users ADD avatar_data NVARCHAR(MAX) NULL;
GO

IF OBJECT_ID(N'dbo.groups_chat', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.groups_chat (
        id BIGINT IDENTITY(1,1) NOT NULL CONSTRAINT PK_groups_chat PRIMARY KEY,
        name NVARCHAR(80) NOT NULL,
        owner_id BIGINT NOT NULL,
        created_at DATETIME2(0) NOT NULL CONSTRAINT DF_groups_chat_created_at DEFAULT SYSUTCDATETIME(),
        CONSTRAINT FK_groups_chat_owner FOREIGN KEY(owner_id) REFERENCES dbo.users(id)
    );
END;
GO
IF OBJECT_ID(N'dbo.group_members', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.group_members (
        group_id BIGINT NOT NULL,
        user_id BIGINT NOT NULL,
        joined_at DATETIME2(0) NOT NULL CONSTRAINT DF_group_members_joined_at DEFAULT SYSUTCDATETIME(),
        CONSTRAINT PK_group_members PRIMARY KEY(group_id,user_id),
        CONSTRAINT FK_group_members_group FOREIGN KEY(group_id) REFERENCES dbo.groups_chat(id) ON DELETE CASCADE,
        CONSTRAINT FK_group_members_user FOREIGN KEY(user_id) REFERENCES dbo.users(id) ON DELETE CASCADE
    );
END;
GO
IF OBJECT_ID(N'dbo.channels', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.channels (
        id BIGINT IDENTITY(1,1) NOT NULL CONSTRAINT PK_channels PRIMARY KEY,
        name NVARCHAR(80) NOT NULL,
        owner_id BIGINT NOT NULL,
        created_at DATETIME2(0) NOT NULL CONSTRAINT DF_channels_created_at DEFAULT SYSUTCDATETIME(),
        CONSTRAINT UQ_channels_name UNIQUE(name),
        CONSTRAINT FK_channels_owner FOREIGN KEY(owner_id) REFERENCES dbo.users(id)
    );
END;
GO
IF OBJECT_ID(N'dbo.channel_members', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.channel_members (
        channel_id BIGINT NOT NULL,
        user_id BIGINT NOT NULL,
        joined_at DATETIME2(0) NOT NULL CONSTRAINT DF_channel_members_joined_at DEFAULT SYSUTCDATETIME(),
        CONSTRAINT PK_channel_members PRIMARY KEY(channel_id,user_id),
        CONSTRAINT FK_channel_members_channel FOREIGN KEY(channel_id) REFERENCES dbo.channels(id) ON DELETE CASCADE,
        CONSTRAINT FK_channel_members_user FOREIGN KEY(user_id) REFERENCES dbo.users(id) ON DELETE CASCADE
    );
END;
GO
IF OBJECT_ID(N'dbo.messages', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.messages (
        id BIGINT IDENTITY(1,1) NOT NULL CONSTRAINT PK_messages PRIMARY KEY,
        sender_id BIGINT NOT NULL,
        scope VARCHAR(12) NOT NULL,
        target_id BIGINT NULL,
        recipient_id BIGINT NULL,
        body NVARCHAR(4000) NOT NULL,
        created_at DATETIME2(0) NOT NULL CONSTRAINT DF_messages_created_at DEFAULT SYSUTCDATETIME(),
        CONSTRAINT CK_messages_scope CHECK(scope IN ('general','direct','group','channel')),
        CONSTRAINT FK_messages_sender FOREIGN KEY(sender_id) REFERENCES dbo.users(id),
        CONSTRAINT FK_messages_recipient FOREIGN KEY(recipient_id) REFERENCES dbo.users(id)
    );
    CREATE INDEX IX_messages_scope_target_created ON dbo.messages(scope,target_id,created_at,id);
    CREATE INDEX IX_messages_direct_pair ON dbo.messages(scope,sender_id,recipient_id,created_at,id);
END;
GO
IF OBJECT_ID(N'dbo.remembered_devices', N'U') IS NULL
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