# reportes del sistema
from flask import (Blueprint, render_template, request,
                   jsonify, current_app)
from auth import login_requerido, rol_requerido
from models_ss import Auditoria
import pyodbc
from datetime import date

reportes_bp = Blueprint("reportes", __name__, url_prefix="/reportes")


def _obtener_conexion_ss():
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


def _ejecutar_reporte(sp_nombre: str, params: dict) -> list[dict]:
    # ejecutar el sp
    try:
        conexion   = _obtener_conexion_ss()
        cursor = conexion.cursor()
        param_str = ", ".join(f"@{k}=?" for k in params)
        cursor.execute(f"EXEC dbo.{sp_nombre} {param_str}", *params.values())
        columnas = [columna[0] for columna in cursor.description]
        filas = [dict(zip(columnas, fila)) for fila in cursor.fetchall()]
        conexion.close()
        return filas
    except Exception as e:
        return []


@reportes_bp.route("/diario")
@login_requerido
@rol_requerido("ADMINISTRADOR")
def diario():
    # ver reporte diario
    fecha_str = request.args.get("fecha", str(date.today()))
    try:
        fecha_param = date.fromisoformat(fecha_str)
    except ValueError:
        fecha_param = date.today()

    datos = _ejecutar_reporte("sp_reporte_diario", {"fecha": fecha_param})

    # Convertir fechas/horas a string para JSON
    for d in datos:
        for k, v in d.items():
            if hasattr(v, "isoformat"):
                d[k] = v.isoformat() if v else None

    if request.args.get("format") == "json":
        return jsonify({
            "fecha": str(fecha_param),
            "total": len(datos),
            "registros": datos,
            "emailjs": {
                "service_id":  current_app.config["EMAILJS_SERVICE_ID"],
                "template_id": current_app.config["EMAILJS_TEMPLATE_ID"],
                "public_key":  current_app.config["EMAILJS_PUBLIC_KEY"],
            }
        })

    return render_template("reportes/diario.html",
                           datos=datos,
                           fecha=fecha_param,
                           emailjs_service_id  = current_app.config["EMAILJS_SERVICE_ID"],
                           emailjs_template_id = current_app.config["EMAILJS_TEMPLATE_ID"],
                           emailjs_public_key  = current_app.config["EMAILJS_PUBLIC_KEY"])


@reportes_bp.route("/mensual")
@login_requerido
@rol_requerido("ADMINISTRADOR")
def mensual():
    # ver reporte mensual
    hoy  = date.today()
    anio = int(request.args.get("anio", hoy.year))
    mes  = int(request.args.get("mes",  hoy.month))

    datos = _ejecutar_reporte("sp_reporte_mensual", {"anio": anio, "mes": mes})

    if request.args.get("format") == "json":
        return jsonify({"anio": anio, "mes": mes, "total": len(datos), "registros": datos})

    return render_template("reportes/mensual.html",
                           datos=datos,
                           anio=anio,
                           mes=mes,
                           emailjs_service_id  = current_app.config["EMAILJS_SERVICE_ID"],
                           emailjs_template_id = current_app.config["EMAILJS_TEMPLATE_ID"],
                           emailjs_public_key  = current_app.config["EMAILJS_PUBLIC_KEY"])
