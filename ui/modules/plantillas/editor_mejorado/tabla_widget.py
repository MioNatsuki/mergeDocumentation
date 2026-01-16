# ui/modules/plantillas/editor_mejorado/tabla_widget.py - VERSIÓN REAL
from PyQt6.QtWidgets import (QFrame, QLabel, QVBoxLayout, QHBoxLayout,
                             QPushButton, QMenu, QDialog, QVBoxLayout, QHBoxLayout,
                             QLabel, QLineEdit, QSpinBox, QCheckBox, QPushButton,
                             QDialogButtonBox, QFormLayout, QComboBox, QMessageBox,
                             QTableWidget, QTableWidgetItem, QHeaderView, QWidget,
                             QScrollArea, QGridLayout, QTextEdit)
from PyQt6.QtCore import Qt, pyqtSignal, QPoint, QSize
from PyQt6.QtGui import QPainter, QPen, QColor, QBrush, QMouseEvent, QFont, QAction
import json

class CeldaTabla:
    """Representa una celda de tabla REAL"""
    
    def __init__(self, tipo='texto', valor='', alineacion='left', negrita=False):
        self.tipo = tipo  # 'texto' o 'campo'
        self.valor = valor  # texto fijo o nombre columna
        self.alineacion = alineacion
        self.negrita = negrita
    
    def to_dict(self):
        return {
            'tipo': self.tipo,
            'valor': self.valor,
            'alineacion': self.alineacion,
            'negrita': self.negrita
        }
    
    @classmethod
    def from_dict(cls, data):
        return cls(
            data.get('tipo', 'texto'),
            data.get('valor', ''),
            data.get('alineacion', 'left'),
            data.get('negrita', False)
        )
    
    def get_texto(self, datos_registro=None):
        """Obtiene texto para mostrar"""
        if self.tipo == 'texto':
            return self.valor
        else:  # campo
            if datos_registro and self.valor in datos_registro:
                return str(datos_registro[self.valor])
            else:
                return f"{{{self.valor}}}"

class TablaWidget(QFrame):
    """Widget de tabla que SÍ genera PDF con reportlab.platypus.Table"""
    
    campo_seleccionado = pyqtSignal(object)
    campo_modificado = pyqtSignal(dict)
    solicita_eliminar = pyqtSignal(object)
    
    def __init__(self, config=None, parent=None):
        super().__init__(parent)
        self.config = config or self._config_default()
        self.modo_actual = 'plantilla'
        self.datos_actuales = {}
        self.setup_ui()
        self.setup_fisica()
        self.actualizar_vista_completa()
    
    def _config_default(self):
        """Configuración por defecto de tabla REAL"""
        return {
            'nombre': 'Nueva Tabla',
            'tipo': 'tabla',
            'x': 50.0, 'y': 50.0, 'ancho': 200.0, 'alto': 100.0,
            'columnas': 3,
            'filas': 4,
            'encabezado': True,
            'borde': True,
            'ancho_columnas': [],  # Lista de anchos personalizados
            'celdas': self._crear_celdas_default(3, 4),
            'fuente': 'Arial',
            'tamano_fuente': 10,
            'color_texto': '#000000',
            'color_borde': '#000000',
            'color_fondo_encabezado': '#f0f0f0'
        }
    
    def _crear_celdas_default(self, columnas, filas):
        """Crea estructura de celdas por defecto"""
        celdas = []
        for fila_idx in range(filas):
            fila = []
            for col_idx in range(columnas):
                if fila_idx == 0 and self.config.get('encabezado', True):
                    # Celda de encabezado
                    celda = CeldaTabla(
                        tipo='texto',
                        valor=f'Col {col_idx + 1}',
                        alineacion='center',
                        negrita=True
                    )
                else:
                    # Celda normal
                    celda = CeldaTabla(
                        tipo='texto',
                        valor=f'Dato {fila_idx + 1}.{col_idx + 1}',
                        alineacion='left',
                        negrita=False
                    )
                fila.append(celda)
            celdas.append(fila)
        return celdas
    
    def setup_ui(self):
        """Configura visualización de tabla en editor (sólo para referencia)"""
        self.setFrameStyle(QFrame.Shape.NoFrame)
        
        # Layout principal
        self.layout_principal = QVBoxLayout()
        self.layout_principal.setContentsMargins(2, 2, 2, 2)
        self.layout_principal.setSpacing(0)
        
        # Área de contenido
        self.widget_contenido = QWidget()
        self.layout_contenido = QGridLayout()
        self.layout_contenido.setSpacing(1)
        self.layout_contenido.setContentsMargins(0, 0, 0, 0)
        
        self.widget_contenido.setLayout(self.layout_contenido)
        self.layout_principal.addWidget(self.widget_contenido)
        
        # Botón de configuración
        self.btn_config = QPushButton("⚙ Configurar tabla")
        self.btn_config.clicked.connect(self.configurar_tabla)
        self.btn_config.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 2px 5px;
                font-size: 9px;
                border-radius: 2px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        self.layout_principal.addWidget(self.btn_config)
        
        self.setLayout(self.layout_principal)
        self.setFixedSize(int(self.config['ancho']), int(self.config['alto']))
    
    def actualizar_vista_completa(self):
        """Actualiza la vista de la tabla según modo actual"""
        # Limpiar contenido
        while self.layout_contenido.count():
            item = self.layout_contenido.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        columnas = self.config['columnas']
        filas = self.config['filas']
        encabezado = self.config.get('encabezado', True)
        borde = self.config.get('borde', True)
        
        # Calcular tamaño de celdas
        ancho_celda = self.width() // max(1, columnas)
        alto_celda = (self.height() - 25) // max(1, filas)  # Restar espacio para botón
        
        # Crear celdas visuales
        for fila_idx in range(filas):
            for col_idx in range(columnas):
                # Obtener celda config
                if fila_idx < len(self.config['celdas']) and col_idx < len(self.config['celdas'][fila_idx]):
                    celda_config = self.config['celdas'][fila_idx][col_idx]
                else:
                    celda_config = CeldaTabla()
                
                # Crear widget de celda
                celda_widget = self._crear_widget_celda(celda_config, fila_idx, col_idx, encabezado)
                celda_widget.setFixedSize(ancho_celda, alto_celda)
                
                # Estilo de borde
                if borde:
                    celda_widget.setStyleSheet("border: 1px solid #cccccc;")
                else:
                    celda_widget.setStyleSheet("border: none;")
                
                self.layout_contenido.addWidget(celda_widget, fila_idx, col_idx)
    
    def _crear_widget_celda(self, celda_config, fila_idx, col_idx, encabezado):
        """Crea widget visual para una celda"""
        from PyQt6.QtWidgets import QLabel
        
        widget = QLabel()
        widget.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Obtener texto según modo
        if self.modo_actual == 'plantilla':
            texto = celda_config.get_texto()
        else:
            texto = celda_config.get_texto(self.datos_actuales)
        
        widget.setText(texto if texto else " ")
        
        # Estilo según tipo de celda
        if fila_idx == 0 and encabezado:
            # Encabezado
            widget.setStyleSheet(f"""
                QLabel {{
                    background-color: #f0f0f0;
                    color: #000000;
                    font-weight: bold;
                    font-size: {self.config['tamano_fuente'] - 1}px;
                    padding: 2px;
                }}
            """)
        elif celda_config.tipo == 'campo' and self.modo_actual == 'plantilla':
            # Campo en modo edición
            widget.setStyleSheet(f"""
                QLabel {{
                    background-color: rgba(200, 200, 255, 0.3);
                    color: #0000CC;
                    font-size: {self.config['tamano_fuente']}px;
                    padding: 2px;
                }}
            """)
        else:
            # Celda normal
            alineacion = celda_config.alineacion
            align_map = {
                'left': 'left',
                'center': 'center', 
                'right': 'right',
                'justify': 'left'
            }
            align_css = align_map.get(alineacion, 'left')
            
            widget.setStyleSheet(f"""
                QLabel {{
                    background-color: white;
                    color: #000000;
                    font-weight: {'bold' if celda_config.negrita else 'normal'};
                    font-size: {self.config['tamano_fuente']}px;
                    padding: 2px;
                    text-align: {align_css};
                }}
            """)
            widget.setAlignment(self._qt_alignment_from_string(alineacion))
        
        return widget
    
    def _qt_alignment_from_string(self, alineacion):
        """Convierte string de alineación a Qt Alignment"""
        align_map = {
            'left': Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
            'center': Qt.AlignmentFlag.AlignCenter,
            'right': Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
            'justify': Qt.AlignmentFlag.AlignJustify | Qt.AlignmentFlag.AlignVCenter
        }
        return align_map.get(alineacion, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
    
    def set_modo(self, modo: str):
        """Cambia entre modo 'plantilla' y 'preview'"""
        self.modo_actual = modo
        self.actualizar_vista_completa()
    
    def set_datos_preview(self, datos_registro: dict):
        """Establece datos reales para modo preview"""
        self.datos_actuales = datos_registro
        if self.modo_actual == 'preview':
            self.actualizar_vista_completa()
    
    def get_config_pdf(self):
        """Devuelve configuración para generación de PDF"""
        # Convertir celdas a dict
        celdas_dict = []
        for fila in self.config['celdas']:
            fila_dict = [celda.to_dict() for celda in fila]
            celdas_dict.append(fila_dict)
        
        return {
            'nombre': self.config['nombre'],
            'tipo': 'tabla',
            'x': self.config['x'],
            'y': self.config['y'],
            'ancho': self.config['ancho'],
            'alto': self.config['alto'],
            'columnas': self.config['columnas'],
            'filas': self.config['filas'],
            'encabezado': self.config.get('encabezado', True),
            'borde': self.config.get('borde', True),
            'ancho_columnas': self.config.get('ancho_columnas', []),
            'celdas': celdas_dict,
            'fuente': self.config['fuente'],
            'tamano_fuente': self.config['tamano_fuente'],
            'color_texto': self.config.get('color_texto', '#000000'),
            'color_borde': self.config.get('color_borde', '#000000'),
            'color_fondo_encabezado': self.config.get('color_fondo_encabezado', '#f0f0f0')
        }
    
    # ========== CONFIGURACIÓN DE TABLA ==========
    
    def configurar_tabla(self):
        """Abre diálogo de configuración de tabla"""
        dialog = DialogoConfigTablaReal(self.config, self)
        if dialog.exec():
            nueva_config = dialog.obtener_configuracion()
            
            # Actualizar configuración
            self.config.update(nueva_config)
            
            # Actualizar vista
            self.actualizar_vista_completa()
            
            # Emitir cambios
            self.campo_modificado.emit({
                'columnas': self.config['columnas'],
                'filas': self.config['filas'],
                'encabezado': self.config['encabezado'],
                'borde': self.config['borde'],
                'celdas': [[celda.to_dict() for celda in fila] for fila in self.config['celdas']]
            })
    
    # ========== MÉTODOS DE FÍSICA ==========
    
    def setup_fisica(self):
        self.drag_pos = None
        self.is_dragging = False
        self.is_resizing = False
        self.resize_corner = None
        self.setMouseTracking(True)
    
    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            # Deseleccionar otros campos
            self._deseleccionar_otros_campos()
            
            self.is_dragging = True
            self.drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
            self.set_seleccionado(True)
            self.campo_seleccionado.emit(self)
    
    def _deseleccionar_otros_campos(self):
        parent = self.parent()
        if not parent:
            return
        
        from ui.modules.plantillas.editor_mejorado.campo_widget import CampoSimpleWidget
        from ui.modules.plantillas.editor_mejorado.campo_compuesto import CampoCompuestoWidget
        
        for sibling in parent.findChildren((CampoSimpleWidget, CampoCompuestoWidget, TablaWidget)):
            if sibling != self and hasattr(sibling, 'set_seleccionado'):
                sibling.set_seleccionado(False)
    
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
    
    def set_seleccionado(self, seleccionado: bool):
        self.config['seleccionado'] = seleccionado
        self.update()
        
        if seleccionado:
            self.setStyleSheet("""
                TablaWidget {
                    border: 2px solid #ff0000;
                    background-color: rgba(255, 200, 200, 0.1);
                }
            """)
        else:
            self.setStyleSheet("")
    
    def paintEvent(self, event):
        super().paintEvent(event)
        
        if self.config.get('seleccionado', False):
            painter = QPainter(self)
            painter.setPen(QPen(QColor(255, 0, 0), 2, Qt.PenStyle.SolidLine))
            painter.drawRect(0, 0, self.width() - 1, self.height() - 1)

class DialogoConfigTablaReal(QDialog):
    """Diálogo de configuración de tabla REAL"""
    
    def __init__(self, config_actual, parent=None):
        super().__init__(parent)
        self.config_actual = config_actual
        self.celdas_config = self._cargar_celdas_desde_config()
        self.setWindowTitle("⚙ Configurar Tabla")
        self.setFixedSize(700, 600)
        self.setup_ui()
    
    def _cargar_celdas_desde_config(self):
        """Carga celdas desde configuración actual"""
        celdas = []
        for fila_dict in self.config_actual.get('celdas', []):
            fila = [CeldaTabla.from_dict(celda_dict) for celda_dict in fila_dict]
            celdas.append(fila)
        return celdas
    
    def setup_ui(self):
        layout = QVBoxLayout()
        
        # ===== CONFIGURACIÓN BÁSICA =====
        group_basico = QWidget()
        form_basico = QFormLayout()
        
        self.txt_nombre = QLineEdit(self.config_actual.get('nombre', 'Nueva Tabla'))
        form_basico.addRow("Nombre:", self.txt_nombre)
        
        self.spin_columnas = QSpinBox()
        self.spin_columnas.setRange(1, 10)
        self.spin_columnas.setValue(self.config_actual.get('columnas', 3))
        self.spin_columnas.valueChanged.connect(self.actualizar_editor_celdas)
        form_basico.addRow("Columnas:", self.spin_columnas)
        
        self.spin_filas = QSpinBox()
        self.spin_filas.setRange(1, 20)
        self.spin_filas.setValue(self.config_actual.get('filas', 4))
        self.spin_filas.valueChanged.connect(self.actualizar_editor_celdas)
        form_basico.addRow("Filas:", self.spin_filas)
        
        self.check_encabezado = QCheckBox()
        self.check_encabezado.setChecked(self.config_actual.get('encabezado', True))
        self.check_encabezado.stateChanged.connect(self.actualizar_editor_celdas)
        form_basico.addRow("Encabezado:", self.check_encabezado)
        
        self.check_borde = QCheckBox()
        self.check_borde.setChecked(self.config_actual.get('borde', True))
        form_basico.addRow("Mostrar bordes:", self.check_borde)
        
        group_basico.setLayout(form_basico)
        layout.addWidget(group_basico)
        
        # ===== EDITOR DE CELDAS =====
        layout.addWidget(QLabel("Contenido de celdas:"))
        
        # Scroll area para editor de celdas
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        
        self.widget_editor_celdas = QWidget()
        self.layout_editor_celdas = QGridLayout()
        self.layout_editor_celdas.setSpacing(5)
        
        self.widget_editor_celdas.setLayout(self.layout_editor_celdas)
        scroll.setWidget(self.widget_editor_celdas)
        
        layout.addWidget(scroll, 1)  # Factor de expansión 1
        
        # Inicializar editor de celdas
        self.actualizar_editor_celdas()
        
        # ===== BOTONES =====
        btn_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | 
            QDialogButtonBox.StandardButton.Cancel
        )
        btn_box.accepted.connect(self.aceptar)
        btn_box.rejected.connect(self.reject)
        
        layout.addWidget(btn_box)
        self.setLayout(layout)
    
    def actualizar_editor_celdas(self):
        """Actualiza el editor de celdas según configuración actual"""
        # Limpiar layout
        while self.layout_editor_celdas.count():
            item = self.layout_editor_celdas.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        columnas = self.spin_columnas.value()
        filas = self.spin_filas.value()
        encabezado = self.check_encabezado.isChecked()
        
        # Asegurar que tenemos suficientes celdas
        self._ajustar_celdas_a_tamano(columnas, filas)
        
        # Crear encabezados de columnas
        for col in range(columnas):
            lbl = QLabel(f"Col {col + 1}")
            lbl.setStyleSheet("font-weight: bold; background-color: #f0f0f0; padding: 3px;")
            self.layout_editor_celdas.addWidget(lbl, 0, col + 1)  # +1 para dejar espacio para encabezados de fila
        
        # Crear celdas
        for fila in range(filas):
            # Encabezado de fila
            lbl_fila = QLabel(f"Fila {fila + 1}")
            lbl_fila.setStyleSheet("font-weight: bold; background-color: #f0f0f0; padding: 3px;")
            self.layout_editor_celdas.addWidget(lbl_fila, fila + 1, 0)
            
            for col in range(columnas):
                # Obtener celda actual
                if fila < len(self.celdas_config) and col < len(self.celdas_config[fila]):
                    celda = self.celdas_config[fila][col]
                else:
                    celda = CeldaTabla()
                
                # Crear widget de edición de celda
                widget_celda = WidgetEditorCelda(celda, encabezado and fila == 0)
                self.layout_editor_celdas.addWidget(widget_celda, fila + 1, col + 1)
    
    def _ajustar_celdas_a_tamano(self, nuevas_columnas, nuevas_filas):
        """Ajusta la matriz de celdas al nuevo tamaño"""
        # Ajustar número de filas
        while len(self.celdas_config) < nuevas_filas:
            nueva_fila = []
            for _ in range(max(nuevas_columnas, len(self.celdas_config[0]) if self.celdas_config else nuevas_columnas)):
                nueva_fila.append(CeldaTabla())
            self.celdas_config.append(nueva_fila)
        
        # Recortar filas si es necesario
        self.celdas_config = self.celdas_config[:nuevas_filas]
        
        # Ajustar número de columnas en cada fila
        for fila in self.celdas_config:
            while len(fila) < nuevas_columnas:
                fila.append(CeldaTabla())
            # Recortar columnas si es necesario
            fila[:] = fila[:nuevas_columnas]
    
    def aceptar(self):
        """Valida y acepta la configuración"""
        # Recolectar configuración de celdas
        nuevas_celdas = []
        
        for fila_idx in range(self.spin_filas.value()):
            fila_celdas = []
            for col_idx in range(self.spin_columnas.value()):
                # Encontrar widget correspondiente
                item = self.layout_editor_celdas.itemAtPosition(fila_idx + 1, col_idx + 1)
                if item and item.widget():
                    widget = item.widget()
                    if isinstance(widget, WidgetEditorCelda):
                        fila_celdas.append(widget.obtener_celda())
            
            if len(fila_celdas) == self.spin_columnas.value():
                nuevas_celdas.append(fila_celdas)
            else:
                # Si falta alguna celda, crear vacías
                fila_vacia = [CeldaTabla() for _ in range(self.spin_columnas.value())]
                nuevas_celdas.append(fila_vacia)
        
        self.celdas_config = nuevas_celdas
        self.accept()
    
    def obtener_configuracion(self):
        """Devuelve la configuración completa de la tabla"""
        # Convertir celdas a dict
        celdas_dict = []
        for fila in self.celdas_config:
            fila_dict = [celda.to_dict() for celda in fila]
            celdas_dict.append(fila_dict)
        
        return {
            'nombre': self.txt_nombre.text(),
            'columnas': self.spin_columnas.value(),
            'filas': self.spin_filas.value(),
            'encabezado': self.check_encabezado.isChecked(),
            'borde': self.check_borde.isChecked(),
            'celdas': celdas_dict
        }

class WidgetEditorCelda(QWidget):
    """Widget para editar una celda individual"""
    
    def __init__(self, celda: CeldaTabla, es_encabezado=False):
        super().__init__()
        self.celda = celda
        self.es_encabezado = es_encabezado
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(2)
        
        # Tipo de contenido
        self.combo_tipo = QComboBox()
        self.combo_tipo.addItems(["Texto fijo", "Campo BD"])
        if self.celda.tipo == 'campo':
            self.combo_tipo.setCurrentIndex(1)
        
        # Valor
        self.txt_valor = QLineEdit(self.celda.valor)
        self.txt_valor.setPlaceholderText("Texto o nombre de columna...")
        
        # Alineación (sólo si no es encabezado)
        if not self.es_encabezado:
            self.combo_alineacion = QComboBox()
            self.combo_alineacion.addItems(["Izquierda", "Centro", "Derecha"])
            align_map = {'left': "Izquierda", 'center': "Centro", 'right': "Derecha"}
            self.combo_alineacion.setCurrentText(align_map.get(self.celda.alineacion, "Izquierda"))
        
        # Negrita
        self.check_negrita = QCheckBox("Negrita")
        self.check_negrita.setChecked(self.celda.negrita or self.es_encabezado)
        if self.es_encabezado:
            self.check_negrita.setEnabled(False)  # Encabezados siempre en negrita
        
        # Agregar al layout
        layout.addWidget(self.combo_tipo)
        layout.addWidget(self.txt_valor)
        if not self.es_encabezado:
            layout.addWidget(self.combo_alineacion)
        layout.addWidget(self.check_negrita)
        
        self.setLayout(layout)
        self.setStyleSheet("""
            QWidget {
                border: 1px solid #ddd;
                border-radius: 3px;
                background-color: white;
            }
            QLineEdit, QComboBox {
                font-size: 10px;
                padding: 1px;
            }
        """)
    
    def obtener_celda(self):
        """Devuelve la celda configurada"""
        tipo = 'texto' if self.combo_tipo.currentText() == "Texto fijo" else 'campo'
        valor = self.txt_valor.text().strip()
        
        # Para encabezados sin texto, usar nombre por defecto
        if self.es_encabezado and not valor:
            valor = "Encabezado"
        
        alineacion = 'left'
        if not self.es_encabezado:
            align_map = {
                "Izquierda": 'left',
                "Centro": 'center',
                "Derecha": 'right'
            }
            alineacion = align_map.get(self.combo_alineacion.currentText(), 'left')
        else:
            alineacion = 'center'  # Encabezados centrados por defecto
        
        return CeldaTabla(
            tipo=tipo,
            valor=valor,
            alineacion=alineacion,
            negrita=self.check_negrita.isChecked() or self.es_encabezado
        )