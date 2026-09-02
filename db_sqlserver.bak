-- ============================================================
-- db_sqlserver.sql
-- Sistema: Registro Becarios
-- Motor:   SQL Server 2017+ / Azure SQL
-- Dominio: Negocio — Becarios, Catálogos, Novedades, Auditoría
-- ============================================================

USE master;
GO

-- Crear BD si no existe
IF NOT EXISTS (SELECT name FROM sys.databases WHERE name = 'registro_becarios_ss')
BEGIN
    CREATE DATABASE registro_becarios_ss
        COLLATE Modern_Spanish_CI_AS;
END
GO

USE registro_becarios_ss;
GO

-- ============================================================
-- 1. LIMPIEZA (desarrollo — eliminar en producción)
-- ============================================================
IF OBJECT_ID('tr_audit_novedades',    'TR') IS NOT NULL DROP TRIGGER tr_audit_novedades;
IF OBJECT_ID('tr_audit_becarios',     'TR') IS NOT NULL DROP TRIGGER tr_audit_becarios;
IF OBJECT_ID('tr_audit_catalogos',    'TR') IS NOT NULL DROP TRIGGER tr_audit_catalogos;
IF OBJECT_ID('dbo.novedades_diarias', 'U')  IS NOT NULL DROP TABLE   dbo.novedades_diarias;
IF OBJECT_ID('dbo.becarios',          'U')  IS NOT NULL DROP TABLE   dbo.becarios;
IF OBJECT_ID('dbo.catalogos',         'U')  IS NOT NULL DROP TABLE   dbo.catalogos;
IF OBJECT_ID('dbo.auditoria',         'U')  IS NOT NULL DROP TABLE   dbo.auditoria;
IF OBJECT_ID('dbo.fn_validar_cedula', 'FN') IS NOT NULL DROP FUNCTION dbo.fn_validar_cedula;
GO

-- ============================================================
-- 2. TABLAS PRINCIPALES
-- ============================================================

-- ── Catálogos ─────────────────────────────────────────────────────────────

CREATE TABLE dbo.catalogos (
    id                  BIGINT IDENTITY(1,1) PRIMARY KEY,
    codigo_referencia   VARCHAR(50),
    nombre              VARCHAR(150)    NOT NULL,
    padre_id            BIGINT          NULL REFERENCES dbo.catalogos(id),
    valor_extra         VARCHAR(255),
    estado              BIT             NOT NULL DEFAULT 1,
    fecha_creacion      DATETIME2       NOT NULL DEFAULT GETDATE(),
    fecha_actualizacion DATETIME2       NOT NULL DEFAULT GETDATE(),
    CONSTRAINT uq_cat_codigo UNIQUE (codigo_referencia)
);
GO

EXEC sp_addextendedproperty
    'MS_Description', 'Tabla maestra jerárquica: estados de novedad, tipos de permiso, etc.',
    'SCHEMA', 'dbo', 'TABLE', 'catalogos';
GO

-- ── Becarios ──────────────────────────────────────────────────────────────

CREATE TABLE dbo.becarios (
    id_becario           INT IDENTITY(1,1) PRIMARY KEY,
    cedula               VARCHAR(13)  NOT NULL,
    nombres              VARCHAR(100) NOT NULL,
    apellidos            VARCHAR(100) NOT NULL,
    correo               VARCHAR(150) NOT NULL,
    telefono             VARCHAR(15),

    -- Datos militares
    rango_militar        VARCHAR(50),
    unidad               VARCHAR(100),
    numero_militar       VARCHAR(30),

    -- Datos académicos
    universidad          VARCHAR(150) NOT NULL DEFAULT 'PUCE',
    carrera              VARCHAR(150),
    semestre             INT          CHECK (semestre BETWEEN 1 AND 12),
    anio_inicio          INT,
    anio_fin_estimado    INT,

    estado               CHAR(1)      NOT NULL DEFAULT 'A'
                         CONSTRAINT chk_becario_estado CHECK (estado IN ('A','I')),
    fecha_registro       DATETIME2    NOT NULL DEFAULT GETDATE(),
    fecha_actualizacion  DATETIME2    NOT NULL DEFAULT GETDATE(),
    registrado_por       VARCHAR(100),

    CONSTRAINT uq_becario_cedula  UNIQUE (cedula),
    CONSTRAINT uq_becario_correo  UNIQUE (correo),
    CONSTRAINT chk_anio_inicio    CHECK (anio_inicio  IS NULL OR anio_inicio  >= 1980),
    CONSTRAINT chk_anio_fin       CHECK (anio_fin_estimado IS NULL OR anio_fin_estimado >= anio_inicio)
);
GO

-- ── Novedades Diarias ─────────────────────────────────────────────────────

CREATE TABLE dbo.novedades_diarias (
    id_novedad         INT IDENTITY(1,1) PRIMARY KEY,
    id_becario         INT      NOT NULL REFERENCES dbo.becarios(id_becario),
    id_catalogo_estado BIGINT   NOT NULL REFERENCES dbo.catalogos(id),
    fecha              DATE     NOT NULL DEFAULT CAST(GETDATE() AS DATE),
    hora               TIME     NOT NULL DEFAULT CAST(GETDATE() AS TIME),
    observacion        NVARCHAR(MAX),
    estado             CHAR(1)  NOT NULL DEFAULT 'A'
                       CONSTRAINT chk_novedad_estado CHECK (estado IN ('A','I')),

    CONSTRAINT uq_novedad_becario_fecha UNIQUE (id_becario, fecha)
);
GO

-- ── Auditoría ─────────────────────────────────────────────────────────────

CREATE TABLE dbo.auditoria (
    id_auditoria     INT IDENTITY(1,1) PRIMARY KEY,
    tabla_afectada   VARCHAR(50)    NOT NULL,
    operacion        VARCHAR(10)    NOT NULL
                     CONSTRAINT chk_auditoria_op CHECK (operacion IN ('INSERT','UPDATE','DELETE')),
    usuario_bd       VARCHAR(100)   NOT NULL DEFAULT SYSTEM_USER,
    usuario_sistema  VARCHAR(100),          -- cédula del usuario Flask logueado
    fecha_hora       DATETIME2      NOT NULL DEFAULT GETDATE(),
    datos_anteriores NVARCHAR(MAX),          -- JSON como texto
    datos_nuevos     NVARCHAR(MAX),          -- JSON como texto
    ip_origen        VARCHAR(45)
);
GO


-- ============================================================
-- 3. FUNCIÓN: Validar Cédula Ecuatoriana (T-SQL)
-- ============================================================

CREATE FUNCTION dbo.fn_validar_cedula(@cedula VARCHAR(13))
RETURNS BIT
AS
BEGIN
    DECLARE @i         INT = 1;
    DECLARE @total     INT = 0;
    DECLARE @digito    INT;
    DECLARE @mult      INT;
    DECLARE @provincia INT;
    DECLARE @tercer    INT;
    DECLARE @ultimo    INT;
    DECLARE @verificador INT;

    -- Solo 10 dígitos numéricos
    IF LEN(@cedula) != 10 OR @cedula NOT LIKE '%[^0-9]%' AND ISNUMERIC(@cedula) = 0
        RETURN 0;

    IF LEN(@cedula) != 10 RETURN 0;
    IF PATINDEX('%[^0-9]%', @cedula) > 0 RETURN 0;

    -- Provincia (01-24)
    SET @provincia = CAST(SUBSTRING(@cedula, 1, 2) AS INT);
    IF @provincia < 1 OR @provincia > 24 RETURN 0;

    -- Tercer dígito < 6
    SET @tercer = CAST(SUBSTRING(@cedula, 3, 1) AS INT);
    IF @tercer >= 6 RETURN 0;

    -- Algoritmo módulo 10
    WHILE @i <= 9
    BEGIN
        SET @digito = CAST(SUBSTRING(@cedula, @i, 1) AS INT);
        IF @i % 2 != 0
        BEGIN
            SET @mult = @digito * 2;
            IF @mult > 9 SET @mult = @mult - 9;
            SET @total = @total + @mult;
        END
        ELSE
            SET @total = @total + @digito;
        SET @i = @i + 1;
    END

    SET @verificador = @total % 10;
    IF @verificador != 0 SET @verificador = 10 - @verificador;

    SET @ultimo = CAST(SUBSTRING(@cedula, 10, 1) AS INT);

    IF @verificador = @ultimo RETURN 1;
    RETURN 0;
END;
GO


-- ============================================================
-- 4. STORED PROCEDURES
-- ============================================================

-- ── sp_becario_crear ─────────────────────────────────────────────────────

CREATE OR ALTER PROCEDURE dbo.sp_becario_crear
    @cedula              VARCHAR(13),
    @nombres             VARCHAR(100),
    @apellidos           VARCHAR(100),
    @correo              VARCHAR(150),
    @telefono            VARCHAR(15)   = NULL,
    @rango_militar       VARCHAR(50)   = NULL,
    @unidad              VARCHAR(100)  = NULL,
    @numero_militar      VARCHAR(30)   = NULL,
    @universidad         VARCHAR(150)  = 'PUCE',
    @carrera             VARCHAR(150)  = NULL,
    @semestre            INT           = NULL,
    @anio_inicio         INT           = NULL,
    @anio_fin_estimado   INT           = NULL,
    @registrado_por      VARCHAR(100)  = NULL
AS
BEGIN
    SET NOCOUNT ON;
    SET XACT_ABORT ON;
    EXEC sp_set_session_context 'usuario_sistema', @registrado_por;

    BEGIN TRY
        BEGIN TRANSACTION;

        -- Validar cédula
        IF dbo.fn_validar_cedula(@cedula) = 0
        BEGIN
            RAISERROR('ERR_CEDULA_INVALIDA: La cédula ecuatoriana [%s] no es válida.', 16, 1, @cedula);
            RETURN;
        END

        -- Duplicados
        IF EXISTS (SELECT 1 FROM dbo.becarios WHERE cedula = @cedula)
        BEGIN
            RAISERROR('ERR_CEDULA_DUPLICADA: Ya existe un becario registrado con la cédula [%s].', 16, 1, @cedula);
            RETURN;
        END

        IF EXISTS (SELECT 1 FROM dbo.becarios WHERE correo = LOWER(@correo))
        BEGIN
            RAISERROR('ERR_CORREO_DUPLICADO: Ya existe un becario con el correo [%s].', 16, 1, @correo);
            RETURN;
        END

        -- Insertar
        INSERT INTO dbo.becarios (
            cedula, nombres, apellidos, correo, telefono,
            rango_militar, unidad, numero_militar,
            universidad, carrera, semestre, anio_inicio, anio_fin_estimado,
            registrado_por
        )
        VALUES (
            @cedula, @nombres, @apellidos, LOWER(@correo), @telefono,
            @rango_militar, @unidad, @numero_militar,
            @universidad, @carrera, @semestre, @anio_inicio, @anio_fin_estimado,
            @registrado_por
        );

        COMMIT TRANSACTION;
        SELECT SCOPE_IDENTITY() AS id_becario_nuevo;

        EXEC sp_set_session_context 'usuario_sistema', NULL;
    END TRY
    BEGIN CATCH
        EXEC sp_set_session_context 'usuario_sistema', NULL;
        IF @@TRANCOUNT > 0 ROLLBACK TRANSACTION;
        DECLARE @msg   NVARCHAR(4000) = ERROR_MESSAGE();
        DECLARE @sev   INT            = ERROR_SEVERITY();
        DECLARE @state INT            = ERROR_STATE();
        RAISERROR(@msg, @sev, @state);
    END CATCH
END;
GO


-- ── sp_becario_actualizar ────────────────────────────────────────────────

CREATE OR ALTER PROCEDURE dbo.sp_becario_actualizar
    @id_becario        INT,
    @nombres           VARCHAR(100) = NULL,
    @apellidos         VARCHAR(100) = NULL,
    @correo            VARCHAR(150) = NULL,
    @telefono          VARCHAR(15)  = NULL,
    @rango_militar     VARCHAR(50)  = NULL,
    @unidad            VARCHAR(100) = NULL,
    @carrera           VARCHAR(150) = NULL,
    @semestre          INT          = NULL,
    @anio_fin_estimado INT          = NULL,
    @usuario_sistema   VARCHAR(100) = NULL
AS
BEGIN
    SET NOCOUNT ON;
    SET XACT_ABORT ON;
    EXEC sp_set_session_context 'usuario_sistema', @usuario_sistema;

    BEGIN TRY
        BEGIN TRANSACTION;

        IF NOT EXISTS (SELECT 1 FROM dbo.becarios WHERE id_becario = @id_becario AND estado = 'A')
        BEGIN
            RAISERROR('ERR_BECARIO_NO_EXISTE: Becario con ID %d no encontrado o inactivo.', 16, 1, @id_becario);
            RETURN;
        END

        UPDATE dbo.becarios
        SET
            nombres           = ISNULL(@nombres,           nombres),
            apellidos         = ISNULL(@apellidos,         apellidos),
            correo            = ISNULL(LOWER(@correo),     correo),
            telefono          = ISNULL(@telefono,          telefono),
            rango_militar     = ISNULL(@rango_militar,     rango_militar),
            unidad            = ISNULL(@unidad,            unidad),
            carrera           = ISNULL(@carrera,           carrera),
            semestre          = ISNULL(@semestre,          semestre),
            anio_fin_estimado = ISNULL(@anio_fin_estimado, anio_fin_estimado),
            fecha_actualizacion = GETDATE()
        WHERE id_becario = @id_becario;

        COMMIT TRANSACTION;

        EXEC sp_set_session_context 'usuario_sistema', NULL;
    END TRY
    BEGIN CATCH
        EXEC sp_set_session_context 'usuario_sistema', NULL;
        IF @@TRANCOUNT > 0 ROLLBACK TRANSACTION;
        DECLARE @msg   NVARCHAR(4000) = ERROR_MESSAGE();
        DECLARE @sev   INT            = ERROR_SEVERITY();
        DECLARE @state INT            = ERROR_STATE();
        RAISERROR(@msg, @sev, @state);
    END CATCH
END;
GO


-- ── sp_becario_baja_logica ───────────────────────────────────────────────

CREATE OR ALTER PROCEDURE dbo.sp_becario_baja_logica
    @id_becario      INT,
    @usuario_sistema VARCHAR(100) = NULL
AS
BEGIN
    SET NOCOUNT ON;
    IF NOT EXISTS (SELECT 1 FROM dbo.becarios WHERE id_becario = @id_becario)
    BEGIN
        RAISERROR('ERR_BECARIO_NO_EXISTE: Becario ID %d no encontrado.', 16, 1, @id_becario);
        RETURN;
    END
    UPDATE dbo.becarios
    SET estado = 'I', fecha_actualizacion = GETDATE()
    WHERE id_becario = @id_becario;
END;
GO


-- ── sp_registrar_novedad ─────────────────────────────────────────────────

CREATE OR ALTER PROCEDURE dbo.sp_registrar_novedad
    @id_becario        INT,
    @id_estado         BIGINT,
    @observacion       NVARCHAR(MAX) = NULL,
    @usuario_sistema   VARCHAR(100)  = NULL
AS
BEGIN
    SET NOCOUNT ON;
    SET XACT_ABORT ON;
    EXEC sp_set_session_context 'usuario_sistema', @usuario_sistema;

    BEGIN TRY
        BEGIN TRANSACTION;

        -- Verificar becario activo
        IF NOT EXISTS (SELECT 1 FROM dbo.becarios WHERE id_becario = @id_becario AND estado = 'A')
        BEGIN
            RAISERROR('ERR_BECARIO_INACTIVO: Becario ID %d no encontrado o inactivo.', 16, 1, @id_becario);
            RETURN;
        END

        -- Verificar catálogo válido
        IF NOT EXISTS (SELECT 1 FROM dbo.catalogos WHERE id = @id_estado AND estado = 1)
        BEGIN
            RAISERROR('ERR_ESTADO_INVALIDO: El estado de catálogo ID %I64d no existe o está inactivo.', 16, 1, @id_estado);
            RETURN;
        END

        -- UPSERT: si ya registró hoy, actualizar; sino, insertar
        IF EXISTS (
            SELECT 1 FROM dbo.novedades_diarias
            WHERE id_becario = @id_becario
              AND fecha = CAST(GETDATE() AS DATE)
        )
        BEGIN
            UPDATE dbo.novedades_diarias
            SET id_catalogo_estado = @id_estado,
                observacion        = @observacion,
                hora               = CAST(GETDATE() AS TIME)
            WHERE id_becario = @id_becario
              AND fecha = CAST(GETDATE() AS DATE);
        END
        ELSE
        BEGIN
            INSERT INTO dbo.novedades_diarias (id_becario, id_catalogo_estado, fecha, hora, observacion)
            VALUES (@id_becario, @id_estado, CAST(GETDATE() AS DATE), CAST(GETDATE() AS TIME), @observacion);
        END

        COMMIT TRANSACTION;

        EXEC sp_set_session_context 'usuario_sistema', NULL;
    END TRY
    BEGIN CATCH
        EXEC sp_set_session_context 'usuario_sistema', NULL;
        IF @@TRANCOUNT > 0 ROLLBACK TRANSACTION;
        DECLARE @msg   NVARCHAR(4000) = ERROR_MESSAGE();
        DECLARE @sev   INT            = ERROR_SEVERITY();
        DECLARE @state INT            = ERROR_STATE();
        RAISERROR(@msg, @sev, @state);
    END CATCH
END;
GO


-- ── sp_reporte_diario ────────────────────────────────────────────────────

CREATE OR ALTER PROCEDURE dbo.sp_reporte_diario
    @fecha DATE = NULL
AS
BEGIN
    SET NOCOUNT ON;
    IF @fecha IS NULL SET @fecha = CAST(GETDATE() AS DATE);

    SELECT
        b.rango_militar,
        b.apellidos + ' ' + b.nombres  AS militar,
        b.cedula,
        b.carrera,
        b.semestre,
        c.nombre                        AS estado_actual,
        n.fecha,
        CONVERT(VARCHAR(5), n.hora, 108) AS hora,
        n.observacion
    FROM dbo.becarios b
    LEFT JOIN dbo.novedades_diarias n
           ON b.id_becario = n.id_becario AND n.fecha = @fecha
    LEFT JOIN dbo.catalogos c
           ON n.id_catalogo_estado = c.id
    WHERE b.estado = 'A'
    ORDER BY b.apellidos, b.nombres;
END;
GO


-- ── sp_reporte_mensual ───────────────────────────────────────────────────

CREATE OR ALTER PROCEDURE dbo.sp_reporte_mensual
    @anio INT = NULL,
    @mes  INT = NULL
AS
BEGIN
    SET NOCOUNT ON;
    IF @anio IS NULL SET @anio = YEAR(GETDATE());
    IF @mes  IS NULL SET @mes  = MONTH(GETDATE());

    SELECT
        b.rango_militar,
        b.apellidos + ' ' + b.nombres   AS militar,
        b.cedula,
        b.carrera,
        c.nombre                         AS tipo_novedad,
        COUNT(*)                         AS total_dias,
        @mes                             AS mes,
        @anio                            AS anio
    FROM dbo.becarios b
    JOIN dbo.novedades_diarias n  ON b.id_becario = n.id_becario
    JOIN dbo.catalogos c          ON n.id_catalogo_estado = c.id
    WHERE b.estado = 'A'
      AND YEAR(n.fecha)  = @anio
      AND MONTH(n.fecha) = @mes
    GROUP BY b.id_becario, b.rango_militar, b.apellidos, b.nombres,
             b.cedula, b.carrera, c.nombre
    ORDER BY b.apellidos, b.nombres, c.nombre;
END;
GO


-- ============================================================
-- 5. TRIGGERS DE AUDITORÍA
-- ============================================================

-- ── Función auxiliar: construir JSON de fila ──────────────────────────────
-- SQL Server no tiene row_to_json(), usamos FOR JSON PATH

-- ── Trigger Becarios ─────────────────────────────────────────────────────

CREATE OR ALTER TRIGGER dbo.tr_audit_becarios
ON dbo.becarios
AFTER INSERT, UPDATE, DELETE
AS
BEGIN
    SET NOCOUNT ON;

    DECLARE @operacion VARCHAR(10);
    DECLARE @ant       NVARCHAR(MAX);
    DECLARE @nue       NVARCHAR(MAX);

    IF EXISTS(SELECT 1 FROM inserted) AND EXISTS(SELECT 1 FROM deleted)
        SET @operacion = 'UPDATE';
    ELSE IF EXISTS(SELECT 1 FROM inserted)
        SET @operacion = 'INSERT';
    ELSE
        SET @operacion = 'DELETE';

    SELECT @ant = (SELECT * FROM deleted  FOR JSON PATH, WITHOUT_ARRAY_WRAPPER);
    SELECT @nue = (SELECT * FROM inserted FOR JSON PATH, WITHOUT_ARRAY_WRAPPER);

    DECLARE @usuario_sistema VARCHAR(100) = CAST(SESSION_CONTEXT(N'usuario_sistema') AS VARCHAR(100));

    INSERT INTO dbo.auditoria (tabla_afectada, operacion, datos_anteriores, datos_nuevos, usuario_sistema)
    VALUES ('becarios', @operacion, @ant, @nue, @usuario_sistema);
END;
GO


-- ── Trigger Novedades ─────────────────────────────────────────────────────

CREATE OR ALTER TRIGGER dbo.tr_audit_novedades
ON dbo.novedades_diarias
AFTER INSERT, UPDATE, DELETE
AS
BEGIN
    SET NOCOUNT ON;

    DECLARE @operacion VARCHAR(10);
    DECLARE @ant       NVARCHAR(MAX);
    DECLARE @nue       NVARCHAR(MAX);

    IF EXISTS(SELECT 1 FROM inserted) AND EXISTS(SELECT 1 FROM deleted)
        SET @operacion = 'UPDATE';
    ELSE IF EXISTS(SELECT 1 FROM inserted)
        SET @operacion = 'INSERT';
    ELSE
        SET @operacion = 'DELETE';

    SELECT @ant = (
        SELECT d.*, c.nombre AS novedad_texto 
        FROM deleted d 
        LEFT JOIN dbo.catalogos c ON d.id_catalogo_estado = c.id 
        FOR JSON PATH, WITHOUT_ARRAY_WRAPPER
    );
    SELECT @nue = (
        SELECT i.*, c.nombre AS novedad_texto 
        FROM inserted i 
        LEFT JOIN dbo.catalogos c ON i.id_catalogo_estado = c.id 
        FOR JSON PATH, WITHOUT_ARRAY_WRAPPER
    );

    DECLARE @usuario_sistema VARCHAR(100) = CAST(SESSION_CONTEXT(N'usuario_sistema') AS VARCHAR(100));

    INSERT INTO dbo.auditoria (tabla_afectada, operacion, datos_anteriores, datos_nuevos, usuario_sistema)
    VALUES ('novedades_diarias', @operacion, @ant, @nue, @usuario_sistema);
END;
GO


-- ── Trigger Catálogos ─────────────────────────────────────────────────────

CREATE OR ALTER TRIGGER dbo.tr_audit_catalogos
ON dbo.catalogos
AFTER INSERT, UPDATE, DELETE
AS
BEGIN
    SET NOCOUNT ON;

    DECLARE @operacion VARCHAR(10);
    DECLARE @ant       NVARCHAR(MAX);
    DECLARE @nue       NVARCHAR(MAX);

    IF EXISTS(SELECT 1 FROM inserted) AND EXISTS(SELECT 1 FROM deleted)
        SET @operacion = 'UPDATE';
    ELSE IF EXISTS(SELECT 1 FROM inserted)
        SET @operacion = 'INSERT';
    ELSE
        SET @operacion = 'DELETE';

    SELECT @ant = (SELECT * FROM deleted  FOR JSON PATH, WITHOUT_ARRAY_WRAPPER);
    SELECT @nue = (SELECT * FROM inserted FOR JSON PATH, WITHOUT_ARRAY_WRAPPER);

    DECLARE @usuario_sistema VARCHAR(100) = CAST(SESSION_CONTEXT(N'usuario_sistema') AS VARCHAR(100));

    INSERT INTO dbo.auditoria (tabla_afectada, operacion, datos_anteriores, datos_nuevos, usuario_sistema)
    VALUES ('catalogos', @operacion, @ant, @nue, @usuario_sistema);
END;
GO


-- ============================================================
-- 6. VISTAS DE REPORTES
-- ============================================================

CREATE OR ALTER VIEW dbo.vw_reporte_diario AS
SELECT
    b.rango_militar,
    b.apellidos + ' ' + b.nombres          AS militar,
    b.cedula,
    b.carrera,
    b.semestre,
    ISNULL(c.nombre, 'Sin registro')        AS estado_actual,
    n.fecha,
    CONVERT(VARCHAR(5), n.hora, 108)        AS hora,
    n.observacion
FROM dbo.becarios b
LEFT JOIN dbo.novedades_diarias n
       ON b.id_becario = n.id_becario
      AND n.fecha = CAST(GETDATE() AS DATE)
LEFT JOIN dbo.catalogos c
       ON n.id_catalogo_estado = c.id
WHERE b.estado = 'A';
GO


CREATE OR ALTER VIEW dbo.vw_resumen_mensual AS
SELECT
    b.rango_militar,
    b.apellidos + ' ' + b.nombres  AS militar,
    b.cedula,
    b.carrera,
    YEAR(n.fecha)                   AS anio,
    MONTH(n.fecha)                  AS mes,
    c.nombre                        AS tipo_novedad,
    COUNT(*)                        AS total_dias
FROM dbo.becarios b
JOIN dbo.novedades_diarias n ON b.id_becario = n.id_becario
JOIN dbo.catalogos c         ON n.id_catalogo_estado = c.id
WHERE b.estado = 'A'
GROUP BY b.id_becario, b.rango_militar, b.apellidos, b.nombres,
         b.cedula, b.carrera, YEAR(n.fecha), MONTH(n.fecha), c.nombre;
GO


-- ============================================================
-- 7. DATOS SEMILLA
-- ============================================================

-- Catálogos padre
INSERT INTO dbo.catalogos (codigo_referencia, nombre) VALUES
    ('ESTADOS_NOVEDAD', 'Estados de Novedad Diaria');

DECLARE @padre_id BIGINT = SCOPE_IDENTITY();

-- Estados hijos
INSERT INTO dbo.catalogos (codigo_referencia, nombre, padre_id) VALUES
    ('DISP_UNI',   'Disponible en la universidad',   @padre_id),
    ('EN_CLASES',  'En clases',                       @padre_id),
    ('PERM_INST',  'Permiso institucional',            @padre_id),
    ('CALAMIDAD',  'Calamidad doméstica',              @padre_id),
    ('SIN_CLASES', 'Sin clases programadas',           @padre_id),
    ('ENFERMEDAD', 'Reposo médico',                    @padre_id),
    ('MISION',     'En misión institucional',          @padre_id);
GO
