from typing import List, Dict
from rapidfuzz import fuzz, process
import re

class ContextMatcher:
    """
    Matching inteligente usando NLP básico y fuzzy matching
    """
    
    def buscar_mejor_coincidencia(self, contexto_word: str, textos_pdf: List[Dict]) -> Dict:
        """
        Encuentra la mejor coincidencia usando múltiples estrategias:
        1. Coincidencia exacta de palabras clave
        2. Fuzzy matching con threshold
        3. Proximidad de palabras
        4. Patrones comunes (fechas, números, etc.)
        """
        # Estrategia 1: Buscar palabras clave únicas
        palabras_clave = self._extraer_palabras_clave(contexto_word)
        
        for texto_pdf in textos_pdf:
            score = self._calcular_score_coincidencia(palabras_clave, texto_pdf['texto'])
            if score > 0.8:  # Threshold alto
                return texto_pdf
        
        # Estrategia 2: Fuzzy matching en texto completo
        mejor_match, score = process.extractOne(
            contexto_word,
            [t['texto'] for t in textos_pdf],
            scorer=fuzz.partial_ratio
        )
        
        if score > 70:
            for texto_pdf in textos_pdf:
                if texto_pdf['texto'] == mejor_match:
                    return texto_pdf
        
        return None
    
    def _extraer_palabras_clave(self, texto: str) -> List[str]:
        """Extrae palabras clave no comunes"""
        # Remover stopwords y palabras comunes
        stopwords = {'el', 'la', 'los', 'las', 'de', 'del', 'y', 'o', 'en', 'a', 'para'}
        palabras = re.findall(r'\b\w+\b', texto.lower())
        return [p for p in palabras if p not in stopwords and len(p) > 3]