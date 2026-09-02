# Sistema de Registro de Novedades - Becarios FAE

Este proyecto es un aplicativo web desarrollado en Python (Flask) para la gestión y registro de novedades de becarios, utilizando una arquitectura de doble base de datos (PostgreSQL y SQL Server).

## 1. Requisitos Previos
* **Python** (versión 3.9 o superior recomendada).
* **PostgreSQL** (para la gestión de perfiles y usuarios).
* **Microsoft SQL Server** (para la gestión de novedades, becarios y reportes).
* **ODBC Driver for SQL Server** (Driver 17 o superior, necesario para la conexión desde Python).

## 2. Restauración de las Bases de Datos
En la carpeta principal del proyecto encontrarás los archivos necesarios para restaurar las estructuras de las bases de datos:

1. **PostgreSQL (`db_postgres.backup`)**: 
   * Crea una base de datos vacía llamada `registro_becarios`.
   * Restaura la estructura y procedimientos almacenados utilizando la opción "Restore" de pgAdmin y seleccionando este archivo `.backup`.
2. **SQL Server (`db_sqlserver.bak`)**: 
   * Abre SQL Server Management Studio (SSMS).
   * Haz clic derecho en "Databases" -> "Restore Database..." y selecciona el archivo `.bak` provisto.

## 3. Configuración del Entorno (`.env`)
El proyecto necesita un archivo `.env` en la raíz (junto a `app.py`) con las credenciales de conexión. Asegúrate de modificar los valores según tu entorno local:

```env
# Seguridad
SECRET_KEY=registro_becarios_2026_secret

# PostgreSQL
PG_USER=postgres
PG_PASSWORD=tu_password
PG_HOST=localhost
PG_PORT=5432
PG_NAME=registro_becarios

# SQL Server
SS_SERVER=localhost
SS_DATABASE=registro_becarios_ss
SS_USER=          # Dejar vacío si usas Windows Authentication
SS_PASSWORD=      # Dejar vacío si usas Windows Authentication
SS_DRIVER=ODBC Driver 17 for SQL Server

# EmailJS (Para reportes)
EMAILJS_PUBLIC_KEY=tu_public_key
EMAILJS_SERVICE_ID=tu_service_id
EMAILJS_TEMPLATE_ID=tu_template_id
```

## 4. Instalación y Ejecución del Proyecto

1. **Abrir una terminal** en la carpeta principal del proyecto.
2. **Crear y activar el entorno virtual** (si no está creado):
   ```bash
   # Crear (solo la primera vez)
   python -m venv venv
   
   # Activar (Windows)
   venv\Scripts\activate
   ```
3. **Instalar dependencias**:
   ```bash
   pip install -r requirements.txt
   ```
4. **Levantar el servidor web**:
   ```bash
   python app.py
   # o alternativamente: flask run
   ```
5. **Acceder a la aplicación**:
   Abre tu navegador web e ingresa a: `http://127.0.0.1:5000`

## 5. Accesos del Sistema
*(Añadir aquí un usuario/contraseña de administrador de prueba si es necesario para la revisión del profesor).*
