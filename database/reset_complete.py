import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from config.database import Base, engine
from core.models import Usuario

def reset_complete_database():
    """Reinicia completamente la base de datos y crea datos iniciales"""
    
    print("ADVERTENCIA: Esto eliminará TODOS los datos existentes")
    confirm = input("¿Estás seguro? (escribe 'SI' para continuar): ")
    
    if confirm != 'SI':
        print("Operación cancelada")
        return
    
    try:
        print("Eliminando todas las tablas...")
        Base.metadata.drop_all(bind=engine)
        
        print("Creando todas las tablas nuevas...")
        Base.metadata.create_all(bind=engine)
        
        print("Creando usuario superadmin...")
        crear_usuario_superadmin()
        
        print("Base de datos reiniciada exitosamente")
        
    except Exception as e:
        print(f"Error: {e}")

def crear_usuario_superadmin():
    """Crea el usuario superadmin por defecto"""
    from config.database import SessionLocal
    
    db = SessionLocal()
    try:
        # Verificar si ya existe
        superadmin = db.query(Usuario).filter(Usuario.usuario == "superadmin").first()
        
        if not superadmin:
            superadmin = Usuario(
                nombre="Administrador Principal",
                usuario="superadmin",
                rol="superadmin",
                activo=True,
                proyecto_permitido="*"
            )
            superadmin.set_password("admin123")
            
            db.add(superadmin)
            db.commit()
            print("Usuario superadmin creado:")
            print("Usuario: superadmin")
            print("Contraseña: admin123")
        else:
            print("Usuario superadmin ya existe")
            
    except Exception as e:
        print(f"Error creando superadmin: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    reset_complete_database()