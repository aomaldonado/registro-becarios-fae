# control de sesiones
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from extensiones import db
from models_pg import Usuario, PerfilUsuario

auth_bp = Blueprint("auth", __name__, url_prefix="/")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if "usuario_id" in session:
        return _redirect_por_rol(session.get("rol"))

    if request.method == "POST":
        correo   = request.form.get("correo", "").strip().lower()
        password = request.form.get("password", "")

        usuario = Usuario.query.filter_by(correo=correo, estado="A").first()

        if usuario and usuario.check_password(password):
            session["usuario_id"] = usuario.id_usuario
            session["nombre"]     = usuario.nombre_completo()
            session["correo"]     = usuario.correo
            session["cedula"]     = usuario.cedula

            pu = PerfilUsuario.query.filter_by(id_usuario=usuario.id_usuario, estado="A").first()
            session["rol"] = pu.perfil.nombre if pu else "SIN_ROL"

            flash(f"¡Bienvenido, {usuario.nombres}!", "success")
            return _redirect_por_rol(session["rol"])
        else:
            flash("Correo o contraseña incorrectos.", "danger")

    return render_template("login.html")


@auth_bp.route("/logout")
def logout():
    nombre = session.get("nombre", "")
    session.clear()
    flash(f"Sesión cerrada. ¡Hasta luego, {nombre.split()[0] if nombre else ''}!", "info")
    return redirect(url_for("auth.login"))


@auth_bp.route("/")
def index():
    """Ruta raíz: redirige según sesión."""
    if "usuario_id" in session:
        return _redirect_por_rol(session.get("rol"))
    return redirect(url_for("auth.login"))


def _redirect_por_rol(rol: str):
    """Redirige al dashboard correspondiente según el rol."""
    if rol == "ADMINISTRADOR":
        return redirect(url_for("admin.dashboard"))
    elif rol == "BECARIO":
        return redirect(url_for("becarios.dashboard_becario"))
    return redirect(url_for("auth.login"))
