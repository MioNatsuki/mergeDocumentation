# ui/modules/plantillas/editor_mejorado/campo_widget.py
from PyQt6.QtWidgets import (QFrame, QLabel, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QMenu, QInputDialog, QFontDialog,
                             QColorDialog, QApplication)
from PyQt6.QtCore import Qt, pyqtSignal, QPoint, QTimer, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import (QFont, QColor, QPainter, QPen, QBrush, QAction, 
                         QCursor, QMouseEvent, QEnterEvent)
import math

class CampoSimpleWidget(QFrame):
    """Widget de campo con drag-drop suave (física realista)"""
    
    campo_seleccionado = pyqtSignal(object)
    campo_modificado = pyqtSignal(dict)
    solicita_eliminar = pyqtSignal(object)
    
    def __init__(self, config=None, parent=None):
        super().__init__(parent)
        self.config = config or self._config_default()
        self.setup_ui()
        self.setup_fisica()
        self.actualizar_estilo()
        
    def _config_default(self):
        """Configuración por defecto"""
        return {
            'nombre': 'Nuevo Campo',
            'tipo': 'texto',  # 'texto' o 'campo'
            'x': 50.0, 'y': 50.0, 'ancho': 80.0, 'alto': 15.0,
            'alineacion': 'left',  # 'left', 'center', 'right', 'justify'
            'fuente': 'Arial', 'tamano_fuente': 12,
            'color': '#000000', 'negrita': False, 'cursiva': False,
            'texto_fijo': '', 'columna_padron': ''
        }
    
    def setup_ui(self):
        """Configura interfaz minimalista"""
        self.setFrameStyle(QFrame.Shape.NoFrame)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.label = QLabel()
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.actualizar_texto()
        
        layout.addWidget(self.label)
        self.setLayout(layout)
        
        # Tamaño inicial (se ajustará después en preview_pdf)
        self.setFixedSize(100, 20)
    
    def setup_fisica(self):
        """Configura sistema de drag-drop con física"""
        self.drag_pos = None
        self.is_dragging = False
        self.is_resizing = False
        self.resize_corner = None
        
        # Para física suave
        self.velocity = QPoint(0, 0)
        self.last_pos = None
        self.drag_start_pos = None
        
        # Timer para animaciones suaves
        self.physics_timer = QTimer()
        self.physics_timer.timeout.connect(self.apply_physics)
        self.physics_timer.start(16)  # ~60 FPS
        
        # Habilitar eventos de mouse
        self.setMouseTracking(True)
    
    def apply_physics(self):
        """Aplica física de inercia después del drag"""
        if not self.is_dragging and (self.velocity.x() != 0 or self.velocity.y() != 0):
            # Fricción
            self.velocity.setX(self.velocity.x() * 0.85)
            self.velocity.setY(self.velocity.y() * 0.85)
            
            # Mover si hay velocidad significativa
            if abs(self.velocity.x()) > 0.5 or abs(self.velocity.y()) > 0.5:
                new_pos = self.pos() + self.velocity
                self.move_within_bounds(new_pos)
            else:
                self.velocity = QPoint(0, 0)
    
    def move_within_bounds(self, new_pos):
        """Mueve el widget manteniéndose dentro del padre"""
        parent = self.parent()
        if parent:
            max_x = parent.width() - self.width()
            max_y = parent.height() - self.height()
            
            new_pos.setX(max(0, min(new_pos.x(), max_x)))
            new_pos.setY(max(0, min(new_pos.y(), max_y)))
        
        self.move(new_pos)
        
        # Actualizar configuración (convertir px a mm)
        if parent and hasattr(parent, 'escala'):
            self.config['x'] = new_pos.x() / parent.escala
            self.config['y'] = new_pos.y() / parent.escala
            
            # Emitir cambios
            self.campo_modificado.emit({
                'x': self.config['x'],
                'y': self.config['y']
            })
    
    def mousePressEvent(self, event: QMouseEvent):
        """Inicia drag o resize"""
        if event.button() == Qt.MouseButton.LeftButton:
            pos = event.pos()
            rect = self.rect()
            
            # Verificar si es resize (esquinas de 8px)
            corners = {
                'top-left': QPoint(0, 0),
                'top-right': QPoint(rect.width(), 0),
                'bottom-left': QPoint(0, rect.height()),
                'bottom-right': QPoint(rect.width(), rect.height())
            }
            
            for corner_name, corner_pos in corners.items():
                if (pos - corner_pos).manhattanLength() < 8:
                    self.is_resizing = True
                    self.resize_corner = corner_name
                    self.resize_start_pos = event.globalPosition().toPoint()
                    self.resize_start_size = self.size()
                    self.setCursor(self.get_resize_cursor(corner_name))
                    return
            
            # Si no es resize, es drag
            self.is_dragging = True
            self.drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            self.drag_start_pos = self.pos()
            self.last_pos = event.globalPosition().toPoint()
            self.velocity = QPoint(0, 0)
            
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
            self.campo_seleccionado.emit(self)
    
    def get_resize_cursor(self, corner):
        """Devuelve cursor apropiado para resize"""
        if corner in ['top-left', 'bottom-right']:
            return Qt.CursorShape.SizeFDiagCursor
        elif corner in ['top-right', 'bottom-left']:
            return Qt.CursorShape.SizeBDiagCursor
        elif 'top' in corner or 'bottom' in corner:
            return Qt.CursorShape.SizeVerCursor
        else:  # 'left' or 'right'
            return Qt.CursorShape.SizeHorCursor
    
    def mouseMoveEvent(self, event: QMouseEvent):
        """Mueve o redimensiona"""
        if self.is_resizing and self.resize_corner:
            self.handle_resize(event)
        elif self.is_dragging and event.buttons() & Qt.MouseButton.LeftButton:
            self.handle_drag(event)
        else:
            # Cambiar cursor según posición (hover)
            pos = event.pos()
            rect = self.rect()
            
            # Verificar si está cerca de una esquina
            near_corner = False
            corners = [QPoint(0, 0), QPoint(rect.width(), 0),
                      QPoint(0, rect.height()), QPoint(rect.width(), rect.height())]
            
            for corner in corners:
                if (pos - corner).manhattanLength() < 8:
                    near_corner = True
                    break
            
            if near_corner:
                self.setCursor(Qt.CursorShape.SizeFDiagCursor)
            else:
                self.setCursor(Qt.CursorShape.OpenHandCursor)
    
    def handle_resize(self, event):
        """Maneja redimensionamiento"""
        delta = event.globalPosition().toPoint() - self.resize_start_pos
        
        new_width = self.resize_start_size.width()
        new_height = self.resize_start_size.height()
        
        if 'right' in self.resize_corner:
            new_width = max(20, self.resize_start_size.width() + delta.x())
        elif 'left' in self.resize_corner:
            new_width = max(20, self.resize_start_size.width() - delta.x())
            if new_width > 20:
                self.move(self.x() + delta.x(), self.y())
        
        if 'bottom' in self.resize_corner:
            new_height = max(10, self.resize_start_size.height() + delta.y())
        elif 'top' in self.resize_corner:
            new_height = max(10, self.resize_start_size.height() - delta.y())
            if new_height > 10:
                self.move(self.x(), self.y() + delta.y())
        
        self.setFixedSize(new_width, new_height)
        
        # Actualizar configuración
        parent = self.parent()
        if parent and hasattr(parent, 'escala'):
            self.config['ancho'] = new_width / parent.escala
            self.config['alto'] = new_height / parent.escala
            
            self.campo_modificado.emit({
                'ancho': self.config['ancho'],
                'alto': self.config['alto']
            })
    
    def handle_drag(self, event):
        """Maneja drag con inercia"""
        # Calcular nueva posición
        new_pos = event.globalPosition().toPoint() - self.drag_pos
        self.move_within_bounds(new_pos)
        
        # Calcular velocidad para inercia
        if self.last_pos:
            delta = event.globalPosition().toPoint() - self.last_pos
            self.velocity = delta * 0.7  # Suavizado
        self.last_pos = event.globalPosition().toPoint()
    
    def mouseReleaseEvent(self, event: QMouseEvent):
        """Finaliza drag o resize"""
        self.is_dragging = False
        self.is_resizing = False
        self.resize_corner = None
        
        # Si se movió significativamente, emitir snap
        if hasattr(self, 'drag_start_pos') and self.drag_start_pos:
            if (self.pos() - self.drag_start_pos).manhattanLength() > 5:
                self.emit_position_change()
        
        self.setCursor(Qt.CursorShape.OpenHandCursor)
    
    def emit_position_change(self):
        """Emite cambio de posición final"""
        parent = self.parent()
        if parent and hasattr(parent, 'escala'):
            self.campo_modificado.emit({
                'x': self.config['x'],
                'y': self.config['y'],
                'ancho': self.config['ancho'],
                'alto': self.config['alto']
            })
    
    def enterEvent(self, event: QEnterEvent):
        """Mouse entra al widget"""
        self.setCursor(Qt.CursorShape.OpenHandCursor)
        if not self.config.get('seleccionado', False):
            self.setStyleSheet("""
                CampoSimpleWidget {
                    border: 1px dashed #999;
                    background-color: rgba(255, 255, 200, 0.3);
                }
            """)
        super().enterEvent(event)
    
    def leaveEvent(self, event):
        """Mouse sale del widget"""
        if not self.config.get('seleccionado', False):
            self.setStyleSheet("")
        super().leaveEvent(event)
    
    def paintEvent(self, event):
        """Dibuja borde de selección y manejadores"""
        super().paintEvent(event)
        
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Dibujar borde de selección
        if self.config.get('seleccionado', False):
            painter.setPen(QPen(QColor(255, 0, 0), 2, Qt.PenStyle.DashLine))
            painter.drawRect(1, 1, self.width() - 2, self.height() - 2)
            
            # Dibujar manejadores de resize
            painter.setPen(QPen(QColor(0, 120, 215), 2))
            painter.setBrush(QBrush(QColor(255, 255, 255)))
            
            # Esquinas
            size = 6
            corners = [
                QPoint(0, 0),
                QPoint(self.width() - size, 0),
                QPoint(0, self.height() - size),
                QPoint(self.width() - size, self.height() - size)
            ]
            
            for corner in corners:
                painter.drawRect(corner.x(), corner.y(), size, size)
    
    def actualizar_texto(self):
        """Actualiza texto según modo (plantilla o preview)"""
        modo = self.config.get('modo', 'plantilla')
        
        if modo == 'plantilla':
            if self.config['tipo'] == 'texto':
                texto = self.config.get('texto_fijo', self.config['nombre'])
                self.label.setText(texto)
            else:  # campo
                columna = self.config.get('columna_padron', self.config['nombre'])
                self.label.setText(f"{{{columna}}}")
        else:  # preview
            # En preview se mostrarán datos reales (se setea desde fuera)
            pass
    
    def actualizar_estilo(self):
        """Actualiza estilo CSS según configuración"""
        # Determinar color según tipo
        if self.config['tipo'] == 'texto':
            color = '#006600'  # Verde para texto fijo
        else:
            color = '#0000CC'  # Azul para campos de BD
        
        # Mapear alineación CSS
        align_map = {
            'left': 'left',
            'center': 'center',
            'right': 'right',
            'justify': 'justify'
        }
        alineacion_css = align_map.get(self.config['alineacion'], 'left')
        
        # Construir CSS
        estilo = f"""
            QLabel {{
                background-color: transparent;
                color: {color};
                font-family: '{self.config['fuente']}';
                font-size: {self.config['tamano_fuente']}px;
                font-weight: {'bold' if self.config['negrita'] else 'normal'};
                font-style: {'italic' if self.config['cursiva'] else 'normal'};
                text-align: {alineacion_css};
                padding: 0px;
                margin: 0px;
            }}
        """
        self.label.setStyleSheet(estilo)
        
        # Ajustar tamaño de fuente en widget
        font = QFont(self.config['fuente'], self.config['tamano_fuente'])
        font.setBold(self.config['negrita'])
        font.setItalic(self.config['cursiva'])
        self.label.setFont(font)
    
    def set_seleccionado(self, seleccionado: bool):
        """Marca/desmarca como seleccionado"""
        self.config['seleccionado'] = seleccionado
        self.update()  # Forzar repaint
    
    def set_modo(self, modo: str):
        """Cambia entre modo 'plantilla' y 'preview'"""
        self.config['modo'] = modo
        self.actualizar_texto()
    
    def set_datos_preview(self, datos: dict):
        """Establece datos reales para modo preview"""
        if self.config['modo'] == 'preview':
            if self.config['tipo'] == 'texto':
                self.label.setText(self.config.get('texto_fijo', ''))
            else:
                valor = datos.get(self.config.get('columna_padron', ''), '')
                self.label.setText(str(valor))
    
    def contextMenuEvent(self, event):
        """Menú contextual"""
        menu = QMenu(self)
        
        # Editar nombre
        action_editar = QAction("📝 Editar nombre", self)
        action_editar.triggered.connect(self.editar_nombre)
        
        # Cambiar tipo
        action_tipo = QMenu("🔄 Cambiar tipo", self)
        action_texto = QAction("Texto fijo", self)
        action_texto.triggered.connect(lambda: self.cambiar_tipo('texto'))
        action_campo = QAction("Campo de BD", self)
        action_campo.triggered.connect(lambda: self.cambiar_tipo('campo'))
        action_tipo.addAction(action_texto)
        action_tipo.addAction(action_campo)
        
        # Alineación
        action_alineacion = QMenu("📐 Alineación", self)
        alignments = ['left', 'center', 'right', 'justify']
        for align in alignments:
            action = QAction(align.title(), self)
            action.triggered.connect(lambda checked, a=align: self.cambiar_alineacion(a))
            action_alineacion.addAction(action)
        
        # Eliminar
        action_eliminar = QAction("🗑️ Eliminar", self)
        action_eliminar.triggered.connect(lambda: self.solicita_eliminar.emit(self))
        
        menu.addAction(action_editar)
        menu.addMenu(action_tipo)
        menu.addMenu(action_alineacion)
        menu.addSeparator()
        menu.addAction(action_eliminar)
        
        menu.exec(event.globalPos())
    
    def editar_nombre(self):
        """Diálogo para editar nombre"""
        nuevo_nombre, ok = QInputDialog.getText(
            self, "Editar nombre",
            "Nombre del campo:",
            text=self.config['nombre']
        )
        
        if ok and nuevo_nombre.strip():
            self.config['nombre'] = nuevo_nombre.strip()
            self.actualizar_texto()
            self.campo_modificado.emit({'nombre': nuevo_nombre.strip()})
    
    def cambiar_tipo(self, nuevo_tipo):
        """Cambia tipo de campo"""
        self.config['tipo'] = nuevo_tipo
        
        if nuevo_tipo == 'texto':
            # Pedir texto fijo
            texto, ok = QInputDialog.getText(
                self, "Texto fijo",
                "Ingrese el texto:",
                text=self.config.get('texto_fijo', '')
            )
            if ok:
                self.config['texto_fijo'] = texto
                self.config['columna_padron'] = ''
        else:  # campo
            # Pedir columna (en implementación real vendría de BD)
            columna, ok = QInputDialog.getText(
                self, "Columna del padrón",
                "Nombre de la columna:",
                text=self.config.get('columna_padron', '')
            )
            if ok:
                self.config['columna_padron'] = columna
                self.config['texto_fijo'] = ''
        
        self.actualizar_texto()
        self.actualizar_estilo()
        self.campo_modificado.emit(self.config)
    
    def cambiar_alineacion(self, alineacion):
        """Cambia alineación del texto"""
        self.config['alineacion'] = alineacion
        self.actualizar_estilo()
        self.campo_modificado.emit({'alineacion': alineacion})