from sqlalchemy.orm import Session
from core.models import Usuario, Bitacora
from utils.logger import auditoria
import datetime

class AuthService:
    def __init__(self, db: Session):
        self.db = db
    
    def autenticar_usuario(self, usuario: str, password: str, ip_address: str = None, user_agent: str = None):
        """Autentica usuario y registra en bitácora"""
        user = self.db.query(Usuario).filter(Usuario.usuario == usuario).first()
        
        if not user or not user.activo:
            self.registrar_intento_fallido(usuario, ip_address, user_agent)
            return None, "Usuario inactivo o no existe"
        
        if not user.check_password(password):
            self.registrar_intento_fallido(usuario, ip_address, user_agent)
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
    
    def registrar_intento_fallido(self, usuario: str, ip_address: str, user_agent: str):
        """Registra intento fallido de login"""
        auditoria(
            db=self.db,
            usuario_id=None,
            accion="login_fallido",
            modulo="auth",
            detalles={"usuario_intento": usuario},
            ip_address=ip_address,
            user_agent=user_agent
        )
    
    def verificar_permisos_proyecto(self, usuario: Usuario, proyecto_id: int) -> bool:
        """Verifica si usuario tiene acceso al proyecto"""
        if usuario.rol == "superadmin":
            return True
        
        if not usuario.proyecto_permitido:
            return False
        
        # Lógica para verificar proyectos permitidos
        proyectos_permitidos = usuario.proyecto_permitido.split(',')
        return str(proyecto_id) in proyectos_permitidos