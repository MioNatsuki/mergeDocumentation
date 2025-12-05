import pandas as pd
import csv
import chardet
from sqlalchemy.orm import Session
from typing import List, Dict, Tuple
import os
from core.models import EmisionTemp, Proyecto
from datetime import datetime
import uuid
from sqlalchemy import text

class CSVService:
    def __init__(self, db: Session):
        self.db = db
    
    def detectar_encoding(self, file_path: str) -> str:
        """Detecta la codificación del archivo CSV"""
        with open(file_path, 'rb') as file:
            raw_data = file.read()
            result = chardet.detect(raw_data)
            return result.get('encoding', 'utf-8')
    
    def validar_estructura_csv(self, file_path: str) -> Tuple[bool, List[str], List[str]]:
        """
        Valida la estructura básica del CSV
        Retorna: (es_válido, campos_encontrados, errores)
        """
        try:
            # Detectar encoding
            encoding = self.detectar_encoding(file_path)
            
            # Leer primeras líneas para validar
            with open(file_path, 'r', encoding=encoding) as file:
                # Leer primera línea para encabezados
                first_line = file.readline().strip()
                if not first_line:
                    return False, [], ["El archivo CSV está vacío"]
                
                # Verificar que sea CSV válido
                try:
                    file.seek(0)
                    reader = csv.DictReader(file)
                    campos = reader.fieldnames or []
                    
                    if not campos:
                        return False, [], ["No se encontraron encabezados en el CSV"]
                    
                    # Validar campos mínimos
                    campos_requeridos = ['cuenta', 'codigo_afiliado']
                    campos_faltantes = [campo for campo in campos_requeridos if campo not in campos]
                    
                    if campos_faltantes:
                        return False, campos, [f"Campos requeridos faltantes: {', '.join(campos_faltantes)}"]
                    
                    # Validar que tenga datos
                    file.seek(0)
                    line_count = sum(1 for line in file) - 1  # Restar encabezado
                    if line_count == 0:
                        return False, campos, ["El CSV no contiene datos (solo encabezados)"]
                    
                    return True, campos, []
                    
                except csv.Error as e:
                    return False, [], [f"Error de formato CSV: {str(e)}"]
                    
        except Exception as e:
            return False, [], [f"Error leyendo archivo: {str(e)}"]
    
    def procesar_csv(self, file_path: str, proyecto_id: int, usuario_id: int, 
                    sesion_id: str = None) -> Tuple[bool, int, List[str]]:
        """
        Procesa el CSV y carga los datos en la tabla temporal
        Retorna: (éxito, registros_procesados, errores)
        """
        if not sesion_id:
            sesion_id = str(uuid.uuid4())
        
        try:
            # Validar estructura primero
            es_valido, campos, errores = self.validar_estructura_csv(file_path)
            if not es_valido:
                return False, 0, errores
            
            # Detectar encoding
            encoding = self.detectar_encoding(file_path)
            
            # Leer CSV con pandas para mejor manejo
            df = pd.read_csv(file_path, encoding=encoding, dtype=str)
            df = df.where(pd.notnull(df), None)  # Convertir NaN a None
            
            registros_procesados = 0
            errores_procesamiento = []
            
            for index, row in df.iterrows():
                try:
                    # Crear registro temporal
                    registro_temp = EmisionTemp(
                        proyecto_id=proyecto_id,
                        usuario_id=usuario_id,
                        datos_json=row.to_dict(),
                        cuenta=row.get('cuenta', ''),
                        codigo_afiliado=row.get('codigo_afiliado', ''),
                        estado='pendiente',
                        sesion_id=sesion_id,
                        fecha_carga=datetime.now()
                    )
                    
                    self.db.add(registro_temp)
                    registros_procesados += 1
                    
                    # Commit cada 100 registros para no saturar
                    if registros_procesados % 100 == 0:
                        self.db.commit()
                        
                except Exception as e:
                    error_msg = f"Fila {index + 2}: {str(e)}"  # +2 por encabezado y base 0
                    errores_procesamiento.append(error_msg)
            
            # Commit final
            self.db.commit()
            
            return True, registros_procesados, errores_procesamiento
            
        except Exception as e:
            self.db.rollback()
            return False, 0, [f"Error general en procesamiento: {str(e)}"]
    
    def hacer_match_padron(self, proyecto_id: int, sesion_id: str) -> Tuple[bool, int, List[str]]:
        """Hace match REAL con la tabla de padrón"""
        try:
            # 1. Obtener proyecto y tabla de padrón
            proyecto = self.db.query(Proyecto).filter(Proyecto.id == proyecto_id).first()
            if not proyecto or not proyecto.tabla_padron:
                return False, 0, ["No se encontró tabla de padrón configurada"]
            
            # 2. Obtener registros temporales
            registros_temp = self.db.query(EmisionTemp).filter(
                EmisionTemp.proyecto_id == proyecto_id,
                EmisionTemp.sesion_id == sesion_id,
                EmisionTemp.estado == 'pendiente'
            ).all()
            
            registros_match = 0
            errores = []
            
            # 3. Consulta dinámica a la tabla de padrón
            nombre_tabla = proyecto.tabla_padron
            
            for registro in registros_temp:
                try:
                    # Construir consulta SQL dinámica
                    query = f"""
                        SELECT * FROM {nombre_tabla} 
                        WHERE cuenta = :cuenta 
                        OR codigo_afiliado = :codigo
                        LIMIT 1
                    """
                    
                    result = self.db.execute(
                        text(query), 
                        {
                            "cuenta": registro.cuenta,
                            "codigo": registro.codigo_afiliado
                        }
                    ).fetchone()
                    
                    if result:
                        # Match encontrado, combinar datos
                        datos_padron = dict(result._mapping)
                        datos_combinados = {**registro.datos_json, **datos_padron}
                        registro.datos_json = datos_combinados
                        registro.estado = 'match_ok'
                        registros_match += 1
                    else:
                        registro.estado = 'no_match'
                        registro.error_mensaje = "No encontrado en padrón"
                        
                except Exception as e:
                    registro.estado = 'error'
                    registro.error_mensaje = str(e)
                    errores.append(f"Registro {registro.id}: {str(e)}")
            
            self.db.commit()
            return True, registros_match, errores
            
        except Exception as e:
            self.db.rollback()
            return False, 0, [f"Error en match: {str(e)}"]
    
    def obtener_estadisticas_sesion(self, sesion_id: str) -> Dict:
        """Obtiene estadísticas de una sesión de procesamiento"""
        stats = {
            'total_registros': 0,
            'pendientes': 0,
            'match_ok': 0,
            'con_errores': 0
        }
        
        try:
            registros = self.db.query(EmisionTemp).filter(EmisionTemp.sesion_id == sesion_id).all()
            stats['total_registros'] = len(registros)
            
            for registro in registros:
                if registro.estado == 'pendiente':
                    stats['pendientes'] += 1
                elif registro.estado == 'match_ok':
                    stats['match_ok'] += 1
                elif registro.estado == 'error':
                    stats['con_errores'] += 1
                    
        except Exception as e:
            print(f"Error obteniendo estadísticas: {e}")
        
        return stats