import psycopg2
from psycopg2 import sql
from psycopg2.extras import RealDictCursor
import logging
import bcrypt
from typing import Dict, List, Optional, Any
import json
from datetime import datetime
import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

class DatabaseManager:
    """Gestor principal de base de datos con conexión PostgreSQL"""
    
    def __init__(self):
        self.connection = None
        self.logger = self._setup_logger()
        self._connection_params = self._get_connection_params()
    
    def _setup_logger(self) -> logging.Logger:
        """Configurar sistema de logging"""
        logger = logging.getLogger('DatabaseManager')
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        return logger
    
    def _get_connection_params(self) -> Dict[str, str]:
        """Obtener parámetros de conexión desde variables de entorno o config"""
        return {
            'host': os.getenv('DB_HOST', 'localhost'),
            'database': os.getenv('DB_NAME', 'sistema_emisiones'),
            'user': os.getenv('DB_USER', 'postgres'),
            'password': os.getenv('DB_PASSWORD', ''),
            'port': os.getenv('DB_PORT', '5432')
        }
    
    def connect(self) -> bool:
        """Establecer conexión con la base de datos"""
        try:
            self.connection = psycopg2.connect(
                **self._connection_params,
                cursor_factory=RealDictCursor
            )
            self.logger.info("Conexión a PostgreSQL establecida correctamente")
            return True
        except Exception as e:
            self.logger.error(f"Error conectando a la base de datos: {e}")
            return False
    
    def disconnect(self):
        """Cerrar conexión con la base de datos"""
        if self.connection:
            self.connection.close()
            self.logger.info("Conexión a PostgreSQL cerrada")
    
    def execute_query(self, query: str, params: tuple = None, fetch: bool = False) -> Optional[List[Dict]]:
        """Ejecutar consulta genérica con manejo de errores"""
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(query, params)
                
                if fetch:
                    result = cursor.fetchall()
                    return result
                else:
                    self.connection.commit()
                    return None
                    
        except Exception as e:
            self.connection.rollback()
            self.logger.error(f"Error en consulta: {e}\nConsulta: {query}\nParams: {params}")
            raise
    
    # =============================================
    # MÉTODOS ESPECÍFICOS PARA AUTENTICACIÓN
    # =============================================
    
    def verificar_usuario(self, usuario: str, password: str) -> Optional[Dict]:
        """Verificar credenciales de usuario"""
        query = """
            SELECT id, nombre, usuario, contraseña_hash, rol, activo, proyecto_permitido
            FROM usuarios 
            WHERE usuario = %s AND activo = true
        """
        
        try:
            result = self.execute_query(query, (usuario,), fetch=True)
            
            if result and bcrypt.checkpw(password.encode('utf-8'), result[0]['contraseña_hash'].encode('utf-8')):
                # Registrar login exitoso en bitácora
                self.registrar_bitacora(
                    result[0]['id'], 
                    'login_exitoso', 
                    'autenticacion',
                    {'ip': '127.0.0.1'}  # IP temporal
                )
                
                # Actualizar último login
                self.actualizar_ultimo_login(result[0]['id'])
                
                return dict(result[0])
            else:
                # Registrar intento fallido
                self.registrar_bitacora(
                    None,  # Usuario no identificado
                    'login_fallido', 
                    'autenticacion',
                    {'usuario_intento': usuario, 'ip': '127.0.0.1'}
                )
                return None
                
        except Exception as e:
            self.logger.error(f"Error en verificación de usuario: {e}")
            return None
    
    def actualizar_ultimo_login(self, usuario_id: int):
        """Actualizar fecha del último login"""
        query = "UPDATE usuarios SET ultimo_login = %s WHERE id = %s"
        self.execute_query(query, (datetime.now(), usuario_id))
    
    def registrar_bitacora(self, usuario_id: Optional[int], accion: str, modulo: str, detalles: Dict = None, ip_address: str = "127.0.0.1", user_agent: str = "Sistema_Desktop"):
        """Registrar evento en la bitácora del sistema"""
        query = """
            INSERT INTO bitacora (usuario_id, accion, modulo, detalles, ip_address, user_agent)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        
        detalles_json = json.dumps(detalles) if detalles else '{}'
        
        self.execute_query(query, (usuario_id, accion, modulo, detalles_json, ip_address, user_agent))
    
    # =============================================
    # MÉTODOS PARA GESTIÓN DE USUARIOS
    # =============================================
    
    def crear_usuario(self, usuario_data: Dict) -> bool:
        """Crear nuevo usuario en el sistema"""
        try:
            # Hash de contraseña
            password_hash = bcrypt.hashpw(
                usuario_data['password'].encode('utf-8'), 
                bcrypt.gensalt()
            ).decode('utf-8')
            
            query = """
                INSERT INTO usuarios (nombre, usuario, contraseña_hash, rol, proyecto_permitido)
                VALUES (%s, %s, %s, %s, %s)
            """
            
            self.execute_query(query, (
                usuario_data['nombre'],
                usuario_data['usuario'],
                password_hash,
                usuario_data['rol'],
                usuario_data.get('proyecto_permitido', 'pensiones')
            ))
            
            self.logger.info(f"Usuario {usuario_data['usuario']} creado exitosamente")
            return True
            
        except Exception as e:
            self.logger.error(f"Error creando usuario: {e}")
            return False
    
    def obtener_usuarios(self) -> List[Dict]:
        """Obtener lista de todos los usuarios (sin contraseñas)"""
        query = """
            SELECT id, nombre, usuario, rol, activo, proyecto_permitido, fecha_creacion, ultimo_login
            FROM usuarios 
            ORDER BY nombre
        """
        return self.execute_query(query, fetch=True) or []
    
    # =============================================
    # MÉTODOS PARA GESTIÓN DE PROYECTOS
    # =============================================
    
    def obtener_proyectos(self, usuario_id: int = None) -> List[Dict]:
        """Obtener lista de proyectos disponibles"""
        query = "SELECT id, nombre, descripcion, activo FROM proyectos WHERE activo = true ORDER BY nombre"
        return self.execute_query(query, fetch=True) or []
    
    def obtener_proyecto_por_nombre(self, nombre: str) -> Optional[Dict]:
        """Obtener proyecto específico por nombre"""
        query = "SELECT * FROM proyectos WHERE nombre = %s"
        result = self.execute_query(query, (nombre,), fetch=True)
        return dict(result[0]) if result else None
    
    # =============================================
    # MÉTODOS PARA CONFIGURACIÓN
    # =============================================
    
    def obtener_configuracion(self, clave: str = None) -> Any:
        """Obtener configuración del sistema"""
        if clave:
            query = "SELECT valor FROM configuracion_sistema WHERE clave = %s"
            result = self.execute_query(query, (clave,), fetch=True)
            return result[0]['valor'] if result else None
        else:
            query = "SELECT clave, valor, descripcion FROM configuracion_sistema"
            return self.execute_query(query, fetch=True) or []
    
    # =============================================
    # MÉTODOS DE HEALTH CHECK
    # =============================================
    
    def health_check(self) -> bool:
        """Verificar que la base de datos esté funcionando correctamente"""
        try:
            result = self.execute_query("SELECT 1 as test", fetch=True)
            return bool(result and result[0]['test'] == 1)
        except Exception:
            return False
    
    def get_database_info(self) -> Dict:
        """Obtener información de la base de datos"""
        try:
            # Obtener versión de PostgreSQL
            version_result = self.execute_query("SELECT version()", fetch=True)
            
            # Obtener estadísticas básicas
            usuarios_count = self.execute_query("SELECT COUNT(*) FROM usuarios", fetch=True)[0]['count']
            proyectos_count = self.execute_query("SELECT COUNT(*) FROM proyectos", fetch=True)[0]['count']
            
            return {
                'version': version_result[0]['version'] if version_result else 'Desconocida',
                'total_usuarios': usuarios_count,
                'total_proyectos': proyectos_count,
                'conexion_activa': self.connection is not None
            }
        except Exception as e:
            self.logger.error(f"Error obteniendo info de BD: {e}")
            return {'error': str(e)}

class DatabaseTester:
    """Clase para probar el DatabaseManager"""
    
    def __init__(self):
        self.db = DatabaseManager()
    
    def run_tests(self):
        """Ejecutar suite de pruebas"""
        print("INICIANDO PRUEBAS DEL DATABASEMANAGER\n")
        
        # 1. Conexión
        print("1. Probando conexión...")
        if self.db.connect():
            print("Conexión exitosa")
        else:
            print("Falló la conexión")
            return
        
        # 2. Health Check
        print("2. Health check...")
        if self.db.health_check():
            print("Health check pasado")
        else:
            print("Health check falló")
        
        # 3. Info de BD
        print("3. Información de BD...")
        info = self.db.get_database_info()
        print(f"{info}")
        
        # 4. Proyectos
        print("4. Obteniendo proyectos...")
        proyectos = self.db.obtener_proyectos()
        print(f"Proyectos encontrados: {len(proyectos)}")
        
        # 5. Configuración
        print("5. Configuración del sistema...")
        config = self.db.obtener_configuracion()
        print(f"Configuraciones: {len(config)}")
        
        # 6. Usuarios
        print("6. Lista de usuarios...")
        usuarios = self.db.obtener_usuarios()
        print(f"Usuarios en sistema: {len(usuarios)}")
        
        print("\nPRUEBAS COMPLETADAS")
        self.db.disconnect()

if __name__ == "__main__":
    tester = DatabaseTester()
    tester.run_tests()