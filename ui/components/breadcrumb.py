from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLabel, QPushButton
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

class Breadcrumb(QWidget):
    """Componente de migas de pan para navegación"""
    navegar_a = pyqtSignal(str)  # Emite el destino de navegación
    
    def __init__(self):
        super().__init__()
        self.setup_ui()
    
    def setup_ui(self):
        layout = QHBoxLayout()
        layout.setSpacing(5)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.layout_breadcrumb = QHBoxLayout()
        self.layout_breadcrumb.setSpacing(5)
        
        layout.addLayout(self.layout_breadcrumb)
        layout.addStretch()
        
        self.setLayout(layout)
        self.setStyleSheet("background-color: #f8f9fa; padding: 8px; border-radius: 4px;")
    
    def actualizar(self, items):
        """Actualiza las migas de pan con nuevos items"""
        # Limpiar layout actual
        for i in reversed(range(self.layout_breadcrumb.count())):
            self.layout_breadcrumb.itemAt(i).widget().setParent(None)
        
        # Agregar nuevos items
        for i, (texto, destino) in enumerate(items):
            if i > 0:
                separator = QLabel(">")
                separator.setStyleSheet("color: #6c757d;")
                self.layout_breadcrumb.addWidget(separator)
            
            if i == len(items) - 1:
                # Último item (activo)
                label = QLabel(texto)
                label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
                label.setStyleSheet("color: #495057;")
                self.layout_breadcrumb.addWidget(label)
            else:
                # Item clickeable
                btn = QPushButton(texto)
                btn.setFlat(True)
                btn.setStyleSheet("""
                    QPushButton {
                        color: #007bff;
                        border: none;
                        text-decoration: underline;
                        padding: 2px 5px;
                    }
                    QPushButton:hover {
                        color: #0056b3;
                        background-color: transparent;
                    }
                """)
                btn.clicked.connect(lambda checked, d=destino: self.navegar_a.emit(d))
                self.layout_breadcrumb.addWidget(btn)