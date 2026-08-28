# modelos de sql server
from datetime import datetime
from extensiones import db


class Catalogo(db.Model):
    __tablename__ = "catalogos"
    __bind_key__  = "sqlserver"

    id                  = db.Column(db.BigInteger, primary_key=True)
    codigo_referencia   = db.Column(db.String(50))
    nombre              = db.Column(db.String(150), nullable=False)
    padre_id            = db.Column(db.BigInteger, db.ForeignKey("catalogos.id"))
    valor_extra         = db.Column(db.String(255))
    estado              = db.Column(db.Boolean, default=True)
    fecha_creacion      = db.Column(db.DateTime, default=datetime.utcnow)
    fecha_actualizacion = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    hijos = db.relationship("Catalogo", backref=db.backref("padre", remote_side=[id]))

    def esta_activo(self): return self.estado is True
    def __repr__(self): return f"<Catalogo [{self.codigo_referencia}] {self.nombre}>"


class Becario(db.Model):
    __tablename__ = "becarios"
    __bind_key__  = "sqlserver"

    id_becario           = db.Column(db.Integer, primary_key=True)
    cedula               = db.Column(db.String(13), unique=True, nullable=False)
    nombres              = db.Column(db.String(100), nullable=False)
    apellidos            = db.Column(db.String(100), nullable=False)
    correo               = db.Column(db.String(150), unique=True, nullable=False)
    telefono             = db.Column(db.String(15))
    rango_militar        = db.Column(db.String(50))
    unidad               = db.Column(db.String(100))
    numero_militar       = db.Column(db.String(30))
    universidad          = db.Column(db.String(150), default="PUCE")
    carrera              = db.Column(db.String(150))
    semestre             = db.Column(db.Integer)
    anio_inicio          = db.Column(db.Integer)
    anio_fin_estimado    = db.Column(db.Integer)
    estado               = db.Column(db.String(1), default="A")
    fecha_registro       = db.Column(db.DateTime, default=datetime.utcnow)
    fecha_actualizacion  = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    registrado_por       = db.Column(db.String(100))

    novedades = db.relationship("NovedadDiaria", back_populates="becario", lazy="dynamic")

    def esta_activo(self): return self.estado == "A"
    def nombre_completo(self): return f"{self.apellidos} {self.nombres}"

    def identificacion_militar(self):
        partes = []
        if self.rango_militar: partes.append(self.rango_militar)
        partes.append(self.nombre_completo())
        return " ".join(partes)

    def __repr__(self): return f"<Becario {self.cedula}>"


class NovedadDiaria(db.Model):
    __tablename__ = "novedades_diarias"
    __bind_key__  = "sqlserver"

    id_novedad         = db.Column(db.Integer, primary_key=True)
    id_becario         = db.Column(db.Integer, db.ForeignKey("becarios.id_becario"), nullable=False)
    id_catalogo_estado = db.Column(db.BigInteger, db.ForeignKey("catalogos.id"), nullable=False)
    fecha              = db.Column(db.Date, nullable=False)
    hora               = db.Column(db.Time, nullable=False)
    observacion        = db.Column(db.Text)
    estado             = db.Column(db.String(1), default="A")

    becario    = db.relationship("Becario", back_populates="novedades")
    estado_cat = db.relationship("Catalogo")

    def nombre_estado(self): return self.estado_cat.nombre if self.estado_cat else "—"
    def __repr__(self): return f"<NovedadDiaria becario={self.id_becario} fecha={self.fecha}>"


class Auditoria(db.Model):
    __tablename__ = "auditoria"
    __bind_key__  = "sqlserver"

    id_auditoria     = db.Column(db.Integer, primary_key=True)
    tabla_afectada   = db.Column(db.String(50), nullable=False)
    operacion        = db.Column(db.String(10), nullable=False)
    usuario_bd       = db.Column(db.String(100))
    usuario_sistema  = db.Column(db.String(100))
    fecha_hora       = db.Column(db.DateTime, default=datetime.utcnow)
    datos_anteriores = db.Column(db.Text)
    datos_nuevos     = db.Column(db.Text)
    ip_origen        = db.Column(db.String(45))

    def __repr__(self): return f"<Auditoria {self.operacion} en {self.tabla_afectada}>"
