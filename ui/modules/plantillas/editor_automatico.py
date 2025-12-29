class EditorAutomatico(QWidget):
    """
    Editor automático completo con:
    1. Carga Word + PDF
    2. Extracción automática de campos
    3. Mapeo automático de coordenadas
    4. Asignación automática a padrón
    5. Vista previa toggle integrada
    6. Ajuste manual si es necesario
    """
    
    def __init__(self, usuario, proyecto_id, stacked_widget):
        super().__init__()
        self.usuario = usuario
        self.proyecto_id = proyecto_id
        self.stacked_widget = stacked_widget
        
        # Estado
        self.word_path = None
        self.pdf_path = None
        self.campos_detectados = []
        self.campos_mapeados = []
        self.modo_vista = 'campos'  # 'campos' o 'preview'
        self.registro_actual_idx = 0
        self.registros_preview = []
        
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout()
        
        # ===== HEADER =====
        header = self.crear_header()
        layout.addWidget(header)
        
        # ===== PROGRESO AUTOMÁTICO =====
        self.progress_automatico = self.crear_progress_automatico()
        layout.addWidget(self.progress_automatico)
        
        # ===== ÁREA PRINCIPAL (Splitter) =====
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Panel izquierdo: Control y configuración
        panel_izquierdo = self.crear_panel_izquierdo()
        splitter.addWidget(panel_izquierdo)
        
        # Panel central: PDF con overlay
        panel_central = self.crear_panel_central()
        splitter.addWidget(panel_central)
        
        # Panel derecho: Vista previa y ajustes
        panel_derecho = self.crear_panel_derecho()
        splitter.addWidget(panel_derecho)
        
        splitter.setSizes([300, 600, 300])
        layout.addWidget(splitter)
        
        # ===== BARRA INFERIOR =====
        barra_inferior = self.crear_barra_inferior()
        layout.addWidget(barra_inferior)
        
        self.setLayout(layout)
    
    def crear_header(self):
        """Header con pasos del proceso automático"""
        header = QFrame()
        header.setStyleSheet("""
            QFrame { background: #2c3e50; border-radius: 5px; padding: 10px; }
            QLabel { color: white; font-weight: bold; }
        """)
        
        layout = QHBoxLayout()
        
        pasos = [
            ("1️⃣", "Cargar Word y PDF"),
            ("2️⃣", "Extraer campos automáticamente"),
            ("3️⃣", "Mapear coordenadas en PDF"),
            ("4️⃣", "Asignar a columnas del padrón"),
            ("5️⃣", "Vista previa y ajustes")
        ]
        
        for icono, texto in pasos:
            paso_widget = QWidget()
            paso_layout = QVBoxLayout()
            
            lbl_icono = QLabel(icono)
            lbl_icono.setAlignment(Qt.AlignmentFlag.AlignCenter)
            
            lbl_texto = QLabel(texto)
            lbl_texto.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl_texto.setWordWrap(True)
            
            paso_layout.addWidget(lbl_icono)
            paso_layout.addWidget(lbl_texto)
            paso_widget.setLayout(paso_layout)
            
            layout.addWidget(paso_widget)
        
        header.setLayout(layout)
        return header
    
    def crear_progress_automatico(self):
        """Barra de progreso para el proceso automático"""
        frame = QFrame()
        frame.setVisible(False)
        
        layout = QVBoxLayout()
        
        self.lbl_progreso = QLabel("Iniciando proceso automático...")
        
        self.barra_progreso = QProgressBar()
        self.barra_progreso.setRange(0, 100)
        
        layout.addWidget(self.lbl_progreso)
        layout.addWidget(self.barra_progreso)
        
        frame.setLayout(layout)
        return frame
    
    def iniciar_proceso_automatico(self):
        """Ejecuta todo el pipeline automático"""
        self.progress_automatico.setVisible(True)
        self.barra_progreso.setValue(0)
        self.lbl_progreso.setText("1. Extrayendo campos del Word...")
        QApplication.processEvents()
        
        try:
            # Paso 1: Extraer campos del Word
            from core.word_advanced_extractor import WordAdvancedExtractor
            extractor = WordAdvancedExtractor()
            self.campos_detectados = extractor.extraer_campos_detallados(self.word_path)
            
            self.barra_progreso.setValue(25)
            self.lbl_progreso.setText("2. Buscando coordenadas en PDF...")
            QApplication.processEvents()
            
            # Paso 2: Encontrar coordenadas en PDF
            from core.pdf_coordinate_finder import PDFCoordinateFinder
            finder = PDFCoordinateFinder()
            self.campos_mapeados = finder.encontrar_coordenadas(self.campos_detectados, self.pdf_path)
            
            self.barra_progreso.setValue(50)
            self.lbl_progreso.setText("3. Asignando a columnas del padrón...")
            QApplication.processEvents()
            
            # Paso 3: Match con columnas del padrón
            from core.template_matcher import TemplateMatcher
            matcher = TemplateMatcher()
            
            # Obtener columnas del padrón
            columnas_padron = self.obtener_columnas_padron()
            
            resultados_match = matcher.match_automatico(
                [c['placeholder'] for c in self.campos_mapeados if c.get('coordenadas_pdf')],
                columnas_padron
            )
            
            self.barra_progreso.setValue(75)
            self.lbl_progreso.setText("4. Preparando vista previa...")
            QApplication.processEvents()
            
            # Paso 4: Preparar vista previa
            self.preparar_vista_previa()
            
            self.barra_progreso.setValue(100)
            self.lbl_progreso.setText("✅ Proceso automático completado")
            
            # Mostrar resultados
            self.mostrar_resultados_automaticos(resultados_match)
            
        except Exception as e:
            self.lbl_progreso.setText(f"❌ Error: {str(e)}")
            QMessageBox.critical(self, "Error", f"Error en proceso automático:\n{str(e)}")