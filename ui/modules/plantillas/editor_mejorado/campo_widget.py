# ui/modules/plantillas/editor_mejorado/campo_widget.py - VERSIÓN CORREGIDA
from PyQt6.QtWidgets import (QFrame, QLabel, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QMenu, QInputDialog, QFontDialog,
                             QColorDialog, QApplication)
from PyQt6.QtCore import Qt, pyqtSignal, QPoint, QTimer, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import (QFont, QColor, QPainter, QPen, QBrush, QAction, 
                         QCursor, QMouseEvent, QEnterEvent)
import math

class CampoSimpleWidget(QFrame):
    """Widget de campo que muestra {columna} en modo edición, datos reales en preview"""
    
    campo_seleccionado = pyqtSignal(object)
    campo_modificado = pyqtSignal(dict)
    solicita_eliminar = pyqtSignal(object)
    
    def __init__(self, config=None, parent=None):
        super().__init__(parent)
        self.config = config or self._config_default()
        self.modo_actual = 'plantilla'  # 'plantilla' o 'preview'
        self.datos_actuales = {}
        self.setup_ui()
        self.setup_fisica()
        self.actualizar_vista_completa()  # ← NUEVO: Actualiza según modo
        
    def _config_default(self):
        return {
            'nombre': 'Nuevo Campo',
            'tipo': 'texto',  # 'texto' o 'campo'
            'x': 50.0, 'y': 50.0, 'ancho': 80.0, 'alto': 15.0,
            'alineacion': 'left',
            'fuente': 'Arial', 'tamano_fuente': 12,
            'color': '#000000', 'negrita': False, 'cursiva': False,
            'texto_fijo': '', 'columna_padron': ''
        }
    
    def setup_ui(self):
        self.setFrameStyle(QFrame.Shape.NoFrame)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.label = QLabel()
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        layout.addWidget(self.label)
        self.setLayout(layout)
        
        self.setFixedSize(100, 20)
    
    def set_modo(self, modo: str):
        """Cambia entre modo 'plantilla' y 'preview'"""
        self.modo_actual = modo
        self.actualizar_vista_completa()
    
    def actualizar_vista_completa(self):
        """Actualiza TODO el widget según el modo actual"""
        texto = self.obtener_texto_para_modo()
        self.label.setText(texto)
        self.actualizar_estilo_segun_modo()
        
        # Ajustar tamaño si es necesario
        self.ajustar_tamano_por_texto(texto)
    
    def obtener_texto_para_modo(self):
        """Obtiene el texto correcto según el modo"""
        if self.modo_actual == 'plantilla':
            # MODO EDICIÓN: mostrar placeholder
            if self.config['tipo'] == 'texto':
                texto = self.config.get('texto_fijo', 'Texto de ejemplo')
                if not texto.strip():
                    texto = '[Texto fijo]'
            else:  # campo dinámico
                columna = self.config.get('columna_padron', '')
                if columna:
                    texto = f"{{{columna}}}"
                else:
                    texto = "{selecciona_columna}"
            return texto
        
        else:  # preview
            # MODO VISTA PREVIA: mostrar datos reales
            if self.config['tipo'] == 'texto':
                return self.config.get('texto_fijo', '')
            else:
                columna = self.config.get('columna_padron', '')
                if columna and columna in self.datos_actuales:
                    valor = self.datos_actuales[columna]
                    return str(valor) if valor is not None else ''
                else:
                    return f"[{columna}]" if columna else "[sin datos]"
    
    def actualizar_estilo_segun_modo(self):
        """Aplica estilos diferentes para cada modo"""
        if self.modo_actual == 'plantilla':
            # ESTILO MODO EDICIÓN (placeholder)
            if self.config['tipo'] == 'texto':
                color = '#006600'  # Verde para texto fijo
                bg_color = 'rgba(200, 255, 200, 0.1)'
                borde = '1px dotted #4CAF50'
            else:  # campo dinámico
                color = '#0000CC'  # Azul para campos de BD
                bg_color = 'rgba(200, 200, 255, 0.1)'
                borde = '1px dotted #2196F3'
        else:
            # ESTILO MODO PREVIEW (datos reales)
            if self.config['tipo'] == 'texto':
                color = '#000000'  # Negro normal para texto fijo
                bg_color = 'transparent'
                borde = 'none'
            else:  # campo dinámico
                color = '#000000'  # Negro normal para datos reales
                bg_color = 'rgba(144, 238, 144, 0.2)'  # Verde claro de fondo
                borde = '1px solid #4CAF50'
        
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
                background-color: {bg_color};
                color: {color};
                font-family: '{self.config['fuente']}';
                font-size: {self.config['tamano_fuente']}px;
                font-weight: {'bold' if self.config['negrita'] else 'normal'};
                font-style: {'italic' if self.config['cursiva'] else 'normal'};
                text-align: {alineacion_css};
                padding: 0px;
                margin: 0px;
                border: {borde};
                border-radius: 2px;
            }}
        """
        self.label.setStyleSheet(estilo)
        
        # También aplicar fuente directamente
        font = QFont(self.config['fuente'], self.config['tamano_fuente'])
        font.setBold(self.config['negrita'])
        font.setItalic(self.config['cursiva'])
        self.label.setFont(font)
    
    def ajustar_tamano_por_texto(self, texto: str):
        """Ajusta el tamaño del widget al texto"""
        if not hasattr(self, 'parent') or not self.parent():
            return
        
        # Calcular ancho aproximado (más generoso para placeholders)
        tamano_fuente = self.config.get('tamano_fuente', 12)
        if self.modo_actual == 'plantilla' and self.config['tipo'] != 'texto':
            # Para placeholders como {nombre}, dar más espacio
            ancho_aprox = len(texto) * tamano_fuente * 0.8
        else:
            ancho_aprox = len(texto) * tamano_fuente * 0.6
        
        # Límites
        ancho_min = max(80, ancho_aprox)  # Mínimo 80px
        ancho_max = 400  # Máximo razonable
        
        nuevo_ancho = min(ancho_max, ancho_min)
        
        # Convertir a mm para la configuración
        if hasattr(self.parent(), 'escala'):
            self.config['ancho'] = nuevo_ancho / self.parent().escala
            self.setFixedWidth(int(nuevo_ancho))
    
    def set_datos_preview(self, datos_registro: dict):
        """Establece datos reales para modo preview"""
        self.datos_actuales = datos_registro
        if self.modo_actual == 'preview':
            self.actualizar_vista_completa()
    
    def setup_fisica(self):
        """Configura sistema de drag-drop (tu código existente)"""
        self.drag_pos = None
        self.is_dragging = False
        self.is_resizing = False
        self.resize_corner = None
        
        self.velocity = QPoint(0, 0)
        self.last_pos = None
        self.drag_start_pos = None
        
        self.physics_timer = QTimer()
        self.physics_timer.timeout.connect(self.apply_physics)
        self.physics_timer.start(16)
        
        self.setMouseTracking(True)
    
    def apply_physics(self):
        if not self.is_dragging and (self.velocity.x() != 0 or self.velocity.y() != 0):
            self.velocity.setX(self.velocity.x() * 0.85)
            self.velocity.setY(self.velocity.y() * 0.85)
            
            if abs(self.velocity.x()) > 0.5 or abs(self.velocity.y()) > 0.5:
                new_pos = self.pos() + self.velocity
                self.move_within_bounds(new_pos)
            else:
                self.velocity = QPoint(0, 0)
    
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
    
    def mousePressEvent(self, event: QMouseEvent):
        """Inicia drag o resize - MEJORADO con deselección global"""
        if event.button() == Qt.MouseButton.LeftButton:
            pos = event.pos()
            rect = self.rect()
            
            # Verificar si es resize
            for corner_name, corner_pos in self._get_corners().items():
                if (pos - corner_pos).manhattanLength() < 8:
                    self.is_resizing = True
                    self.resize_corner = corner_name
                    self.resize_start_pos = event.globalPosition().toPoint()
                    self.resize_start_size = self.size()
                    self.setCursor(self.get_resize_cursor(corner_name))
                    
                    # IMPORTANTE: Deseleccionar otros campos
                    self._deseleccionar_otros_campos()
                    self.set_seleccionado(True)
                    return
            
            # Si no es resize, es drag
            self.is_dragging = True
            self.drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            self.drag_start_pos = self.pos()
            self.last_pos = event.globalPosition().toPoint()
            self.velocity = QPoint(0, 0)
            
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
            
            # IMPORTANTE: Deseleccionar otros campos ANTES de seleccionar este
            self._deseleccionar_otros_campos()
            self.set_seleccionado(True)
            self.campo_seleccionado.emit(self)
    
    def get_resize_cursor(self, corner):
        """Devuelve cursor apropiado para resize"""
        if corner in ['top-left', 'bottom-right']:
            return Qt.CursorShape.SizeFDiagCursor
        elif corner in ['top-right', 'bottom-left']:
            return Qt.CursorShape.SizeBDiagCursor
        elif 'top' in corner or 'bottom' in corner:
            return Qt.CursorShape.SizeVerCursor
        else:
            return Qt.CursorShape.SizeHorCursor
    
    def mouseMoveEvent(self, event: QMouseEvent):
        if self.is_resizing and self.resize_corner:
            self.handle_resize(event)
        elif self.is_dragging and event.buttons() & Qt.MouseButton.LeftButton:
            self.handle_drag(event)
        else:
            pos = event.pos()
            rect = self.rect()
            
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
        delta = event.globalPosition().toPoint() - self.resize_start_pos
        
        new_width = max(20, self.resize_start_size.width() + delta.x())
        new_height = max(10, self.resize_start_size.height() + delta.y())
        
        if 'left' in self.resize_corner and new_width > 20:
            self.move(self.x() + delta.x(), self.y())
        
        if 'top' in self.resize_corner and new_height > 10:
            self.move(self.x(), self.y() + delta.y())
        
        self.setFixedSize(new_width, new_height)
        
        parent = self.parent()
        if parent and hasattr(parent, 'escala'):
            self.config['ancho'] = new_width / parent.escala
            self.config['alto'] = new_height / parent.escala
            
            self.campo_modificado.emit({
                'ancho': self.config['ancho'],
                'alto': self.config['alto']
            })
        
        # Recalcular texto después de resize
        self.actualizar_vista_completa()
    
    def handle_drag(self, event):
        new_pos = event.globalPosition().toPoint() - self.drag_pos
        self.move_within_bounds(new_pos)
        
        if self.last_pos:
            delta = event.globalPosition().toPoint() - self.last_pos
            self.velocity = delta * 0.7
        self.last_pos = event.globalPosition().toPoint()
    
    def mouseReleaseEvent(self, event: QMouseEvent):
        self.is_dragging = False
        self.is_resizing = False
        self.resize_corner = None
        
        if hasattr(self, 'drag_start_pos') and self.drag_start_pos:
            if (self.pos() - self.drag_start_pos).manhattanLength() > 5:
                self.emit_position_change()
        
        self.setCursor(Qt.CursorShape.OpenHandCursor)
    
    def emit_position_change(self):
        parent = self.parent()
        if parent and hasattr(parent, 'escala'):
            self.campo_modificado.emit({
                'x': self.config['x'],
                'y': self.config['y'],
                'ancho': self.config['ancho'],
                'alto': self.config['alto']
            })
    
    def enterEvent(self, event: QEnterEvent):
        """Mouse entra al widget - NO cambiar borde si ya está seleccionado"""
        if not self.config.get('seleccionado', False):
            self.setStyleSheet("""
                CampoSimpleWidget {
                    border: 1px dashed #999;
                    background-color: rgba(255, 255, 200, 0.3);
                }
            """)
        self.setCursor(Qt.CursorShape.OpenHandCursor)
        super().enterEvent(event)
    
    def leaveEvent(self, event):
        """Mouse sale del widget - NO quitar borde si está seleccionado"""
        if not self.config.get('seleccionado', False):
            self.setStyleSheet("")
        super().leaveEvent(event)
    
    def paintEvent(self, event):
        """Dibuja borde de selección y manejadores - MEJOR VISIBILIDAD"""
        super().paintEvent(event)
        
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Dibujar borde de selección ROJO FUERTE
        if self.config.get('seleccionado', False):
            # Borde externo ROJO (2px)
            painter.setPen(QPen(QColor(255, 0, 0), 2, Qt.PenStyle.SolidLine))
            painter.drawRect(0, 0, self.width() - 1, self.height() - 1)
            
            # Borde interno NEGRO discontinuo (1px)
            painter.setPen(QPen(QColor(0, 0, 0), 1, Qt.PenStyle.DashLine))
            painter.drawRect(1, 1, self.width() - 3, self.height() - 3)
            
            # Dibujar manejadores de resize AZUL BRILLANTE
            painter.setPen(QPen(QColor(0, 120, 255), 2))
            painter.setBrush(QBrush(QColor(255, 255, 255)))
            
            # Esquinas más grandes y visibles
            size = 8
            half = size // 2
            
            corners = [
                QPoint(0, 0),                      # top-left
                QPoint(self.width() - size, 0),    # top-right
                QPoint(0, self.height() - size),   # bottom-left
                QPoint(self.width() - size, self.height() - size)  # bottom-right
            ]
            
            for corner in corners:
                # Círculo en lugar de rectángulo (más visible)
                painter.drawEllipse(corner.x(), corner.y(), size, size)
                
                # Punto interior para mejor visibilidad
                painter.setBrush(QBrush(QColor(0, 120, 255)))
                painter.drawEllipse(corner.x() + half//2, corner.y() + half//2, 
                                half, half)
                painter.setBrush(QBrush(QColor(255, 255, 255)))
    
    def set_seleccionado(self, seleccionado: bool):
        """Marca/desmarca como seleccionado con repintado FORZADO"""
        self.config['seleccionado'] = seleccionado
        
        # FORZAR repintado inmediato
        self.update()
        
        # También cambiar estilo CSS para borde permanente
        if seleccionado:
            self.setStyleSheet("""
                CampoSimpleWidget {
                    border: 2px solid #ff0000;
                    background-color: rgba(255, 200, 200, 0.1);
                }
            """)
        else:
            self.setStyleSheet("")  # Quitar borde
    
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
        self.actualizar_estilo_segun_modo()  # Ya existe
        self.campo_modificado.emit({'alineacion': alineacion})
        
        # DEBUG: Verificar que se guarda
        print(f"📐 Campo '{self.config['nombre']}': alineación cambiada a '{alineacion}'")
    
    def set_datos_preview_real(self, datos_registro: dict):
        """Muestra datos REALES en modo preview"""
        if self.config.get('modo', 'plantilla') == 'preview':
            if self.config['tipo'] == 'texto':
                # Texto fijo se mantiene igual
                texto = self.config.get('texto_fijo', '')
            else:  # campo dinámico
                columna = self.config.get('columna_padron', '')
                if columna:
                    # Buscar en datos del registro
                    valor = datos_registro.get(columna, f'{{{columna}}}')
                    texto = str(valor)
                else:
                    texto = '{sin_columna}'
            
            # Actualizar label
            self.label.setText(texto)
            
            # Si el texto es muy largo, ajustar ancho
            if hasattr(self, 'parent') and hasattr(self.parent(), 'escala'):
                ancho_texto = len(texto) * self.config['tamano_fuente'] * 0.6
                ancho_min = max(20, ancho_texto)
                self.setFixedWidth(int(ancho_min))
    
    def set_modo_preview(self, datos_registro: dict):
        """Configura el campo para modo preview con datos específicos"""
        self.set_modo('preview')
        
        if self.config['tipo'] == 'texto':
            texto = self.config.get('texto_fijo', '')
        else:  # campo dinámico
            columna = self.config.get('columna_padron', '')
            if columna:
                # Buscar valor en los datos del registro
                valor = datos_registro.get(columna, f'{{{columna}}}')
                texto = str(valor) if valor is not None else ''
            else:
                texto = '{sin_columna}'
        
        self.label.setText(texto)
        self.actualizar_tamano_texto(texto)

    def actualizar_tamano_texto(self, texto: str):
        """Ajusta el tamaño del widget según el texto"""
        if hasattr(self, 'parent') and hasattr(self.parent(), 'escala'):
            # Calcular ancho aproximado en píxeles
            tamano_fuente = self.config.get('tamano_fuente', 12)
            ancho_aprox = len(texto) * tamano_fuente * 0.6  # Factor aproximado
            
            # Limitar mínimo y máximo
            ancho_min = max(50, ancho_aprox)
            ancho_max = 500  # Máximo razonable
            
            nuevo_ancho = min(ancho_max, ancho_min)
            
            # Convertir a mm para la configuración
            self.config['ancho'] = nuevo_ancho / self.parent().escala
            self.setFixedWidth(int(nuevo_ancho))

    def _deseleccionar_otros_campos(self):
        """Deselecciona todos los otros campos en el mismo preview"""
        parent = self.parent()
        if not parent:
            return
        
        # Buscar en todos los widgets hijos del mismo padre
        for sibling in parent.findChildren(CampoSimpleWidget):
            if sibling != self and sibling.config.get('seleccionado', False):
                sibling.set_seleccionado(False)
        
        # También deseleccionar campos compuestos y tablas si existen
        try:
            from ui.modules.plantillas.editor_mejorado.campo_compuesto import CampoCompuestoWidget
            for sibling in parent.findChildren(CampoCompuestoWidget):
                if sibling != self and sibling.config.get('seleccionado', False):
                    sibling.set_seleccionado(False)
        except ImportError:
            pass
        
        try:
            from ui.modules.plantillas.editor_mejorado.tabla_widget import TablaWidget
            for sibling in parent.findChildren(TablaWidget):
                if sibling != self and sibling.config.get('seleccionado', False):
                    sibling.set_seleccionado(False)
        except ImportError:
            pass

    def _get_corners(self): 
        """Devuelve coordenadas de las esquinas"""
        rect = self.rect()
        return {
            'top-left': QPoint(0, 0),
            'top-right': QPoint(rect.width(), 0),
            'bottom-left': QPoint(0, rect.height()),
            'bottom-right': QPoint(rect.width(), rect.height())
        }
    
    def obtener_config_alineacion_pdf(self):
        """Devuelve la configuración de alineación para ReportLab"""
        align_map = {
            'left': 'LEFT',
            'center': 'CENTER', 
            'right': 'RIGHT',
            'justify': 'LEFT'  # ReportLab no tiene JUSTIFY nativo, usamos LEFT
        }
        return align_map.get(self.config.get('alineacion', 'left'), 'LEFT')