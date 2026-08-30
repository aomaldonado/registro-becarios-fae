# decoradores de permisos
from functools import wraps
from flask import session, redirect, url_for, flash


def login_requerido(f):
    # validar que haya sesion
    @wraps(f)
    def decorada(*args, **kwargs):
        if "usuario_id" not in session:
            flash("Debes iniciar sesión para acceder a esa página.", "warning")
            return redirect(url_for("auth.login"))
        return f(*args, **kwargs)
    return decorada


def rol_requerido(*roles):
    # verificar el rol
    def decorador(f):
        @wraps(f)
        def decorada(*args, **kwargs):
            if "usuario_id" not in session:
                flash("Debes iniciar sesión para acceder a esa página.", "warning")
                return redirect(url_for("auth.login"))
            rol_actual = session.get("rol", "")
            if rol_actual not in roles:
                flash(f"Acceso denegado. Se requiere el rol: {' o '.join(roles)}.", "danger")
                return redirect(url_for("auth.login"))
            return f(*args, **kwargs)
        return decorada
    return decorador
