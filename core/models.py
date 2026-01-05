from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, JSON, ForeignKey, Numeric
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from config.database import Base
import bcrypt

class Usuario(Base):
    __tablename__ = "usuarios"
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), nullable=False)
    usuario = Column(String(50), unique=True, index=True, nullable=False)
    contraseña_hash = Column(String(255), nullable=False)
    
    rol = Column(
        String(20), 
        nullable=False, 
        default='auxiliar',  # Por defecto el rol menos privilegiado
        server_default='auxiliar'  # También a nivel de BD
    )  # Valores: 'superadmin', 'analista', 'auxiliar'
    
    activo = Column(Boolean, default=True)
    fecha_creacion = Column(DateTime(timezone=True), server_default=func.now())
    ultimo_login = Column(DateTime(timezone=True))

    proyecto_permitido = Column(String(200))
    
    bitacoras = relationship("Bitacora", back_populates="usuario")

    def set_password(self, password):
        """Encripta y establece la contraseña"""
        salt = bcrypt.gensalt(rounds=12)
        self.contraseña_hash = bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
    
    def check_password(self, password):
        """Verifica si la contraseña coincide con el hash"""
        try:
            return bcrypt.checkpw(password.encode('utf-8'), self.contraseña_hash.encode('utf-8'))
        except Exception:
            return False
    
    def puede_acceder_proyecto(self, proyecto_id: int) -> bool:
        """Verifica si el usuario puede acceder a un proyecto específico"""
        if self.rol == 'superadmin':
            return True
        
        if not self.proyecto_permitido:
            return False
        
        # Para analista/auxiliar: proyecto_permitido debe contener el ID del proyecto
        try:
            # Puede ser un solo ID o una lista separada por comas
            proyectos_permitidos = [int(p.strip()) for p in self.proyecto_permitido.split(',') if p.strip().isdigit()]
            return proyecto_id in proyectos_permitidos
        except:
            return False
    
    def puede_crear_proyectos(self) -> bool:
        """Verifica si puede crear proyectos"""
        return self.rol == 'superadmin'
    
    def puede_editar_proyectos(self) -> bool:
        """Verifica si puede editar proyectos"""
        return self.rol in ['superadmin', 'analista']
    
    def puede_eliminar_proyectos(self) -> bool:
        """Verifica si puede eliminar proyectos (soft delete)"""
        return self.rol == 'superadmin'
    
    def puede_gestionar_plantillas(self) -> bool:
        """Verifica si puede crear/editar plantillas"""
        return self.rol in ['superadmin', 'analista']
    
    def puede_ver_estadisticas_globales(self) -> bool:
        """Verifica si puede ver estadísticas de todos los proyectos"""
        return self.rol == 'superadmin'
    
    def puede_ver_bitacora(self) -> bool:
        """Verifica si puede ver la bitácora completa"""
        return self.rol == 'superadmin'

class Proyecto(Base):
    __tablename__ = "proyectos"
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), nullable=False)
    descripcion = Column(Text)
    tabla_padron = Column(String(100))  # UUID del padrón (referencia a identificador_padrones)
    activo = Column(Boolean, default=True)
    fecha_creacion = Column(DateTime(timezone=True), server_default=func.now())
    config_json = Column(JSON)
    is_deleted = Column(Boolean, default=False)
    logo = Column(String(500))
    
    plantillas = relationship("Plantilla", back_populates="proyecto")

class IdentificadorPadrones(Base):
    __tablename__ = "identificador_padrones"
    __table_args__ = {'extend_existing': True}
    
    uuid_padron = Column(String(100), primary_key=True, index=True)
    nombre_tabla = Column(String(100), unique=True, nullable=False)  # nombre REAL de la tabla
    activo = Column(Boolean, default=True)
    descripcion = Column(Text)

class Plantilla(Base):
    __tablename__ = "plantillas"
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True, index=True)
    proyecto_id = Column(Integer, ForeignKey("proyectos.id"))
    nombre = Column(String(100), nullable=False)
    descripcion = Column(Text)
    
    # 🆕 CAMPOS NUEVOS PARA WORD-BASED
    ruta_archivo_docx = Column(String(500))  # Ruta al archivo Word original
    campos_mapeo = Column(JSON)  # {"nombre": "nombre_completo", "direccion": "calle"}
    configuracion = Column(JSON)  # {"fuente": "Calibri", "tamano": 11}
    
    # 🏷️ CAMPOS EXISTENTES (legacy - mantener compatibilidad)
    ruta_archivo_pdf_legacy = Column(String(255))  # Renombrado de ruta_archivo
    tipo_plantilla = Column(String(20))
    campos_json = Column(JSON)  # Legacy - campos con coordenadas
    activa = Column(Boolean, default=True)
    fecha_creacion = Column(DateTime(timezone=True), server_default=func.now())
    usuario_creador = Column(Integer, ForeignKey("usuarios.id"))
    is_deleted = Column(Boolean, default=False)
    
    # Relaciones
    proyecto = relationship("Proyecto", back_populates="plantillas")

class Bitacora(Base):
    __tablename__ = "bitacora"
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"))
    accion = Column(String(50), nullable=False)
    modulo = Column(String(50), nullable=False)
    detalles = Column(JSON)
    ip_address = Column(String(45))
    user_agent = Column(Text)
    fecha_evento = Column(DateTime(timezone=True), server_default=func.now())
    
    usuario = relationship("Usuario", back_populates="bitacoras")

class EmisionTemp(Base):
    __tablename__ = "emisiones_temp"
    __table_args__ = {'extend_existing': True}
    
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
    orden_impresion = Column(Integer)  # 🆕 NUEVO

class EmisionFinal(Base):
    __tablename__ = "emisiones_final"
    __table_args__ = {'extend_existing': True}
    
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
    cuenta = Column(String(50))
    orden_impresion = Column(Integer)

class EmisionesAcumuladas(Base):
    __tablename__ = "emisiones_acumuladas"
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True, index=True)
    proyecto_id = Column(Integer, ForeignKey("proyectos.id"))
    plantilla_id = Column(Integer, ForeignKey("plantillas.id"))
    usuario_id = Column(Integer, ForeignKey("usuarios.id"))
    cuenta = Column(String(50))
    codigo_afiliado = Column(String(50))
    nombre_afiliado = Column(String(200))
    datos_completos = Column(JSON)
    nombre_archivo = Column(String(255))
    ruta_archivo = Column(String(500))
    fecha_emision = Column(DateTime(timezone=True))
    fecha_registro = Column(DateTime(timezone=True), server_default=func.now())

class ConfiguracionSistema(Base):
    __tablename__ = "configuracion_sistema"
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True, index=True)
    clave = Column(String(50), unique=True, nullable=False)
    valor = Column(Text)
    tipo = Column(String(20))
    descripcion = Column(Text)
    editable = Column(Boolean, default=True)