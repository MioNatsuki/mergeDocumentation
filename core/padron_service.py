# core/padron_service.py - VERSIÓN COMPLETA
from sqlalchemy.orm import Session
from typing import List, Dict, Optional
from core.models import IdentificadorPadrones
from sqlalchemy import text

# core/padron_service.py - MANEJAR UUIDs
class PadronService:
    def __init__(self, db: Session):
        self.db = db
    
    def obtener_padrones_activos(self) -> List[Dict]:
        """Obtiene padrones activos"""
        try:
            padrones = self.db.query(IdentificadorPadrones).filter(
                IdentificadorPadrones.activo == True
            ).order_by(IdentificadorPadrones.nombre_tabla).all()  # ← CORREGIDO
            
            return [
                {
                    "id": padron.id,
                    "nombre_tabla": padron.nombre_tabla,  # ← CORREGIDO
                    "uuid_padron": padron.uuid_padron,
                    "descripcion": padron.descripcion
                }
                for padron in padrones
            ]
        except Exception as e:
            print(f"Error obteniendo padrones: {e}")
            return []
    
    def obtener_padron_por_uuid(self, uuid_padron: str) -> Optional[IdentificadorPadrones]:
        """Obtiene un padrón por su UUID"""
        try:
            return self.db.query(IdentificadorPadrones).filter(
                IdentificadorPadrones.uuid_padron == uuid_padron
            ).first()
        except Exception as e:
            print(f"Error obteniendo padrón por UUID {uuid_padron}: {e}")
            return None
    
    def obtener_padron_por_nombre(self, nombre: str) -> Optional[IdentificadorPadrones]:
        """Obtiene un padrón por su nombre"""
        try:
            return self.db.query(IdentificadorPadrones).filter(
                IdentificadorPadrones.nombre == nombre
            ).first()
        except Exception as e:
            print(f"Error obteniendo padrón por nombre {nombre}: {e}")
            return None
        
    def obtener_columnas_padron(self, uuid_padron: str) -> List[Dict]:
        """Obtiene las columnas REALES de una tabla de padrón específica"""
        try:
            # 1. Obtener el identificador del padrón
            identificador = self.db.query(IdentificadorPadrones).filter(
                IdentificadorPadrones.uuid_padron == uuid_padron
            ).first()
            
            if not identificador:
                print(f"DEBUG: No se encontró padrón con UUID: {uuid_padron}")
                return []
            
            # 2. Obtener el nombre REAL de la tabla
            nombre_tabla_real = identificador.nombre_tabla
            print(f"DEBUG: Buscando columnas de tabla REAL: {nombre_tabla_real}")
            
            # 3. Consultar information_schema para obtener columnas REALES
            query = text("""
                SELECT 
                    column_name as nombre,
                    data_type as tipo,
                    is_nullable as nullable,
                    column_default as valor_default
                FROM information_schema.columns 
                WHERE table_schema = 'public'
                AND table_name = :table_name
                ORDER BY ordinal_position
            """)
            
            resultado = self.db.execute(query, {"table_name": nombre_tabla_real})
            columnas = []
            
            for row in resultado:
                # Excluir columnas de sistema/metadatos que no queremos mostrar
                nombre = row.nombre
                
                # Determinar tipo amigable
                tipo_db = row.tipo
                if 'char' in tipo_db or 'text' in tipo_db:
                    tipo_amigable = 'texto'
                elif 'int' in tipo_db or 'numeric' in tipo_db or 'decimal' in tipo_db:
                    tipo_amigable = 'numero'
                elif 'date' in tipo_db or 'time' in tipo_db:
                    tipo_amigable = 'fecha'
                elif 'bool' in tipo_db:
                    tipo_amigable = 'booleano'
                else:
                    tipo_amigable = 'texto'
                
                columnas.append({
                    "nombre": nombre,
                    "tipo_db": tipo_db,
                    "tipo": tipo_amigable,
                    "nullable": row.nullable == 'YES',
                    "valor_default": row.valor_default
                })
            
            print(f"DEBUG: Se encontraron {len(columnas)} columnas REALES")
            return columnas
            
        except Exception as e:
            print(f"ERROR obteniendo columnas REALES: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def obtener_datos_ejemplo_real(self, uuid_padron: str, limit: int = 3) -> List[Dict]:
        """Obtiene datos REALES de ejemplo del padrón"""
        try:
            identificador = self.db.query(IdentificadorPadrones).filter(
                IdentificadorPadrones.uuid_padron == uuid_padron
            ).first()
            
            if not identificador:
                return []
            
            nombre_tabla_real = identificador.nombre_tabla
            
            # Consulta para obtener algunos registros REALES
            query = text(f"SELECT * FROM {nombre_tabla_real} LIMIT {limit}")
            resultado = self.db.execute(query)
            
            datos = []
            for row in resultado:
                datos.append(dict(row._mapping))
            
            return datos
            
        except Exception as e:
            print(f"Error obteniendo datos ejemplo REALES: {e}")
            return []