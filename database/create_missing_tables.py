import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from config.database import Base, engine
from core.models import ConfiguracionSistema, EmisionesAcumuladas, EmisionFinal

def create_missing_tables():
    """Crea las tablas faltantes en la base de datos"""
    print("🔧 Creando tablas faltantes...")
    
    try:
        # Crear solo las tablas faltantes
        ConfiguracionSistema.__table__.create(bind=engine, checkfirst=True)
        EmisionesAcumuladas.__table__.create(bind=engine, checkfirst=True)
        EmisionFinal.__table__.create(bind=engine, checkfirst=True)
        
        print("✅ Tablas faltantes creadas exitosamente")
        
        # Insertar configuraciones por defecto
        insert_default_configurations()
        
    except Exception as e:
        print(f"❌ Error creando tablas: {e}")

def insert_default_configurations():
    """Inserta configuraciones por defecto"""
    from config.database import SessionLocal
    from core.models import ConfiguracionSistema
    
    db = SessionLocal()
    try:
        configuraciones = [
            {
                'clave': 'db_host',
                'valor': 'localhost',
                'tipo': 'string',
                'descripcion': 'Servidor de base de datos',
                'editable': True
            },
            {
                'clave': 'db_port', 
                'valor': '5432',
                'tipo': 'string',
                'descripcion': 'Puerto de base de datos',
                'editable': True
            },
            {
                'clave': 'db_name',
                'valor': 'correspondencia_db',
                'tipo': 'string', 
                'descripcion': 'Nombre de la base de datos',
                'editable': True
            },
            {
                'clave': 'db_user',
                'valor': 'postgres',
                'tipo': 'string',
                'descripcion': 'Usuario de base de datos',
                'editable': True
            },
            {
                'clave': 'ruta_pdfs',
                'valor': 'C:/temp/documentos/',
                'tipo': 'string',
                'descripcion': 'Ruta para guardar PDFs generados',
                'editable': True
            },
            {
                'clave': 'ruta_logs',
                'valor': 'C:/temp/logs/',
                'tipo': 'string',
                'descripcion': 'Ruta para archivos de log',
                'editable': True
            },
            {
                'clave': 'ruta_backup',
                'valor': 'C:/temp/backup/',
                'tipo': 'string',
                'descripcion': 'Ruta para backups',
                'editable': True
            }
        ]
        
        for config_data in configuraciones:
            # Verificar si ya existe
            existente = db.query(ConfiguracionSistema).filter(
                ConfiguracionSistema.clave == config_data['clave']
            ).first()
            
            if not existente:
                config = ConfiguracionSistema(**config_data)
                db.add(config)
        
        db.commit()
        print("✅ Configuraciones por defecto insertadas")
        
    except Exception as e:
        print(f"❌ Error insertando configuraciones: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    create_missing_tables()