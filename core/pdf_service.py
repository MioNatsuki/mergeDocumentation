import os
from datetime import datetime
from reportlab.lib.pagesizes import letter, A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm, inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.colors import black, blue, red
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import Paragraph, Table, TableStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
import json
from typing import Dict, List, Tuple, Optional

class PDFService:
    def __init__(self):
        self.setup_fonts()
    
    def setup_fonts(self):
        """Configura fuentes para los PDFs"""
        try:
            # Registrar fuentes básicas (usar las disponibles en el sistema)
            pdfmetrics.registerFont(TTFont('Helvetica', 'Helvetica'))
            pdfmetrics.registerFont(TTFont('Helvetica-Bold', 'Helvetica-Bold'))
        except:
            # Si no se pueden cargar fuentes personalizadas, usar las por defecto
            pass
    
    def generar_pdf(self, datos: Dict, plantilla_config: Dict, 
                   ruta_salida: str, nombre_archivo: str) -> Tuple[bool, str]:
        """ Genera un PDF real con los datos proporcionados """
        try:
            # Crear directorio si no existe
            os.makedirs(ruta_salida, exist_ok=True)
            
            ruta_completa = os.path.join(ruta_salida, nombre_archivo)
            
            # Configurar página
            pagina_tamano = plantilla_config.get('page_size', 'A4')
            margen = plantilla_config.get('margin', 20) * mm
            
            if pagina_tamano.upper() == 'LETTER':
                page_size = letter
            else:
                page_size = A4
            
            # Crear canvas PDF
            c = canvas.Canvas(ruta_completa, pagesize=page_size)
            ancho, alto = page_size
            
            # Estilos
            estilos = getSampleStyleSheet()
            
            # Agregar estilos personalizados
            estilos.add(ParagraphStyle(
                name='CampoDinamico',
                fontName='Helvetica',
                fontSize=10,
                leading=12,
                textColor=black,
                alignment=TA_LEFT
            ))
            
            estilos.add(ParagraphStyle(
                name='CampoDestacado',
                fontName='Helvetica-Bold', 
                fontSize=12,
                leading=14,
                textColor=black,
                alignment=TA_LEFT
            ))
            
            # Dibujar campos dinámicos
            campos = plantilla_config.get('campos', {})
            campos_generados = 0
            
            for campo_nombre, config_campo in campos.items():
                try:
                    # Obtener valor del dato
                    valor = self.obtener_valor_campo(datos, campo_nombre, config_campo)
                    if valor is None:
                        continue
                    
                    # Posicionamiento
                    x = config_campo.get('x', 0) * mm
                    y = alto - config_campo.get('y', 0) * mm  # Invertir Y para coordenadas PDF
                    
                    # Estilo del campo
                    estilo = config_campo.get('estilo', 'normal')
                    fuente_tamano = config_campo.get('font_size', 10)
                    negrita = config_campo.get('bold', False)
                    alineacion = config_campo.get('alignment', 'left')
                    
                    # Configurar fuente
                    if negrita:
                        c.setFont("Helvetica-Bold", fuente_tamano)
                    else:
                        c.setFont("Helvetica", fuente_tamano)
                    
                    # Aplicar alineación
                    ancho_campo = config_campo.get('width', 100) * mm
                    if alineacion == 'center':
                        x = x + (ancho_campo - c.stringWidth(str(valor))) / 2
                    elif alineacion == 'right':
                        x = x + ancho_campo - c.stringWidth(str(valor))
                    
                    # Dibujar texto
                    c.drawString(x, y, str(valor))
                    campos_generados += 1
                    
                except Exception as e:
                    print(f"Error dibujando campo {campo_nombre}: {e}")
                    continue
            
            # Dibujar información de sistema (opcional)
            if plantilla_config.get('mostrar_info_sistema', False):
                self.dibujar_info_sistema(c, ancho, alto)
            
            # Guardar PDF
            c.save()
            
            if campos_generados == 0:
                return False, "No se generaron campos dinámicos"
            
            return True, ruta_completa
            
        except Exception as e:
            return False, f"Error generando PDF: {str(e)}"
    
    def obtener_valor_campo(self, datos: Dict, campo_nombre: str, config_campo: Dict) -> Optional[str]:
        """Obtiene y formatea el valor de un campo"""
        try:
            # Buscar valor en datos
            valor = datos.get(campo_nombre, '')
            
            # Si no se encuentra, buscar en datos_json
            if not valor and 'datos_json' in datos:
                datos_json = datos['datos_json']
                if isinstance(datos_json, str):
                    datos_json = json.loads(datos_json)
                valor = datos_json.get(campo_nombre, '')
            
            # Aplicar formato si está especificado
            formato = config_campo.get('formato', '')
            if formato and valor:
                valor = self.aplicar_formato(valor, formato)
            
            # Valor por defecto si está vacío
            if not valor:
                valor = config_campo.get('valor_default', '')
            
            return str(valor) if valor is not None else ''
            
        except Exception as e:
            print(f"Error obteniendo valor para {campo_nombre}: {e}")
            return config_campo.get('valor_default', '')
    
    def aplicar_formato(self, valor: str, formato: str) -> str:
        """Aplica formato al valor según la especificación"""
        try:
            if formato == 'moneda':
                return f"${float(valor):,.2f}"
            elif formato == 'porcentaje':
                return f"{float(valor):.1f}%"
            elif formato == 'fecha':
                # Intentar parsear fecha
                try:
                    from datetime import datetime
                    fecha = datetime.strptime(str(valor), '%Y-%m-%d')
                    return fecha.strftime('%d/%m/%Y')
                except:
                    return str(valor)
            elif formato == 'mayusculas':
                return str(valor).upper()
            elif formato == 'capitalize':
                return str(valor).title()
            else:
                return str(valor)
        except:
            return str(valor)
    
    def dibujar_info_sistema(self, c: canvas.Canvas, ancho: float, alto: float):
        """Dibuja información del sistema en el PDF"""
        info_texto = f"Generado el: {datetime.now().strftime('%d/%m/%Y %H:%M')} - Sistema de Correspondencia"
        c.setFont("Helvetica", 8)
        c.setFillColor(blue)
        c.drawString(20 * mm, 10 * mm, info_texto)
    
    def validar_configuracion_plantilla(self, plantilla_config: Dict) -> Tuple[bool, List[str]]:
        """Valida la configuración de una plantilla"""
        errores = []
        
        if not plantilla_config.get('campos'):
            errores.append("La plantilla no tiene campos configurados")
        
        # Validar campos requeridos
        campos_requeridos = ['cuenta', 'codigo_afiliado', 'nombre_afiliado']
        campos_configurados = list(plantilla_config.get('campos', {}).keys())
        
        for campo in campos_requeridos:
            if campo not in campos_configurados:
                errores.append(f"Campo requerido faltante: {campo}")
        
        # Validar coordenadas
        for campo_nombre, config in plantilla_config.get('campos', {}).items():
            if 'x' not in config or 'y' not in config:
                errores.append(f"Campo {campo_nombre} sin coordenadas x,y")
        
        return len(errores) == 0, errores
    
    def generar_lote_pdfs(self, registros: List[Dict], plantilla_config: Dict, 
                         ruta_salida: str, callback_progreso=None) -> Dict:
        """Genera un lote de PDFs"""
        resultados = {
            'total': len(registros),
            'exitosos': 0,
            'fallidos': 0,
            'errores': [],
            'archivos_generados': []
        }
        
        for i, registro in enumerate(registros):
            try:
                # Nombre de archivo basado en cuenta
                cuenta = registro.get('cuenta', f'doc_{i+1}')
                nombre_archivo = f"{cuenta}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
                
                # Generar PDF
                exito, resultado = self.generar_pdf(registro, plantilla_config, ruta_salida, nombre_archivo)
                
                if exito:
                    resultados['exitosos'] += 1
                    resultados['archivos_generados'].append({
                        'archivo': nombre_archivo,
                        'ruta': resultado,
                        'cuenta': cuenta
                    })
                else:
                    resultados['fallidos'] += 1
                    resultados['errores'].append(f"{cuenta}: {resultado}")
                
                # Callback de progreso
                if callback_progreso:
                    callback_progreso(i + 1, len(registros), cuenta, exito)
                    
            except Exception as e:
                resultados['fallidos'] += 1
                resultados['errores'].append(f"Error procesando registro {i+1}: {str(e)}")
        
        return resultados