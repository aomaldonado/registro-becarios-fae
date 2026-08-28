-- ============================================================
-- db_postgres.sql
-- Sistema: Registro Becarios
-- Motor:   PostgreSQL 14+
-- Dominio: Autenticación y Seguridad del Sistema
-- Tablas:  usuario, usuario_clave, perfil, perfil_usuario
-- ============================================================

-- Limpiar si ya existen (desarrollo)
DROP TABLE IF EXISTS perfil_usuario CASCADE;
DROP TABLE IF EXISTS usuario_clave  CASCADE;
DROP TABLE IF EXISTS usuario        CASCADE;
DROP TABLE IF EXISTS perfil         CASCADE;

DROP FUNCTION IF EXISTS fn_validar_cedula(VARCHAR)   CASCADE;
DROP FUNCTION IF EXISTS fn_auditoria_pg_trigger()    CASCADE;
DROP PROCEDURE IF EXISTS sp_usuario_crear(VARCHAR,VARCHAR,VARCHAR,VARCHAR,VARCHAR,VARCHAR);
DROP PROCEDURE IF EXISTS sp_usuario_actualizar(INT,VARCHAR,VARCHAR,VARCHAR,VARCHAR);
DROP PROCEDURE IF EXISTS sp_usuario_baja_logica(INT);
DROP PROCEDURE IF EXISTS sp_cambiar_password(INT,VARCHAR);


-- ============================================================
-- 1. TABLAS
-- ============================================================

CREATE TABLE perfil (
    id_perfil   SERIAL PRIMARY KEY,
    nombre      VARCHAR(50)  NOT NULL UNIQUE,
    descripcion VARCHAR(255),
    estado      CHAR(1)      DEFAULT 'A' CHECK (estado IN ('A','I'))
);

COMMENT ON TABLE  perfil IS 'Perfiles/roles del sistema: ADMINISTRADOR, BECARIO';
COMMENT ON COLUMN perfil.estado IS 'A=Activo, I=Inactivo';


CREATE TABLE usuario (
    id_usuario     SERIAL PRIMARY KEY,
    cedula         VARCHAR(13)  UNIQUE NOT NULL,
    nombres        VARCHAR(100) NOT NULL,
    apellidos      VARCHAR(100) NOT NULL,
    correo         VARCHAR(150) UNIQUE NOT NULL,
    rango_militar  VARCHAR(50),
    password_hash  VARCHAR(255) NOT NULL,
    estado         CHAR(1)      DEFAULT 'A' CHECK (estado IN ('A','I')),
    fecha_creacion TIMESTAMP    DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE  usuario IS 'Usuarios del sistema (administradores y becarios)';
COMMENT ON COLUMN usuario.cedula IS 'Cédula ecuatoriana de 10 dígitos, validada por fn_validar_cedula';


CREATE TABLE usuario_clave (
    id_clave      SERIAL PRIMARY KEY,
    id_usuario    INT          NOT NULL REFERENCES usuario(id_usuario) ON DELETE CASCADE,
    password_hash VARCHAR(255) NOT NULL,
    fecha_cambio  TIMESTAMP    DEFAULT CURRENT_TIMESTAMP,
    activa        BOOLEAN      DEFAULT TRUE
);

COMMENT ON TABLE usuario_clave IS 'Historial de contraseñas por usuario para evitar reutilización';


CREATE TABLE perfil_usuario (
    id_usuario INT    NOT NULL REFERENCES usuario(id_usuario) ON DELETE CASCADE,
    id_perfil  INT    NOT NULL REFERENCES perfil(id_perfil)  ON DELETE CASCADE,
    estado     CHAR(1) DEFAULT 'A' CHECK (estado IN ('A','I')),
    PRIMARY KEY (id_usuario, id_perfil)
);

COMMENT ON TABLE perfil_usuario IS 'Relación N:M entre usuario y perfil';


-- ============================================================
-- 2. FUNCIÓN: Validar Cédula Ecuatoriana
-- ============================================================

CREATE OR REPLACE FUNCTION fn_validar_cedula(p_cedula VARCHAR)
RETURNS BOOLEAN AS $$
DECLARE
    v_total              INT := 0;
    v_multiplicador      INT;
    v_digito             INT;
    v_provincia          INT;
    v_tercer_digito      INT;
    v_ultimo_digito      INT;
    v_digito_verificador INT;
BEGIN
    -- Longitud exacta de 10 dígitos
    IF length(p_cedula) != 10 THEN RETURN FALSE; END IF;

    -- Solo numérico
    IF NOT p_cedula ~ '^[0-9]+$' THEN RETURN FALSE; END IF;

    -- Provincia válida (01-24)
    v_provincia := CAST(substr(p_cedula, 1, 2) AS INT);
    IF v_provincia < 1 OR v_provincia > 24 THEN RETURN FALSE; END IF;

    -- Tercer dígito debe ser < 6 (persona natural)
    v_tercer_digito := CAST(substr(p_cedula, 3, 1) AS INT);
    IF v_tercer_digito >= 6 THEN RETURN FALSE; END IF;

    -- Algoritmo módulo 10
    FOR i IN 1..9 LOOP
        v_digito := CAST(substr(p_cedula, i, 1) AS INT);
        IF i % 2 != 0 THEN
            v_multiplicador := v_digito * 2;
            IF v_multiplicador > 9 THEN v_multiplicador := v_multiplicador - 9; END IF;
            v_total := v_total + v_multiplicador;
        ELSE
            v_total := v_total + v_digito;
        END IF;
    END LOOP;

    v_digito_verificador := v_total % 10;
    IF v_digito_verificador != 0 THEN
        v_digito_verificador := 10 - v_digito_verificador;
    END IF;

    v_ultimo_digito := CAST(substr(p_cedula, 10, 1) AS INT);
    RETURN v_digito_verificador = v_ultimo_digito;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION fn_validar_cedula IS 'Valida cédula ecuatoriana usando algoritmo módulo 10';


-- ============================================================
-- 3. STORED PROCEDURES
-- ============================================================

-- Crear usuario con validación de cédula
CREATE OR REPLACE PROCEDURE sp_usuario_crear(
    p_cedula         VARCHAR,
    p_nombres        VARCHAR,
    p_apellidos      VARCHAR,
    p_correo         VARCHAR,
    p_rango          VARCHAR,
    p_password_hash  VARCHAR
)
LANGUAGE plpgsql AS $$
DECLARE
    v_id_usuario  INT;
    v_id_perfil   INT;
BEGIN
    -- Validar cédula
    IF NOT fn_validar_cedula(p_cedula) THEN
        RAISE EXCEPTION 'CEDULA_INVALIDA: La cédula ecuatoriana % no es válida', p_cedula
            USING ERRCODE = 'P0001';
    END IF;

    -- Verificar duplicado
    IF EXISTS (SELECT 1 FROM usuario WHERE cedula = p_cedula) THEN
        RAISE EXCEPTION 'CEDULA_DUPLICADA: Ya existe un usuario con cédula %', p_cedula
            USING ERRCODE = 'P0002';
    END IF;

    IF EXISTS (SELECT 1 FROM usuario WHERE correo = LOWER(p_correo)) THEN
        RAISE EXCEPTION 'CORREO_DUPLICADO: Ya existe un usuario con el correo %', p_correo
            USING ERRCODE = 'P0003';
    END IF;

    -- Insertar usuario
    INSERT INTO usuario (cedula, nombres, apellidos, correo, rango_militar, password_hash)
    VALUES (p_cedula, p_nombres, p_apellidos, LOWER(p_correo), p_rango, p_password_hash)
    RETURNING id_usuario INTO v_id_usuario;

    -- Guardar contraseña en historial
    INSERT INTO usuario_clave (id_usuario, password_hash)
    VALUES (v_id_usuario, p_password_hash);

    -- Asignar perfil BECARIO por defecto
    SELECT id_perfil INTO v_id_perfil FROM perfil WHERE nombre = 'BECARIO' AND estado = 'A';
    IF v_id_perfil IS NOT NULL THEN
        INSERT INTO perfil_usuario (id_usuario, id_perfil) VALUES (v_id_usuario, v_id_perfil);
    END IF;

    COMMIT;
END;
$$;


-- Actualizar datos de usuario
CREATE OR REPLACE PROCEDURE sp_usuario_actualizar(
    p_id_usuario INT,
    p_nombres    VARCHAR,
    p_apellidos  VARCHAR,
    p_correo     VARCHAR,
    p_rango      VARCHAR
)
LANGUAGE plpgsql AS $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM usuario WHERE id_usuario = p_id_usuario AND estado = 'A') THEN
        RAISE EXCEPTION 'USUARIO_NO_ENCONTRADO: Usuario % no existe o está inactivo', p_id_usuario
            USING ERRCODE = 'P0004';
    END IF;

    UPDATE usuario
    SET nombres       = p_nombres,
        apellidos     = p_apellidos,
        correo        = LOWER(p_correo),
        rango_militar = p_rango
    WHERE id_usuario = p_id_usuario AND estado = 'A';
END;
$$;


-- Baja lógica de usuario
CREATE OR REPLACE PROCEDURE sp_usuario_baja_logica(
    p_id_usuario INT
)
LANGUAGE plpgsql AS $$
BEGIN
    UPDATE usuario      SET estado = 'I' WHERE id_usuario = p_id_usuario;
    UPDATE perfil_usuario SET estado = 'I' WHERE id_usuario = p_id_usuario;
END;
$$;


-- Cambiar contraseña (con historial)
CREATE OR REPLACE PROCEDURE sp_cambiar_password(
    p_id_usuario     INT,
    p_password_hash  VARCHAR
)
LANGUAGE plpgsql AS $$
BEGIN
    -- Desactivar claves anteriores
    UPDATE usuario_clave SET activa = FALSE WHERE id_usuario = p_id_usuario;

    -- Actualizar hash en usuario
    UPDATE usuario SET password_hash = p_password_hash WHERE id_usuario = p_id_usuario;

    -- Registrar en historial
    INSERT INTO usuario_clave (id_usuario, password_hash) VALUES (p_id_usuario, p_password_hash);
END;
$$;


-- ============================================================
-- 4. DATOS SEMILLA (Seeds)
-- ============================================================

INSERT INTO perfil (nombre, descripcion) VALUES
    ('ADMINISTRADOR', 'Administrador con acceso total al sistema'),
    ('BECARIO',       'Becario militar — acceso limitado a su propio perfil')
ON CONFLICT (nombre) DO NOTHING;
