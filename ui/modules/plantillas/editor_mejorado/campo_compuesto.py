# ui/modules/plantillas/editor_mejorado/campo_compuesto.py - VERSIÓN REAL
from PyQt6.QtWidgets import (QFrame, QLabel, QHBoxLayout, QVBoxLayout,
                             QPushButton, QMenu, QInputDialog, QDialog,
                             QListWidget, QListWidgetItem, QDialogButtonBox,
                             QFormLayout, QComboBox, QLineEdit, QHBoxLayout,
                             QMessageBox, QWidget, QScrollArea, QVBoxLayout)
from PyQt6.QtCore import Qt, pyqtSignal, QPoint
from PyQt6.QtGui import QPainter, QPen, QColor, QBrush, QMouseEvent, QFont
import json

class ComponenteCompuesto:
    """Componente REAL dentro de un campo compuesto"""
    
    def __init__(self, tipo='texto', valor=''):
        self.tipo = tipo  # 'texto' o 'campo'
        self.valor = valor  # texto fijo o nombre columna
        self.visible = True
    
    def to_dict(self):
        return {'tipo': self.tipo, 'valor': self.valor, 'visible': self.visible}
    
    @classmethod
    def from_dict(cls, data):
        componente = cls(data.get('tipo', 'texto'), data.get('valor', ''))
        componente.visible = data.get('visible', True)
        return componente
    
    def get_texto(self, datos_registro=None):
        """Obtiene texto para mostrar según tipo y datos"""
        if self.tipo == 'texto':
            return self.valor
        else:  # campo
            if datos_registro and self.valor in datos_registro:
                return str(datos_registro[self.valor])
            else:
                return f"{{{self.valor}}}"

class CampoCompuestoWidget(QFrame):
    """Campo compuesto REAL que genera PDF y muestra concatenación"""
    
    campo_seleccionado = pyqtSignal(object)
    campo_modificado = pyqtSignal(dict)
    solicita_eliminar = pyqtSignal(object)
    
    def __init__(self, config=None, parent=None):
        super().__init__(parent)
        self.config = config or self._config_default()
        self.componentes = self._cargar_componentes()
        self.modo_actual = 'plantilla'  # 'plantilla' o 'preview'
        self.datos_actuales = {}
        self.setup_ui()
        self.setup_fisica()
        self.actualizar_vista_completa()
    
    def _config_default(self):
        return {
            'nombre': 'Campo Compuesto',
            'tipo': 'compuesto',
            'x': 50.0, 'y': 50.0, 'ancho': 200.0, 'alto': 20.0,
            'alineacion': 'left',
            'fuente': 'Arial', 'tamano_fuente': 12,
            'color': '#000000', 'negrita': False, 'cursiva': False,
            'componentes': []
        }
    
    def _cargar_componentes(self):
        """Carga componentes desde config"""
        componentes = []
        for comp_data in self.config.get('componentes', []):
            componentes.append(ComponenteCompuesto.from_dict(comp_data))
        return componentes
    
    def setup_ui(self):
        """Configura interfaz DINÁMICA que muestra concatenación REAL"""
        self.setFrameStyle(QFrame.Shape.NoFrame)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        self.layout_principal = QHBoxLayout()
        self.layout_principal.setContentsMargins(5, 2, 5, 2)
        self.layout_principal.setSpacing(3)
        self.setLayout(self.layout_principal)
        
        # Tamaño inicial
        self.setFixedSize(200, 25)
    
    def actualizar_vista_completa(self):
        """Reconstruye la vista con componentes actuales"""
        # Limpiar layout
        while self.layout_principal.count():
            item = self.layout_principal.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # Construir vista según modo
        texto_completo = ""
        
        for componente in self.componentes:
            if not componente.visible:
                continue
                
            texto_actual = componente.get_texto(self.datos_actuales)
            texto_completo += texto_actual
            
            # Crear widget para este componente
            if self.modo_actual == 'plantilla':
                # MODO EDICIÓN: diferenciar tipos
                if componente.tipo == 'texto':
                    lbl = QLabel(texto_actual)
                    lbl.setStyleSheet(f"""
                        QLabel {{
                            background-color: rgba(200, 255, 200, 0.3);
                            color: #006600;
                            border: 1px solid #4CAF50;
                            border-radius: 3px;
                            padding: 1px 3px;
                            font-family: '{self.config['fuente']}';
                            font-size: {self.config['tamano_fuente']}px;
                            font-weight: {'bold' if self.config['negrita'] else 'normal'};
                            font-style: {'italic' if self.config['cursiva'] else 'normal'};
                        }}
                    """)
                else:  # campo
                    lbl = QLabel(f"{{{componente.valor}}}")
                    lbl.setStyleSheet(f"""
                        QLabel {{
                            background-color: rgba(200, 200, 255, 0.3);
                            color: #0000CC;
                            border: 1px solid #2196F3;
                            border-radius: 3px;
                            padding: 1px 3px;
                            font-family: '{self.config['fuente']}';
                            font-size: {self.config['tamano_fuente']}px;
                            font-weight: {'bold' if self.config['negrita'] else 'normal'};
                        }}
                    """)
            else:
                # MODO PREVIEW: mostrar datos reales unificados
                lbl = QLabel(texto_actual)
                lbl.setStyleSheet(f"""
                    QLabel {{
                        background-color: rgba(144, 238, 144, 0.2);
                        color: #000000;
                        border: 1px solid #4CAF50;
                        border-radius: 3px;
                        padding: 1px 3px;
                        font-family: '{self.config['fuente']}';
                        font-size: {self.config['tamano_fuente']}px;
                        font-weight: {'bold' if self.config['negrita'] else 'normal'};
                        font-style: {'italic' if self.config['cursiva'] else 'normal'};
                    }}
                """)
            
            self.layout_principal.addWidget(lbl)
        
        # Si no hay componentes, mostrar placeholder
        if not self.componentes:
            lbl = QLabel("[Campo vacío]")
            lbl.setStyleSheet("color: #999; font-style: italic;")
            self.layout_principal.addWidget(lbl)
        
        # Botón para editar componentes
        btn_editar = QPushButton("✏️")
        btn_editar.setFixedSize(22, 22)
        btn_editar.setStyleSheet("""
            QPushButton {
                background-color: #FF9800;
                color: white;
                border: none;
                border-radius: 3px;
                font-weight: bold;
                font-size: 10px;
            }
            QPushButton:hover {
                background-color: #F57C00;
            }
        """)
        btn_editar.clicked.connect(self.mostrar_editor_componentes)
        btn_editar.setToolTip("Editar componentes")
        self.layout_principal.addWidget(btn_editar)
        
        # Ajustar tamaño según texto completo
        self.ajustar_tamano_segun_texto(texto_completo)
    
    def ajustar_tamano_segun_texto(self, texto: str):
        """Ajusta el tamaño del widget al texto completo"""
        if not hasattr(self, 'parent') or not self.parent():
            return
        
        # Calcular ancho aproximado
        tamano_fuente = self.config.get('tamano_fuente', 12)
        caracteres = len(texto)
        
        # Factor más ancho para componentes múltiples
        factor = 0.7 if self.modo_actual == 'plantilla' else 0.6
        ancho_aprox = max(150, caracteres * tamano_fuente * factor)
        
        # Limitar
        ancho_max = 600
        nuevo_ancho = min(ancho_max, ancho_aprox)
        
        # Convertir a mm para configuración
        if hasattr(self.parent(), 'escala'):
            self.config['ancho'] = nuevo_ancho / self.parent().escala
            self.setFixedWidth(int(nuevo_ancho))
    
    def set_modo(self, modo: str):
        """Cambia entre modo 'plantilla' y 'preview'"""
        self.modo_actual = modo
        self.actualizar_vista_completa()
    
    def set_datos_preview(self, datos_registro: dict):
        """Establece datos reales para modo preview"""
        self.datos_actuales = datos_registro
        if self.modo_actual == 'preview':
            self.actualizar_vista_completa()
    
    def get_texto_completo(self, datos_registro=None):
        """Devuelve texto completo concatenado"""
        texto = ""
        for componente in self.componentes:
            if componente.visible:
                texto += componente.get_texto(datos_registro)
        return texto
    
    def get_config_pdf(self):
        """Devuelve configuración para generación de PDF"""
        return {
            'nombre': self.config['nombre'],
            'tipo': 'compuesto',
            'x': self.config['x'],
            'y': self.config['y'],
            'ancho': self.config['ancho'],
            'alto': self.config['alto'],
            'alineacion': self.config['alineacion'],
            'fuente': self.config['fuente'],
            'tamano_fuente': self.config['tamano_fuente'],
            'color': self.config['color'],
            'negrita': self.config['negrita'],
            'cursiva': self.config['cursiva'],
            'componentes': [comp.to_dict() for comp in self.componentes]
        }
    
    # ========== EDITOR DE COMPONENTES ==========
    
    def mostrar_editor_componentes(self):
        """Muestra diálogo para editar componentes"""
        dialog = DialogoEditorComponentes(self.componentes, self)
        if dialog.exec():
            nuevos_componentes = dialog.obtener_componentes()
            if nuevos_componentes is not None:
                self.componentes = nuevos_componentes
                self.guardar_componentes()
                self.actualizar_vista_completa()
    
    def guardar_componentes(self):
        """Guarda componentes en config y emite señal"""
        self.config['componentes'] = [comp.to_dict() for comp in self.componentes]
        self.campo_modificado.emit({'componentes': self.config['componentes']})
    
    # ========== MÉTODOS DE FÍSICA (similar a CampoSimpleWidget) ==========
    
    def setup_fisica(self):
        self.drag_pos = None
        self.is_dragging = False
        self.is_resizing = False
        self.resize_corner = None
        self.setMouseTracking(True)
    
    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            # Deseleccionar otros campos primero
            self._deseleccionar_otros_campos()
            
            self.is_dragging = True
            self.drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
            self.set_seleccionado(True)
            self.campo_seleccionado.emit(self)
    
    def _deseleccionar_otros_campos(self):
        """Deselecciona otros campos"""
        parent = self.parent()
        if not parent:
            return
        
        from ui.modules.plantillas.editor_mejorado.campo_widget import CampoSimpleWidget
        from ui.modules.plantillas.editor_mejorado.tabla_widget import TablaWidget
        
        for sibling in parent.findChildren((CampoSimpleWidget, TablaWidget, CampoCompuestoWidget)):
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
                CampoCompuestoWidget {
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

class DialogoEditorComponentes(QDialog):
    """Diálogo SIMPLE para agregar/editar componentes"""
    
    def __init__(self, componentes_actuales, parent=None):
        super().__init__(parent)
        self.componentes = [ComponenteCompuesto.from_dict(comp.to_dict()) 
                           for comp in componentes_actuales]
        self.setWindowTitle("🧩 Editor de Componentes")
        self.setFixedSize(600, 400)
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout()
        
        # Título
        titulo = QLabel("Componentes del Campo Compuesto")
        titulo.setStyleSheet("font-size: 14px; font-weight: bold; color: #2c3e50;")
        layout.addWidget(titulo)
        
        # Lista de componentes
        self.lista_componentes = QListWidget()
        self.lista_componentes.setAlternatingRowColors(True)
        self.lista_componentes.setStyleSheet("""
            QListWidget {
                border: 1px solid #ddd;
                border-radius: 4px;
                padding: 5px;
            }
            QListWidget::item {
                padding: 5px;
                border-bottom: 1px solid #eee;
            }
            QListWidget::item:selected {
                background-color: #e3f2fd;
                color: #1565c0;
            }
        """)
        
        self.actualizar_lista()
        layout.addWidget(self.lista_componentes)
        
        # Botones de acción para componentes
        btn_layout = QHBoxLayout()
        
        btn_agregar = QPushButton("➕ Agregar")
        btn_agregar.clicked.connect(self.agregar_componente)
        
        btn_editar = QPushButton("✏️ Editar")
        btn_editar.clicked.connect(self.editar_componente)
        
        btn_eliminar = QPushButton("🗑️ Eliminar")
        btn_eliminar.clicked.connect(self.eliminar_componente)
        
        btn_subir = QPushButton("⬆ Subir")
        btn_subir.clicked.connect(self.subir_componente)
        
        btn_bajar = QPushButton("⬇ Bajar")
        btn_bajar.clicked.connect(self.bajar_componente)
        
        for btn in [btn_agregar, btn_editar, btn_eliminar, btn_subir, btn_bajar]:
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #f8f9fa;
                    border: 1px solid #dee2e6;
                    border-radius: 3px;
                    padding: 5px 10px;
                    font-size: 11px;
                }
                QPushButton:hover {
                    background-color: #e9ecef;
                }
            """)
        
        btn_layout.addWidget(btn_agregar)
        btn_layout.addWidget(btn_editar)
        btn_layout.addWidget(btn_eliminar)
        btn_layout.addStretch()
        btn_layout.addWidget(btn_subir)
        btn_layout.addWidget(btn_bajar)
        
        layout.addLayout(btn_layout)
        
        # Ejemplo de vista previa
        layout.addWidget(QLabel("Vista previa:"))
        
        self.lbl_vista_previa = QLabel("")
        self.lbl_vista_previa.setStyleSheet("""
            QLabel {
                background-color: #f5f5f5;
                border: 1px solid #ddd;
                border-radius: 4px;
                padding: 10px;
                font-family: 'Arial';
                font-size: 12px;
                min-height: 40px;
            }
        """)
        layout.addWidget(self.lbl_vista_previa)
        
        # Datos de ejemplo para vista previa
        self.datos_ejemplo = {
            'nombre': 'CARLOS',
            'apellido': 'SANTANA',
            'direccion': 'AV. PRINCIPAL 123',
            'ciudad': 'MEXICO DF',
            'codigo_postal': '12345'
        }
        
        self.actualizar_vista_previa()
        
        # Botones de diálogo
        btn_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | 
            QDialogButtonBox.StandardButton.Cancel
        )
        btn_box.accepted.connect(self.accept)
        btn_box.rejected.connect(self.reject)
        
        layout.addWidget(btn_box)
        self.setLayout(layout)
    
    def actualizar_lista(self):
        """Actualiza la lista de componentes"""
        self.lista_componentes.clear()
        for i, comp in enumerate(self.componentes):
            icono = "📝" if comp.tipo == 'texto' else "🔤"
            texto = comp.valor if comp.tipo == 'texto' else f"{{{comp.valor}}}"
            item = QListWidgetItem(f"{icono} {texto}")
            item.setData(Qt.ItemDataRole.UserRole, i)
            self.lista_componentes.addItem(item)
    
    def actualizar_vista_previa(self):
        """Actualiza la vista previa con datos de ejemplo"""
        texto = ""
        for comp in self.componentes:
            if comp.visible:
                texto += comp.get_texto(self.datos_ejemplo)
        self.lbl_vista_previa.setText(texto or "(vacío)")
    
    def agregar_componente(self):
        """Añade un nuevo componente"""
        dialog = DialogoNuevoComponente(self)
        if dialog.exec():
            tipo, valor = dialog.obtener_valores()
            if valor:
                self.componentes.append(ComponenteCompuesto(tipo, valor))
                self.actualizar_lista()
                self.actualizar_vista_previa()
    
    def editar_componente(self):
        """Edita el componente seleccionado"""
        item = self.lista_componentes.currentItem()
        if not item:
            QMessageBox.warning(self, "Seleccionar", "Selecciona un componente")
            return
        
        idx = item.data(Qt.ItemDataRole.UserRole)
        componente = self.componentes[idx]
        
        dialog = DialogoNuevoComponente(self, componente)
        if dialog.exec():
            tipo, valor = dialog.obtener_valores()
            if valor:
                componente.tipo = tipo
                componente.valor = valor
                self.actualizar_lista()
                self.actualizar_vista_previa()
    
    def eliminar_componente(self):
        """Elimina el componente seleccionado"""
        item = self.lista_componentes.currentItem()
        if not item:
            return
        
        idx = item.data(Qt.ItemDataRole.UserRole)
        if idx < len(self.componentes):
            del self.componentes[idx]
            self.actualizar_lista()
            self.actualizar_vista_previa()
    
    def subir_componente(self):
        """Sube el componente seleccionado"""
        item = self.lista_componentes.currentItem()
        if not item:
            return
        
        idx = item.data(Qt.ItemDataRole.UserRole)
        if idx > 0:
            self.componentes[idx], self.componentes[idx-1] = self.componentes[idx-1], self.componentes[idx]
            self.actualizar_lista()
            self.lista_componentes.setCurrentRow(idx-1)
    
    def bajar_componente(self):
        """Baja el componente seleccionado"""
        item = self.lista_componentes.currentItem()
        if not item:
            return
        
        idx = item.data(Qt.ItemDataRole.UserRole)
        if idx < len(self.componentes) - 1:
            self.componentes[idx], self.componentes[idx+1] = self.componentes[idx+1], self.componentes[idx]
            self.actualizar_lista()
            self.lista_componentes.setCurrentRow(idx+1)
    
    def obtener_componentes(self):
        """Devuelve los componentes actuales"""
        return self.componentes

class DialogoNuevoComponente(QDialog):
    """Diálogo para crear/editar un componente individual"""
    
    def __init__(self, parent=None, componente=None):
        super().__init__(parent)
        self.componente_existente = componente
        self.setWindowTitle("Nuevo Componente" if not componente else "Editar Componente")
        self.setFixedSize(400, 200)
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout()
        
        form = QFormLayout()
        
        # Tipo
        self.combo_tipo = QComboBox()
        self.combo_tipo.addItems(["Texto fijo", "Campo de la base de datos"])
        self.combo_tipo.currentTextChanged.connect(self.actualizar_placeholder)
        
        # Valor
        self.txt_valor = QLineEdit()
        self.txt_valor.setPlaceholderText("Ingresa el texto o nombre de columna...")
        
        if self.componente_existente:
            if self.componente_existente.tipo == 'texto':
                self.combo_tipo.setCurrentIndex(0)
            else:
                self.combo_tipo.setCurrentIndex(1)
            self.txt_valor.setText(self.componente_existente.valor)
        
        form.addRow("Tipo:", self.combo_tipo)
        form.addRow("Valor:", self.txt_valor)
        
        layout.addLayout(form)
        
        # Ejemplos
        ejemplos = QLabel()
        ejemplos.setStyleSheet("color: #666; font-size: 10px;")
        
        if self.combo_tipo.currentText() == "Texto fijo":
            ejemplos.setText("Ejemplos: 'Domicilio: ', ', ', 'Tel: '")
        else:
            ejemplos.setText("Ejemplos: nombre, apellido, direccion, telefono")
        
        self.combo_tipo.currentTextChanged.connect(
            lambda text: ejemplos.setText(
                "Ejemplos: 'Domicilio: ', ', ', 'Tel: '" if text == "Texto fijo" 
                else "Ejemplos: nombre, apellido, direccion, telefono"
            )
        )
        
        layout.addWidget(ejemplos)
        layout.addStretch()
        
        # Botones
        btn_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | 
            QDialogButtonBox.StandardButton.Cancel
        )
        btn_box.accepted.connect(self.validar_y_aceptar)
        btn_box.rejected.connect(self.reject)
        
        layout.addWidget(btn_box)
        self.setLayout(layout)
    
    def actualizar_placeholder(self, text):
        if text == "Texto fijo":
            self.txt_valor.setPlaceholderText("Ingresa el texto fijo...")
        else:
            self.txt_valor.setPlaceholderText("Ingresa nombre de columna...")
    
    def validar_y_aceptar(self):
        """Valida y acepta el diálogo"""
        valor = self.txt_valor.text().strip()
        if not valor:
            QMessageBox.warning(self, "Valor vacío", "El valor no puede estar vacío")
            return
        
        self.accept()
    
    def obtener_valores(self):
        """Devuelve tipo y valor"""
        tipo = 'texto' if self.combo_tipo.currentText() == "Texto fijo" else 'campo'
        valor = self.txt_valor.text().strip()
        return tipo, valor