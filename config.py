# configuraciones del sistema
import os
from dotenv import load_dotenv

load_dotenv(override=True)


class Config:
    # seguridad
    SECRET_KEY = os.getenv("SECRET_KEY", "registro_becarios_2026_secret")

    # postgres
    PG_USER     = os.getenv("PG_USER", "andres")
    PG_PASSWORD = os.getenv("PG_PASSWORD", "1991")
    PG_HOST     = os.getenv("PG_HOST", "localhost")
    PG_PORT     = os.getenv("PG_PORT", "5432")
    PG_NAME     = os.getenv("PG_NAME", "registro_becarios")

    _PG_URI = f"postgresql://{PG_USER}:{PG_PASSWORD}@{PG_HOST}:{PG_PORT}/{PG_NAME}"

    # sql server
    SS_SERVER   = os.getenv("SS_SERVER", "localhost")
    SS_DATABASE = os.getenv("SS_DATABASE", "registro_becarios_ss")
    SS_USER     = os.getenv("SS_USER", "")        # vacío = Windows Auth
    SS_PASSWORD = os.getenv("SS_PASSWORD", "")
    SS_DRIVER   = os.getenv("SS_DRIVER", "ODBC Driver 17 for SQL Server")

    # conexion sql server
    if SS_USER:
        # SQL Server Authentication
        _SS_URI = (
            f"mssql+pyodbc://{SS_USER}:{SS_PASSWORD}@{SS_SERVER}/{SS_DATABASE}"
            f"?driver={SS_DRIVER.replace(' ', '+')}&TrustServerCertificate=yes"
        )
    else:
        # Windows Authentication (Trusted_Connection)
        _SS_URI = (
            f"mssql+pyodbc://@{SS_SERVER}/{SS_DATABASE}"
            f"?driver={SS_DRIVER.replace(' ', '+')}"
            f"&Trusted_Connection=yes&TrustServerCertificate=yes"
        )

    # configuracion sqlalchemy
    SQLALCHEMY_DATABASE_URI = _PG_URI
    SQLALCHEMY_BINDS = {
        "postgres":  _PG_URI,
        "sqlserver": _SS_URI,
    }
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
        "pool_recycle": 1800,
    }

    # correos
    EMAILJS_PUBLIC_KEY  = os.getenv("EMAILJS_PUBLIC_KEY", "4Z0MzzpsR8yZx8Jcr")
    EMAILJS_SERVICE_ID  = os.getenv("EMAILJS_SERVICE_ID", "service_53o1lh8")
    EMAILJS_TEMPLATE_ID = os.getenv("EMAILJS_TEMPLATE_ID", "template_17rq3gr")

    # archivos
    UPLOAD_FOLDER       = os.path.join(os.path.abspath(os.path.dirname(__file__)), "static", "uploads")
    MAX_CONTENT_LENGTH  = 16 * 1024 * 1024   # 16 MB
