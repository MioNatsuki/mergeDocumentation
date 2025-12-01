# core/padron_service.py - VERSIÓN COMPLETA
from sqlalchemy.orm import Session
from typing import List, Dict, Optional
from core.models import IdentificadorPadrones

# core/padron_service.py - MANEJAR UUIDs
class PadronService:
    def __init__(self, db: Session):
        self.db = db
    
    def obtener_padrones_activos(self) -> List[Dict]:
        """
        Obtiene padrones con sus UUIDs para el dropdown
        SELECT id, nombre, uuid_padron, descripcion FROM identificador_padrones
        """
        try:
            padrones = self.db.query(IdentificadorPadrones).filter(
                IdentificadorPadrones.activo == True
            ).order_by(IdentificadorPadrones.nombre).all()
            
            return [
                {
                    "id": padron.id,
                    "nombre": padron.nombre,
                    "uuid_padron": padron.uuid_padron,  # ← EL UUID
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