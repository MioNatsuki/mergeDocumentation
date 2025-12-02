# ui/modules/plantillas/editor_mejorado/panel_campos.py
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QPushButton, 
                             QGroupBox, QListWidget, QListWidgetItem, QScrollArea,
                             QFrame)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

class PanelCampos(QWidget):
    """Panel izquierdo con tipos de campos disponibles"""
    
    campo_solicitado = pyqtSignal(str)  # Tipo de campo solicitado
    
    def __init__(self):
        super().__init__()
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(10)
        
        # Título
        lbl_titulo = QLabel("📦 Campos Disponibles")
        lbl_titulo.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        layout.addWidget(lbl_titulo)
        
        # Instrucción
        lbl_instruccion = QLabel("Arrastra o haz clic, luego haz clic en el PDF")
        lbl_instruccion.setStyleSheet("color: #666; font-size: 11px;")
        layout.addWidget(lbl_instruccion)
        
        # Scroll area para los botones
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        
        container = QWidget()
        container_layout = QVBoxLayout()
        container_layout.setSpacing(8)
        
        # Botones por tipo de campo
        tipos_campos = [
            ("📝 Texto", "texto", "Campos de texto (nombre, dirección, etc.)"),
            ("📊 Tabla", "tabla", "Tablas dinámicas (historial de pagos)"),
            ("🖼️ Imagen", "imagen", "Imágenes, logos, firmas"),
            ("📅 Fecha", "fecha", "Fechas automáticas o del padrón"),
            ("💰 Moneda", "moneda", "Valores monetarios con formato"),
            ("📊 Código Barras", "codigo_barras", "Códigos de barras únicos"),
            ("🔢 Número", "numero", "Números con formato"),
            ("📍 Dirección", "direccion", "Direcciones completas"),
            ("📞 Teléfono", "telefono", "Números de contacto"),
            ("📧 Email", "email", "Correos electrónicos")
        ]
        
        for icono, tipo, descripcion in tipos_campos:
            btn = self.crear_boton_campo(icono, tipo, descripcion)
            container_layout.addWidget(btn)
        
        container_layout.addStretch()
        container.setLayout(container_layout)
        scroll.setWidget(container)
        layout.addWidget(scroll)
        
        self.setLayout(layout)
    
    def crear_boton_campo(self, icono, tipo, descripcion):
        """Crea botón para un tipo de campo"""
        btn = QPushButton(f"{icono} {tipo.title()}")
        btn.setToolTip(descripcion)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.clicked.connect(lambda checked, t=tipo: self.campo_solicitado.emit(t))
        
        btn.setStyleSheet("""
            QPushButton {
                text-align: left;
                padding: 10px;
                border: 1px solid #ddd;
                border-radius: 5px;
                background-color: white;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #e3f2fd;
                border-color: #2196F3;
            }
            QPushButton:pressed {
                background-color: #bbdefb;
            }
        """)
        
        return btn