import docx
from docx.oxml import parse_xml
from docx.oxml.ns import qn
import re
from typing import List, Dict, Tuple
import zipfile
import xml.etree.ElementTree as ET

class WordAdvancedExtractor:
    """
    Extrae placeholders con contexto y posiciones RELATIVAS del Word
    Analiza el XML interno del .docx para máxima precisión
    """
    
    def extraer_campos_detallados(self, word_path: str) -> List[Dict]:
        """
        Extrae cada {placeholder} con:
        - Texto anterior y posterior (contexto)
        - Página aproximada
        - Posición relativa en párrafo
        - Estilos aplicados (fuente, tamaño, negrita, etc.)
        - Si está en tabla, celda específica
        """
        try:
            # Abrir .docx como ZIP para acceder a XML
            with zipfile.ZipFile(word_path, 'r') as docx_zip:
                # Leer document.xml
                document_xml = docx_zip.read('word/document.xml')
                
                # Parsear XML
                root = ET.fromstring(document_xml)
                
                # Buscar todos los text elements
                campos = self._buscar_campos_en_xml(root)
                
                # Enriquecer con estilos
                campos = self._agregar_estilos(campos, docx_zip)
                
                return campos
                
        except Exception as e:
            # Fallback a python-docx simple
            return self._extraer_con_fallback(word_path)
    
    def _buscar_campos_en_xml(self, root: ET.Element) -> List[Dict]:
        """Busca {placeholders} en el XML del documento"""
        campos = []
        namespace = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
        
        # Buscar todos los elementos de texto (w:t)
        for t_elem in root.findall('.//w:t', namespace):
            texto = t_elem.text or ''
            
            # Buscar placeholders en este texto
            matches = re.finditer(r'\{(\w+)\}', texto)
            for match in matches:
                placeholder = match.group(1)
                inicio = match.start()
                fin = match.end()
                
                # Obtener contexto (texto alrededor)
                contexto_previo = texto[max(0, inicio-30):inicio]
                contexto_posterior = texto[fin:min(len(texto), fin+30)]
                
                # Obtener posición en el documento
                posicion = self._obtener_posicion_elemento(t_elem, root, namespace)
                
                campo = {
                    'placeholder': placeholder,
                    'texto_completo': texto,
                    'contexto_previo': contexto_previo,
                    'contexto_posterior': contexto_posterior,
                    'posicion_relativa': inicio / max(len(texto), 1),
                    'estilo': self._extraer_estilo_elemento(t_elem, namespace),
                    **posicion
                }
                campos.append(campo)
        
        return campos