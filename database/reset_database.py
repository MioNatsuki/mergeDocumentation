import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from config.database import Base, engine
from core.models import Usuario, Proyecto, Plantilla, Bitacora

def reset_database():
    """Reinicia completamente la base de datos (SOLO PARA DESARROLLO)"""
    print("⚠️  ADVERTENCIA: Esto eliminará TODOS los datos existentes")
    confirm = input("¿Estás seguro? (escribe 'SI' para continuar): ")
    
    if confirm != 'SI':
        print("Operación cancelada")
        return
    
    print("🔄 Eliminando tablas existentes...")
    Base.metadata.drop_all(bind=engine)
    
    print("🔄 Creando nuevas tablas...")
    Base.metadata.create_all(bind=engine)
    
    print("✅ Base de datos reiniciada exitosamente")
    print("📋 Ejecuta 'python database/init_db.py' para crear datos de prueba")

if __name__ == "__main__":
    reset_database()