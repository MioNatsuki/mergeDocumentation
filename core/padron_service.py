# core/padron_service.py - VERSIÓN COMPLETA CON TABLAS DINÁMICAS
from sqlalchemy.orm import Session
from sqlalchemy import text, inspect, MetaData, Table, Column, Integer, String, Date, Numeric, Boolean, Text
from typing import List, Dict, Optional, Tuple
from core.models import IdentificadorPadrones, Proyecto
import uuid
import pandas as pd
import re

class PadronService:
    def __init__(self, db: Session):
        self.db = db
        self.metadata = MetaData()
    
    # ========== MÉTODOS EXISTENTES ==========
    
    def obtener_padrones_activos(self) -> List[Dict]:
        """Obtiene padrones activos"""
        try:
            padrones = self.db.query(IdentificadorPadrones).filter(
                IdentificadorPadrones.activo == True
            ).order_by(IdentificadorPadrones.nombre_tabla).all()
            
            return [
                {
                    "nombre_tabla": padron.nombre_tabla,
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
    
    def obtener_columnas_padron(self, uuid_padron: str) -> List[Dict]:
        """Obtiene las columnas REALES de una tabla de padrón específica"""
        try:
            identificador = self.db.query(IdentificadorPadrones).filter(
                IdentificadorPadrones.uuid_padron == uuid_padron
            ).first()
            
            if not identificador:
                print(f"DEBUG: No se encontró padrón con UUID: {uuid_padron}")
                return []
            
            nombre_tabla_real = identificador.nombre_tabla
            print(f"DEBUG: Buscando columnas de tabla REAL: {nombre_tabla_real}")
            
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
                nombre = row.nombre
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
            query = text(f"SELECT * FROM {nombre_tabla_real} LIMIT {limit}")
            resultado = self.db.execute(query)
            
            datos = []
            for row in resultado:
                datos.append(dict(row._mapping))
            
            return datos
            
        except Exception as e:
            print(f"Error obteniendo datos ejemplo REALES: {e}")
            return []
    
    def obtener_todos_registros(self, uuid_padron: str, limit: int = 100) -> List[Dict]:
        """Obtiene todos los registros de un padrón"""
        try:
            identificador = self.obtener_padron_por_uuid(uuid_padron)
            if not identificador:
                return []
            
            nombre_tabla_real = identificador.nombre_tabla
            query = text(f"SELECT * FROM {nombre_tabla_real} LIMIT {limit}")
            resultado = self.db.execute(query)
            
            registros = []
            for row in resultado:
                registros.append(dict(row._mapping))
            
            return registros
            
        except Exception as e:
            print(f"Error obteniendo registros: {e}")
            return []
    
    # ========== NUEVOS MÉTODOS PARA PADRÓN DINÁMICO ==========
    
    def analizar_estructura_csv(self, csv_path: str) -> Tuple[bool, List[Dict], List[str]]:
        """
        Analiza CSV y devuelve estructura de columnas detectadas
        Returns: (éxito, columnas, errores)
        """
        try:
            # Detectar encoding
            import chardet
            with open(csv_path, 'rb') as f:
                raw_data = f.read()
                result = chardet.detect(raw_data)
                encoding = result.get('encoding', 'utf-8')
            
            # Leer CSV
            df = pd.read_csv(csv_path, encoding=encoding, nrows=100)  # Solo primeras 100 filas para análisis
            
            if df.empty:
                return False, [], ["El CSV está vacío"]
            
            columnas = []
            for col_name in df.columns:
                # Detectar tipo de dato
                tipo_detectado = self._detectar_tipo_columna(df[col_name])
                
                # Crear definición de columna
                columna_def = {
                    'nombre_original': col_name,
                    'nombre_limpio': self._limpiar_nombre_columna(col_name),
                    'tipo_sugerido': tipo_detectado,
                    'tipo_sql': self._tipo_a_sql(tipo_detectado),
                    'nullable': df[col_name].isnull().any(),
                    'ejemplos': df[col_name].dropna().head(3).tolist()
                }
                
                columnas.append(columna_def)
            
            return True, columnas, []
            
        except Exception as e:
            return False, [], [f"Error analizando CSV: {str(e)}"]
    
    def _detectar_tipo_columna(self, serie: pd.Series) -> str:
        """Detecta el tipo de dato de una columna"""
        # Eliminar nulos para análisis
        serie_limpia = serie.dropna()
        
        if len(serie_limpia) == 0:
            return 'texto'
        
        # Intentar convertir a numérico
        try:
            pd.to_numeric(serie_limpia)
            # Verificar si son enteros
            if all(serie_limpia.apply(lambda x: str(x).replace('.', '', 1).replace('-', '', 1).isdigit())):
                return 'entero'
            return 'decimal'
        except:
            pass
        
        # Intentar convertir a fecha
        try:
            pd.to_datetime(serie_limpia)
            return 'fecha'
        except:
            pass
        
        # Verificar booleanos
        valores_unicos = serie_limpia.unique()
        if len(valores_unicos) <= 2 and all(str(v).lower() in ['true', 'false', '1', '0', 'si', 'no', 'yes', 'no'] for v in valores_unicos):
            return 'booleano'
        
        # Por defecto, texto
        return 'texto'
    
    def _limpiar_nombre_columna(self, nombre: str) -> str:
        """Limpia nombre de columna para SQL"""
        # Convertir a minúsculas
        nombre = nombre.lower()
        
        # Reemplazar espacios y caracteres especiales
        nombre = re.sub(r'[^\w\s]', '', nombre)
        nombre = re.sub(r'\s+', '_', nombre)
        
        # Quitar acentos
        reemplazos = {
            'á': 'a', 'é': 'e', 'í': 'i', 'ó': 'o', 'ú': 'u',
            'ñ': 'n', 'ü': 'u'
        }
        for viejo, nuevo in reemplazos.items():
            nombre = nombre.replace(viejo, nuevo)
        
        # Asegurar que empiece con letra
        if nombre and nombre[0].isdigit():
            nombre = 'col_' + nombre
        
        # Limitar longitud
        if len(nombre) > 50:
            nombre = nombre[:50]
        
        return nombre or 'columna'
    
    def _tipo_a_sql(self, tipo_detectado: str, longitud: int = 255) -> str:
        """Convierte tipo detectado a tipo SQL"""
        mapeo = {
            'texto': f'VARCHAR({longitud})',
            'entero': 'INTEGER',
            'decimal': 'NUMERIC(15, 2)',
            'fecha': 'DATE',
            'booleano': 'BOOLEAN'
        }
        return mapeo.get(tipo_detectado, 'TEXT')
    
    def crear_tabla_padron_dinamica(self, nombre_proyecto: str, columnas: List[Dict]) -> Tuple[bool, str, str, List[str]]:
        """
        Crea tabla de padrón dinámica
        Returns: (éxito, uuid_padron, nombre_tabla, errores)
        """
        try:
            # Generar nombre de tabla único
            nombre_tabla = self._generar_nombre_tabla(nombre_proyecto)
            
            # Verificar que no exista
            if self._tabla_existe(nombre_tabla):
                return False, "", "", [f"La tabla {nombre_tabla} ya existe"]
            
            # Generar UUID único
            uuid_padron = str(uuid.uuid4())
            
            # Construir SQL CREATE TABLE
            sql_columnas = []
            
            # ID autoincremental
            sql_columnas.append("id SERIAL PRIMARY KEY")
            
            # Columnas del usuario
            for col in columnas:
                nombre = col['nombre_limpio']
                tipo_sql = col.get('tipo_sql', 'TEXT')
                nullable = "NULL" if col.get('nullable', True) else "NOT NULL"
                
                sql_columnas.append(f"{nombre} {tipo_sql} {nullable}")
            
            # Timestamps automáticos
            sql_columnas.append("fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
            sql_columnas.append("fecha_actualizacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
            
            # Crear tabla
            create_sql = f"""
                CREATE TABLE {nombre_tabla} (
                    {', '.join(sql_columnas)}
                )
            """
            
            print(f"📝 SQL generado:\n{create_sql}")
            
            self.db.execute(text(create_sql))
            self.db.commit()
            
            # Registrar en identificador_padrones
            identificador = IdentificadorPadrones(
                uuid_padron=uuid_padron,
                nombre_tabla=nombre_tabla,
                activo=True,
                descripcion=f"Padrón del proyecto: {nombre_proyecto}"
            )
            
            self.db.add(identificador)
            self.db.commit()
            
            print(f"✅ Tabla {nombre_tabla} creada con UUID {uuid_padron}")
            
            return True, uuid_padron, nombre_tabla, []
            
        except Exception as e:
            self.db.rollback()
            print(f"❌ Error creando tabla: {e}")
            import traceback
            traceback.print_exc()
            return False, "", "", [f"Error creando tabla: {str(e)}"]
    
    def _generar_nombre_tabla(self, nombre_proyecto: str) -> str:
        """Genera nombre de tabla único y válido"""
        # Limpiar nombre
        nombre_limpio = self._limpiar_nombre_columna(nombre_proyecto)
        
        # Prefijo
        prefijo = "padron_completo_"
        
        # Generar nombre base
        nombre_base = f"{prefijo}{nombre_limpio}"
        
        # Verificar longitud (PostgreSQL max 63 caracteres)
        if len(nombre_base) > 60:
            nombre_base = nombre_base[:60]
        
        # Si ya existe, agregar sufijo numérico
        nombre_final = nombre_base
        contador = 1
        
        while self._tabla_existe(nombre_final):
            nombre_final = f"{nombre_base}_{contador}"
            contador += 1
            
            if contador > 100:  # Evitar loop infinito
                nombre_final = f"{prefijo}{uuid.uuid4().hex[:8]}"
                break
        
        return nombre_final
    
    def _tabla_existe(self, nombre_tabla: str) -> bool:
        """Verifica si una tabla existe"""
        try:
            query = text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public'
                    AND table_name = :table_name
                )
            """)
            
            resultado = self.db.execute(query, {"table_name": nombre_tabla}).scalar()
            return resultado
            
        except Exception as e:
            print(f"Error verificando tabla: {e}")
            return False
    
    def cargar_datos_csv_a_padron(self, uuid_padron: str, csv_path: str, columnas_mapeo: Dict[str, str]) -> Tuple[bool, int, List[str]]:
        """
        Carga datos de CSV a tabla de padrón
        columnas_mapeo: {nombre_csv: nombre_columna_tabla}
        Returns: (éxito, registros_insertados, errores)
        """
        try:
            # Obtener nombre de tabla
            identificador = self.obtener_padron_por_uuid(uuid_padron)
            if not identificador:
                return False, 0, ["Padrón no encontrado"]
            
            nombre_tabla = identificador.nombre_tabla
            
            # Detectar encoding
            import chardet
            with open(csv_path, 'rb') as f:
                raw_data = f.read()
                result = chardet.detect(raw_data)
                encoding = result.get('encoding', 'utf-8')
            
            # Leer CSV
            df = pd.read_csv(csv_path, encoding=encoding)
            df = df.where(pd.notnull(df), None)  # NaN a None
            
            # Preparar datos para inserción
            columnas_insert = list(columnas_mapeo.values())
            
            registros_insertados = 0
            errores = []
            
            # Insertar por lotes (100 registros por vez)
            batch_size = 100
            
            for i in range(0, len(df), batch_size):
                batch = df.iloc[i:i+batch_size]
                
                try:
                    # Construir SQL INSERT
                    placeholders = ', '.join([f':{col}' for col in columnas_insert])
                    sql = f"""
                        INSERT INTO {nombre_tabla} ({', '.join(columnas_insert)})
                        VALUES ({placeholders})
                    """
                    
                    # Preparar datos
                    for _, row in batch.iterrows():
                        datos = {}
                        for csv_col, tabla_col in columnas_mapeo.items():
                            if csv_col in row.index:
                                datos[tabla_col] = row[csv_col]
                        
                        self.db.execute(text(sql), datos)
                        registros_insertados += 1
                    
                    self.db.commit()
                    
                except Exception as e:
                    self.db.rollback()
                    errores.append(f"Error en lote {i//batch_size + 1}: {str(e)}")
            
            return True, registros_insertados, errores
            
        except Exception as e:
            self.db.rollback()
            return False, 0, [f"Error cargando datos: {str(e)}"]
    
    def actualizar_padron_desde_csv(self, uuid_padron: str, csv_path: str, columnas_mapeo: Dict[str, str], 
                                    columna_clave: str = 'cuenta') -> Tuple[bool, int, int, List[str]]:
        """
        Actualiza padrón desde CSV (UPDATE si existe, INSERT si no)
        Returns: (éxito, actualizados, nuevos, errores)
        """
        try:
            identificador = self.obtener_padron_por_uuid(uuid_padron)
            if not identificador:
                return False, 0, 0, ["Padrón no encontrado"]
            
            nombre_tabla = identificador.nombre_tabla
            
            # Detectar encoding y leer CSV
            import chardet
            with open(csv_path, 'rb') as f:
                result = chardet.detect(f.read())
                encoding = result.get('encoding', 'utf-8')
            
            df = pd.read_csv(csv_path, encoding=encoding)
            df = df.where(pd.notnull(df), None)
            
            actualizados = 0
            nuevos = 0
            errores = []
            
            # Verificar que columna_clave existe
            if columna_clave not in columnas_mapeo.values():
                return False, 0, 0, [f"Columna clave '{columna_clave}' no encontrada en mapeo"]
            
            # Obtener nombre CSV de la columna clave
            csv_clave = None
            for csv_col, tabla_col in columnas_mapeo.items():
                if tabla_col == columna_clave:
                    csv_clave = csv_col
                    break
            
            if not csv_clave or csv_clave not in df.columns:
                return False, 0, 0, [f"Columna clave '{csv_clave}' no encontrada en CSV"]
            
            # Procesar cada registro
            for _, row in df.iterrows():
                try:
                    valor_clave = row[csv_clave]
                    
                    # Verificar si existe
                    check_sql = f"SELECT id FROM {nombre_tabla} WHERE {columna_clave} = :clave"
                    existe = self.db.execute(text(check_sql), {"clave": valor_clave}).first()
                    
                    # Preparar datos
                    datos = {}
                    for csv_col, tabla_col in columnas_mapeo.items():
                        if csv_col in row.index:
                            datos[tabla_col] = row[csv_col]
                    
                    if existe:
                        # UPDATE
                        set_clauses = ', '.join([f"{col} = :{col}" for col in datos.keys()])
                        update_sql = f"""
                            UPDATE {nombre_tabla}
                            SET {set_clauses}, fecha_actualizacion = CURRENT_TIMESTAMP
                            WHERE {columna_clave} = :clave
                        """
                        datos['clave'] = valor_clave
                        self.db.execute(text(update_sql), datos)
                        actualizados += 1
                    else:
                        # INSERT
                        columnas = ', '.join(datos.keys())
                        placeholders = ', '.join([f':{col}' for col in datos.keys()])
                        insert_sql = f"INSERT INTO {nombre_tabla} ({columnas}) VALUES ({placeholders})"
                        self.db.execute(text(insert_sql), datos)
                        nuevos += 1
                    
                except Exception as e:
                    errores.append(f"Error en registro con clave {valor_clave}: {str(e)}")
            
            self.db.commit()
            return True, actualizados, nuevos, errores
            
        except Exception as e:
            self.db.rollback()
            return False, 0, 0, [f"Error actualizando padrón: {str(e)}"]