# rutas de administracion
from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify
from werkzeug.security import generate_password_hash
from auth import login_requerido, rol_requerido
from extensiones import db
from models_pg import Usuario, PerfilUsuario, Perfil
from models_ss import Auditoria, Catalogo
from sqlalchemy import text
import pyodbc
import os

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


def _obtener_conexion_ss():
    # conexion a sql server
    from flask import current_app
    cfg = current_app.config
    if cfg.get('SS_USER'):
        conn_str = (
            f"DRIVER={{{cfg['SS_DRIVER']}}};"
            f"SERVER={cfg['SS_SERVER']};"
            f"DATABASE={cfg['SS_DATABASE']};"
            f"UID={cfg['SS_USER']};"
            f"PWD={cfg['SS_PASSWORD']};"
            f"TrustServerCertificate=yes;"
        )
    else:
        conn_str = (
            f"DRIVER={{{cfg['SS_DRIVER']}}};"
            f"SERVER={cfg['SS_SERVER']};"
            f"DATABASE={cfg['SS_DATABASE']};"
            f"Trusted_Connection=yes;"
            f"TrustServerCertificate=yes;"
        )
    return pyodbc.connect(conn_str)


@admin_bp.route("/dashboard")
@login_requerido
@rol_requerido("ADMINISTRADOR")
def dashboard():
    # vista del dashboard
    try:
        with _obtener_conexion_ss() as conexion:
            cursor = conexion.cursor()
            cursor.execute("EXEC dbo.sp_reporte_diario")
            columnas = [columna[0] for columna in cursor.description]
            reportes = [dict(zip(columnas, fila)) for fila in cursor.fetchall()]
            
            # Obtener total de becarios reales desde SQL Server
            cursor.execute("SELECT COUNT(*) FROM dbo.becarios WHERE estado = 'A'")
            total_activos = cursor.fetchone()[0]
    except Exception as e:
        flash(f"Error al cargar el reporte diario: {e}", "danger")
        reportes = []
        total_activos = 0

    return render_template("dashboard_admin.html",
                           reportes=reportes,
                           total_activos=total_activos)


@admin_bp.route("/usuarios")
@login_requerido
@rol_requerido("ADMINISTRADOR")
def usuarios():
    # listar usuarios
    lista = (Usuario.query
             .order_by(Usuario.apellidos, Usuario.nombres)
             .all())
    return render_template("admin/usuarios.html", usuarios=lista)


@admin_bp.route("/usuarios/nuevo", methods=["GET", "POST"])
@login_requerido
@rol_requerido("ADMINISTRADOR")
def nuevo_usuario():
    # crear usuario
    perfiles = Perfil.query.filter_by(estado="A").all()

    if request.method == "POST":
        cedula    = request.form.get("cedula", "").strip()
        nombres   = request.form.get("nombres", "").strip()
        apellidos = request.form.get("apellidos", "").strip()
        correo    = request.form.get("correo", "").strip().lower()
        rango     = request.form.get("rango", "").strip()
        id_perfil = request.form.get("id_perfil")
        password  = request.form.get("password", "")

        # Campos académicos (para SQL Server)
        carrera           = request.form.get("carrera", "").strip()
        semestre          = request.form.get("semestre")
        anio_inicio       = request.form.get("anio_inicio")
        anio_fin_estimado = request.form.get("anio_fin_estimado")
        unidad            = request.form.get("unidad", "").strip()
        numero_militar    = request.form.get("numero_militar", "").strip()
        telefono          = request.form.get("telefono", "").strip()

        pwd_hash = generate_password_hash(password)

        try:
            # 1. Crear usuario en PostgreSQL via SP
            with db.engine.connect().execution_options(isolation_level="AUTOCOMMIT") as conexion:
                conexion.execute(
                    text("CALL sp_usuario_crear(:cedula, :nombres, :apellidos, :correo, :rango, :pwd)"),
                    {"cedula": cedula, "nombres": nombres, "apellidos": apellidos,
                     "correo": correo, "rango": rango, "pwd": pwd_hash}
                )

            # 2. Asignar perfil específico si no es BECARIO
            if id_perfil:
                usuario = Usuario.query.filter_by(cedula=cedula).first()
                if usuario:
                    pu_existente = PerfilUsuario.query.filter_by(
                        id_usuario=usuario.id_usuario).first()
                    if pu_existente:
                        pu_existente.id_perfil = int(id_perfil)
                    db.session.commit()

            # 3. Registrar en SQL Server si es BECARIO
            perfil_obj = Perfil.query.get(int(id_perfil)) if id_perfil else None
            if perfil_obj and perfil_obj.nombre == "BECARIO":
                conexion_ss = _obtener_conexion_ss()
                cursor  = conexion_ss.cursor()
                cursor.execute(
                    "EXEC dbo.sp_becario_crear ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?",
                    cedula, nombres, apellidos, correo, telefono or None,
                    rango or None, unidad or None, numero_militar or None,
                    "PUCE", carrera or None,
                    int(semestre) if semestre else None,
                    int(anio_inicio) if anio_inicio else None,
                    int(anio_fin_estimado) if anio_fin_estimado else None,
                    session.get("cedula")
                )
                conexion_ss.commit()
                conexion_ss.close()

            flash(f"Usuario {nombres} {apellidos} creado exitosamente.", "success")
            return redirect(url_for("admin.usuarios"))

        except Exception as e:
            msg = str(e)
            if "CEDULA_INVALIDA" in msg:
                flash("La cédula ecuatoriana ingresada no es válida.", "danger")
            elif "CEDULA_DUPLICADA" in msg:
                flash("Ya existe un usuario con esa cédula.", "danger")
            elif "CORREO_DUPLICADO" in msg:
                flash("Ya existe un usuario con ese correo.", "danger")
            else:
                flash(f"Error: {msg}", "danger")

    return render_template("admin/nuevo_usuario.html", perfiles=perfiles)


@admin_bp.route("/usuarios/<int:id_usuario>/baja", methods=["POST"])
@login_requerido
@rol_requerido("ADMINISTRADOR")
def baja_usuario(id_usuario):
    # dar de baja
    try:
        with db.engine.connect().execution_options(isolation_level="AUTOCOMMIT") as conexion:
            conexion.execute(
                text("CALL sp_usuario_baja_logica(:id)"),
                {"id": id_usuario}
            )
        flash("Usuario dado de baja correctamente.", "success")
    except Exception as e:
        flash(f"Error: {e}", "danger")
    return redirect(url_for("admin.usuarios"))


@admin_bp.route("/auditoria")
@login_requerido
@rol_requerido("ADMINISTRADOR")
def auditoria():
    # revisar auditoria
    tabla  = request.args.get("tabla", "")
    op     = request.args.get("operacion", "")
    limite = int(request.args.get("limite", 100))

    query = Auditoria.query
    if tabla:
        query = query.filter_by(tabla_afectada=tabla)
    if op:
        query = query.filter_by(operacion=op)

    registros = (query
                 .order_by(Auditoria.fecha_hora.desc())
                 .limit(limite)
                 .all())

    tablas_disponibles = (db.session.query(Auditoria.tabla_afectada)
                          .distinct().all())
    tablas_disponibles = [t[0] for t in tablas_disponibles]

    return render_template("auditoria/index.html",
                           registros=registros,
                           tablas=tablas_disponibles,
                           filtro_tabla=tabla,
                           filtro_op=op)
