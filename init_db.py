# inicializar base de datos
import os
import sys
import psycopg2
import pyodbc
from app import crear_app
from models_pg import db_pg
from models_ss import db_ss
from config import Config

app = crear_app()


def init_postgres():
    # crear base de datos local postgres
    print("\n📦 Inicializando PostgreSQL...")
    try:
        conn = psycopg2.connect(
            host=Config.PG_HOST,
            port=Config.PG_PORT,
            dbname=Config.PG_NAME,
            user=Config.PG_USER,
            password=Config.PG_PASSWORD,
        )
        conn.autocommit = True
        cur = conn.cursor()

        script_path = os.path.join(os.path.dirname(__file__), "db_postgres.sql")
        with open(script_path, "r", encoding="utf-8") as f:
            sql = f.read()

        # Ejecutar el script completo
        cur.execute(sql)
        print("  ✅ PostgreSQL: tablas, funciones y SPs creados.")

        # Crear usuario ADMINISTRADOR inicial
        from werkzeug.security import generate_password_hash
        pwd_hash = generate_password_hash("Admin2026!")

        cur.execute("""
            INSERT INTO usuario (cedula, nombres, apellidos, correo, rango_militar, password_hash)
            VALUES ('1700000000', 'Administrador', 'Sistema', 'admin@becarios.mil.ec',
                    'MAYOR', %s)
            ON CONFLICT (cedula) DO NOTHING;
        """, (pwd_hash,))

        cur.execute("""
            INSERT INTO perfil_usuario (id_usuario, id_perfil)
            SELECT u.id_usuario, p.id_perfil
            FROM usuario u, perfil p
            WHERE u.cedula = '1700000000' AND p.nombre = 'ADMINISTRADOR'
            ON CONFLICT DO NOTHING;
        """)

        conn.close()
        print("  ✅ Usuario admin@becarios.mil.ec creado (pwd: Admin2026!)")

    except Exception as e:
        print(f"  ❌ Error en PostgreSQL: {e}")
        sys.exit(1)


def init_sqlserver():
    # crear sql server
    print("\n🗄️  Inicializando SQL Server...")
    try:
        conn_str = (
            f"DRIVER={{{Config.SS_DRIVER}}};"
            f"SERVER={Config.SS_SERVER};"
            f"DATABASE=master;"
            f"UID={Config.SS_USER};"
            f"PWD={Config.SS_PASSWORD};"
            f"TrustServerCertificate=yes;"
        )
        conn = pyodbc.connect(conn_str, autocommit=True)
        cursor = conn.cursor()

        script_path = os.path.join(os.path.dirname(__file__), "db_sqlserver.sql")
        with open(script_path, "r", encoding="utf-8") as f:
            sql = f.read()

        # Dividir por GO (separador de lotes T-SQL)
        lotes = [l.strip() for l in sql.split("\nGO\n") if l.strip()]
        for i, lote in enumerate(lotes, 1):
            if lote:
                try:
                    cursor.execute(lote)
                except Exception as e:
                    print(f"  ⚠️  Lote {i}: {e}")

        conn.close()
        print("  ✅ SQL Server: tablas, SPs, triggers y vistas creados.")

    except Exception as e:
        print(f"  ❌ Error en SQL Server: {e}")
        print("  ℹ️  Verifica que SQL Server esté corriendo y el driver ODBC esté instalado.")
        print(f"  ℹ️  Driver configurado: {Config.SS_DRIVER}")


if __name__ == "__main__":
    print("=" * 55)
    print(" 🚀 Iniciando bases de datos — Registro Becarios")
    print("=" * 55)

    init_postgres()
    init_sqlserver()

    print("\n" + "=" * 55)
    print(" ✅ Inicialización completada.")
    print("    Accede a: http://localhost:5000/login")
    print("    Admin:    admin@becarios.mil.ec / Admin2026!")
    print("=" * 55 + "\n")
