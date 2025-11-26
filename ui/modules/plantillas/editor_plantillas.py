from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QFrame, QMessageBox, QListWidget,
                             QListWidgetItem, QDialog, QFormLayout, QLineEdit,
                             QSpinBox, QComboBox, QCheckBox, QGroupBox,
                             QTabWidget, QTextEdit)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QMouseEvent, QPainter, QColor
from config.database import SessionLocal
from core.models import Plantilla
import json

class CampoDialog(QDialog):
    """Diálogo para configurar un campo dinámico"""
    def __init__(self, campo_existente=None):
        super().__init__()
        self.campo_existente = campo_existente
        self.setup_ui()
    
    def setup_ui(self):
        self.setWindowTitle("Configurar Campo Dinámico" if self.campo_existente else "Nuevo Campo")
        self.setFixedSize(400, 500)
        
        layout = QVBoxLayout()
        
        # Formulario de configuración
        form_group = QGroupBox("Configuración del Campo")
        form_layout = QFormLayout()
        
        # Nombre del campo
        self.txt_nombre = QLineEdit()
        self.txt_nombre.setPlaceholderText("Ej: cuenta, nombre_afiliado")
        if self.campo_existente:
            self.txt_nombre.setText(self.campo_existente.get('nombre', ''))
            self.txt_nombre.setEnabled(False)  # No editar nombre existente
        
        # Coordenadas
        coord_layout = QHBoxLayout()
        self.spin_x = QSpinBox()
        self.spin_x.setRange(0, 500)
        self.spin_x.setSuffix(" mm")
        self.spin_x.setValue(self.campo_existente.get('x', 50) if self.campo_existente else 50)
        
        self.spin_y = QSpinBox()
        self.spin_y.setRange(0, 500)
        self.spin_y.setSuffix(" mm")
        self.spin_y.setValue(self.campo_existente.get('y', 50) if self.campo_existente else 50)
        
        coord_layout.addWidget(QLabel("X:"))
        coord_layout.addWidget(self.spin_x)
        coord_layout.addWidget(QLabel("Y:"))
        coord_layout.addWidget(self.spin_y)
        
        # Dimensiones
        dim_layout = QHBoxLayout()
        self.spin_ancho = QSpinBox()
        self.spin_ancho.setRange(10, 200)
        self.spin_ancho.setSuffix(" mm")
        self.spin_ancho.setValue(self.campo_existente.get('width', 50) if self.campo_existente else 50)
        
        self.spin_alto = QSpinBox()
        self.spin_alto.setRange(5, 100)
        self.spin_alto.setSuffix(" mm")
        self.spin_alto.setValue(self.campo_existente.get('height', 10) if self.campo_existente else 10)
        
        dim_layout.addWidget(QLabel("Ancho:"))
        dim_layout.addWidget(self.spin_ancho)
        dim_layout.addWidget(QLabel("Alto:"))
        dim_layout.addWidget(self.spin_alto)
        
        # Estilo
        self.combo_alineacion = QComboBox()
        self.combo_alineacion.addItems(["left", "center", "right"])
        if self.campo_existente:
            self.combo_alineacion.setCurrentText(self.campo_existente.get('alignment', 'left'))
        
        self.spin_tamano_fuente = QSpinBox()
        self.spin_tamano_fuente.setRange(6, 72)
        self.spin_tamano_fuente.setValue(self.campo_existente.get('font_size', 10) if self.campo_existente else 10)
        
        self.check_negrita = QCheckBox("Texto en negrita")
        if self.campo_existente:
            self.check_negrita.setChecked(self.campo_existente.get('bold', False))
        
        # Formato
        self.combo_formato = QComboBox()
        self.combo_formato.addItems(["", "moneda", "porcentaje", "fecha", "mayusculas", "capitalize"])
        if self.campo_existente:
            self.combo_formato.setCurrentText(self.campo_existente.get('formato', ''))
        
        self.txt_valor_default = QLineEdit()
        self.txt_valor_default.setPlaceholderText("Valor por defecto si el campo está vacío")
        if self.campo_existente:
            self.txt_valor_default.setText(self.campo_existente.get('valor_default', ''))
        
        # Agregar al formulario
        form_layout.addRow("Nombre del campo *:", self.txt_nombre)
        form_layout.addRow("Posición:", coord_layout)
        form_layout.addRow("Dimensiones:", dim_layout)
        form_layout.addRow("Alineación:", self.combo_alineacion)
        form_layout.addRow("Tamaño fuente:", self.spin_tamano_fuente)
        form_layout.addRow("", self.check_negrita)
        form_layout.addRow("Formato:", self.combo_formato)
        form_layout.addRow("Valor por defecto:", self.txt_valor_default)
        
        form_group.setLayout(form_layout)
        layout.addWidget(form_group)
        
        # Botones
        button_layout = QHBoxLayout()
        
        btn_guardar = QPushButton("💾 Guardar Campo")
        btn_guardar.clicked.connect(self.aceptar)
        btn_guardar.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
            }
        """)
        
        btn_cancelar = QPushButton("❌ Cancelar")
        btn_cancelar.clicked.connect(self.reject)
        btn_cancelar.setStyleSheet("""
            QPushButton {
                background-color: #6c757d;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
            }
        """)
        
        button_layout.addWidget(btn_guardar)
        button_layout.addStretch()
        button_layout.addWidget(btn_cancelar)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
    
    def aceptar(self):
        """Valida y acepta la configuración"""
        nombre = self.txt_nombre.text().strip()
        if not nombre:
            QMessageBox.warning(self, "Error", "El nombre del campo es obligatorio")
            return
        
        self.campo_config = {
            'nombre': nombre,
            'x': self.spin_x.value(),
            'y': self.spin_y.value(),
            'width': self.spin_ancho.value(),
            'height': self.spin_alto.value(),
            'alignment': self.combo_alineacion.currentText(),
            'font_size': self.spin_tamano_fuente.value(),
            'bold': self.check_negrita.isChecked(),
            'formato': self.combo_formato.currentText(),
            'valor_default': self.txt_valor_default.text()
        }
        
        self.accept()
    
    def get_campo_config(self):
        return self.campo_config

class VistaPreviaPDF(QFrame):
    """Vista previa del PDF con campos dinámicos"""
    campo_seleccionado = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.campos = {}
        self.campo_activo = None
        self.setup_ui()
    
    def setup_ui(self):
        self.setFrameStyle(QFrame.Shape.StyledPanel)
        self.setStyleSheet("""
            VistaPreviaPDF {
                background-color: white;
                border: 2px solid #ddd;
            }
        """)
        self.setMinimumSize(600, 800)
    
    def cargar_campos(self, campos: dict):
        """Carga los campos para mostrar en vista previa"""
        self.campos = campos
        self.update()
    
    def mousePressEvent(self, event: QMouseEvent):
        """Maneja clics para seleccionar campos"""
        pos = event.pos()
        x_mm = pos.x() / 2.0  # Aproximación de escala
        y_mm = (self.height() - pos.y()) / 2.0
        
        # Buscar campo clickeado
        for nombre_campo, config in self.campos.items():
            campo_x = config.get('x', 0)
            campo_y = config.get('y', 0)
            campo_ancho = config.get('width', 50)
            campo_alto = config.get('height', 10)
            
            if (campo_x <= x_mm <= campo_x + campo_ancho and 
                campo_y <= y_mm <= campo_y + campo_alto):
                self.campo_activo = nombre_campo
                self.campo_seleccionado.emit(nombre_campo)
                self.update()
                break
    
    def paintEvent(self, event):
        """Dibuja la vista previa del PDF con campos"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Dibujar fondo de página A4 (escala reducida)
        escala = 2.0  # 2px = 1mm
        ancho_a4 = 210 * escala
        alto_a4 = 297 * escala
        
        # Centrar página
        margen_x = (self.width() - ancho_a4) / 2
        margen_y = (self.height() - alto_a4) / 2
        
        # Dibujar página
        painter.fillRect(margen_x, margen_y, ancho_a4, alto_a4, QColor(255, 255, 255))
        painter.setPen(QColor(200, 200, 200))
        painter.drawRect(margen_x, margen_y, ancho_a4, alto_a4)
        
        # Dibujar campos
        for nombre_campo, config in self.campos.items():
            x = margen_x + config.get('x', 0) * escala
            y = margen_y + (alto_a4 - config.get('y', 0) * escala)  # Invertir Y
            ancho = config.get('width', 50) * escala
            alto = config.get('height', 10) * escala
            
            # Color según si está activo
            if nombre_campo == self.campo_activo:
                painter.setBrush(QColor(173, 216, 230, 100))  # Azul claro
                painter.setPen(QColor(0, 0, 255))
            else:
                painter.setBrush(QColor(144, 238, 144, 80))  # Verde claro
                painter.setPen(QColor(0, 128, 0))
            
            painter.drawRect(x, y - alto, ancho, alto)
            
            # Dibujar nombre del campo
            painter.setPen(QColor(0, 0, 0))
            painter.drawText(x + 2, y - alto + 12, nombre_campo)

class EditorPlantillas(QWidget):
    """Editor visual de plantillas con sistema de coordenadas"""
    plantilla_guardada = pyqtSignal()
    
    def __init__(self, usuario, plantilla_id):
        super().__init__()
        self.usuario = usuario
        self.plantilla_id = plantilla_id
        self.plantilla = None
        self.campos = {}
        self.setup_ui()
        self.cargar_plantilla()
    
    def setup_ui(self):
        layout = QHBoxLayout()
        layout.setSpacing(15)
        
        # Panel izquierdo - Lista de campos
        panel_izquierdo = QFrame()
        panel_izquierdo.setFixedWidth(300)
        panel_layout = QVBoxLayout()
        
        # Lista de campos
        lbl_campos = QLabel("Campos Dinámicos")
        lbl_campos.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        panel_layout.addWidget(lbl_campos)
        
        self.lista_campos = QListWidget()
        self.lista_campos.itemClicked.connect(self.on_campo_seleccionado)
        panel_layout.addWidget(self.lista_campos)
        
        # Botones de campos
        btn_layout = QHBoxLayout()
        
        btn_agregar = QPushButton("➕ Agregar")
        btn_agregar.clicked.connect(self.agregar_campo)
        btn_agregar.setStyleSheet("background-color: #28a745; color: white;")
        
        btn_editar = QPushButton("✏️ Editar")
        btn_editar.clicked.connect(self.editar_campo)
        btn_editar.setStyleSheet("background-color: #ffc107; color: black;")
        
        btn_eliminar = QPushButton("🗑️ Eliminar")
        btn_eliminar.clicked.connect(self.eliminar_campo)
        btn_eliminar.setStyleSheet("background-color: #dc3545; color: white;")
        
        btn_layout.addWidget(btn_agregar)
        btn_layout.addWidget(btn_editar)
        btn_layout.addWidget(btn_eliminar)
        
        panel_layout.addLayout(btn_layout)
        
        # Información de la plantilla
        info_group = QGroupBox("Información")
        info_layout = QVBoxLayout()
        
        self.lbl_nombre = QLabel("")
        self.lbl_tipo = QLabel("")
        self.lbl_archivo = QLabel("")
        
        info_layout.addWidget(QLabel("Nombre:"))
        info_layout.addWidget(self.lbl_nombre)
        info_layout.addWidget(QLabel("Tipo:"))
        info_layout.addWidget(self.lbl_tipo)
        info_layout.addWidget(QLabel("Archivo:"))
        info_layout.addWidget(self.lbl_archivo)
        
        info_group.setLayout(info_layout)
        panel_layout.addWidget(info_group)
        
        # Botones de acción
        btn_guardar = QPushButton("💾 Guardar Plantilla")
        btn_guardar.clicked.connect(self.guardar_plantilla)
        btn_guardar.setStyleSheet("""
            QPushButton {
                background-color: #007bff;
                color: white;
                border: none;
                padding: 10px;
                font-weight: bold;
            }
        """)
        
        panel_layout.addWidget(btn_guardar)
        panel_layout.addStretch()
        
        panel_izquierdo.setLayout(panel_layout)
        layout.addWidget(panel_izquierdo)
        
        # Panel derecho - Vista previa
        panel_derecho = QFrame()
        panel_derecho_layout = QVBoxLayout()
        
        lbl_vista_previa = QLabel("Vista Previa - PDF")
        lbl_vista_previa.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        panel_derecho_layout.addWidget(lbl_vista_previa)
        
        self.vista_previa = VistaPreviaPDF()
        self.vista_previa.campo_seleccionado.connect(self.on_campo_vista_previa_seleccionado)
        panel_derecho_layout.addWidget(self.vista_previa)
        
        panel_derecho.setLayout(panel_derecho_layout)
        layout.addWidget(panel_derecho)
        
        self.setLayout(layout)
    
    def cargar_plantilla(self):
        """Carga los datos de la plantilla"""
        db = SessionLocal()
        try:
            self.plantilla = db.query(Plantilla).filter(Plantilla.id == self.plantilla_id).first()
            if self.plantilla:
                self.lbl_nombre.setText(self.plantilla.nombre)
                self.lbl_tipo.setText(self.plantilla.tipo_plantilla or "No especificado")
                self.lbl_archivo.setText(self.plantilla.ruta_archivo or "No especificado")
                
                # Cargar campos
                if self.plantilla.campos_json:
                    self.campos = self.plantilla.campos_json
                    self.actualizar_lista_campos()
                    self.vista_previa.cargar_campos(self.campos)
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error cargando plantilla: {str(e)}")
        finally:
            db.close()
    
    def actualizar_lista_campos(self):
        """Actualiza la lista de campos"""
        self.lista_campos.clear()
        for nombre_campo in self.campos.keys():
            item = QListWidgetItem(nombre_campo)
            self.lista_campos.addItem(item)
    
    def agregar_campo(self):
        """Abre diálogo para agregar nuevo campo"""
        dialogo = CampoDialog()
        if dialogo.exec():
            campo_config = dialogo.get_campo_config()
            nombre_campo = campo_config.pop('nombre')
            self.campos[nombre_campo] = campo_config
            self.actualizar_lista_campos()
            self.vista_previa.cargar_campos(self.campos)
    
    def editar_campo(self):
        """Edita el campo seleccionado"""
        item = self.lista_campos.currentItem()
        if not item:
            QMessageBox.warning(self, "Error", "Seleccione un campo para editar")
            return
        
        nombre_campo = item.text()
        campo_existente = self.campos.get(nombre_campo, {})
        campo_existente['nombre'] = nombre_campo
        
        dialogo = CampoDialog(campo_existente)
        if dialogo.exec():
            nuevo_config = dialogo.get_campo_config()
            nuevo_nombre = nuevo_config.pop('nombre')
            
            # Si cambió el nombre, eliminar el viejo y crear nuevo
            if nuevo_nombre != nombre_campo:
                del self.campos[nombre_campo]
            
            self.campos[nuevo_nombre] = nuevo_config
            self.actualizar_lista_campos()
            self.vista_previa.cargar_campos(self.campos)
    
    def eliminar_campo(self):
        """Elimina el campo seleccionado"""
        item = self.lista_campos.currentItem()
        if not item:
            QMessageBox.warning(self, "Error", "Seleccione un campo para eliminar")
            return
        
        nombre_campo = item.text()
        reply = QMessageBox.question(
            self, "Confirmar",
            f"¿Está seguro de eliminar el campo '{nombre_campo}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            del self.campos[nombre_campo]
            self.actualizar_lista_campos()
            self.vista_previa.cargar_campos(self.campos)
    
    def on_campo_seleccionado(self, item):
        """Cuando se selecciona un campo en la lista"""
        nombre_campo = item.text()
        self.vista_previa.campo_activo = nombre_campo
        self.vista_previa.update()
    
    def on_campo_vista_previa_seleccionado(self, nombre_campo):
        """Cuando se selecciona un campo en la vista previa"""
        # Seleccionar en la lista
        items = self.lista_campos.findItems(nombre_campo, Qt.MatchFlag.MatchExactly)
        if items:
            self.lista_campos.setCurrentItem(items[0])
    
    def guardar_plantilla(self):
        """Guarda la configuración de la plantilla"""
        if not self.plantilla:
            return
        
        db = SessionLocal()
        try:
            self.plantilla.campos_json = self.campos
            db.commit()
            QMessageBox.information(self, "Éxito", "Plantilla guardada correctamente")
            self.plantilla_guardada.emit()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error guardando plantilla: {str(e)}")
            db.rollback()
        finally:
            db.close()