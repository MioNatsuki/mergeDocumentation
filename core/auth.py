from sqlalchemy.orm import Session
from core.models import Usuario, Bitacora
from utils.logger import auditoria
import datetime
import socket

class AuthService:
    def __init__(self, db: Session):
        self.db = db
    
    def obtener_ip_real(self):
        """Obtiene la IP real del cliente o retorna una válida para localhost"""
        try:
            # Intentar obtener IP local
            hostname = socket.gethostname()
            local_ip = socket.gethostbyname(hostname)
            return local_ip
        except:
            # Fallback a IPv4 localhost
            return "127.0.0.1"
    
    def autenticar_usuario(self, usuario: str, password: str, ip_address: str = None, user_agent: str = None):
        """Autentica usuario y registra en bitácora"""
        try:
            # Si no se proporciona IP, obtener una válida
            if not ip_address or ip_address == "localhost":
                ip_address = self.obtener_ip_real()
            
            user = self.db.query(Usuario).filter(Usuario.usuario == usuario).first()
            
            if not user:
                self.registrar_intento_fallido(usuario, ip_address, user_agent, "Usuario no existe")
                return None, "Credenciales incorrectas"
            
            if not user.activo:
                self.registrar_intento_fallido(usuario, ip_address, user_agent, "Usuario inactivo")
                return None, "Usuario inactivo"
            
            if not hasattr(user, 'check_password'):
                self.registrar_intento_fallido(usuario, ip_address, user_agent, "Error en modelo de usuario")
                return None, "Error interno del sistema"
            
            if not user.check_password(password):
                self.registrar_intento_fallido(usuario, ip_address, user_agent, "Contraseña incorrecta")
                return None, "Credenciales incorrectas"
            
            # Actualizar último login
            user.ultimo_login = datetime.datetime.now()
            self.db.commit()
            
            # Registrar en bitácora
            auditoria(
                db=self.db,
                usuario_id=user.id,
                accion="login",
                modulo="auth",
                ip_address=ip_address,
                user_agent=user_agent
            )
            
            return user, "Autenticación exitosa"
            
        except Exception as e:
            ip_fallback = self.obtener_ip_real()
            self.registrar_intento_fallido(usuario, ip_fallback, user_agent, f"Error: {str(e)}")
            return None, f"Error de autenticación: {str(e)}"
    
    def registrar_intento_fallido(self, usuario: str, ip_address: str, user_agent: str, motivo: str = ""):
        """Registra intento fallido de login"""
        detalles = {"usuario_intento": usuario}
        if motivo:
            detalles["motivo"] = motivo
            
        # Asegurar que la IP sea válida
        if not ip_address or ip_address == "localhost":
            ip_address = self.obtener_ip_real()
            
        auditoria(
            db=self.db,
            usuario_id=None,
            accion="login_fallido",
            modulo="auth",
            detalles=detalles,
            ip_address=ip_address,
            user_agent=user_agent
        )
    
    def verificar_permisos_proyecto(self, usuario: Usuario, proyecto_id: int) -> bool:
        """Verifica si usuario tiene acceso al proyecto"""
        if usuario.rol == "superadmin":
            return True
        
        if not usuario.proyecto_permitido:
            return False
        
        proyectos_permitidos = [p.strip() for p in usuario.proyecto_permitido.split(',')]
        return str(proyecto_id) in proyectos_permitidos