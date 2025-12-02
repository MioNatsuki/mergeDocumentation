import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from sqlalchemy import create_engine
from config.database import Base, engine
from core.models import Usuario, Proyecto, Plantilla
from config.settings import settings

def init_database():
    """Inicializa la base de datos y crea usuario superadmin"""
    
    # Crear todas las tablas
    print("Creando tablas en la base de datos...")
    Base.metadata.create_all(bind=engine)
    print("Tablas creadas exitosamente")
    
    # Crear usuario superadmin por defecto
    from sqlalchemy.orm import sessionmaker
    Session = sessionmaker(bind=engine)
    db = Session()
    
    try:
        # Verificar si ya existe el superadmin
        superadmin = db.query(Usuario).filter(Usuario.usuario == "superadmin").first()
        
        if not superadmin:
            superadmin = Usuario(
                nombre="Administrador Principal",
                usuario="superadmin",
                rol="superadmin",
                activo=True,
                proyecto_permitido="*"  # Acceso a todos los proyectos
            )
            superadmin.set_password("admin123")  # Contraseña temporal
            
            db.add(superadmin)
            db.commit()
            print("Usuario superadmin creado:")
            print("Usuario: superadmin")
            print("Contraseña: admin123")
            print("Cambia la contraseña después del primer login!")
        else:
            print("Usuario superadmin ya existe")
        
        # Crear proyecto de ejemplo
        proyecto = db.query(Proyecto).filter(Proyecto.nombre == "Proyecto Demo").first()
        if not proyecto:
            proyecto = Proyecto(
                nombre="Proyecto Demo",
                descripcion="Proyecto de demostración",
                tabla_padron="padron_completo_pensiones",
                activo=True
            )
            db.add(proyecto)
            db.commit()
            print("Proyecto demo creado")
            
    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    init_database()