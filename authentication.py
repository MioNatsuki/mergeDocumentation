# authentication_fixed.py
import bcrypt
import logging
from typing import Optional, Dict, Tuple
from databasemanager import DatabaseManager
from datetime import datetime

class AuthenticationManager:
    """Gestor de autenticación y seguridad del sistema - VERSIÓN COMPLETAMENTE CORREGIDA"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
        self.logger = self._setup_logger()
        self.current_user = None
    
    def _setup_logger(self) -> logging.Logger:
        """Configurar logger específico para autenticación"""
        logger = logging.getLogger('AuthenticationManager')
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        return logger
    
    def login(self, username: str, password: str, ip_address: str = "127.0.0.1") -> Tuple[bool, Optional[Dict], str]:
        """
        Realizar proceso de autenticación
        
        Returns:
            Tuple[bool, Optional[Dict], str]: (éxito, datos_usuario, mensaje)
        """
        try:
            # Validaciones básicas
            if not username or not password:
                self._log_failed_attempt(None, ip_address, "Usuario o contraseña vacíos", username)
                return False, None, "Usuario y contraseña son requeridos"
            
            if len(username) < 3 or len(password) < 4:
                self._log_failed_attempt(None, ip_address, "Credenciales muy cortas", username)
                return False, None, "Credenciales inválidas"
            
            # Buscar usuario en la base de datos
            user = self._get_user_by_username(username)
            
            if not user:
                self._log_failed_attempt(None, ip_address, "Usuario no encontrado", username)
                return False, None, "Credenciales incorrectas"
            
            if not user['activo']:
                self._log_failed_attempt(user['id'], ip_address, "Usuario inactivo", username)
                return False, None, "Usuario inactivo. Contacte al administrador"
            
            # Verificar contraseña
            if self._verify_password(password, user['contraseña_hash']):
                # Login exitoso
                self.current_user = user
                
                # Registrar en bitácora
                self.db.registrar_bitacora(
                    user_id=user['id'],
                    accion='login_exitoso',
                    modulo='autenticacion',
                    detalles={'ip': ip_address, 'user_agent': 'Sistema_Desktop'},
                    ip_address=ip_address,
                    user_agent='Sistema_Desktop'
                )
                
                # Actualizar último login
                self._update_last_login(user['id'])
                
                self.logger.info(f"✅ Login exitoso: {username} desde {ip_address}")
                return True, user, f"Bienvenido {user['nombre']}"
            else:
                # Contraseña incorrecta
                self._log_failed_attempt(user['id'], ip_address, "Contraseña incorrecta", username)
                return False, None, "Credenciales incorrectas"
                
        except Exception as e:
            self.logger.error(f"❌ Error en proceso de login: {e}")
            return False, None, f"Error del sistema: {str(e)}"
    
    def _log_failed_attempt(self, user_id: Optional[int], ip_address: str, reason: str, username: str = None):
        """Registrar intento fallido de login - CORREGIDO"""
        detalles = {
            'ip': ip_address,
            'razon': reason
        }
        
        if username:
            detalles['usuario_intento'] = username
        
        self.db.registrar_bitacora(
            usuario_id=user_id,
            accion='login_fallido',
            modulo='autenticacion',
            detalles=detalles,
            ip_address=ip_address,
            user_agent='Sistema_Desktop'
        )

    def logout(self, ip_address: str = "127.0.0.1") -> bool:
        """Cerrar sesión del usuario actual"""
        if self.current_user:
            user_id = self.current_user['id']
            username = self.current_user['usuario']
            
            # Registrar en bitácora
            self.db.registrar_bitacora(
                usuario_id=user_id,
                accion='logout',
                modulo='autenticacion',
                detalles={'ip': ip_address},
                ip_address=ip_address,
                user_agent='Sistema_Desktop'
            )
            
            self.logger.info(f"🔒 Logout: {username} desde {ip_address}")
            self.current_user = None
            return True
        return False
    
    def change_password(self, current_password: str, new_password: str, confirm_password: str) -> Tuple[bool, str]:
        """Cambiar contraseña del usuario actual"""
        try:
            if not self.current_user:
                return False, "No hay usuario autenticado"
            
            if new_password != confirm_password:
                return False, "Las contraseñas nuevas no coinciden"
            
            if len(new_password) < 6:
                return False, "La contraseña debe tener al menos 6 caracteres"
            
            # Verificar contraseña actual
            if not self._verify_password(current_password, self.current_user['contraseña_hash']):
                return False, "Contraseña actual incorrecta"
            
            # Generar nuevo hash
            new_password_hash = self._hash_password(new_password)
            
            # Actualizar en base de datos
            query = "UPDATE usuarios SET contraseña_hash = %s WHERE id = %s"
            self.db.execute_query(query, (new_password_hash, self.current_user['id']))
            
            # Registrar en bitácora
            self.db.registrar_bitacora(
                usuario_id=self.current_user['id'],
                accion='cambio_password',
                modulo='autenticacion',
                detalles={'cambio': 'exitoso'}
            )
            
            self.logger.info(f"🔑 Contraseña cambiada para: {self.current_user['usuario']}")
            return True, "Contraseña cambiada exitosamente"
            
        except Exception as e:
            self.logger.error(f"❌ Error cambiando contraseña: {e}")
            return False, f"Error del sistema: {str(e)}"
    
    def _get_user_by_username(self, username: str) -> Optional[Dict]:
        """Obtener usuario por nombre de usuario"""
        query = """
            SELECT id, nombre, usuario, contraseña_hash, rol, activo, proyecto_permitido
            FROM usuarios 
            WHERE usuario = %s
        """
        result = self.db.execute_query(query, (username,), fetch=True)
        return dict(result[0]) if result else None
    
    def _verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verificar contraseña contra hash bcrypt"""
        try:
            return bcrypt.checkpw(
                plain_password.encode('utf-8'),
                hashed_password.encode('utf-8')
            )
        except Exception as e:
            self.logger.error(f"❌ Error verificando contraseña: {e}")
            return False
    
    def _hash_password(self, password: str) -> str:
        """Generar hash bcrypt para contraseña"""
        return bcrypt.hashpw(
            password.encode('utf-8'),
            bcrypt.gensalt()
        ).decode('utf-8')
    
    def _update_last_login(self, user_id: int):
        """Actualizar último login del usuario"""
        query = "UPDATE usuarios SET ultimo_login = %s WHERE id = %s"
        self.db.execute_query(query, (datetime.now(), user_id))
    
    def is_authenticated(self) -> bool:
        """Verificar si hay un usuario autenticado"""
        return self.current_user is not None
    
    def has_permission(self, required_role: str) -> bool:
        """Verificar si el usuario actual tiene el rol requerido"""
        if not self.current_user:
            return False
        
        # Jerarquía de roles (de mayor a menor privilegio)
        role_hierarchy = {
            'administrador': 4,
            'supervisor': 3,
            'capturista': 2,
            'lector': 1
        }
        
        user_role_level = role_hierarchy.get(self.current_user['rol'], 0)
        required_role_level = role_hierarchy.get(required_role, 0)
        
        return user_role_level >= required_role_level
    
    def get_user_info(self) -> Optional[Dict]:
        """Obtener información del usuario actual"""
        return self.current_user.copy() if self.current_user else None