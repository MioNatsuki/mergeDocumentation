from sqlalchemy.orm import Session
from sqlalchemy import and_, func, text
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
import json
from core.models import EmisionTemp, EmisionFinal, EmisionesAcumuladas, Proyecto, Plantilla, Usuario

class EmissionService:
    def __init__(self, db: Session):
        self.db = db
    
    def mover_a_emisiones_final(self, sesion_id: str, usuario_id: int) -> Tuple[bool, int, List[str]]:
        """Mueve registros de temporal a final después de generación exitosa"""
        try:
            # Obtener registros temporales exitosos
            registros_temp = self.db.query(EmisionTemp).filter(
                EmisionTemp.sesion_id == sesion_id,
                EmisionTemp.estado == 'match_ok'
            ).all()
            
            if not registros_temp:
                return False, 0, ["No hay registros válidos para mover"]
            
            registros_movidos = 0
            errores = []
            
            for registro_temp in registros_temp:
                try:
                    # Crear registro final
                    registro_final = EmisionFinal(
                        emision_temp_id=registro_temp.id,
                        proyecto_id=registro_temp.proyecto_id,
                        plantilla_id=registro_temp.plantilla_id,
                        usuario_id=usuario_id,
                        datos_completos=registro_temp.datos_json,
                        archivo_generado=f"documento_{registro_temp.cuenta}.pdf",
                        fecha_generacion=datetime.now(),
                        estado_generacion='completado'
                    )
                    
                    self.db.add(registro_final)
                    registros_movidos += 1
                    
                except Exception as e:
                    errores.append(f"Error moviendo registro {registro_temp.id}: {str(e)}")
            
            if registros_movidos > 0:
                self.db.commit()
                return True, registros_movidos, errores
            else:
                self.db.rollback()
                return False, 0, errores
                
        except Exception as e:
            self.db.rollback()
            return False, 0, [f"Error general moviendo a final: {str(e)}"]
    
    def acumular_emisiones(self, proyecto_id: int, dias_retroceso: int = 30) -> Tuple[bool, int, List[str]]:
        """Mueve emisiones finales a la tabla de acumulados para limpieza"""
        try:
            fecha_limite = datetime.now() - timedelta(days=dias_retroceso)
            
            # Obtener emisiones finales antiguas
            emisiones_final = self.db.query(EmisionFinal).filter(
                EmisionFinal.proyecto_id == proyecto_id,
                EmisionFinal.fecha_creacion < fecha_limite
            ).all()
            
            if not emisiones_final:
                return True, 0, []  # No hay nada que acumular es éxito
            
            registros_acumulados = 0
            errores = []
            
            for emision_final in emisiones_final:
                try:
                    # Crear registro acumulado
                    acumulado = EmisionesAcumuladas(
                        proyecto_id=emision_final.proyecto_id,
                        plantilla_id=emision_final.plantilla_id,
                        usuario_id=emision_final.usuario_id,
                        cuenta=emision_final.datos_completos.get('cuenta', ''),
                        codigo_afiliado=emision_final.datos_completos.get('codigo_afiliado', ''),
                        nombre_afiliado=emision_final.datos_completos.get('nombre_afiliado', ''),
                        datos_completos=emision_final.datos_completos,
                        nombre_archivo=emision_final.archivo_generado,
                        ruta_archivo=f"/acumulados/{emision_final.archivo_generado}",
                        fecha_emision=emision_final.fecha_generacion,
                        fecha_registro=datetime.now()
                    )
                    
                    self.db.add(acumulado)
                    
                    # Eliminar de final (Quizá podría ser soft delete)
                    self.db.delete(emision_final)
                    
                    registros_acumulados += 1
                    
                except Exception as e:
                    errores.append(f"Error acumulando emisión {emision_final.id}: {str(e)}")
            
            if registros_acumulados > 0:
                self.db.commit()
                return True, registros_acumulados, errores
            else:
                self.db.rollback()
                return False, 0, errores
                
        except Exception as e:
            self.db.rollback()
            return False, 0, [f"Error general en acumulación: {str(e)}"]
    
    def limpiar_temporales(self, sesion_id: str = None, horas_antiguedad: int = 24) -> Tuple[bool, int, List[str]]:
        """Limpia registros temporales antiguos"""
        try:
            fecha_limite = datetime.now() - timedelta(hours=horas_antiguedad)
            
            query = self.db.query(EmisionTemp).filter(
                EmisionTemp.fecha_carga < fecha_limite
            )
            
            if sesion_id:
                query = query.filter(EmisionTemp.sesion_id == sesion_id)
            
            registros_eliminar = query.all()
            
            if not registros_eliminar:
                return True, 0, []  # No hay nada que limpiar es éxito
            
            registros_eliminados = 0
            for registro in registros_eliminar:
                self.db.delete(registro)
                registros_eliminados += 1
            
            self.db.commit()
            return True, registros_eliminados, []
            
        except Exception as e:
            self.db.rollback()
            return False, 0, [f"Error limpiando temporales: {str(e)}"]
    
    def obtener_estadisticas_proyecto(self, proyecto_id: int) -> Dict:
        """Obtiene estadísticas detalladas de un proyecto"""
        stats = {
            'total_emisiones': 0,
            'emisiones_hoy': 0,
            'emisiones_semana': 0,
            'emisiones_mes': 0,
            'plantillas_activas': 0,
            'usuarios_activos': 0,
            'ultima_emision': None
        }
        
        try:
            # Total de emisiones
            stats['total_emisiones'] = self.db.query(EmisionFinal).filter(
                EmisionFinal.proyecto_id == proyecto_id
            ).count()
            
            # Emisiones hoy
            hoy = datetime.now().date()
            stats['emisiones_hoy'] = self.db.query(EmisionFinal).filter(
                and_(
                    EmisionFinal.proyecto_id == proyecto_id,
                    func.date(EmisionFinal.fecha_creacion) == hoy
                )
            ).count()
            
            # Emisiones esta semana
            inicio_semana = hoy - timedelta(days=hoy.weekday())
            stats['emisiones_semana'] = self.db.query(EmisionFinal).filter(
                and_(
                    EmisionFinal.proyecto_id == proyecto_id,
                    func.date(EmisionFinal.fecha_creacion) >= inicio_semana
                )
            ).count()
            
            # Emisiones este mes
            inicio_mes = hoy.replace(day=1)
            stats['emisiones_mes'] = self.db.query(EmisionFinal).filter(
                and_(
                    EmisionFinal.proyecto_id == proyecto_id,
                    func.date(EmisionFinal.fecha_creacion) >= inicio_mes
                )
            ).count()
            
            # Plantillas activas
            stats['plantillas_activas'] = self.db.query(Plantilla).filter(
                and_(
                    Plantilla.proyecto_id == proyecto_id,
                    Plantilla.activa == True
                )
            ).count()
            
            # Última emisión
            ultima = self.db.query(EmisionFinal).filter(
                EmisionFinal.proyecto_id == proyecto_id
            ).order_by(EmisionFinal.fecha_creacion.desc()).first()
            
            if ultima:
                stats['ultima_emision'] = ultima.fecha_creacion.strftime('%d/%m/%Y %H:%M')
            
        except Exception as e:
            print(f"Error obteniendo estadísticas: {e}")
        
        return stats
    
    def generar_reporte_auditoria(self, proyecto_id: int, fecha_inicio: datetime, fecha_fin: datetime) -> List[Dict]: #DEJARLO PARA EL FINAL PARA HACERLO CON DATOS REALES
        """Genera reporte de auditoría para un proyecto"""
        try:
            reporte = []
            reporte.append({
                'fecha': datetime.now().strftime('%d/%m/%Y %H:%M'),
                'usuario': 'Sistema',
                'accion': 'Reporte generado',
                'detalles': f'Reporte de auditoría para proyecto {proyecto_id}'
            })
            
            return reporte
            
        except Exception as e:
            print(f"Error generando reporte: {e}")
            return []