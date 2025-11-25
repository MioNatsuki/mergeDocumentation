from sqlalchemy.orm import Session
from sqlalchemy import and_
from core.models import Proyecto, Usuario, Plantilla
from typing import List

class ProjectService:
    def __init__(self, db: Session):
        self.db = db
    
    def obtener_proyectos_usuario(self, usuario: Usuario) -> List[Proyecto]:
        """Obtiene proyectos visibles para el usuario según su rol"""
        try:
            if usuario.rol == "superadmin":
                return self.db.query(Proyecto).filter(Proyecto.activo == True).all()
            
            elif usuario.rol == "admin":
                return self.db.query(Proyecto).filter(Proyecto.activo == True).all()
            
            else:  # lector
                if not usuario.proyecto_permitido:
                    return []
                
                try:
                    proyectos_permitidos = [int(p.strip()) for p in usuario.proyecto_permitido.split(',') if p.strip().isdigit()]
                except:
                    proyectos_permitidos = []
                
                if not proyectos_permitidos:
                    return []
                
                return self.db.query(Proyecto).filter(
                    and_(
                        Proyecto.activo == True,
                        Proyecto.id.in_(proyectos_permitidos)
                    )
                ).all()
                
        except Exception as e:
            print(f"DEBUG - Error en obtener_proyectos_usuario: {e}")
            return []
    
    def crear_proyecto(self, nombre: str, descripcion: str, tabla_padron: str, usuario: Usuario) -> Proyecto:
        """Crea un nuevo proyecto"""
        if usuario.rol not in ["superadmin", "admin"]:
            raise PermissionError("No tiene permisos para crear proyectos")
        
        try:
            proyecto = Proyecto(
                nombre=nombre,
                descripcion=descripcion,
                tabla_padron=tabla_padron,
                config_json={}
            )
            
            self.db.add(proyecto)
            self.db.commit()
            self.db.refresh(proyecto)
            
            return proyecto
            
        except Exception as e:
            self.db.rollback()
            raise e
    
    def actualizar_proyecto(self, proyecto_id: int, datos_actualizacion: dict, usuario: Usuario) -> Proyecto:
        """Actualiza un proyecto existente"""
        if usuario.rol not in ["superadmin", "admin"]:
            raise PermissionError("No tiene permisos para editar proyectos")
        
        try:
            proyecto = self.db.query(Proyecto).filter(Proyecto.id == proyecto_id).first()
            if not proyecto:
                raise ValueError("Proyecto no encontrado")
            
            for key, value in datos_actualizacion.items():
                if hasattr(proyecto, key):
                    setattr(proyecto, key, value)
            
            self.db.commit()
            self.db.refresh(proyecto)
            
            return proyecto
            
        except Exception as e:
            self.db.rollback()
            raise e
    
    def eliminar_proyecto(self, proyecto_id: int, usuario: Usuario) -> bool:
        """Elimina un proyecto (soft delete)"""
        if usuario.rol != "superadmin":
            raise PermissionError("Solo superadmin puede eliminar proyectos")
        
        try:
            proyecto = self.db.query(Proyecto).filter(Proyecto.id == proyecto_id).first()
            if not proyecto:
                raise ValueError("Proyecto no encontrado")
            
            proyecto.activo = False
            self.db.commit()
            
            return True
            
        except Exception as e:
            self.db.rollback()
            raise e
    
    def obtener_plantillas_proyecto(self, proyecto_id: int, usuario: Usuario) -> List[Plantilla]:
        """Obtiene plantillas de un proyecto específico"""
        try:
            proyectos_permitidos = self.obtener_proyectos_usuario(usuario)
            proyecto_ids_permitidos = [p.id for p in proyectos_permitidos]
            
            if proyecto_id not in proyecto_ids_permitidos:
                raise PermissionError("No tiene acceso a este proyecto")
            
            return self.db.query(Plantilla).filter(
                and_(
                    Plantilla.proyecto_id == proyecto_id,
                    Plantilla.activa == True
                )
            ).all()
            
        except Exception as e:
            print(f"DEBUG - Error en obtener_plantillas_proyecto: {e}")
            raise e