# core/word_advanced_extractor.py - VERSIÓN CON CONSTANTES NUMÉRICAS

import os
import re
import json
from datetime import datetime
from typing import List, Dict, Optional
import tempfile
import pythoncom
import win32com.client

class WordAdvancedExtractor:
    """
    Extrae campos de combinación REALES usando la API de Word (win32com)
    Usa constantes numéricas para evitar problemas de importación
    """
    
    # CONSTANTES DE WORD (valores numéricos)
    # Estos son los valores reales que Word usa internamente
    WD_FIELD_MERGE_FIELD = 80          # Campo de combinación de correspondencia
    WD_VERTICAL_POSITION_RELATIVE_TO_PAGE = 4
    WD_HORIZONTAL_POSITION_RELATIVE_TO_PAGE = 5
    WD_ACTIVE_END_PAGE_NUMBER = 3
    MS0_TEXT_BOX = 17                  # msoTextBox
    WD_UNDERLINE_NONE = 0
    WD_ALIGN_PARAGRAPH_CENTER = 1
    WD_ALIGN_PARAGRAPH_RIGHT = 2
    WD_ALIGN_PARAGRAPH_JUSTIFY = 3
    
    def __init__(self):
        self.word_app = None
        self.doc = None
    
    def __enter__(self):
        """Context manager para manejar Word correctamente"""
        pythoncom.CoInitialize()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Cierra Word correctamente"""
        self.cerrar_word()
        pythoncom.CoUninitialize()
    
    def abrir_word(self, visible: bool = False):
        """Inicializa aplicación Word"""
        try:
            self.word_app = win32com.client.Dispatch("Word.Application")
            self.word_app.Visible = visible
            self.word_app.DisplayAlerts = False  # Desactivar alertas
            return True
        except Exception as e:
            print(f"❌ Error iniciando Word: {e}")
            return False
    
    def cerrar_word(self):
        """Cierra Word y libera recursos"""
        try:
            if self.doc:
                try:
                    self.doc.Close(SaveChanges=False)
                except:
                    pass
                self.doc = None
            
            if self.word_app:
                try:
                    self.word_app.Quit()
                except:
                    pass
                self.word_app = None
                
        except Exception as e:
            print(f"⚠️ Error cerrando Word: {e}")
    
    def extraer_campos_detallados(self, word_path: str) -> List[Dict]:
        """
        Extrae campos de combinación usando la API REAL de Word
        """
        if not os.path.exists(word_path):
            print(f"❌ Archivo no encontrado: {word_path}")
            return []
        
        print(f"🔍 Analizando documento Word: {word_path}")
        
        try:
            if not self.abrir_word(visible=False):
                return []
            
            # Abrir documento
            self.doc = self.word_app.Documents.Open(
                os.path.abspath(word_path),
                ReadOnly=True,
                Visible=False
            )
            
            # Extraer en este orden:
            # 1. Campos de combinación (los más importantes)
            campos_combinacion = self._extraer_campos_combinacion()
            
            # 2. Textos con placeholders en el documento
            campos_texto = self._extraer_campos_de_texto()
            
            # 3. Textboxes
            campos_textbox = self._extraer_textboxes()
            
            # 4. Tablas
            campos_tabla = self._extraer_tablas()
            
            # Combinar todos
            todos_campos = campos_combinacion + campos_texto + campos_textbox + campos_tabla
            
            # Eliminar duplicados (mismo placeholder en misma posición)
            campos_unicos = self._eliminar_duplicados(todos_campos)
            
            print(f"✅ Extracción completa: {len(campos_unicos)} campos únicos encontrados")
            
            return campos_unicos
            
        except Exception as e:
            print(f"❌ Error en extracción: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def _extraer_campos_combinacion(self) -> List[Dict]:
        """Extrae campos de combinación de correspondencia"""
        campos = []
        
        try:
            field_count = 0
            
            # Iterar sobre todos los campos del documento
            for field in self.doc.Fields:
                field_count += 1
                
                try:
                    # Solo campos de combinación (tipo = 80)
                    if field.Type == self.WD_FIELD_MERGE_FIELD:
                        campo = self._analizar_campo_combinacion(field, field_count)
                        if campo:
                            campos.append(campo)
                            
                except Exception as e:
                    print(f"⚠️ Error en campo {field_count}: {e}")
                    continue
            
            print(f"📊 Campos de combinación: {len(campos)} encontrados")
            return campos
            
        except Exception as e:
            print(f"❌ Error extrayendo campos: {e}")
            return []
    
    def _analizar_campo_combinacion(self, field, numero: int) -> Optional[Dict]:
        """Analiza un campo de combinación individual"""
        try:
            # Obtener código del campo
            codigo = field.Code.Text.strip()
            
            # Extraer placeholder del código
            # Formato típico: «NOMBRE» o MERGEFIELD "NOMBRE"
            placeholder = self._extraer_placeholder_del_codigo(codigo)
            
            if not placeholder:
                return None
            
            # Obtener posición
            try:
                pos_y = field.Result.Information(self.WD_VERTICAL_POSITION_RELATIVE_TO_PAGE)
                pos_x = field.Result.Information(self.WD_HORIZONTAL_POSITION_RELATIVE_TO_PAGE)
                pagina = field.Result.Information(self.WD_ACTIVE_END_PAGE_NUMBER)
            except:
                pos_y = 0
                pos_x = 0
                pagina = 1
            
            # Obtener texto del resultado (lo que se muestra en el documento)
            texto_resultado = field.Result.Text.strip()
            
            # Determinar si está en tabla
            en_tabla = False
            try:
                # Si podemos acceder a la propiedad Tables del rango, está en tabla
                field.Result.Tables(1)
                en_tabla = True
            except:
                en_tabla = False
            
            return {
                'tipo': 'merge_field',
                'placeholder': placeholder,
                'codigo_word': codigo,
                'posicion_x_puntos': round(float(pos_x), 2),
                'posicion_y_puntos': round(float(pos_y), 2),
                'pagina': int(pagina) if pagina else 1,
                'texto_mostrado': texto_resultado,
                'en_tabla': en_tabla,
                'numero_campo': numero,
                'metadata': {
                    'field_type': 'MERGE_FIELD',
                    'has_position': pos_x > 0 or pos_y > 0
                }
            }
            
        except Exception as e:
            print(f"⚠️ Error analizando campo {numero}: {e}")
            return None
    
    def _extraer_placeholder_del_codigo(self, codigo: str) -> str:
        """Extrae el nombre del placeholder del código de campo"""
        # Diferentes formatos de código:
        # 1. «NOMBRE» (el más común)
        # 2. MERGEFIELD "NOMBRE"
        # 3. { MERGEFIELD "NOMBRE" }
        
        # Intentar formato « »
        match = re.search(r'«([^»]+)»', codigo)
        if match:
            return match.group(1).strip()
        
        # Intentar formato MERGEFIELD "NOMBRE"
        match = re.search(r'MERGEFIELD\s+"([^"]+)"', codigo, re.IGNORECASE)
        if match:
            return match.group(1).strip()
        
        # Intentar cualquier texto entre comillas
        match = re.search(r'"([^"]+)"', codigo)
        if match:
            return match.group(1).strip()
        
        # Si no se puede extraer, devolver el código limpio
        return codigo.replace('MERGEFIELD', '').replace('"', '').strip()
    
    def _extraer_campos_de_texto(self) -> List[Dict]:
        """Extrae placeholders de texto plano en el documento"""
        campos = []
        
        try:
            # Obtener todo el texto del documento
            texto_completo = self.doc.Content.Text
            
            # Buscar placeholders con diferentes patrones
            patrones = [
                (r'\{\{([^{}]+)\}\}', 'doble_llave'),
                (r'\{([^{}]+)\}', 'llave_simple'),
                (r'\[([^\[\]]+)\]', 'corchete'),
                (r'<<([^<>]+)>>', 'doble_angulo'),
                (r'\(\(([^()]+)\)\)', 'doble_parentesis'),
            ]
            
            for patron, tipo_patron in patrones:
                for match in re.finditer(patron, texto_completo):
                    placeholder = match.group(1).strip()
                    
                    # Buscar posición aproximada
                    pos_inicio = match.start()
                    
                    # Convertir posición de caracter a rango
                    rango = self.doc.Range(pos_inicio, pos_inicio + len(match.group(0)))
                    
                    try:
                        pos_y = rango.Information(self.WD_VERTICAL_POSITION_RELATIVE_TO_PAGE)
                        pos_x = rango.Information(self.WD_HORIZONTAL_POSITION_RELATIVE_TO_PAGE)
                        pagina = rango.Information(self.WD_ACTIVE_END_PAGE_NUMBER)
                    except:
                        pos_y = 0
                        pos_x = 0
                        pagina = 1
                    
                    # Obtener contexto
                    contexto_inicio = max(0, pos_inicio - 50)
                    contexto_fin = min(len(texto_completo), pos_inicio + len(match.group(0)) + 50)
                    contexto = texto_completo[contexto_inicio:contexto_fin]
                    
                    campo = {
                        'tipo': 'texto_plano',
                        'placeholder': placeholder,
                        'patron': tipo_patron,
                        'posicion_x_puntos': round(float(pos_x), 2),
                        'posicion_y_puntos': round(float(pos_y), 2),
                        'pagina': int(pagina) if pagina else 1,
                        'texto_completo': match.group(0),
                        'contexto': contexto,
                        'posicion_caracter': pos_inicio,
                        'metadata': {
                            'pattern_type': tipo_patron,
                            'extracted_from': 'plain_text'
                        }
                    }
                    
                    campos.append(campo)
            
            print(f"📝 Texto plano: {len(campos)} placeholders encontrados")
            return campos
            
        except Exception as e:
            print(f"❌ Error extrayendo texto plano: {e}")
            return []
    
    def _extraer_textboxes(self) -> List[Dict]:
        """Extrae campos dentro de textboxes/shapes"""
        campos = []
        
        try:
            for i in range(1, self.doc.Shapes.Count + 1):
                try:
                    shape = self.doc.Shapes(i)
                    
                    # Verificar si es un textbox
                    if shape.Type == self.MSO_TEXT_BOX:
                        if hasattr(shape, 'TextFrame') and shape.TextFrame.HasText():
                            texto = shape.TextFrame.TextRange.Text
                            
                            # Buscar placeholders en el texto
                            placeholders_textbox = self._buscar_placeholders_en_texto(texto)
                            
                            for placeholder in placeholders_textbox:
                                campo = {
                                    'tipo': 'textbox',
                                    'placeholder': placeholder,
                                    'posicion_x_puntos': round(float(shape.Left), 2),
                                    'posicion_y_puntos': round(float(shape.Top), 2),
                                    'ancho_puntos': round(float(shape.Width), 2),
                                    'alto_puntos': round(float(shape.Height), 2),
                                    'nombre_shape': shape.Name,
                                    'texto_shape': texto[:100] + ('...' if len(texto) > 100 else ''),
                                    'numero_shape': i,
                                    'metadata': {
                                        'shape_type': 'TEXTBOX',
                                        'shape_name': shape.Name
                                    }
                                }
                                campos.append(campo)
                                
                except Exception as e:
                    print(f"⚠️ Error en shape {i}: {e}")
                    continue
            
            print(f"📦 Textboxes: {len(campos)} campos encontrados")
            return campos
            
        except Exception as e:
            print(f"❌ Error extrayendo textboxes: {e}")
            return []
    
    def _extraer_tablas(self) -> List[Dict]:
        """Extrae campos dentro de tablas"""
        campos = []
        
        try:
            for t_idx in range(1, self.doc.Tables.Count + 1):
                try:
                    table = self.doc.Tables(t_idx)
                    
                    for r_idx in range(1, table.Rows.Count + 1):
                        for c_idx in range(1, table.Columns.Count + 1):
                            try:
                                celda = table.Cell(r_idx, c_idx)
                                texto = celda.Range.Text.strip()
                                
                                # Eliminar marca de fin de celda (^)
                                texto = texto.replace('\x07', '').replace('\r', '').strip()
                                
                                if not texto:
                                    continue
                                
                                # Buscar placeholders en la celda
                                placeholders_celda = self._buscar_placeholders_en_texto(texto)
                                
                                for placeholder in placeholders_celda:
                                    campo = {
                                        'tipo': 'tabla',
                                        'placeholder': placeholder,
                                        'texto_celda': texto,
                                        'tabla_numero': t_idx,
                                        'fila': r_idx,
                                        'columna': c_idx,
                                        'direccion_celda': f"R{r_idx}C{c_idx}",
                                        'metadata': {
                                            'table_index': t_idx,
                                            'cell_address': f"R{r_idx}C{c_idx}"
                                        }
                                    }
                                    campos.append(campo)
                                    
                            except Exception as e:
                                print(f"⚠️ Error en celda R{r_idx}C{c_idx}: {e}")
                                continue
                                
                except Exception as e:
                    print(f"⚠️ Error en tabla {t_idx}: {e}")
                    continue
            
            print(f"📊 Tablas: {len(campos)} campos encontrados")
            return campos
            
        except Exception as e:
            print(f"❌ Error extrayendo tablas: {e}")
            return []
    
    def _buscar_placeholders_en_texto(self, texto: str) -> List[str]:
        """Busca placeholders en texto"""
        placeholders = []
        
        patrones = [
            r'\{\{([^{}]+)\}\}',
            r'\{([^{}]+)\}',
            r'\[([^\[\]]+)\]',
            r'<<([^<>]+)>>',
            r'«([^«»]+)»',
        ]
        
        for patron in patrones:
            for match in re.finditer(patron, texto):
                placeholder = match.group(1).strip()
                if placeholder and placeholder not in placeholders:
                    placeholders.append(placeholder)
        
        return placeholders
    
    def _eliminar_duplicados(self, campos: List[Dict]) -> List[Dict]:
        """Elimina campos duplicados basados en placeholder y posición"""
        unicos = []
        vistos = set()
        
        for campo in campos:
            # Crear clave única basada en placeholder y posición aproximada
            placeholder = campo.get('placeholder', '').lower()
            pos_x = campo.get('posicion_x_puntos', 0)
            pos_y = campo.get('posicion_y_puntos', 0)
            
            # Redondear posición para agrupar similares
            clave = f"{placeholder}_{int(pos_x/10)}_{int(pos_y/10)}"
            
            if clave not in vistos:
                vistos.add(clave)
                unicos.append(campo)
        
        return unicos
    
    def exportar_resultados(self, campos: List[Dict], output_path: str = None) -> str:
        """Exporta resultados a JSON"""
        resultados = {
            'timestamp': datetime.now().isoformat(),
            'total_campos': len(campos),
            'estadisticas': {
                'merge_fields': sum(1 for c in campos if c.get('tipo') == 'merge_field'),
                'texto_plano': sum(1 for c in campos if c.get('tipo') == 'texto_plano'),
                'textboxes': sum(1 for c in campos if c.get('tipo') == 'textbox'),
                'tablas': sum(1 for c in campos if c.get('tipo') == 'tabla')
            },
            'campos': campos
        }
        
        if output_path:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(resultados, f, indent=2, ensure_ascii=False)
            print(f"💾 Resultados exportados a: {output_path}")
        
        return json.dumps(resultados, indent=2, ensure_ascii=False)


# ==================== TEST SIMPLIFICADO ====================

def test_con_documento_existente():
    """Prueba con un documento Word existente"""
    print("🧪 TEST DEL EXTRACTOR DE WORD")
    print("=" * 60)
    
    # Buscar documentos de prueba
    documentos_prueba = [
        "AFILIADOS.docx",
        "documento_prueba.docx",
        "ejemplo.docx",
        "plantilla.docx"
    ]
    
    doc_encontrado = None
    for doc in documentos_prueba:
        if os.path.exists(doc):
            doc_encontrado = doc
            break
    
    if not doc_encontrado:
        print("⚠️ No se encontró documento de prueba")
        print("💡 Crea un documento Word con:")
        print("   - Campos de combinación (Insertar → Campo → MergeField)")
        print("   - Texto con {placeholders}")
        print("   - O usa cualquier documento Word existente")
        return
    
    print(f"📄 Usando documento: {doc_encontrado}")
    
    # Usar extractor
    with WordAdvancedExtractor() as extractor:
        campos = extractor.extraer_campos_detallados(doc_encontrado)
        
        # Mostrar resultados
        print(f"\n📊 RESULTADOS PARA: {doc_encontrado}")
        print(f"Total campos encontrados: {len(campos)}")
        
        if campos:
            # Agrupar por tipo
            tipos = {}
            for campo in campos:
                tipo = campo.get('tipo', 'desconocido')
                tipos[tipo] = tipos.get(tipo, 0) + 1
            
            print("\n📈 DISTRIBUCIÓN POR TIPO:")
            for tipo, cantidad in tipos.items():
                print(f"  {tipo}: {cantidad}")
            
            # Mostrar primeros 5 campos
            print("\n🔍 PRIMEROS 5 CAMPOS DETECTADOS:")
            for i, campo in enumerate(campos[:5]):
                placeholder = campo.get('placeholder', 'N/A')
                tipo = campo.get('tipo', 'N/A')
                
                if tipo == 'merge_field':
                    pos_x = campo.get('posicion_x_puntos', 0)
                    pos_y = campo.get('posicion_y_puntos', 0)
                    print(f"  {i+1}. {placeholder} [{tipo}] - Pos: ({pos_x}, {pos_y}) pt")
                elif tipo == 'textbox':
                    print(f"  {i+1}. {placeholder} [{tipo}] - TextBox")
                else:
                    print(f"  {i+1}. {placeholder} [{tipo}]")
            
            if len(campos) > 5:
                print(f"  ... y {len(campos)-5} más")
            
            # Exportar a JSON
            extractor.exportar_resultados(campos, "word_campos_extraidos.json")
            print(f"\n💾 Datos guardados en: word_campos_extraidos.json")
            
        else:
            print("❌ No se encontraron campos en el documento")
            print("💡 Asegúrate de que el documento tenga:")
            print("   - Campos de combinación (Insertar → Campo)")
            print("   - Texto entre llaves: {nombre_campo}")
            print("   - O formato: <<campo>> o [campo]")
    
    print("\n✅ Prueba completada")


def test_rapido():
    """Prueba rápida sin crear documento"""
    print("⚡ PRUEBA RÁPIDA DEL EXTRACTOR")
    
    # Verificar si Word está instalado
    try:
        word = win32com.client.Dispatch("Word.Application")
        word.Quit()
        print("✅ Word está disponible")
    except:
        print("❌ Word no está disponible o no está instalado")
        print("💡 Instala Microsoft Office para usar esta funcionalidad")
        return
    
    # Verificar si hay documentos para probar
    import glob
    docs_word = glob.glob("*.docx") + glob.glob("*.doc")
    
    if docs_word:
        print(f"📁 Documentos encontrados: {len(docs_word)}")
        for doc in docs_word[:3]:  # Mostrar primeros 3
            print(f"  - {doc}")
        
        test_con_documento_existente()
    else:
        print("📭 No hay documentos Word en el directorio actual")
        print("💡 Coloca un documento Word aquí o especifica la ruta:")
        print("   extractor = WordAdvancedExtractor()")
        print("   campos = extractor.extraer_campos_detallados('ruta/documento.docx')")


if __name__ == "__main__":
    test_rapido()