# modelos de postgres
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from extensiones import db


# tabla perfil
class Perfil(db.Model):
    __tablename__ = "perfil"
    __bind_key__  = "postgres"

    id_perfil   = db.Column(db.Integer, primary_key=True)
    nombre      = db.Column(db.String(50), nullable=False, unique=True)
    descripcion = db.Column(db.String(255))
    estado      = db.Column(db.String(1), default="A")

    def esta_activo(self): return self.estado == "A"
    def __repr__(self): return f"<Perfil {self.nombre}>"


# tabla usuario
class Usuario(db.Model):
    __tablename__ = "usuario"
    __bind_key__  = "postgres"

    id_usuario    = db.Column(db.Integer, primary_key=True)
    cedula        = db.Column(db.String(13), unique=True, nullable=False)
    nombres       = db.Column(db.String(100), nullable=False)
    apellidos     = db.Column(db.String(100), nullable=False)
    correo        = db.Column(db.String(150), unique=True, nullable=False)
    rango_militar = db.Column(db.String(50))
    password_hash = db.Column(db.String(255), nullable=False)
    estado        = db.Column(db.String(1), default="A")

    perfiles      = db.relationship("PerfilUsuario", back_populates="usuario", lazy="dynamic")
    historial_pwd = db.relationship("UsuarioClave",  back_populates="usuario", lazy="dynamic",
                                    order_by="UsuarioClave.fecha_cambio.desc()")

    def set_password(self, password_plano):
        self.password_hash = generate_password_hash(password_plano)

    def check_password(self, password_plano):
        return check_password_hash(self.password_hash, password_plano)

    def esta_activo(self): return self.estado == "A"
    def nombre_completo(self): return f"{self.apellidos} {self.nombres}"

    def get_rol(self):
        pu = self.perfiles.filter_by(estado="A").first()
        return pu.perfil.nombre if pu else None

    def __repr__(self): return f"<Usuario {self.cedula}>"


# historial de claves
class UsuarioClave(db.Model):
    __tablename__ = "usuario_clave"
    __bind_key__  = "postgres"

    id_clave      = db.Column(db.Integer, primary_key=True)
    id_usuario    = db.Column(db.Integer, db.ForeignKey("usuario.id_usuario"), nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    fecha_cambio  = db.Column(db.DateTime, default=datetime.utcnow)
    activa        = db.Column(db.Boolean, default=True)

    usuario = db.relationship("Usuario", back_populates="historial_pwd")


# tabla union perfil usuario
class PerfilUsuario(db.Model):
    __tablename__ = "perfil_usuario"
    __bind_key__  = "postgres"

    id_usuario = db.Column(db.Integer, db.ForeignKey("usuario.id_usuario"), primary_key=True)
    id_perfil  = db.Column(db.Integer, db.ForeignKey("perfil.id_perfil"),   primary_key=True)
    estado     = db.Column(db.String(1), default="A")

    usuario = db.relationship("Usuario", back_populates="perfiles")
    perfil  = db.relationship("Perfil")


# jerarquia de roles
class PerfilBase:
    # clase base para roles
    NOMBRE_ROL: str = ""

    def __init__(self, usuario: Usuario):
        self.usuario = usuario

    def dashboard_url(self) -> str:
        raise NotImplementedError

    def permisos(self) -> list:
        raise NotImplementedError


class PerfilAdmin(PerfilBase):
    NOMBRE_ROL = "ADMINISTRADOR"

    def dashboard_url(self): return "/admin/dashboard"

    def permisos(self):
        return ["ver_becarios", "crear_becario", "editar_becario",
                "dar_baja_becario", "ver_auditoria", "ver_reportes",
                "enviar_reportes", "gestionar_usuarios"]


class PerfilBecario(PerfilBase):
    NOMBRE_ROL = "BECARIO"

    def dashboard_url(self): return "/becarios/mi-perfil"

    def permisos(self):
        return ["registrar_novedad", "ver_mi_historial"]


def crear_perfil_instancia(usuario: Usuario) -> PerfilBase:
    # crear instancia de perfil
    rol = usuario.get_rol()
    if rol == PerfilAdmin.NOMBRE_ROL:
        return PerfilAdmin(usuario)
    elif rol == PerfilBecario.NOMBRE_ROL:
        return PerfilBecario(usuario)
    raise ValueError(f"Rol desconocido: {rol}")
