# Crea nuevo archivo: core/pdf_generator.py

from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.units import mm, inch
from reportlab.pdfgen import canvas
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import Paragraph
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT, TA_JUSTIFY
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import os
from typing import Dict, List, Optional
import traceback
from reportlab.platypus import Table, TableStyle
from reportlab.lib import colors
import math
from reportlab.lib.units import mm, inch

OFICIO_MEXICO = (215.9*mm, 340.1*mm)
class PDFGenerator:
    """Genera PDFs REALES con campos dinámicos y ALINEACIÓN"""
    
    def __init__(self, pdf_template_path: str, page_size=OFICIO_MEXICO):
        self.pdf_template_path = pdf_template_path
        self.page_size = page_size  # 210x297 mm
        
        # Registrar fuentes comunes (si existen)
        self._register_fonts()
    
    def _register_fonts(self):
        """Registrar fuentes para ReportLab"""
        try:
            # Fuentes estándar de ReportLab (ya disponibles)
            standard_fonts = ['Helvetica', 'Helvetica-Bold', 'Helvetica-Oblique',
                             'Times-Roman', 'Times-Bold', 'Times-Italic',
                             'Courier', 'Courier-Bold', 'Courier-Oblique']
            
            # Intentar registrar Arial si existe en sistema
            arial_paths = [
                'C:/Windows/Fonts/arial.ttf',
                '/usr/share/fonts/truetype/msttcorefonts/Arial.ttf',
                '/System/Library/Fonts/Arial.ttf'
            ]
            
            for path in arial_paths:
                if os.path.exists(path):
                    pdfmetrics.registerFont(TTFont('Arial', path))
                    pdfmetrics.registerFont(TTFont('Arial-Bold', path))
                    print(f"✅ Fuente Arial registrada desde: {path}")
                    break
                    
        except Exception as e:
            print(f"⚠️ No se pudieron registrar fuentes personalizadas: {e}")
    
    def _get_font_name(self, config: Dict) -> str:
        """Convierte nombre de fuente a uno compatible con ReportLab"""
        font_map = {
            'Arial': 'Helvetica',
            'Times New Roman': 'Times-Roman',
            'Courier New': 'Courier',
            'Helvetica': 'Helvetica',
            'Times': 'Times-Roman',
            'Courier': 'Courier'
        }
        
        font_name = config.get('fuente', 'Helvetica')
        return font_map.get(font_name, 'Helvetica')
    
    def _get_alignment_code(self, alineacion: str) -> int:
        """Convierte alineación texto a código ReportLab"""
        align_map = {
            'left': TA_LEFT,
            'center': TA_CENTER,
            'right': TA_RIGHT,
            'justify': TA_JUSTIFY
        }
        return align_map.get(alineacion.lower(), TA_LEFT)
    
    def generar_pdf_con_datos(self, campos: List[Dict], datos: Dict, 
                             output_path: str) -> bool:
        """Genera PDF con datos reales y alineación CORRECTA"""
        try:
            print(f"🎨 Generando PDF con {len(campos)} campos...")
            
            # Crear canvas
            c = canvas.Canvas(output_path, pagesize=self.page_size)
            width, height = self.page_size
            
            # Procesar cada campo
            for campo in campos:
                self._dibujar_campo_en_pdf(c, campo, datos, width, height)
            
            # Guardar
            c.save()
            print(f"✅ PDF generado: {output_path}")
            return True
            
        except Exception as e:
            print(f"❌ Error generando PDF: {e}")
            traceback.print_exc()
            return False
    
    def _dibujar_campo_en_pdf(self, canvas_obj, campo: Dict, datos: Dict, 
                             page_width, page_height):
        """Dibuja un campo individual en el PDF con alineación REAL"""
        try:
            # Obtener configuración
            tipo = campo.get('tipo', 'texto')
            x_mm = float(campo.get('x', 0))
            y_mm = float(campo.get('y', 0))
            ancho_mm = float(campo.get('ancho', 50))
            alto_mm = float(campo.get('alto', 10))
            
            alineacion = campo.get('alineacion', 'left')

            # Convertir mm a puntos (1 mm = 2.83465 puntos)
            x_pt = x_mm * mm
            y_pt = y_mm * mm
            
            # IMPORTANTE: Coordenadas Y invertidas en PDF
            # En tu editor: Y=0 es arriba, en PDF: Y=0 es abajo
            y_pt = page_height - y_pt - (alto_mm * mm)
            
            # Obtener texto según tipo
            if tipo == 'texto':
                texto = campo.get('texto_fijo', '')
            else:  # campo dinámico
                columna = campo.get('columna_padron', '')
                texto = str(datos.get(columna, f'{{{columna}}}'))
            
            if not texto:
                return
            
            # Obtener configuración de estilo
            fuente_nombre = self._get_font_name(campo)
            tamano = int(campo.get('tamano_fuente', 12))
            negrita = campo.get('negrita', False)
            cursiva = campo.get('cursiva', False)
            alineacion = campo.get('alineacion', 'left')
            color_hex = campo.get('color', '#000000')
            
            # Configurar fuente
            if negrita and cursiva:
                fuente_nombre += '-BoldOblique'
            elif negrita:
                fuente_nombre += '-Bold'
            elif cursiva:
                fuente_nombre += '-Oblique'
            
            # Configurar color
            if color_hex.startswith('#'):
                try:
                    r = int(color_hex[1:3], 16) / 255.0
                    g = int(color_hex[3:5], 16) / 255.0
                    b = int(color_hex[5:7], 16) / 255.0
                    canvas_obj.setFillColorRGB(r, g, b)
                except:
                    canvas_obj.setFillColorRGB(0, 0, 0)  # Negro por defecto
            
            # DECISIÓN: ¿usar justify multilínea o simple?
            if alineacion == 'justify':
                # Para textos largos o áreas altas, usar multilínea
                if alto_mm > tamano/2:  # Si hay espacio para múltiples líneas
                    self._dibujar_texto_justificado_multilinea(
                        canvas_obj, texto, x_pt, y_pt, ancho_mm*mm, alto_mm*mm,
                        fuente_nombre, tamano, color_hex
                    )
                else:
                    # Para una línea, usar justify simple
                    self._dibujar_texto_alineado_simple(
                        canvas_obj, texto, x_pt, y_pt, ancho_mm*mm,
                        fuente_nombre, tamano, 'left'  # justify en una línea = left
                    )
            else:
                # Para otras alineaciones
                if alineacion in ['left', 'center', 'right']:
                    self._dibujar_texto_alineado_simple(
                        canvas_obj, texto, x_pt, y_pt, ancho_mm*mm,
                        fuente_nombre, tamano, alineacion
                    )
                else:
                    # Usar Paragraph para casos complejos
                    self._dibujar_texto_con_paragraph(
                        canvas_obj, texto, x_pt, y_pt, ancho_mm*mm, alto_mm*mm,
                        fuente_nombre, tamano, alineacion, color_hex
                    )
                    
        except Exception as e:
            print(f"⚠️ Error dibujando campo: {e}")
            traceback.print_exc()
    
    def _obtener_texto_compuesto(self, campo: Dict, datos: Dict) -> str:
        """Concatena todos los componentes de un campo compuesto"""
        texto = ""
        componentes = campo.get('componentes', [])
        
        for comp in componentes:
            if not comp.get('visible', True):
                continue
                
            tipo = comp.get('tipo', 'texto')
            valor = comp.get('valor', '')
            
            if tipo == 'texto':
                texto += valor
            else:  # campo
                texto += str(datos.get(valor, f'{{{valor}}}'))
        
        return texto

    def _dibujar_campo_compuesto(self, canvas_obj, campo: Dict, datos: Dict, 
                            x_pt: float, y_pt: float, ancho_pt: float, alto_pt: float):
        """Dibuja un campo compuesto en el PDF"""
        try:
            # Obtener texto concatenado
            texto_completo = self._obtener_texto_compuesto(campo, datos)
            if not texto_completo:
                return
            
            # Configuración de estilo
            fuente_nombre = self._get_font_name(campo)
            tamano = int(campo.get('tamano_fuente', 12))
            alineacion = campo.get('alineacion', 'left')
            color_hex = campo.get('color', '#000000')
            
            # Aplicar negrita/cursiva a fuente
            if campo.get('negrita', False) and campo.get('cursiva', False):
                fuente_nombre += '-BoldOblique'
            elif campo.get('negrita', False):
                fuente_nombre += '-Bold'
            elif campo.get('cursiva', False):
                fuente_nombre += '-Oblique'
            
            # Configurar color
            if color_hex.startswith('#'):
                try:
                    r = int(color_hex[1:3], 16) / 255.0
                    g = int(color_hex[3:5], 16) / 255.0
                    b = int(color_hex[5:7], 16) / 255.0
                    canvas_obj.setFillColorRGB(r, g, b)
                except:
                    canvas_obj.setFillColorRGB(0, 0, 0)
            
            # Dibujar según alineación
            if alineacion in ['left', 'center', 'right']:
                self._dibujar_texto_alineado_simple(
                    canvas_obj, texto_completo, x_pt, y_pt, ancho_pt,
                    fuente_nombre, tamano, alineacion
                )
            else:  # justify
                if alto_pt > tamano * 1.5:  # Si hay espacio para múltiples líneas
                    self._dibujar_texto_justificado_multilinea(
                        canvas_obj, texto_completo, x_pt, y_pt, ancho_pt, alto_pt,
                        fuente_nombre, tamano, color_hex
                    )
                else:
                    self._dibujar_texto_alineado_simple(
                        canvas_obj, texto_completo, x_pt, y_pt, ancho_pt,
                        fuente_nombre, tamano, 'left'
                    )
                    
        except Exception as e:
            print(f"⚠️ Error dibujando campo compuesto: {e}")
            import traceback
            traceback.print_exc()

    def _dibujar_texto_alineado_simple(self, canvas_obj, texto, x, y, ancho, 
                                      fuente, tamano, alineacion):
        """Dibuja texto con alineación simple (left/center/right)"""
        canvas_obj.setFont(fuente, tamano)
        
        # Calcular posición según alineación
        if alineacion == 'left':
            # Izquierda: usar x directamente
            pos_x = x
        elif alineacion == 'center':
            # Centro: calcular ancho del texto
            text_width = canvas_obj.stringWidth(texto, fuente, tamano)
            pos_x = x + (ancho - text_width) / 2
        else:  # right
            # Derecha: alinear a la derecha del área
            text_width = canvas_obj.stringWidth(texto, fuente, tamano)
            pos_x = x + ancho - text_width
        
        # Dibujar (ajustar Y para alineación vertical)
        canvas_obj.drawString(pos_x, y + (tamano * 0.7), texto)
    
    def _dibujar_texto_con_paragraph(self, canvas_obj, texto, x, y, ancho, alto,
                                fuente, tamano, alineacion, color):
        """Dibuja texto con Paragraph para alineación compleja, ESPECIALMENTE justify"""
        try:
            # Para justify, necesitamos lógica especial
            if alineacion == 'justify':
                return self._dibujar_texto_justificado(
                    canvas_obj, texto, x, y, ancho, alto, 
                    fuente, tamano, color
                )
            
            # Para left/center/right, usar Paragraph normal
            estilo = ParagraphStyle(
                name='CustomStyle',
                fontName=fuente,
                fontSize=tamano,
                alignment=self._get_alignment_code(alineacion),
                textColor=self._hex_to_color(color),
                leading=tamano * 1.2,
                wordWrap='CJK'
            )
            
            para = Paragraph(texto, estilo)
            w, h = para.wrap(ancho, alto)
            
            # Ajustar posición vertical
            y_adj = y + (alto - h) / 2
            para.drawOn(canvas_obj, x, y_adj)
            
        except Exception as e:
            print(f"⚠️ Error con Paragraph: {e}")
            # Fallback
            self._dibujar_texto_alineado_simple(
                canvas_obj, texto, x, y, ancho, fuente, tamano, 'left'
            )
    
    def _dibujar_texto_justificado(self, canvas_obj, texto, x, y, ancho, alto,
                              fuente, tamano, color):
        """Dibuja texto JUSTIFICADO con cálculo real de espacios"""
        try:
            # Si el texto es muy corto, justificar no tiene sentido -> usar left
            palabras = texto.strip().split()
            if len(palabras) <= 1:
                self._dibujar_texto_alineado_simple(
                    canvas_obj, texto, x, y, ancho, fuente, tamano, 'left'
                )
                return
            
            # Configurar fuente
            canvas_obj.setFont(fuente, tamano)
            canvas_obj.setFillColor(self._hex_to_color(color))
            
            # Calcular métricas
            espacio_ancho = canvas_obj.stringWidth(' ', fuente, tamano)
            
            # Calcular ancho total de palabras (sin espacios)
            ancho_palabras = 0
            for palabra in palabras:
                ancho_palabras += canvas_obj.stringWidth(palabra, fuente, tamano)
            
            # Calcular espacios necesarios
            espacios_necesarios = len(palabras) - 1
            if espacios_necesarios == 0:
                espacios_necesarios = 1
            
            # Calcular espacio extra por espacio para justificar
            ancho_disponible = ancho - ancho_palabras
            espacio_extra_por_espacio = ancho_disponible / espacios_necesarios
            
            # Dibujar línea justificada
            current_x = x
            for i, palabra in enumerate(palabras):
                # Dibujar palabra
                canvas_obj.drawString(current_x, y + (tamano * 0.7), palabra)
                
                # Mover posición
                palabra_ancho = canvas_obj.stringWidth(palabra, fuente, tamano)
                current_x += palabra_ancho
                
                # Añadir espacio (normal + extra para justificar)
                if i < len(palabras) - 1:  # No añadir espacio después de última palabra
                    espacio_total = espacio_ancho + espacio_extra_por_espacio
                    current_x += espacio_total
            
        except Exception as e:
            print(f"⚠️ Error en justify, usando left: {e}")
            self._dibujar_texto_alineado_simple(
                canvas_obj, texto, x, y, ancho, fuente, tamano, 'left'
            )

    def _dibujar_texto_justificado_multilinea(self, canvas_obj, texto, x, y, ancho, alto,
                                         fuente, tamano, color):
        """Dibuja texto JUSTIFICADO con salto de línea automático"""
        try:
            # Configurar fuente
            canvas_obj.setFont(fuente, tamano)
            canvas_obj.setFillColor(self._hex_to_color(color))
            
            # Dividir texto en palabras
            palabras = texto.strip().split()
            if not palabras:
                return
            
            # Calcular ancho de espacio
            espacio_ancho = canvas_obj.stringWidth(' ', fuente, tamano)
            
            # Variables para el layout
            lineas = []
            linea_actual = []
            ancho_linea_actual = 0
            
            # Distribuir palabras en líneas
            for palabra in palabras:
                palabra_ancho = canvas_obj.stringWidth(palabra, fuente, tamano)
                
                # Si la palabra cabe en la línea actual
                espacio_necesario = palabra_ancho + (len(linea_actual) * espacio_ancho if linea_actual else 0)
                
                if ancho_linea_actual + espacio_necesario <= ancho or not linea_actual:
                    # Añadir palabra a línea actual
                    linea_actual.append(palabra)
                    ancho_linea_actual += palabra_ancho + (espacio_ancho if linea_actual else 0)
                else:
                    # Guardar línea actual y empezar nueva
                    lineas.append((linea_actual.copy(), ancho_linea_actual - espacio_ancho))
                    linea_actual = [palabra]
                    ancho_linea_actual = palabra_ancho
            
            # Añadir última línea
            if linea_actual:
                lineas.append((linea_actual.copy(), ancho_linea_actual - espacio_ancho if len(linea_actual) > 1 else ancho_linea_actual))
            
            # Calcular altura total y posición vertical
            line_height = tamano * 1.2
            total_height = len(lineas) * line_height
            
            # Centrar verticalmente si hay espacio
            y_start = y + (alto - total_height) / 2 if alto > total_height else y
            current_y = y_start + (len(lineas) - 1) * line_height  # Empezar desde abajo
            
            # Dibujar cada línea justificada
            for palabras_linea, ancho_palabras in lineas:
                if len(palabras_linea) <= 1:
                    # Una sola palabra, alinear a la izquierda
                    self._dibujar_texto_alineado_simple(
                        canvas_obj, ' '.join(palabras_linea), x, current_y, 
                        ancho, fuente, tamano, 'left'
                    )
                else:
                    # Múltiples palabras, justificar
                    self._dibujar_linea_justificada(
                        canvas_obj, palabras_linea, x, current_y, ancho,
                        fuente, tamano, ancho_palabras
                    )
                
                current_y -= line_height  # Mover hacia arriba para siguiente línea
        
        except Exception as e:
            print(f"⚠️ Error en justify multilínea: {e}")
            # Fallback a Paragraph
            self._dibujar_texto_con_paragraph_fallback(
                canvas_obj, texto, x, y, ancho, alto, fuente, tamano, color
            )

    def _dibujar_linea_justificada(self, canvas_obj, palabras, x, y, ancho_total,
                                fuente, tamano, ancho_palabras):
        """Dibuja una sola línea justificada"""
        # Calcular espacios
        num_espacios = len(palabras) - 1
        ancho_espacios = ancho_total - ancho_palabras
        espacio_extra = ancho_espacios / num_espacios if num_espacios > 0 else 0
        
        # Calcular ancho de espacio normal
        espacio_normal = canvas_obj.stringWidth(' ', fuente, tamano)
        
        # Dibujar palabras con espacios ajustados
        current_x = x
        for i, palabra in enumerate(palabras):
            # Dibujar palabra
            canvas_obj.drawString(current_x, y + (tamano * 0.7), palabra)
            
            # Calcular ancho de esta palabra
            palabra_ancho = canvas_obj.stringWidth(palabra, fuente, tamano)
            current_x += palabra_ancho
            
            # Añadir espacio (excepto después de última palabra)
            if i < len(palabras) - 1:
                espacio_total = espacio_normal + espacio_extra
                current_x += espacio_total

    def _dibujar_texto_con_paragraph_fallback(self, canvas_obj, texto, x, y, ancho, alto,
                                            fuente, tamano, color):
        """Fallback usando Paragraph (menos preciso para justify)"""
        try:
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.platypus import Paragraph
            from reportlab.lib.enums import TA_JUSTIFY
            
            # Crear estilo con justify
            styles = getSampleStyleSheet()
            estilo = ParagraphStyle(
                'JustifyStyle',
                parent=styles['Normal'],
                fontName=fuente,
                fontSize=tamano,
                textColor=self._hex_to_color(color),
                alignment=TA_JUSTIFY,
                leading=tamano * 1.2,
                wordWrap='CJK'
            )
            
            # Crear y dibujar párrafo
            para = Paragraph(texto, estilo)
            w, h = para.wrap(ancho, alto)
            
            # Centrar verticalmente
            y_adj = y + (alto - h) / 2
            para.drawOn(canvas_obj, x, y_adj)
            
        except Exception as e:
            print(f"⚠️ Fallback también falló: {e}")
            # Último recurso: texto simple izquierda
            canvas_obj.setFont(fuente, tamano)
            canvas_obj.drawString(x, y + (tamano * 0.7), texto)

    def _hex_to_color(self, hex_color: str):
        """Convierte hex color a objeto Color de ReportLab"""
        from reportlab.lib.colors import Color, HexColor
        try:
            return HexColor(hex_color)
        except:
            # Fallback a negro
            return Color(0, 0, 0, alpha=1)
    
    def generar_multiples_pdfs(self, campos: List[Dict], lista_datos: List[Dict],
                              output_dir: str, nombre_base: str = "documento"):
        """Genera múltiples PDFs (uno por registro)"""
        os.makedirs(output_dir, exist_ok=True)
        
        archivos_generados = []
        for i, datos in enumerate(lista_datos):
            output_path = os.path.join(output_dir, f"{nombre_base}_{i+1}.pdf")
            if self.generar_pdf_con_datos(campos, datos, output_path):
                archivos_generados.append(output_path)
        
        return archivos_generados
    
    def _dibujar_tabla_real(self, canvas_obj, campo: Dict, datos: Dict, 
                       x_pt: float, y_pt: float):
        """Dibuja una tabla REAL usando reportlab.platypus.Table"""
        try:
            # Obtener configuración
            columnas = campo.get('columnas', 3)
            filas = campo.get('filas', 4)
            encabezado = campo.get('encabezado', True)
            mostrar_borde = campo.get('borde', True)
            ancho_total_mm = campo.get('ancho', 200)
            alto_total_mm = campo.get('alto', 100)
            
            # Convertir mm a puntos
            ancho_total_pt = ancho_total_mm * mm
            alto_total_pt = alto_total_mm * mm
            
            # Preparar datos de la tabla
            tabla_data = []
            celdas_config = campo.get('celdas', [])
            
            for fila_idx in range(filas):
                fila_data = []
                for col_idx in range(columnas):
                    # Obtener configuración de celda
                    if fila_idx < len(celdas_config) and col_idx < len(celdas_config[fila_idx]):
                        celda_config = celdas_config[fila_idx][col_idx]
                    else:
                        celda_config = {'tipo': 'texto', 'valor': '', 'alineacion': 'left'}
                    
                    # Obtener texto según tipo
                    if celda_config['tipo'] == 'texto':
                        texto = celda_config.get('valor', '')
                    else:  # campo
                        columna = celda_config.get('valor', '')
                        texto = str(datos.get(columna, f'{{{columna}}}'))
                    
                    fila_data.append(texto)
                tabla_data.append(fila_data)
            
            # Crear tabla de ReportLab
            tabla = Table(tabla_data, colWidths=ancho_total_pt/columnas, rowHeights=alto_total_pt/filas)
            
            # Configurar estilo de la tabla
            estilo_tabla = []
            
            # Bordes
            if mostrar_borde:
                estilo_tabla.append(('GRID', (0, 0), (-1, -1), 1, colors.black))
            else:
                estilo_tabla.append(('GRID', (0, 0), (-1, -1), 0, colors.white))
            
            # Encabezado
            if encabezado and filas > 0:
                estilo_tabla.append(('BACKGROUND', (0, 0), (-1, 0), 
                                self._hex_to_color(campo.get('color_fondo_encabezado', '#f0f0f0'))))
                estilo_tabla.append(('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'))
                estilo_tabla.append(('FONTSIZE', (0, 0), (-1, 0), campo.get('tamano_fuente', 10)))
                estilo_tabla.append(('ALIGN', (0, 0), (-1, 0), 'CENTER'))
                estilo_tabla.append(('VALIGN', (0, 0), (-1, 0), 'MIDDLE'))
            
            # Aplicar estilos de celdas individuales
            for fila_idx in range(filas):
                for col_idx in range(columnas):
                    if fila_idx < len(celdas_config) and col_idx < len(celdas_config[fila_idx]):
                        celda_config = celdas_config[fila_idx][col_idx]
                        
                        # Saltar encabezado (ya tiene estilo)
                        if encabezado and fila_idx == 0:
                            continue
                        
                        # Alineación
                        align_map = {'left': 'LEFT', 'center': 'CENTER', 'right': 'RIGHT', 'justify': 'LEFT'}
                        alineacion = align_map.get(celda_config.get('alineacion', 'left'), 'LEFT')
                        estilo_tabla.append(('ALIGN', (col_idx, fila_idx), (col_idx, fila_idx), alineacion))
                        
                        # Negrita
                        if celda_config.get('negrita', False):
                            estilo_tabla.append(('FONTNAME', (col_idx, fila_idx), (col_idx, fila_idx), 'Helvetica-Bold'))
                        
                        # Tamaño de fuente
                        estilo_tabla.append(('FONTSIZE', (col_idx, fila_idx), (col_idx, fila_idx), 
                                        campo.get('tamano_fuente', 10)))
            
            # Aplicar estilo
            tabla.setStyle(TableStyle(estilo_tabla))
            
            # Dibujar tabla en posición correcta
            # Nota: y_pt ya está ajustado para coordenadas PDF (0 abajo)
            tabla.wrapOn(canvas_obj, ancho_total_pt, alto_total_pt)
            tabla.drawOn(canvas_obj, x_pt, y_pt)
            
            print(f"✅ Tabla dibujada: {columnas}x{filas} en ({x_pt:.1f}, {y_pt:.1f})")
            
        except Exception as e:
            print(f"❌ Error dibujando tabla: {e}")
            import traceback
            traceback.print_exc()
            
            # Fallback: dibujar rectángulo con texto de error
            canvas_obj.setStrokeColor(colors.red)
            canvas_obj.setFillColor(colors.white)
            canvas_obj.rect(x_pt, y_pt, ancho_total_pt, alto_total_pt, fill=1)
            canvas_obj.setFillColor(colors.red)
            canvas_obj.setFont("Helvetica", 8)
            canvas_obj.drawString(x_pt + 5, y_pt + alto_total_pt/2, f"Error tabla: {str(e)[:50]}")