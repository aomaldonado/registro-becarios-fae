# rutas para becarios
from flask import (Blueprint, render_template, request,
                   redirect, url_for, session, flash, jsonify)
from auth import login_requerido, rol_requerido
from extensiones import db
from models_ss import Becario, Catalogo, NovedadDiaria
import pyodbc

becarios_bp = Blueprint("becarios", __name__, url_prefix="/becarios")


def _obtener_conexion_ss():
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


@becarios_bp.route("/")
@login_requerido
@rol_requerido("ADMINISTRADOR")
def lista():
    # listar activos
    busqueda = request.args.get("q", "").strip()
    query = Becario.query.filter_by(estado="A")

    if busqueda:
        query = query.filter(
            db_ss.or_(
                Becario.nombres.ilike(f"%{busqueda}%"),
                Becario.apellidos.ilike(f"%{busqueda}%"),
                Becario.cedula.ilike(f"%{busqueda}%"),
                Becario.carrera.ilike(f"%{busqueda}%"),
            )
        )

    becarios = query.order_by(Becario.apellidos, Becario.nombres).all()
    return render_template("becarios/lista.html", becarios=becarios, busqueda=busqueda)


@becarios_bp.route("/<int:id_becario>")
@login_requerido
@rol_requerido("ADMINISTRADOR", "BECARIO")
def detalle(id_becario):
    # ver detalle
    becario   = Becario.query.get_or_404(id_becario)
    novedades = (NovedadDiaria.query
                 .filter_by(id_becario=id_becario, estado="A")
                 .order_by(NovedadDiaria.fecha.desc())
                 .limit(30)
                 .all())
    return render_template("becarios/detalle.html",
                           becario=becario, novedades=novedades)




@becarios_bp.route("/<int:id_becario>/editar", methods=["GET", "POST"])
@login_requerido
@rol_requerido("ADMINISTRADOR")
def editar(id_becario):
    # actualizar becario
    becario = Becario.query.get_or_404(id_becario)

    if request.method == "POST":
        try:
            conexion   = _obtener_conexion_ss()
            cursor = conexion.cursor()
            cursor.execute(
                "EXEC dbo.sp_becario_actualizar ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?",
                id_becario,
                request.form.get("nombres"),
                request.form.get("apellidos"),
                request.form.get("correo"),
                request.form.get("telefono") or None,
                request.form.get("rango_militar") or None,
                request.form.get("unidad") or None,
                request.form.get("carrera") or None,
                int(request.form.get("semestre")) if request.form.get("semestre") else None,
                int(request.form.get("anio_fin_estimado")) if request.form.get("anio_fin_estimado") else None,
                session.get("cedula"),
            )
            conexion.commit()
            conexion.close()
            flash("Datos del becario actualizados.", "success")
            return redirect(url_for("becarios.detalle", id_becario=id_becario))
        except Exception as e:
            flash(f"Error al actualizar: {e}", "danger")

    return render_template("becarios/editar.html", becario=becario)


@becarios_bp.route("/<int:id_becario>/baja", methods=["POST"])
@login_requerido
@rol_requerido("ADMINISTRADOR")
def baja(id_becario):
    # eliminar becario
    try:
        conexion   = _obtener_conexion_ss()
        cursor = conexion.cursor()
        cursor.execute("EXEC dbo.sp_becario_baja_logica ?, ?",
                       id_becario, session.get("cedula"))
        conexion.commit()
        conexion.close()
        flash("Becario dado de baja correctamente.", "success")
    except Exception as e:
        flash(f"Error: {e}", "danger")
    return redirect(url_for("becarios.lista"))


@becarios_bp.route("/mi-perfil", methods=["GET", "POST"])
@login_requerido
@rol_requerido("BECARIO")
def dashboard_becario():
    # inicio becario
    cedula  = session.get("cedula")
    becario = Becario.query.filter_by(cedula=cedula, estado="A").first()

    estados = Catalogo.query.filter_by(estado=True).filter(
        Catalogo.padre_id.isnot(None)).all()

    if request.method == "POST":
        id_estado    = request.form.get("id_estado")
        observacion  = request.form.get("observacion", "")

        try:
            conexion   = _obtener_conexion_ss()
            cursor = conexion.cursor()
            cursor.execute(
                "EXEC dbo.sp_registrar_novedad ?, ?, ?, ?",
                becario.id_becario if becario else None,
                int(id_estado),
                observacion or None,
                cedula,
            )
            conexion.commit()
            conexion.close()
            flash("Estado registrado para el día de hoy.", "success")
        except Exception as e:
            flash(f"Error al registrar novedad: {e}", "danger")

        return redirect(url_for("becarios.dashboard_becario"))

    # Novedad de hoy (si ya registró)
    novedad_hoy = None
    if becario:
        novedad_hoy = (NovedadDiaria.query
                       .filter_by(id_becario=becario.id_becario)
                       .order_by(NovedadDiaria.fecha.desc())
                       .first())

    return render_template("dashboard_estudiante.html",
                           becario=becario,
                           estados=estados,
                           novedad_hoy=novedad_hoy)
