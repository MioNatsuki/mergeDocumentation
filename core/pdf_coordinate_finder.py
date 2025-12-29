import fitz  # PyMuPDF
import re
from typing import List, Dict
from rapidfuzz import fuzz, process

class PDFCoordinateFinder:
    """
    Encuentra coordenadas exactas en el PDF basándose en el contexto
    extraído del Word
    """
    
    def encontrar_coordenadas(self, campos_word: List[Dict], pdf_path: str) -> List[Dict]:
        """
        Para cada campo del Word, busca su posición en el PDF
        usando matching de contexto inteligente
        """
        # 1. Extraer TODO el texto del PDF con coordenadas
        textos_pdf = self._extraer_texto_pdf_con_coordenadas(pdf_path)
        
        # 2. Para cada campo del Word, buscar la mejor coincidencia
        campos_con_coordenadas = []
        
        for campo in campos_word:
            coordenadas = self._buscar_coordenadas_campo(campo, textos_pdf)
            if coordenadas:
                campo['coordenadas_pdf'] = coordenadas
                campos_con_coordenadas.append(campo)
            else:
                # Marcar para revisión manual
                campo['coordenadas_pdf'] = None
                campo['necesita_ajuste_manual'] = True
                campos_con_coordenadas.append(campo)
        
        return campos_con_coordenadas
    
    def _extraer_texto_pdf_con_coordenadas(self, pdf_path: str) -> List[Dict]:
        """Extrae todo texto del PDF con coordenadas exactas por palabra"""
        doc = fitz.open(pdf_path)
        textos = []
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            
            # Obtener palabras con bboxes
            words = page.get_text("words")
            
            for word in words:
                x0, y0, x1, y1, word_text, block_no, line_no, word_no = word
                
                # Convertir puntos a mm (1 punto = 0.3528 mm)
                x0_mm = x0 * 0.3528
                y0_mm = y0 * 0.3528
                x1_mm = x1 * 0.3528
                y1_mm = y1 * 0.3528
                
                textos.append({
                    'texto': word_text,
                    'x_mm': x0_mm,
                    'y_mm': y0_mm,
                    'ancho_mm': x1_mm - x0_mm,
                    'alto_mm': y1_mm - y0_mm,
                    'pagina': page_num + 1,
                    'bbox': (x0, y0, x1, y1)
                })
        
        # Agrupar palabras en líneas y párrafos
        textos = self._agrupar_en_lineas(textos)
        
        return textos
    
    def _buscar_coordenadas_campo(self, campo: Dict, textos_pdf: List[Dict]) -> Dict:
        """
        Busca las coordenadas de un campo específico usando:
        1. Contexto anterior/posterior
        2. Fuzzy matching
        3. Posición relativa estimada
        """
        # Construir patrón de búsqueda con contexto
        patron_busqueda = (
            campo.get('contexto_previo', '') + 
            '{' + campo['placeholder'] + '}' + 
            campo.get('contexto_posterior', '')
        )
        
        # Buscar coincidencias aproximadas
        coincidencias = self._buscar_coincidencias_fuzzy(patron_busqueda, textos_pdf)
        
        if not coincidencias:
            return None
        
        # Tomar la mejor coincidencia
        mejor_coincidencia = coincidencias[0]
        
        # Calcular coordenadas del placeholder dentro de la coincidencia
        return self._calcular_coordenadas_placeholder(campo, mejor_coincidencia)