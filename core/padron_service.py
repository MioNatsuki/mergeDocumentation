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
        """Obtiene las columnas de una tabla de padrón específica"""
        try:
            # 1. Obtener el identificador del padrón
            identificador = self.db.query(IdentificadorPadrones).filter(
                IdentificadorPadrones.uuid_padron == uuid_padron
            ).first()
            
            if not identificador:
                print(f"DEBUG: No se encontró padrón con UUID: {uuid_padron}")
                return []
            
            # 2. Obtener el nombre real de la tabla
            nombre_tabla = identificador.nombre_tabla
            print(f"DEBUG: Buscando columnas de tabla: {nombre_tabla}")
            
            # 3. Consultar information_schema para obtener columnas
            # (Esto requiere permisos de lectura en information_schema)
            query = text("""
                SELECT 
                    column_name as nombre,
                    data_type as tipo,
                    is_nullable as nullable,
                    column_default as valor_default
                FROM information_schema.columns 
                WHERE table_name = :table_name
                ORDER BY ordinal_position
            """)
            
            resultado = self.db.execute(query, {"table_name": nombre_tabla})
            columnas = []
            
            for row in resultado:
                # Filtrar columnas que no queremos mostrar
                nombre = row.nombre
                
                # Excluir columnas de sistema/metadatos
                if nombre in ['id', 'created_at', 'updated_at', 'uuid_padron']:
                    continue
                
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
                    "ejemplo": self.generar_ejemplo_por_tipo(nombre, tipo_amigable)
                })
            
            print(f"DEBUG: Se encontraron {len(columnas)} columnas")
            return columnas
            
        except Exception as e:
            print(f"ERROR obteniendo columnas: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def generar_ejemplo_por_tipo(self, nombre_columna: str, tipo: str) -> str:
        """Genera un ejemplo basado en el nombre y tipo de columna"""
        nombre_lower = nombre_columna.lower()
        
        if tipo == 'texto':
            if 'nombre' in nombre_lower:
                return 'Juan Pérez'
            elif 'direccion' in nombre_lower or 'domicilio' in nombre_lower:
                return 'Calle Principal 123, Colonia Centro'
            elif 'colonia' in nombre_lower:
                return 'Centro'
            elif 'ciudad' in nombre_lower or 'municipio' in nombre_lower:
                return 'Ciudad de México'
            elif 'rfc' in nombre_lower:
                return 'XAXX010101000'
            elif 'email' in nombre_lower or 'correo' in nombre_lower:
                return 'ejemplo@correo.com'
            else:
                return 'Texto de ejemplo'
        
        elif tipo == 'numero':
            if 'telefono' in nombre_lower or 'celular' in nombre_lower:
                return '5512345678'
            elif 'cp' in nombre_lower or 'codigo_postal' in nombre_lower:
                return '01000'
            elif 'cuenta' in nombre_lower or 'folio' in nombre_lower:
                return '123456'
            else:
                return '1234.56'
        
        elif tipo == 'fecha':
            return '2024-01-15'
        
        else:
            return 'Ejemplo'
    
    def obtener_datos_ejemplo(self, uuid_padron: str, limit: int = 5) -> List[Dict]:
        """Obtiene datos de ejemplo del padrón para previsualización"""
        try:
            identificador = self.db.query(IdentificadorPadrones).filter(
                IdentificadorPadrones.uuid_padron == uuid_padron
            ).first()
            
            if not identificador:
                return []
            
            nombre_tabla = identificador.nombre_tabla
            
            # Consulta para obtener algunos registros
            query = text(f"SELECT * FROM {nombre_tabla} LIMIT {limit}")
            resultado = self.db.execute(query)
            
            datos = []
            for row in resultado:
                datos.append(dict(row._mapping))
            
            return datos
            
        except Exception as e:
            print(f"Error obteniendo datos ejemplo: {e}")
            return []