# init_users.py
from databasemanager import DatabaseManager
from authentication import AuthenticationManager

def initialize_default_users():
    """Crear usuarios por defecto para testing"""
    db = DatabaseManager()
    
    if not db.connect():
        print("No se pudo conectar a la base de datos")
        return
    
    # Datos de usuarios iniciales
    default_users = [
        {
            'nombre': 'Administrador Principal',
            'usuario': 'admin',
            'password': 'admin123',
            'rol': 'administrador',
            'proyecto_permitido': 'pensiones'
        },
        {
            'nombre': 'Analista de Datos',
            'usuario': 'sistemas',
            'password': 'super123',
            'rol': 'sistemas', 
            'proyecto_permitido': 'pensiones'
        },
        {
            'nombre': 'Auxiliar de Sistemas',
            'usuario': 'auxiliar',
            'password': 'lector123', 
            'rol': 'lector',
            'proyecto_permitido': 'pensiones'
        }
    ]
    
    auth = AuthenticationManager(db)
    
    print("INICIALIZANDO USUARIOS POR DEFECTO\n")
    
    for user_data in default_users:
        try:
            # Verificar si el usuario ya existe
            existing_user = auth._get_user_by_username(user_data['usuario'])
            
            if existing_user:
                print(f"Usuario {user_data['usuario']} ya existe, omitiendo...")
                continue
            
            # Crear usuario
            success = db.crear_usuario(user_data)
            if success:
                print(f"Usuario {user_data['usuario']} creado exitosamente")
            else:
                print(f"Error creando usuario {user_data['usuario']}")
                
        except Exception as e:
            print(f"Error con usuario {user_data['usuario']}: {e}")
    
    db.disconnect()
    print("\nInicialización de usuarios completada")

if __name__ == "__main__":
    initialize_default_users()