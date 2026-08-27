# archivo principal de la aplicacion
import os
from datetime import datetime
from flask import Flask
from config import Config
from extensiones import db


def crear_app(clase_configuracion=Config) -> Flask:
    # configurar app
    app = Flask(__name__)
    app.config.from_object(clase_configuracion)

    # Exponer vars SS directamente para pyodbc en blueprints
    app.config["SS_SERVER"]   = clase_configuracion.SS_SERVER
    app.config["SS_DATABASE"] = clase_configuracion.SS_DATABASE
    app.config["SS_USER"]     = clase_configuracion.SS_USER
    app.config["SS_PASSWORD"] = clase_configuracion.SS_PASSWORD
    app.config["SS_DRIVER"]   = clase_configuracion.SS_DRIVER

    # config base de datos
    db.init_app(app)

    # registrar blueprints
    from blueprints.auth_bp     import auth_bp
    from blueprints.admin_bp    import admin_bp
    from blueprints.becarios_bp import becarios_bp
    from blueprints.reportes_bp import reportes_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(becarios_bp)
    app.register_blueprint(reportes_bp)

    # variables para las plantillas
    @app.context_processor
    def inyectar_globales():
        return {
            "now":      datetime.now(),
            "now_year": datetime.now().year,
            "today":    datetime.now().strftime("%Y-%m-%d"),
            "config":   app.config,
        }

    # crear carpeta si no existe
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    return app


# arrancar server
app = crear_app()

if __name__ == "__main__":
    app.run(debug=True, port=5000)
