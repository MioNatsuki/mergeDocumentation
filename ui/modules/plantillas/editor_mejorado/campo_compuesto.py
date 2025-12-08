# ui/modules/plantillas/editor_mejorado/campo_compuesto.py
from PyQt6.QtWidgets import (QFrame, QLabel, QHBoxLayout, QVBoxLayout,
                             QPushButton, QMenu, QInputDialog, QDialog,
                             QListWidget, QListWidgetItem, QDialogButtonBox,
                             QFormLayout, QComboBox, QLineEdit)
from PyQt6.QtCore import Qt, pyqtSignal, QPoint
from PyQt6.QtGui import QPainter, QPen, QColor, QBrush, QMouseEvent
import json

class ComponenteCompuesto:
    """Componente individual dentro de un campo compuesto"""
    def __init__(self, tipo='texto', valor=''):
        self.tipo = tipo  # 'texto' o 'campo'
        self.valor = valor  # texto fijo o nombre columna
    
    def to_dict(self):
        return {'tipo': self.tipo, 'valor': self.valor}
    
    @classmethod
    def from_dict(cls, data):
        return cls(data.get('tipo', 'texto'), data.get('valor', ''))

class CampoCompuestoWidget(QFrame):
    """Campo que combina texto fijo y campos dinámicos en un solo widget"""
    
    campo_seleccionado = pyqtSignal(object)
    campo_modificado = pyqtSignal(dict)
    solicita_eliminar = pyqtSignal(object)
    
    def __init__(self, config=None, parent=None):
        super().__init__(parent)
        self.config = config or self._config_default()
        self.componentes = self._cargar_componentes()
        self.setup_ui()
        self.setup_fisica()  # Hereda física de CampoSimpleWidget
        self.actualizar_estilo()
    
    def _config_default(self):
        return {
            'nombre': 'Campo Compuesto',
            'tipo': 'compuesto',
            'x': 50.0, 'y': 50.0, 'ancho': 200.0, 'alto': 20.0,
            'alineacion': 'left',
            'fuente': 'Arial', 'tamano_fuente': 12,
            'color': '#000000', 'negrita': False, 'cursiva': False,
            'componentes': []  # Lista de componentes
        }
    
    def _cargar_componentes(self):
        """Carga componentes desde config"""
        componentes = []
        for comp_data in self.config.get('componentes', []):
            componentes.append(ComponenteCompuesto.from_dict(comp_data))
        return componentes
    
    def setup_ui(self):
        """Configura interfaz dinámica"""
        self.setFrameStyle(QFrame.Shape.NoFrame)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        self.layout_principal = QHBoxLayout()
        self.layout_principal.setContentsMargins(5, 2, 5, 2)
        self.layout_principal.setSpacing(3)
        
        self.actualizar_vista()
        self.setLayout(self.layout_principal)
        
        # Tamaño inicial
        self.setFixedSize(200, 25)
    
    def actualizar_vista(self):
        """Reconstruye la vista con los componentes actuales"""
        # Limpiar layout
        while self.layout_principal.count():
            item = self.layout_principal.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # Construir vista
        for componente in self.componentes:
            if componente.tipo == 'texto':
                lbl = QLabel(componente.valor)
                lbl.setStyleSheet(f"""
                    QLabel {{
                        background-color: transparent;
                        color: #006600;
                        font-family: '{self.config['fuente']}';
                        font-size: {self.config['tamano_fuente']}px;
                        font-weight: {'bold' if self.config['negrita'] else 'normal'};
                        font-style: {'italic' if self.config['cursiva'] else 'normal'};
                    }}
                """)
                self.layout_principal.addWidget(lbl)
                
            else:  # campo
                lbl = QLabel(f"{{{componente.valor}}}")
                lbl.setStyleSheet(f"""
                    QLabel {{
                        background-color: rgba(144, 238, 144, 0.3);
                        color: #0000CC;
                        border: 1px dashed #4CAF50;
                        padding: 1px 3px;
                        font-family: '{self.config['fuente']}';
                        font-size: {self.config['tamano_fuente']}px;
                        font-weight: {'bold' if self.config['negrita'] else 'normal'};
                    }}
                """)
                self.layout_principal.addWidget(lbl)
        
        # Botón para agregar más
        btn_agregar = QPushButton("+")
        btn_agregar.setFixedSize(20, 20)
        btn_agregar.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 3px;
                font-weight: bold;
                font-size: 10px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        btn_agregar.clicked.connect(self.mostrar_dialogo_agregar)
        self.layout_principal.addWidget(btn_agregar)
    
    def mostrar_dialogo_agregar(self):
        """Muestra diálogo para agregar componente"""
        dialog = QDialog(self)
        dialog.setWindowTitle("Agregar componente")
        dialog.setFixedSize(300, 200)
        
        layout = QVBoxLayout()
        
        # Tipo
        form_layout = QFormLayout()
        combo_tipo = QComboBox()
        combo_tipo.addItems(["Texto fijo", "Campo de BD"])
        
        txt_valor = QLineEdit()
        txt_valor.setPlaceholderText("Texto o nombre de columna...")
        
        form_layout.addRow("Tipo:", combo_tipo)
        form_layout.addRow("Valor:", txt_valor)
        
        layout.addLayout(form_layout)
        
        # Botones
        btn_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | 
            QDialogButtonBox.StandardButton.Cancel
        )
        btn_box.accepted.connect(dialog.accept)
        btn_box.rejected.connect(dialog.reject)
        
        layout.addWidget(btn_box)
        dialog.setLayout(layout)
        
        if dialog.exec():
            tipo = 'texto' if combo_tipo.currentText() == 'Texto fijo' else 'campo'
            valor = txt_valor.text().strip()
            
            if valor:
                self.agregar_componente(tipo, valor)
    
    def agregar_componente(self, tipo, valor):
        """Agrega un nuevo componente"""
        self.componentes.append(ComponenteCompuesto(tipo, valor))
        self.actualizar_vista()
        self.guardar_componentes()
    
    def guardar_componentes(self):
        """Guarda componentes en config y emite señal"""
        self.config['componentes'] = [comp.to_dict() for comp in self.componentes]
        self.campo_modificado.emit({'componentes': self.config['componentes']})
    
    def get_texto_preview(self, datos_registro):
        """Genera texto para modo preview"""
        texto = ""
        for componente in self.componentes:
            if componente.tipo == 'texto':
                texto += componente.valor
            else:
                texto += str(datos_registro.get(componente.valor, ''))
        return texto
    
    # Heredamos los métodos de física de CampoSimpleWidget
    # (Para evitar duplicación, en la implementación real
    # CampoCompuestoWidget heredaría de una clase base)
    
    def setup_fisica(self):
        """Configuración similar a CampoSimpleWidget"""
        self.drag_pos = None
        self.is_dragging = False
        self.is_resizing = False
        self.setMouseTracking(True)
    
    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self.is_dragging = True
            self.drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
            self.campo_seleccionado.emit(self)
    
    def mouseMoveEvent(self, event: QMouseEvent):
        if self.is_dragging and event.buttons() & Qt.MouseButton.LeftButton:
            new_pos = event.globalPosition().toPoint() - self.drag_pos
            self.move_within_bounds(new_pos)
    
    def move_within_bounds(self, new_pos):
        parent = self.parent()
        if parent:
            max_x = parent.width() - self.width()
            max_y = parent.height() - self.height()
            
            new_pos.setX(max(0, min(new_pos.x(), max_x)))
            new_pos.setY(max(0, min(new_pos.y(), max_y)))
        
        self.move(new_pos)
        
        if parent and hasattr(parent, 'escala'):
            self.config['x'] = new_pos.x() / parent.escala
            self.config['y'] = new_pos.y() / parent.escala
            self.campo_modificado.emit({'x': self.config['x'], 'y': self.config['y']})
    
    def mouseReleaseEvent(self, event: QMouseEvent):
        self.is_dragging = False
        self.setCursor(Qt.CursorShape.ArrowCursor)
    
    def paintEvent(self, event):
        """Dibuja borde de selección"""
        super().paintEvent(event)
        
        if self.config.get('seleccionado', False):
            painter = QPainter(self)
            painter.setPen(QPen(QColor(255, 0, 0), 2, Qt.PenStyle.DashLine))
            painter.drawRect(1, 1, self.width() - 2, self.height() - 2)
    
    def set_seleccionado(self, seleccionado: bool):
        self.config['seleccionado'] = seleccionado
        self.update()
    
    def actualizar_estilo(self):
        """Estilo base del widget"""
        if self.config.get('seleccionado', False):
            self.setStyleSheet("""
                CampoCompuestoWidget {
                    background-color: rgba(255, 255, 200, 0.1);
                    border: 1px dashed #ff0000;
                }
            """)
        else:
            self.setStyleSheet("")