from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, JSON, ForeignKey, Numeric, Date
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from config.database import Base
import bcrypt

class Usuario(Base):
    __tablename__ = "usuarios"
    
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), nullable=False)
    usuario = Column(String(50), unique=True, index=True, nullable=False)
    contraseña_hash = Column(String(255), nullable=False)
    rol = Column(String(20), nullable=False)  # superadmin, admin, lector
    activo = Column(Boolean, default=True)
    fecha_creacion = Column(DateTime(timezone=True), server_default=func.now())
    ultimo_login = Column(DateTime(timezone=True))
    proyecto_permitido = Column(String(200))  # JSON string o lista separada por comas
    
    # Relaciones
    bitacoras = relationship("Bitacora", back_populates="usuario")
    emisiones = relationship("EmisionFinal", back_populates="usuario")
    
    def set_password(self, password):
        salt = bcrypt.gensalt(rounds=12)
        self.contraseña_hash = bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
    
    def check_password(self, password):
        return bcrypt.checkpw(password.encode('utf-8'), self.contraseña_hash.encode('utf-8'))

class Proyecto(Base):
    __tablename__ = "proyectos"
    
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), nullable=False)
    descripcion = Column(Text)
    tabla_padron = Column(String(50))
    activo = Column(Boolean, default=True)
    fecha_creacion = Column(DateTime(timezone=True), server_default=func.now())
    config_json = Column(JSON)
    
    # Relaciones
    plantillas = relationship("Plantilla", back_populates="proyecto")

class Plantilla(Base):
    __tablename__ = "plantillas"
    
    id = Column(Integer, primary_key=True, index=True)
    proyecto_id = Column(Integer, ForeignKey("proyectos.id"))
    nombre = Column(String(100), nullable=False)
    descripcion = Column(Text)
    ruta_archivo = Column(String(255))
    tipo_plantilla = Column(String(20))
    campos_json = Column(JSON)  # {campo: {x: 100, y: 200, ancho: 150, ...}}
    activa = Column(Boolean, default=True)
    fecha_creacion = Column(DateTime(timezone=True), server_default=func.now())
    usuario_creador = Column(Integer, ForeignKey("usuarios.id"))
    
    # Relaciones
    proyecto = relationship("Proyecto", back_populates="plantillas")

class Bitacora(Base):
    __tablename__ = "bitacora"
    
    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"))
    accion = Column(String(50), nullable=False)  # login, logout, crear, editar, eliminar
    modulo = Column(String(50), nullable=False)  # auth, proyectos, plantillas, emisiones
    detalles = Column(JSON)
    ip_address = Column(String(45))
    user_agent = Column(Text)
    fecha_evento = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relaciones
    usuario = relationship("Usuario", back_populates="bitacoras")

# Modelos adicionales (estructura básica)
class EmisionTemp(Base):
    __tablename__ = "emisiones_temp"
    
    id = Column(Integer, primary_key=True, index=True)
    proyecto_id = Column(Integer, ForeignKey("proyectos.id"))
    plantilla_id = Column(Integer, ForeignKey("plantillas.id"))
    usuario_id = Column(Integer, ForeignKey("usuarios.id"))
    datos_json = Column(JSON)
    cuenta = Column(String(50))
    codigo_afiliado = Column(String(50))
    estado = Column(String(20))
    error_mensaje = Column(Text)
    fecha_carga = Column(DateTime(timezone=True), server_default=func.now())
    sesion_id = Column(String(100))

class EmisionFinal(Base):
    __tablename__ = "emisiones_final"
    
    id = Column(Integer, primary_key=True, index=True)
    emision_temp_id = Column(Integer)
    proyecto_id = Column(Integer, ForeignKey("proyectos.id"))
    plantilla_id = Column(Integer, ForeignKey("plantillas.id"))
    usuario_id = Column(Integer, ForeignKey("usuarios.id"))
    datos_completos = Column(JSON)
    archivo_generado = Column(String(255))
    fecha_generacion = Column(DateTime(timezone=True))
    estado_generacion = Column(String(20))
    fecha_creacion = Column(DateTime(timezone=True), server_default=func.now())
    
    usuario = relationship("Usuario", back_populates="emisiones")

class ConfiguracionSistema(Base):
    __tablename__ = "configuracion_sistema"
    
    id = Column(Integer, primary_key=True, index=True)
    clave = Column(String(50), unique=True, nullable=False)
    valor = Column(Text)
    tipo = Column(String(20))
    descripcion = Column(Text)
    editable = Column(Boolean, default=True)