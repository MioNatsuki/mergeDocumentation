# ui/modules/plantillas/editor_mejorado/tabla_widget.py
from PyQt6.QtWidgets import (QFrame, QTableWidget, QTableWidgetItem, QVBoxLayout,
                             QHeaderView, QMenu, QDialog, QVBoxLayout, QHBoxLayout,
                             QLabel, QLineEdit, QSpinBox, QCheckBox, QPushButton,
                             QDialogButtonBox, QFormLayout, QComboBox, QMessageBox)
from PyQt6.QtCore import Qt, pyqtSignal, QPoint, QSize
from PyQt6.QtGui import QPainter, QPen, QColor, QBrush, QMouseEvent, QFont, QAction
import json

class TablaWidget(QFrame):
    """Widget de tabla editable que SÍ genera PDF"""
    
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
        """Configuración por defecto de tabla"""
        return {
            'nombre': 'Nueva Tabla',
            'tipo': 'tabla',
            'x': 50.0, 'y': 50.0, 'ancho': 300.0, 'alto': 150.0,
            'columnas': 3,
            'filas': 4,
            'encabezado': True,
            'borde': True,
            'celdas': self._celdas_default(3, 4),
            'fuente': 'Arial',
            'tamano_fuente': 10
        }
    
    def _celdas_default(self, columnas, filas):
        """Celdas por defecto"""
        celdas = []
        for fila in range(filas):
            fila_data = []
            for col in range(columnas):
                if fila == 0 and self.config.get('encabezado', True):
                    fila_data.append({
                        'tipo': 'texto',
                        'valor': f'Col {col+1}',
                        'alineacion': 'center',
                        'negrita': True
                    })
                else:
                    fila_data.append({
                        'tipo': 'texto',
                        'valor': f'Dato {fila+1}.{col+1}',
                        'alineacion': 'left',
                        'negrita': False
                    })
            celdas.append(fila_data)
        return celdas
    
    def setup_ui(self):
        """Configura la tabla visual"""
        self.setFrameStyle(QFrame.Shape.NoFrame)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(2, 2, 2, 2)
        
        # Crear tabla QTableWidget (solo para visualización en editor)
        self.tabla_visual = QTableWidget(self.config['filas'], self.config['columnas'])
        self.tabla_visual.horizontalHeader().setVisible(self.config['encabezado'])
        self.tabla_visual.verticalHeader().setVisible(False)
        
        # Configurar headers
        if self.config['encabezado']:
            headers = []
            for col in range(self.config['columnas']):
                header_text = self.config['celdas'][0][col].get('valor', f'Col {col+1}')
                headers.append(header_text)
            self.tabla_visual.setHorizontalHeaderLabels(headers)
        
        # Llenar celdas
        start_row = 0 if not self.config['encabezado'] else 1
        for fila_idx in range(start_row, self.config['filas']):
            for col_idx in range(self.config['columnas']):
                if fila_idx < len(self.config['celdas']) and col_idx < len(self.config['celdas'][fila_idx]):
                    celda = self.config['celdas'][fila_idx][col_idx]
                    item = QTableWidgetItem(celda.get('valor', ''))
                    
                    # Aplicar alineación
                    align_map = {
                        'left': Qt.AlignmentFlag.AlignLeft,
                        'center': Qt.AlignmentFlag.AlignCenter,
                        'right': Qt.AlignmentFlag.AlignRight
                    }
                    alignment = align_map.get(celda.get('alineacion', 'left'), Qt.AlignmentFlag.AlignLeft)
                    item.setTextAlignment(alignment)
                    
                    # Aplicar negrita
                    font = QFont()
                    font.setBold(celda.get('negrita', False))
                    item.setFont(font)
                    
                    self.tabla_visual.setItem(fila_idx if not self.config['encabezado'] else fila_idx-1, 
                                            col_idx, item)
        
        # Ajustar tamaño de columnas
        self.tabla_visual.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        
        # Deshabilitar edición directa (se edita desde diálogo)
        self.tabla_visual.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        
        layout.addWidget(self.tabla_visual)
        self.setLayout(layout)
        
        # Tamaño inicial
        self.setFixedSize(int(self.config['ancho']), int(self.config['alto']))
    
    def setup_fisica(self):
        """Configura drag and resize (similar a CampoSimpleWidget)"""
        self.drag_pos = None
        self.is_dragging = False
        self.is_resizing = False
        self.resize_corner = None
        self.setMouseTracking(True)
    
    def mousePressEvent(self, event: QMouseEvent):
        """Inicia drag o resize"""
        if event.button() == Qt.MouseButton.LeftButton:
            pos = event.pos()
            
            # Verificar si es resize (esquinas)
            if self._is_near_corner(pos):
                self.is_resizing = True
                self.resize_start_pos = event.globalPosition().toPoint()
                self.resize_start_size = self.size()
                self.setCursor(Qt.CursorShape.SizeFDiagCursor)
            else:
                # Drag
                self.is_dragging = True
                self.drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
                self.setCursor(Qt.CursorShape.ClosedHandCursor)
                self.campo_seleccionado.emit(self)
    
    def _is_near_corner(self, pos, threshold=10):
        """Verifica si el mouse está cerca de una esquina"""
        corners = [
            QPoint(0, 0),  # top-left
            QPoint(self.width(), 0),  # top-right
            QPoint(0, self.height()),  # bottom-left
            QPoint(self.width(), self.height())  # bottom-right
        ]
        
        for corner in corners:
            if (pos - corner).manhattanLength() < threshold:
                return True
        return False
    
    def mouseMoveEvent(self, event: QMouseEvent):
        """Maneja drag o resize"""
        if self.is_resizing:
            self._handle_resize(event)
        elif self.is_dragging and event.buttons() & Qt.MouseButton.LeftButton:
            self._handle_drag(event)
        else:
            # Cambiar cursor según posición
            if self._is_near_corner(event.pos()):
                self.setCursor(Qt.CursorShape.SizeFDiagCursor)
            else:
                self.setCursor(Qt.CursorShape.OpenHandCursor)
    
    def _handle_resize(self, event):
        """Maneja redimensionamiento"""
        delta = event.globalPosition().toPoint() - self.resize_start_pos
        
        # Mínimos: 100x50
        new_width = max(100, self.resize_start_size.width() + delta.x())
        new_height = max(50, self.resize_start_size.height() + delta.y())
        
        self.setFixedSize(new_width, new_height)
        
        # Actualizar tabla visual
        self.tabla_visual.setFixedSize(new_width - 4, new_height - 4)
        
        # Actualizar configuración
        parent = self.parent()
        if parent and hasattr(parent, 'escala'):
            self.config['ancho'] = new_width / parent.escala
            self.config['alto'] = new_height / parent.escala
            
            self.campo_modificado.emit({
                'ancho': self.config['ancho'],
                'alto': self.config['alto']
            })
    
    def _handle_drag(self, event):
        """Maneja drag"""
        new_pos = event.globalPosition().toPoint() - self.drag_pos
        self._move_within_bounds(new_pos)
    
    def _move_within_bounds(self, new_pos):
        """Mueve manteniéndose dentro del padre"""
        parent = self.parent()
        if parent:
            max_x = parent.width() - self.width()
            max_y = parent.height() - self.height()
            
            new_pos.setX(max(0, min(new_pos.x(), max_x)))
            new_pos.setY(max(0, min(new_pos.y(), max_y)))
        
        self.move(new_pos)
        
        # Actualizar configuración
        if parent and hasattr(parent, 'escala'):
            self.config['x'] = new_pos.x() / parent.escala
            self.config['y'] = new_pos.y() / parent.escala
            
            self.campo_modificado.emit({
                'x': self.config['x'],
                'y': self.config['y']
            })
    
    def mouseReleaseEvent(self, event: QMouseEvent):
        """Finaliza drag/resize"""
        self.is_dragging = False
        self.is_resizing = False
        self.setCursor(Qt.CursorShape.ArrowCursor)
    
    def paintEvent(self, event):
        """Dibuja borde de selección"""
        super().paintEvent(event)
        
        if self.config.get('seleccionado', False):
            painter = QPainter(self)
            painter.setPen(QPen(QColor(255, 0, 0), 2, Qt.PenStyle.DashLine))
            painter.drawRect(0, 0, self.width() - 1, self.height() - 1)
    
    def set_seleccionado(self, seleccionado: bool):
        """Marca/desmarca como seleccionado"""
        self.config['seleccionado'] = seleccionado
        self.update()
    
    def get_datos_preview(self, datos_registro):
        """Genera datos para modo preview"""
        datos = []
        
        for fila_idx, fila in enumerate(self.config['celdas']):
            fila_data = []
            for celda in fila:
                if celda['tipo'] == 'texto':
                    fila_data.append(celda['valor'])
                else:  # campo
                    valor = datos_registro.get(celda.get('columna', ''), '')
                    fila_data.append(str(valor))
            datos.append(fila_data)
        
        return datos
    
    def contextMenuEvent(self, event):
        """Menú contextual"""
        menu = QMenu(self)
        
        action_configurar = QAction("⚙️ Configurar tabla", self)
        action_configurar.triggered.connect(self.configurar_tabla)
        
        action_eliminar = QAction("🗑️ Eliminar tabla", self)
        action_eliminar.triggered.connect(lambda: self.solicita_eliminar.emit(self))
        
        menu.addAction(action_configurar)
        menu.addSeparator()
        menu.addAction(action_eliminar)
        
        menu.exec(event.globalPos())
    
    def configurar_tabla(self):
        """Abre diálogo de configuración"""
        dialog = DialogoConfigTabla(self.config, self)
        if dialog.exec():
            nueva_config = dialog.get_configuracion()
            
            # Actualizar configuración
            self.config.update(nueva_config)
            
            # Recrear tabla
            self.setup_ui()
            
            # Emitir cambios
            self.campo_modificado.emit({
                'columnas': self.config['columnas'],
                'filas': self.config['filas'],
                'encabezado': self.config['encabezado'],
                'borde': self.config['borde'],
                'celdas': self.config['celdas']
            })

class DialogoConfigTabla(QDialog):
    """Diálogo para configurar tablas"""
    
    def __init__(self, config_actual=None, parent=None):
        super().__init__(parent)
        self.config_actual = config_actual or {}
        self.setup_ui()
    
    def setup_ui(self):
        self.setWindowTitle("Configurar Tabla")
        self.setFixedSize(500, 600)
        
        layout = QVBoxLayout()
        
        # Configuración básica
        group_basico = QFormLayout()
        
        self.txt_nombre = QLineEdit(self.config_actual.get('nombre', 'Nueva Tabla'))
        group_basico.addRow("Nombre:", self.txt_nombre)
        
        self.spin_columnas = QSpinBox()
        self.spin_columnas.setRange(1, 10)
        self.spin_columnas.setValue(self.config_actual.get('columnas', 3))
        group_basico.addRow("Columnas:", self.spin_columnas)
        
        self.spin_filas = QSpinBox()
        self.spin_filas.setRange(1, 20)
        self.spin_filas.setValue(self.config_actual.get('filas', 4))
        group_basico.addRow("Filas:", self.spin_filas)
        
        self.check_encabezado = QCheckBox()
        self.check_encabezado.setChecked(self.config_actual.get('encabezado', True))
        group_basico.addRow("Encabezado:", self.check_encabezado)
        
        self.check_borde = QCheckBox()
        self.check_borde.setChecked(self.config_actual.get('borde', True))
        group_basico.addRow("Mostrar bordes:", self.check_borde)
        
        layout.addLayout(group_basico)
        
        # Editor de celdas
        layout.addWidget(QLabel("Contenido de celdas:"))
        
        # Crear tabla de edición
        self.tabla_edicion = QTableWidget(
            self.config_actual.get('filas', 4),
            self.config_actual.get('columnas', 3)
        )
        self.tabla_edicion.horizontalHeader().setVisible(True)
        
        # Llenar con datos actuales
        celdas = self.config_actual.get('celdas', [])
        for fila in range(self.tabla_edicion.rowCount()):
            for col in range(self.tabla_edicion.columnCount()):
                valor = ""
                if fila < len(celdas) and col < len(celdas[fila]):
                    valor = celdas[fila][col].get('valor', '')
                
                item = QTableWidgetItem(valor)
                self.tabla_edicion.setItem(fila, col, item)
        
        layout.addWidget(self.tabla_edicion)
        
        # Botones
        btn_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | 
            QDialogButtonBox.StandardButton.Cancel
        )
        btn_box.accepted.connect(self.aceptar)
        btn_box.rejected.connect(self.reject)
        
        layout.addWidget(btn_box)
        self.setLayout(layout)
    
    def aceptar(self):
        """Valida y acepta la configuración"""
        # Validar que todas las celdas tienen valor
        for fila in range(self.tabla_edicion.rowCount()):
            for col in range(self.tabla_edicion.columnCount()):
                item = self.tabla_edicion.item(fila, col)
                if not item or not item.text().strip():
                    QMessageBox.warning(self, "Error", 
                                      f"La celda [{fila+1},{col+1}] está vacía")
                    return
        
        self.accept()
    
    def get_configuracion(self):
        """Devuelve la configuración actual"""
        # Reconstruir celdas
        celdas = []
        for fila in range(self.tabla_edicion.rowCount()):
            fila_data = []
            for col in range(self.tabla_edicion.columnCount()):
                item = self.tabla_edicion.item(fila, col)
                valor = item.text() if item else ""
                
                # Determinar tipo (simple por ahora, se puede extender)
                celda_config = {
                    'tipo': 'texto',
                    'valor': valor,
                    'alineacion': 'left',
                    'negrita': False
                }
                
                # Si es encabezado, centrar y negrita
                if fila == 0 and self.check_encabezado.isChecked():
                    celda_config['alineacion'] = 'center'
                    celda_config['negrita'] = True
                
                fila_data.append(celda_config)
            celdas.append(fila_data)
        
        return {
            'nombre': self.txt_nombre.text(),
            'columnas': self.spin_columnas.value(),
            'filas': self.spin_filas.value(),
            'encabezado': self.check_encabezado.isChecked(),
            'borde': self.check_borde.isChecked(),
            'celdas': celdas
        }