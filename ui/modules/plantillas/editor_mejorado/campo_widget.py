# ui/modules/plantillas/editor_mejorado/campo_widget.py
from PyQt6.QtWidgets import QFrame, QLabel, QVBoxLayout, QSizeGrip, QInputDialog, QMenu, QFontDialog, QColorDialog
from PyQt6.QtCore import Qt, pyqtSignal, QPoint, QRect
from PyQt6.QtGui import QFont, QColor, QPixmap, QImage, QPainter, QPen, QBrush, QAction, QCursor

class CampoTextoWidget(QFrame):
    """Widget de campo de texto mejorado - modo Word"""
    
    campo_modificado = pyqtSignal(dict)
    campo_seleccionado = pyqtSignal(object)
    solicita_eliminar = pyqtSignal(object)
    
    def __init__(self, nombre: str = "Nuevo Campo", tipo: str = "texto", parent=None):
        super().__init__(parent)
        self.nombre = nombre
        self.tipo = tipo
        self.columna_padron = ""
        
        self.config = {
            "nombre": nombre,
            "tipo": tipo,
            "columna_padron": "",
            "fuente": "Arial",
            "tamano": 12,
            "color": "#000000",
            "negrita": False,
            "cursiva": False,
            "alineacion": "left",
            "x": 50,
            "y": 50,
            "ancho": 100,
            "alto": 30,
            "margen": 2,
            "borde": False
        }
        
        self.seleccionado = False
        self.drag_pos = None
        self.redimensionando = False
        self.resize_corner = None
        self.manejador_size = 10
        
        self.setup_ui()
        self.actualizar_estilo()
    
    def setup_ui(self):
        """Configura SIN fondo, SIN borde - TRANSPARENTE"""
        self.setFrameStyle(QFrame.Shape.NoFrame)
        self.setCursor(Qt.CursorShape.ArrowCursor)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.label = QLabel()
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.actualizar_texto()
        layout.addWidget(self.label)
        
        self.setLayout(layout)
        self.setFixedSize(self.config["ancho"], self.config["alto"])
        
        # Establecer fondo transparente
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
    
    def actualizar_texto(self):
        """Muestra solo la columna asignada, NO placeholder"""
        if self.columna_padron:
            self.label.setText(f"[{self.columna_padron}]")
        else:
            self.label.setText(f"[{self.nombre}]")
    
    def set_columna_padron(self, columna: str):
        """Asigna una columna específica a ESTE campo"""
        self.columna_padron = columna
        self.config["columna_padron"] = columna
        self.actualizar_texto()
        self.actualizar_estilo()
    
    def mousePressEvent(self, event):
        """Maneja clic para selección y arrastre"""
        if event.button() == Qt.MouseButton.LeftButton:
            pos = event.pos()
            rect = self.rect()
            
            # Areas de redimensionamiento (más grandes y visibles)
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
                    new_width = max(30, self.resize_start_size.width() + delta.x())
                elif "left" in self.resize_corner:
                    new_width = max(30, self.resize_start_size.width() - delta.x())
                    if new_width > 30:
                        new_x = self.resize_start_pos_widget.x() + delta.x()
                
                if "bottom" in self.resize_corner:
                    new_height = max(20, self.resize_start_size.height() + delta.y())
                elif "top" in self.resize_corner:
                    new_height = max(20, self.resize_start_size.height() - delta.y())
                    if new_height > 20:
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
            
            # Dibujar manejadores de redimensionamiento (solo cuando está seleccionado)
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
    
    def mouseDoubleClickEvent(self, event):
        """Permite edición rápida del nombre"""
        nuevo_nombre, ok = QInputDialog.getText(self, "Editar nombre", 
                                               "Nuevo nombre del campo:", 
                                               text=self.nombre)
        if ok and nuevo_nombre.strip():
            self.nombre = nuevo_nombre.strip()
            self.config["nombre"] = self.nombre
            self.actualizar_texto()
            self.campo_modificado.emit({"nombre": self.nombre})
    
    def contextMenuEvent(self, event):
        """Menú contextual mejorado"""
        menu = QMenu(self)
        
        action_editar_nombre = QAction("📝 Editar nombre", self)
        action_editar_nombre.triggered.connect(self.mouseDoubleClickEvent)
        
        action_fuente = QAction("🔤 Cambiar fuente", self)
        action_fuente.triggered.connect(self.cambiar_fuente)
        
        action_color = QAction("🎨 Cambiar color", self)
        action_color.triggered.connect(self.cambiar_color)
        
        menu.addAction(action_editar_nombre)
        menu.addAction(action_fuente)
        menu.addAction(action_color)
        menu.addSeparator()
        
        action_eliminar = QAction("🗑️ Eliminar campo", self)
        action_eliminar.triggered.connect(self.eliminar_campo)
        menu.addAction(action_eliminar)
        
        menu.exec(event.globalPos())
    
    def eliminar_campo(self):
        """Emitir señal para eliminar este campo"""
        self.solicita_eliminar.emit(self)
    
    def cambiar_fuente(self):
        """Diálogo para cambiar fuente"""
        font = QFont(self.config["fuente"], self.config["tamano"])
        font.setBold(self.config["negrita"])
        font.setItalic(self.config["cursiva"])
        
        font, ok = QFontDialog.getFont(font, self, "Seleccionar fuente")
        if ok:
            self.config["fuente"] = font.family()
            self.config["tamano"] = font.pointSize()
            self.config["negrita"] = font.bold()
            self.config["cursiva"] = font.italic()
            
            self.label.setFont(font)
            self.actualizar_estilo()
            self.campo_modificado.emit({
                "fuente": font.family(),
                "tamano": font.pointSize(),
                "negrita": font.bold(),
                "cursiva": font.italic()
            })
    
    def cambiar_color(self):
        """Diálogo para cambiar color"""
        color = QColorDialog.getColor(QColor(self.config["color"]), self, "Seleccionar color")
        if color.isValid():
            self.config["color"] = color.name()
            self.actualizar_estilo()
            self.campo_modificado.emit({"color": color.name()})
    
    def actualizar_estilo(self):
        """Estilo con fondo TRANSPARENTE"""
        if self.seleccionado:
            borde_label = "1px dashed #ff0000"
        else:
            borde_label = "none"
        
        # Color del texto según si tiene columna asignada
        if self.columna_padron:
            color_texto = "#0066cc"  # Azul cuando tiene columna
        else:
            color_texto = "#666666"  # Gris cuando no tiene
        
        estilo = f"""
            QLabel {{
                background-color: transparent;
                color: {color_texto};
                font-family: '{self.config['fuente']}';
                font-size: {self.config['tamano']}pt;
                font-weight: {'bold' if self.config['negrita'] else 'normal'};
                font-style: {'italic' if self.config['cursiva'] else 'normal'};
                border: {borde_label};
                padding: 2px;
            }}
        """
        self.label.setStyleSheet(estilo)
    
    def set_seleccionado(self, seleccionado: bool):
        """Marca/desmarca como seleccionado"""
        self.seleccionado = seleccionado
        self.actualizar_estilo()
        if seleccionado:
            self.setCursor(Qt.CursorShape.SizeAllCursor)
        else:
            self.setCursor(Qt.CursorShape.ArrowCursor)
        self.update()