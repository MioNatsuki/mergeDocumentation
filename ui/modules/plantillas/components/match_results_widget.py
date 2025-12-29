class MatchResultsWidget(QWidget):
    """
    Muestra resultados del match automático con:
    - Campos correctamente mapeados (✅)
    - Campos con #REF (advertencia)
    - Campos que necesitan ajuste manual
    """
    
    def __init__(self):
        super().__init__()
        self.setup_ui()
    
    def mostrar_resultados(self, resultados: Dict):
        """
        resultados = {
            'matches': {'nombre': 'nombre_completo', ...},
            'no_matches': ['campo1', 'campo2'],
            'match_rate': 0.85,
            'campos_sin_coordenadas': [...],
            'sugerencias': {...}
        }
        """
        # Limpiar widget
        # Mostrar estadísticas
        # Mostrar lista de matches
        # Mostrar lista de #REF con opción de asignar manualmente
        pass