# ui/modules/plantillas/editor_mejorado/campo_compuesto.py
from PyQt6.QtWidgets import QFrame, QHBoxLayout, QLabel, QLineEdit, QPushButton, QMenu, QInputDialog, QFontDialog, QColorDialog
from PyQt6.QtCore import Qt, pyqtSignal, QPoint, QRect
from PyQt6.QtGui import QFont, QColor, QPainter, QPen, QAction, QCursor, QBrush

class ComponenteCampo:
    """Representa un componente dentro de un campo compuesto"""
    def __init__(self, tipo, contenido=""):
        self.tipo = tipo  # "texto" o "campo"
        self.contenido = contenido
        self.ancho = 50  # Ancho en píxeles

class CampoCompuestoWidget(QFrame):
    """Widget para campos compuestos (texto + campo + texto + campo)"""
    
    campo_modificado = pyqtSignal(dict)
    campo_seleccionado = pyqtSignal(object)
    solicita_eliminar = pyqtSignal(object)
    
    def __init__(self, nombre: str = "Campo Compuesto", parent=None):
        super().__init__(parent)
        self.nombre = nombre
        self.tipo = "compuesto"
        self.componentes = []
        self.config = {
            "nombre": nombre,
            "tipo": "compuesto",
            "x": 50,
            "y": 50,
            "ancho": 300,
            "alto": 30,
            "fuente": "Arial",
            "tamano": 12,
            "color": "#000000",
            "negrita": False,
            "cursiva": False
        }
        
        self.seleccionado = False
        self.drag_pos = None
        self.redimensionando = False
        self.resize_corner = None
        self.manejador_size = 10
        
        self.setup_ui()
        self.actualizar_estilo()
    
    def setup_ui(self):
        """Configura la interfaz del campo compuesto"""
        self.setFrameStyle(QFrame.Shape.NoFrame)
        self.setCursor(Qt.CursorShape.ArrowCursor)
        
        self.layout_principal = QHBoxLayout()
        self.layout_principal.setContentsMargins(5, 5, 5, 5)
        self.layout_principal.setSpacing(5)
        
        # Inicializar con un componente de texto por defecto
        self.agregar_componente("texto", "Texto: ")
        
        self.setLayout(self.layout_principal)
        self.setFixedSize(self.config["ancho"], self.config["alto"])
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
    
    def agregar_componente(self, tipo, contenido=""):
        """Agrega un componente al campo compuesto"""
        componente = ComponenteCampo(tipo, contenido)
        self.componentes.append(componente)
        self.actualizar_vista()
    
    def actualizar_vista(self):
        """Actualiza la vista visual del campo compuesto"""
        # Limpiar layout
        while self.layout_principal.count():
            item = self.layout_principal.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # Reconstruir vista
        for componente in self.componentes:
            if componente.tipo == "texto":
                lbl = QLabel(componente.contenido)
                lbl.setStyleSheet(f"""
                    QLabel {{
                        background-color: transparent;
                        color: {self.config['color']};
                        font-family: '{self.config['fuente']}';
                        font-size: {self.config['tamano']}pt;
                        font-weight: {'bold' if self.config['negrita'] else 'normal'};
                        font-style: {'italic' if self.config['cursiva'] else 'normal'};
                    }}
                """)
                lbl.mouseDoubleClickEvent = lambda e, c=componente: self.editar_componente(c)
                self.layout_principal.addWidget(lbl)
            
            elif componente.tipo == "campo":
                campo_widget = QLabel(f"[{componente.contenido}]")
                campo_widget.setStyleSheet(f"""
                    QLabel {{
                        background-color: rgba(144, 238, 144, 0.3);
                        color: #006600;
                        border: 1px dashed #4CAF50;
                        padding: 2px 5px;
                        font-family: '{self.config['fuente']}';
                        font-size: {self.config['tamano']}pt;
                        font-weight: {'bold' if self.config['negrita'] else 'normal'};
                    }}
                """)
                campo_widget.mouseDoubleClickEvent = lambda e, c=componente: self.editar_componente(c)
                self.layout_principal.addWidget(campo_widget)
        
        # Botón para agregar más componentes
        btn_agregar = QPushButton("+")
        btn_agregar.setFixedSize(20, 20)
        btn_agregar.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 3px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        btn_agregar.clicked.connect(self.mostrar_menu_agregar)
        self.layout_principal.addWidget(btn_agregar)
    
    def mostrar_menu_agregar(self):
        """Muestra menú para agregar componentes"""
        menu = QMenu(self)
        
        action_texto = QAction("📝 Agregar Texto", self)
        action_texto.triggered.connect(lambda: self.agregar_nuevo_componente("texto"))
        
        action_campo = QAction("🔤 Agregar Campo", self)
        action_campo.triggered.connect(lambda: self.agregar_nuevo_componente("campo"))
        
        menu.addAction(action_texto)
        menu.addAction(action_campo)
        menu.exec(QCursor.pos())
    
    def agregar_nuevo_componente(self, tipo):
        """Agrega un nuevo componente del tipo especificado"""
        if tipo == "texto":
            texto, ok = QInputDialog.getText(self, "Texto", "Ingrese el texto:")
            if ok and texto:
                self.agregar_componente("texto", texto)
        
        elif tipo == "campo":
            campo, ok = QInputDialog.getText(self, "Campo", "Nombre del campo dinámico:")
            if ok and campo:
                self.agregar_componente("campo", campo)
    
    def editar_componente(self, componente):
        """Edita un componente existente"""
        if componente.tipo == "texto":
            nuevo_texto, ok = QInputDialog.getText(self, "Editar Texto", 
                                                  "Editar texto:", 
                                                  text=componente.contenido)
            if ok:
                componente.contenido = nuevo_texto
                self.actualizar_vista()
        
        elif componente.tipo == "campo":
            nuevo_campo, ok = QInputDialog.getText(self, "Editar Campo", 
                                                  "Editar campo:", 
                                                  text=componente.contenido)
            if ok:
                componente.contenido = nuevo_campo
                self.actualizar_vista()
    
    # Métodos para arrastre y redimensionamiento (similares a CampoTextoWidget)
    def mousePressEvent(self, event):
        """Maneja clic para selección y arrastre"""
        if event.button() == Qt.MouseButton.LeftButton:
            pos = event.pos()
            rect = self.rect()
            
            # Areas de redimensionamiento
            handles = {
                "top-left": QRect(0, 0, self.manejador_size, self.manejador_size),
                "top-right": QRect(rect.width() - self.manejador_size, 0, self.manejador_size, self.manejador_size),
                "bottom-left": QRect(0, rect.height() - self.manejador_size, self.manejador_size, self.manejador_size),
                "bottom-right": QRect(rect.width() - self.manejador_size, rect.height() - self.manejador_size, self.manejador_size, self.manejador_size),
            }
            
            # Verificar si es redimensionamiento
            for corner_name, handle_rect in handles.items():
                if handle_rect.contains(pos):
                    self.redimensionando = True
                    self.resize_corner = corner_name
                    self.setCursor(self.get_resize_cursor(corner_name))
                    self.resize_start_pos = event.globalPosition().toPoint()
                    self.resize_start_size = self.size()
                    self.resize_start_pos_widget = self.pos()
                    return
            
            # Si no, es arrastre normal
            self.drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            self.setCursor(Qt.CursorShape.SizeAllCursor)
            self.campo_seleccionado.emit(self)
            event.accept()
    
    def get_resize_cursor(self, corner_name):
        """Devuelve el cursor apropiado para redimensionar"""
        if corner_name == "top-left" or corner_name == "bottom-right":
            return Qt.CursorShape.SizeFDiagCursor
        elif corner_name == "top-right" or corner_name == "bottom-left":
            return Qt.CursorShape.SizeBDiagCursor
        return Qt.CursorShape.SizeAllCursor
    
    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.MouseButton.LeftButton:
            if self.redimensionando and self.resize_corner:
                # Redimensionar
                delta = event.globalPosition().toPoint() - self.resize_start_pos
                
                new_width = self.resize_start_size.width()
                new_height = self.resize_start_size.height()
                new_x = self.x()
                new_y = self.y()
                
                if "right" in self.resize_corner:
                    new_width = max(100, self.resize_start_size.width() + delta.x())
                elif "left" in self.resize_corner:
                    new_width = max(100, self.resize_start_size.width() - delta.x())
                    if new_width > 100:
                        new_x = self.resize_start_pos_widget.x() + delta.x()
                
                if "bottom" in self.resize_corner:
                    new_height = max(30, self.resize_start_size.height() + delta.y())
                elif "top" in self.resize_corner:
                    new_height = max(30, self.resize_start_size.height() - delta.y())
                    if new_height > 30:
                        new_y = self.resize_start_pos_widget.y() + delta.y()
                
                self.move(new_x, new_y)
                self.setFixedSize(new_width, new_height)
                
                self.config["x"] = new_x
                self.config["y"] = new_y
                self.config["ancho"] = new_width
                self.config["alto"] = new_height
                
                self.campo_modificado.emit({
                    "x": new_x,
                    "y": new_y,
                    "ancho": new_width,
                    "alto": new_height
                })
                
            elif self.drag_pos:
                # Arrastrar
                new_pos = event.globalPosition().toPoint() - self.drag_pos
                self.move(new_pos)
                
                self.config["x"] = new_pos.x()
                self.config["y"] = new_pos.y()
                self.campo_modificado.emit({"x": new_pos.x(), "y": new_pos.y()})
    
    def mouseReleaseEvent(self, event):
        self.redimensionando = False
        self.drag_pos = None
        self.resize_corner = None
        self.setCursor(Qt.CursorShape.ArrowCursor)
    
    def enterEvent(self, event):
        """Cambia cursor al pasar sobre el campo"""
        if not self.seleccionado:
            self.setCursor(Qt.CursorShape.PointingHandCursor)
        super().enterEvent(event)
    
    def leaveEvent(self, event):
        """Restaura cursor al salir"""
        if not self.seleccionado:
            self.setCursor(Qt.CursorShape.ArrowCursor)
        super().leaveEvent(event)
    
    def paintEvent(self, event):
        """Dibuja solo cuando está seleccionado"""
        super().paintEvent(event)
        
        if self.seleccionado:
            painter = QPainter(self)
            
            # Borde punteado rojo
            painter.setPen(QPen(QColor(255, 0, 0), 1, Qt.PenStyle.DashLine))
            painter.drawRect(0, 0, self.width()-1, self.height()-1)
            
            # Dibujar manejadores de redimensionamiento
            painter.setPen(QPen(QColor(0, 120, 215), 2))
            painter.setBrush(QBrush(QColor(255, 255, 255)))
            
            # Esquinas
            corners = [
                QRect(0, 0, self.manejador_size, self.manejador_size),
                QRect(self.width() - self.manejador_size, 0, self.manejador_size, self.manejador_size),
                QRect(0, self.height() - self.manejador_size, self.manejador_size, self.manejador_size),
                QRect(self.width() - self.manejador_size, self.height() - self.manejador_size, self.manejador_size, self.manejador_size)
            ]
            
            for corner in corners:
                painter.drawRect(corner)
    
    def contextMenuEvent(self, event):
        """Menú contextual"""
        menu = QMenu(self)
        
        action_configurar = QAction("⚙️ Configurar campo compuesto", self)
        action_configurar.triggered.connect(self.configurar_campo)
        
        action_eliminar = QAction("🗑️ Eliminar campo", self)
        action_eliminar.triggered.connect(self.eliminar_campo)
        
        menu.addAction(action_configurar)
        menu.addSeparator()
        menu.addAction(action_eliminar)
        
        menu.exec(event.globalPos())
    
    def configurar_campo(self):
        """Configura el campo compuesto"""
        from PyQt6.QtWidgets import QDialog, QVBoxLayout, QFormLayout, QFontDialog, QColorDialog
        
        dialog = QDialog(self)
        dialog.setWindowTitle("Configurar Campo Compuesto")
        dialog.setFixedSize(400, 300)
        
        layout = QVBoxLayout()
        
        form_layout = QFormLayout()
        
        # Nombre
        from PyQt6.QtWidgets import QLineEdit
        self.txt_nombre_config = QLineEdit(self.nombre)
        form_layout.addRow("Nombre:", self.txt_nombre_config)
        
        # Botones para fuente y color
        btn_fuente = QPushButton("🔤 Cambiar Fuente")
        btn_fuente.clicked.connect(self.cambiar_fuente)
        
        btn_color = QPushButton("🎨 Cambiar Color")
        btn_color.clicked.connect(self.cambiar_color)
        
        form_layout.addRow("Fuente:", btn_fuente)
        form_layout.addRow("Color:", btn_color)
        
        layout.addLayout(form_layout)
        
        # Botones
        from PyQt6.QtWidgets import QDialogButtonBox
        btn_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | 
                                   QDialogButtonBox.StandardButton.Cancel)
        btn_box.accepted.connect(lambda: self.aplicar_configuracion(dialog))
        btn_box.rejected.connect(dialog.reject)
        
        layout.addWidget(btn_box)
        dialog.setLayout(layout)
        dialog.exec()
    
    def cambiar_fuente(self):
        """Cambia la fuente"""
        font = QFont(self.config["fuente"], self.config["tamano"])
        font.setBold(self.config["negrita"])
        font.setItalic(self.config["cursiva"])
        
        font, ok = QFontDialog.getFont(font, self, "Seleccionar fuente")
        if ok:
            self.config["fuente"] = font.family()
            self.config["tamano"] = font.pointSize()
            self.config["negrita"] = font.bold()
            self.config["cursiva"] = font.italic()
            self.actualizar_vista()
            self.campo_modificado.emit({
                "fuente": font.family(),
                "tamano": font.pointSize(),
                "negrita": font.bold(),
                "cursiva": font.italic()
            })
    
    def cambiar_color(self):
        """Cambia el color"""
        color = QColorDialog.getColor(QColor(self.config["color"]), self, "Seleccionar color")
        if color.isValid():
            self.config["color"] = color.name()
            self.actualizar_vista()
            self.campo_modificado.emit({"color": color.name()})
    
    def aplicar_configuracion(self, dialog):
        """Aplica la configuración"""
        nuevo_nombre = self.txt_nombre_config.text().strip()
        if nuevo_nombre:
            self.nombre = nuevo_nombre
            self.config["nombre"] = nuevo_nombre
            self.campo_modificado.emit({"nombre": nuevo_nombre})
        
        dialog.accept()
    
    def eliminar_campo(self):
        """Emitir señal para eliminar este campo"""
        self.solicita_eliminar.emit(self)
    
    def actualizar_estilo(self):
        """Actualiza el estilo visual"""
        pass  # El estilo se maneja en actualizar_vista()
    
    def set_seleccionado(self, seleccionado: bool):
        """Marca/desmarca como seleccionado"""
        self.seleccionado = seleccionado
        if seleccionado:
            self.setCursor(Qt.CursorShape.SizeAllCursor)
        else:
            self.setCursor(Qt.CursorShape.ArrowCursor)
        self.update()