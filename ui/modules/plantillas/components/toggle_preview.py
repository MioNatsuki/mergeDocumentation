class TogglePreview(QWidget):
    """
    Componente de toggle entre:
    - Modo Campos: Muestra {placeholders} en sus posiciones
    - Modo Preview: Muestra datos reales del registro actual
    """
    
    def __init__(self):
        super().__init__()
        self.modo = 'campos'  # 'campos' o 'preview'
        self.datos_actuales = {}
        self.campos_config = []
        
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout()
        
        # Barra de control
        barra_control = QHBoxLayout()
        
        self.btn_toggle = QPushButton("👁️ Vista Previa de Resultados")
        self.btn_toggle.setCheckable(True)
        self.btn_toggle.clicked.connect(self.toggle_modo)
        
        self.lbl_modo = QLabel("Modo: Mostrando Campos")
        
        # Navegación (solo visible en modo preview)
        self.nav_widget = QWidget()
        nav_layout = QHBoxLayout()
        
        self.btn_anterior = QPushButton("◀ Anterior")
        self.btn_anterior.clicked.connect(self.registro_anterior)
        
        self.lbl_registro = QLabel("Registro 0/0")
        
        self.btn_siguiente = QPushButton("Siguiente ▶")
        self.btn_siguiente.clicked.connect(self.registro_siguiente)
        
        nav_layout.addWidget(self.btn_anterior)
        nav_layout.addWidget(self.lbl_registro)
        nav_layout.addWidget(self.btn_siguiente)
        
        self.nav_widget.setLayout(nav_layout)
        self.nav_widget.setVisible(False)
        
        barra_control.addWidget(self.btn_toggle)
        barra_control.addWidget(self.lbl_modo)
        barra_control.addStretch()
        barra_control.addWidget(self.nav_widget)
        
        layout.addLayout(barra_control)
        
        # Área de contenido
        self.contenido_widget = QWidget()
        self.contenido_layout = QVBoxLayout()
        self.contenido_widget.setLayout(self.contenido_layout)
        
        layout.addWidget(self.contenido_widget)
        
        self.setLayout(layout)
    
    def toggle_modo(self):
        """Cambia entre modo campos y modo preview"""
        if self.modo == 'campos':
            self.modo = 'preview'
            self.btn_toggle.setText("📝 Mostrar Campos")
            self.lbl_modo.setText("Modo: Vista Previa")
            self.nav_widget.setVisible(True)
            self.mostrar_datos_preview()
        else:
            self.modo = 'campos'
            self.btn_toggle.setText("👁️ Vista Previa de Resultados")
            self.lbl_modo.setText("Modo: Mostrando Campos")
            self.nav_widget.setVisible(False)
            self.mostrar_placeholders()
    
    def mostrar_placeholders(self):
        """Muestra los placeholders en sus posiciones"""
        self.limpiar_contenido()
        
        for campo in self.campos_config:
            if campo.get('coordenadas_pdf'):
                # Crear label con placeholder
                label = QLabel(f"{{{campo['placeholder']}}}")
                label.setStyleSheet(self.obtener_estilo_campo(campo))
                
                # Posicionar según coordenadas
                x = int(campo['coordenadas_pdf']['x_mm'])
                y = int(campo['coordenadas_pdf']['y_mm'])
                
                label.move(x, y)
                self.contenido_layout.addWidget(label)
    
    def mostrar_datos_preview(self):
        """Muestra datos reales del registro actual"""
        self.limpiar_contenido()
        
        for campo in self.campos_config:
            if campo.get('coordenadas_pdf') and campo.get('columna_asignada'):
                # Obtener valor del registro actual
                valor = self.datos_actuales.get(campo['columna_asignada'], '')
                
                # Crear label con valor real
                label = QLabel(str(valor))
                label.setStyleSheet(self.obtener_estilo_campo(campo))
                
                # Posicionar
                x = int(campo['coordenadas_pdf']['x_mm'])
                y = int(campo['coordenadas_pdf']['y_mm'])
                
                label.move(x, y)
                self.contenido_layout.addWidget(label)