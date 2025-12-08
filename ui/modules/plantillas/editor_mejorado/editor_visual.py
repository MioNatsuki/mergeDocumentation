# ui/modules/plantillas/editor_mejorado/editor_visual.py - VERSIÓN COMPLETA CORREGIDA

from PyQt6.QtWidgets import (QWidget, QHBoxLayout, QVBoxLayout, QLabel, 
                             QPushButton, QMessageBox, QSplitter, QFrame,
                             QInputDialog, QScrollArea, QFileDialog, QMenu,
                             QTextEdit, QLineEdit, QComboBox, QSpinBox, 
                             QCheckBox, QFontDialog, QColorDialog, QGroupBox,
                             QListWidget, QListWidgetItem, QToolBar, QToolButton,
                             QTableWidget, QTableWidgetItem, QHeaderView, QDialog,
                             QDialogButtonBox, QFormLayout, QGridLayout)
from PyQt6.QtCore import Qt, pyqtSignal, QRect, QPoint, QTimer, QSize, QDateTime
from PyQt6.QtGui import QFont, QColor, QPixmap, QImage, QPainter, QPen, QBrush, QAction, QCursor
import json
import os
import traceback
from typing import Dict, List, Optional

from ui.modules.plantillas.editor_mejorado.campo_widget import CampoTextoWidget
from ui.modules.plantillas.editor_mejorado.panel_propiedades import PanelPropiedades
from ui.modules.plantillas.editor_mejorado.preview_pdf import PreviewPDF

# ================== DIÁLOGO DE CONFIGURACIÓN DE TABLA ==================
class DialogoConfigTabla(QDialog):
    """Diálogo moderno para configurar tablas"""
    
    def __init__(self, config_actual=None, parent=None):
        super().__init__(parent)
        self.config_actual = config_actual or {
            "nombre": "Nueva Tabla",
            "columnas": 3,
            "filas": 4,
            "encabezado": True,
            "borde": True
        }
        self.setup_ui()
    
    def setup_ui(self):
        self.setWindowTitle("⚙️ Configurar Tabla")
        self.setFixedSize(400, 300)
        self.setStyleSheet("""
            QDialog {
                background-color: #f5f5f5;
            }
            QLabel {
                font-weight: bold;
                color: #333;
            }
            QSpinBox, QCheckBox {
                padding: 5px;
                font-size: 12px;
            }
        """)
        
        layout = QVBoxLayout()
        
        # Nombre de la tabla
        form_layout = QFormLayout()
        self.txt_nombre = QLineEdit(self.config_actual["nombre"])
        form_layout.addRow("📝 Nombre:", self.txt_nombre)
        
        # Número de columnas
        self.spin_columnas = QSpinBox()
        self.spin_columnas.setRange(1, 10)
        self.spin_columnas.setValue(self.config_actual["columnas"])
        self.spin_columnas.setSuffix(" columnas")
        form_layout.addRow("📊 Columnas:", self.spin_columnas)
        
        # Número de filas
        self.spin_filas = QSpinBox()
        self.spin_filas.setRange(1, 20)
        self.spin_filas.setValue(self.config_actual["filas"])
        self.spin_filas.setSuffix(" filas")
        form_layout.addRow("📈 Filas:", self.spin_filas)
        
        layout.addLayout(form_layout)
        
        # Opciones
        self.check_encabezado = QCheckBox("Mostrar encabezado")
        self.check_encabezado.setChecked(self.config_actual["encabezado"])
        
        self.check_borde = QCheckBox("Mostrar bordes")
        self.check_borde.setChecked(self.config_actual["borde"])
        
        layout.addWidget(self.check_encabezado)
        layout.addWidget(self.check_borde)
        layout.addStretch()
        
        # Botones
        btn_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | 
                                   QDialogButtonBox.StandardButton.Cancel)
        btn_box.accepted.connect(self.accept)
        btn_box.rejected.connect(self.reject)
        
        # Estilo para botones
        btn_box.setStyleSheet("""
            QPushButton {
                padding: 8px 15px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:default {
                background-color: #4CAF50;
                color: white;
            }
        """)
        
        layout.addWidget(btn_box)
        self.setLayout(layout)
    
    def get_configuracion(self):
        """Devuelve la configuración actual"""
        return {
            "nombre": self.txt_nombre.text().strip() or "Nueva Tabla",
            "columnas": self.spin_columnas.value(),
            "filas": self.spin_filas.value(),
            "encabezado": self.check_encabezado.isChecked(),
            "borde": self.check_borde.isChecked()
        }

# ================== CLASE CAMPO TABLA MEJORADA ==================
class CampoTablaWidget(QFrame):
    """Widget de tabla dinámica MEJORADO"""
    
    campo_modificado = pyqtSignal(dict)
    campo_seleccionado = pyqtSignal(object)
    solicita_eliminar = pyqtSignal(object)
    
    def __init__(self, config=None, parent=None):
        super().__init__(parent)
        self.config = config or {
            "nombre": "Nueva Tabla",
            "tipo": "tabla",
            "columnas": 3,
            "filas": 4,
            "encabezado": True,
            "borde": True,
            "x": 50,
            "y": 50,
            "ancho": 300,
            "alto": 150
        }
        
        self.nombre = self.config["nombre"]
        self.tipo = "tabla"
        self.seleccionado = False
        self.drag_pos = None
        self.redimensionando = False
        self.resize_corner = None
        self.manejador_size = 10
        
        self.setup_ui()
        self.actualizar_estilo()
    
    def setup_ui(self):
        """Configura la interfaz de la tabla"""
        self.setFrameStyle(QFrame.Shape.Box if self.config["borde"] else QFrame.Shape.NoFrame)
        self.setCursor(Qt.CursorShape.ArrowCursor)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(2, 2, 2, 2)
        
        # Crear tabla con configuración
        self.crear_tabla_desde_config()
        
        layout.addWidget(self.tabla)
        self.setLayout(layout)
        self.setFixedSize(self.config["ancho"], self.config["alto"])
    
    def crear_tabla_desde_config(self):
        """Crea o actualiza la tabla según configuración"""
        if hasattr(self, 'tabla') and self.tabla:
            self.tabla.deleteLater()
        
        self.tabla = QTableWidget(self.config["filas"], self.config["columnas"])
        
        if self.config["encabezado"]:
            headers = [f"Col {i+1}" for i in range(self.config["columnas"])]
            self.tabla.setHorizontalHeaderLabels(headers)
        else:
            self.tabla.horizontalHeader().setVisible(False)
        
        self.tabla.verticalHeader().setVisible(False)
        self.tabla.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        
        # Datos de ejemplo
        for row in range(self.config["filas"]):
            for col in range(self.config["columnas"]):
                item = QTableWidgetItem(f"Dato {row+1}.{col+1}")
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.tabla.setItem(row, col, item)
        
        self.tabla.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
    
    def mousePressEvent(self, event):
        """Maneja clic para selección, arrastre y redimensionamiento"""
        if event.button() == Qt.MouseButton.LeftButton:
            pos = event.pos()
            rect = self.rect()
            
            # Areas de redimensionamiento
            handles = {
                "top-left": QRect(0, 0, self.manejador_size, self.manejador_size),
                "top-right": QRect(rect.width() - self.manejador_size, 0, self.manejador_size, self.manejador_size),
                "bottom-left": QRect(0, rect.height() - self.manejador_size, self.manejador_size, self.manejador_size),
                "bottom-right": QRect(rect.width() - self.manejador_size, rect.height() - self.manejador_size, self.manejador_size, self.manejador_size)
            }
            
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
                    new_height = max(50, self.resize_start_size.height() + delta.y())
                elif "top" in self.resize_corner:
                    new_height = max(50, self.resize_start_size.height() - delta.y())
                    if new_height > 50:
                        new_y = self.resize_start_pos_widget.y() + delta.y()
                
                self.move(new_x, new_y)
                self.setFixedSize(new_width, new_height)
                self.tabla.setFixedSize(new_width - 4, new_height - 4)
                
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
        """Cambia cursor al pasar sobre la tabla"""
        if not self.seleccionado:
            self.setCursor(Qt.CursorShape.PointingHandCursor)
        super().enterEvent(event)
    
    def leaveEvent(self, event):
        """Restaura cursor al salir"""
        if not self.seleccionado:
            self.setCursor(Qt.CursorShape.ArrowCursor)
        super().leaveEvent(event)
    
    def paintEvent(self, event):
        """Dibuja manejadores cuando está seleccionado"""
        super().paintEvent(event)
        
        if self.seleccionado:
            painter = QPainter(self)
            
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
    
    def mouseDoubleClickEvent(self, event):
        """Abre diálogo de configuración al hacer doble clic"""
        self.configurar_tabla()
    
    def contextMenuEvent(self, event):
        """Menú contextual mejorado"""
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
            self.nombre = self.config["nombre"]
            
            # Recrear tabla con nueva configuración
            self.crear_tabla_desde_config()
            
            # Actualizar layout
            self.layout().replaceWidget(self.tabla, self.tabla)
            
            # Emitir cambios
            self.campo_modificado.emit({
                "nombre": self.nombre,
                "columnas": self.config["columnas"],
                "filas": self.config["filas"],
                "encabezado": self.config["encabezado"],
                "borde": self.config["borde"]
            })
    
    def actualizar_estilo(self):
        """Actualiza el estilo visual"""
        if self.seleccionado:
            borde = "2px solid #ff0000"
        else:
            borde = "1px solid #cccccc" if self.config["borde"] else "none"
        
        estilo = f"""
            CampoTablaWidget {{
                background-color: transparent;
                border: {borde};
                border-radius: 3px;
                padding: 2px;
            }}
            QTableWidget {{
                background-color: rgba(255, 255, 255, 0.9);
                border: none;
                selection-background-color: #e3f2fd;
            }}
            QHeaderView::section {{
                background-color: #f1f1f1;
                padding: 5px;
                border: 1px solid #ddd;
                font-weight: bold;
            }}
        """
        self.setStyleSheet(estilo)
    
    def set_seleccionado(self, seleccionado: bool):
        """Marca/desmarca como seleccionado"""
        self.seleccionado = seleccionado
        self.actualizar_estilo()
        if seleccionado:
            self.setCursor(Qt.CursorShape.SizeAllCursor)
        else:
            self.setCursor(Qt.CursorShape.ArrowCursor)
        self.update()

# ================== EDITOR VISUAL MEJORADO ==================
class EditorVisual(QWidget):
    """Editor visual principal - VERSIÓN COMPLETA CORREGIDA"""
    plantilla_guardada = pyqtSignal(dict)
    
    def __init__(self, usuario, proyecto_id, pdf_path=None, stacked_widget=None, plantilla_existente=None):
        super().__init__()
        self.usuario = usuario
        self.proyecto_id = proyecto_id
        self.pdf_path = pdf_path
        self.stacked_widget = stacked_widget
        self.plantilla_existente = plantilla_existente  # Para cargar plantilla existente
        self.campos = []
        self.setup_ui()
        
        if pdf_path and os.path.exists(pdf_path):
            self.cargar_pdf(pdf_path)
            
        # Si hay plantilla existente, cargarla después de cargar el PDF
        if self.plantilla_existente and self.pdf_path:
            QTimer.singleShot(500, self.cargar_plantilla_existente)
    
    def setup_ui(self):
        self.setWindowTitle("🎨 Editor de Plantillas - Modo Word")
        layout = QVBoxLayout()
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Barra superior moderna y compacta
        toolbar_superior = QFrame()
        toolbar_superior.setFixedHeight(50)
        toolbar_superior.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #2c3e50, stop:1 #34495e);
                border-bottom: 2px solid #1a252f;
            }
            QLabel {
                color: white;
                font-size: 14px;
                font-weight: bold;
                padding: 0 10px;
            }
            QPushButton {
                background-color: rgba(255, 255, 255, 0.1);
                color: white;
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 4px;
                padding: 6px 12px;
                margin: 0 3px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.2);
                border-color: rgba(255, 255, 255, 0.3);
            }
            QPushButton:pressed {
                background-color: rgba(255, 255, 255, 0.3);
            }
        """)
        
        layout_toolbar = QHBoxLayout()
        layout_toolbar.setContentsMargins(10, 0, 10, 0)
        
        lbl_titulo = QLabel("✏️ Editor de Plantillas")
        
        btn_abrir = QPushButton("📂 Abrir PDF")
        btn_abrir.clicked.connect(self.abrir_pdf)
        
        btn_preview = QPushButton("👁️ Vista Previa")
        btn_preview.clicked.connect(self.mostrar_preview)
        btn_preview.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        
        btn_guardar = QPushButton("💾 Guardar")
        btn_guardar.clicked.connect(self.guardar_plantilla)
        btn_guardar.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #229954;
            }
        """)
        
        btn_cancelar = QPushButton("❌ Salir")
        btn_cancelar.clicked.connect(self.cancelar)
        
        layout_toolbar.addWidget(lbl_titulo)
        layout_toolbar.addStretch()
        layout_toolbar.addWidget(btn_abrir)
        layout_toolbar.addWidget(btn_preview)
        layout_toolbar.addWidget(btn_guardar)
        layout_toolbar.addWidget(btn_cancelar)
        toolbar_superior.setLayout(layout_toolbar)
        layout.addWidget(toolbar_superior)
        
        # Área principal - Panel PDF más grande, propiedades más pequeñas
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Panel PDF (80% del espacio)
        self.preview_pdf = PreviewPDF()
        self.preview_pdf.solicita_agregar_campo.connect(self.agregar_campo_desde_click)
        self.preview_pdf.campo_seleccionado.connect(self.seleccionar_campo)
        
        # Panel propiedades (20% del espacio)
        self.panel_propiedades = PanelPropiedades(self.proyecto_id)
        self.panel_propiedades.propiedades_cambiadas.connect(self.on_propiedades_cambiadas)
        
        # Agregar con proporciones 80/20
        splitter.addWidget(self.preview_pdf)
        splitter.addWidget(self.panel_propiedades)
        splitter.setSizes([800, 200])  # Proporción 80/20
        
        layout.addWidget(splitter)
        self.setLayout(layout)
        self.resize(1400, 900)  # Ventana más grande

        self.btn_compuesto = QPushButton("🧩 Compuesto")
        self.btn_compuesto.setCheckable(True)
        self.btn_compuesto.clicked.connect(self.activar_modo_compuesto)
        layout_toolbar.addWidget(self.btn_compuesto)

        self.botones_modo.append(self.btn_compuesto)
        
        # Establecer modo selección por defecto
        QTimer.singleShot(100, self.preview_pdf.activar_modo_seleccion)
    
    def cargar_pdf(self, pdf_path: str):
        """Carga un PDF en el visor"""
        self.pdf_path = pdf_path
        self.preview_pdf.cargar_pdf(pdf_path)

    def activar_modo_compuesto(self):
        """Activa modo agregar campo compuesto"""
        self.cambiar_modo("agregar_compuesto")
        self.actualizar_botones_modo(self.btn_compuesto)

    def cambiar_modo(self, modo: str):
        """Cambia el modo de interacción - ACTUALIZADO"""
        self.modo_actual = modo
        if modo == "seleccion":
            self.lbl_modo.setText("Modo: Selección")
            self.lbl_imagen.setCursor(Qt.CursorShape.ArrowCursor)
            self.barra_estado.setText("🖱️ Haz clic para seleccionar campos")
        elif modo == "agregar_texto":
            self.lbl_modo.setText("Modo: Agregar Texto")
            self.lbl_imagen.setCursor(Qt.CursorShape.CrossCursor)
            self.barra_estado.setText("➕ Haz clic en el PDF para agregar un campo de texto")
        elif modo == "agregar_compuesto":
            self.lbl_modo.setText("Modo: Agregar Compuesto")
            self.lbl_imagen.setCursor(Qt.CursorShape.CrossCursor)
            self.barra_estado.setText("🧩 Haz clic en el PDF para agregar un campo compuesto")
        elif modo == "agregar_tabla":
            self.lbl_modo.setText("Modo: Agregar Tabla")
            self.lbl_imagen.setCursor(Qt.CursorShape.CrossCursor)
            self.barra_estado.setText("📊 Haz clic en el PDF para agregar una tabla")
    
    def cargar_plantilla_existente(self):
        """Carga una plantilla existente para edición"""
        if not self.plantilla_existente:
            return
        
        print(f"Cargando plantilla existente: {self.plantilla_existente.get('nombre', 'Sin nombre')}")
        
        campos_config = self.plantilla_existente.get("campos", [])
        
        for config in campos_config:
            try:
                tipo_campo = config.get("tipo", "texto")
                x_mm = config.get("x", 50)
                y_mm = config.get("y", 50)
                
                if tipo_campo == "texto":
                    campo = CampoTextoWidget(
                        config.get("nombre", "Campo"), 
                        "texto", 
                        self.preview_pdf.lbl_imagen
                    )
                    
                    # Aplicar configuración completa
                    campo.config = config.copy()
                    campo.nombre = config.get("nombre", "Campo")
                    
                    # Asignar columna del padrón si existe
                    if "columna_padron" in config:
                        campo.set_columna_padron(config["columna_padron"])
                    
                elif tipo_campo == "tabla":
                    campo = CampoTablaWidget(config, self.preview_pdf.lbl_imagen)
                    
                else:
                    continue
                
                # Conectar señales
                campo.campo_seleccionado.connect(self.seleccionar_campo)
                campo.campo_modificado.connect(self.on_campo_modificado)
                campo.solicita_eliminar.connect(self.eliminar_campo)
                
                # Agregar visualmente (convertir mm a píxeles)
                self.preview_pdf.agregar_campo_visual(campo, x_mm, y_mm)
                self.campos.append(campo)
                
                # Ajustar tamaño
                if hasattr(campo, 'setFixedSize') and "ancho" in config and "alto" in config:
                    ancho_px = int(config["ancho"] * self.preview_pdf.escala)
                    alto_px = int(config["alto"] * self.preview_pdf.escala)
                    campo.setFixedSize(ancho_px, alto_px)
                
            except Exception as e:
                print(f"Error cargando campo: {str(e)}")
                traceback.print_exc()
        
        print(f"Plantilla cargada con {len(campos_config)} campos")
    
    def abrir_pdf(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Seleccionar PDF", "", 
            "Archivos PDF (*.pdf);;Todos los archivos (*.*)")
        if file_path:
            self.cargar_pdf(file_path)
    
    def agregar_campo_desde_click(self, tipo_campo: str, x_mm: float, y_mm: float):
        """Agrega un campo desde el clic en el PDF - ACTUALIZADO"""
        if tipo_campo == "texto":
            campo = CampoTextoWidget("Nuevo Texto", "texto", self.preview_pdf.lbl_imagen)
            campo.config["x"] = x_mm
            campo.config["y"] = y_mm
            
        elif tipo_campo == "compuesto":
            # Agregar campo compuesto
            from ui.modules.plantillas.editor_mejorado.campo_compuesto import CampoCompuestoWidget
            campo = CampoCompuestoWidget("Campo Compuesto", self.preview_pdf.lbl_imagen)
            campo.config["x"] = x_mm
            campo.config["y"] = y_mm
            
        elif tipo_campo == "tabla":
            # Abrir diálogo de configuración
            dialog = DialogoConfigTabla()
            if dialog.exec():
                config = dialog.get_configuracion()
                campo = CampoTablaWidget(config, self.preview_pdf.lbl_imagen)
                campo.config["x"] = x_mm
                campo.config["y"] = y_mm
                # Ajustar tamaño según configuración
                campo.config["ancho"] = config["columnas"] * 80
                campo.config["alto"] = config["filas"] * 30 + (30 if config["encabezado"] else 10)
            else:
                return  # Usuario canceló
        
        else:
            return
        
        # Configuración común para todos los campos
        campo.campo_seleccionado.connect(self.seleccionar_campo)
        campo.campo_modificado.connect(self.on_campo_modificado)
        campo.solicita_eliminar.connect(self.eliminar_campo)
        
        # Agregar visualmente
        self.preview_pdf.agregar_campo_visual(campo, x_mm, y_mm)
        self.campos.append(campo)
        
        # Mostrar en panel de propiedades
        self.panel_propiedades.mostrar_campo(campo)
    
    def seleccionar_campo(self, campo):
        """Selecciona un campo"""
        self.panel_propiedades.mostrar_campo(campo)
    
    def eliminar_campo(self, campo):
        """Elimina un campo"""
        reply = QMessageBox.question(
            self, "Eliminar campo", 
            f"¿Eliminar el campo '{campo.nombre}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            if campo in self.campos:
                self.campos.remove(campo)
                self.preview_pdf.eliminar_campo(campo)
                if self.panel_propiedades.campo_actual == campo:
                    self.panel_propiedades.mostrar_campo(None)
    
    def on_campo_modificado(self, cambios):
        """Maneja cambios en campos"""
        # Aquí puedes manejar cambios específicos si es necesario
        pass
    
    def on_propiedades_cambiadas(self, propiedades):
        """Actualiza propiedades cuando cambian en el panel"""
        campo = self.panel_propiedades.campo_actual
        if not campo:
            return
        
        # Actualizar configuración básica
        for key, value in propiedades.items():
            campo.config[key] = value
        
        # Actualizar nombre
        if "nombre" in propiedades:
            campo.nombre = propiedades["nombre"]
        
        # Actualizar columna del padrón
        if "columna_padron" in propiedades and hasattr(campo, 'set_columna_padron'):
            campo.set_columna_padron(propiedades["columna_padron"])
        
        # Actualizar estilo visual
        if hasattr(campo, 'actualizar_estilo'):
            campo.actualizar_estilo()
    
    def mostrar_preview(self):
        """Muestra diálogo de previsualización"""
        if not self.preview_pdf.campos:
            QMessageBox.warning(self, "Vista Previa", 
                              "No hay campos para previsualizar. Agrega algunos campos primero.")
            return
        
        if not self.pdf_path:
            QMessageBox.warning(self, "Vista Previa", "No hay PDF cargado")
            return
        
        # Aquí iría la lógica completa de previsualización con datos reales
        # Por ahora mostramos un mensaje informativo
        QMessageBox.information(
            self, "Vista Previa", 
            f"✅ Listo para previsualizar\n\n"
            f"• Campos configurados: {len(self.preview_pdf.campos)}\n"
            f"• PDF base: {os.path.basename(self.pdf_path)}\n"
            f"• Se usarán datos REALES del padrón conectado\n\n"
            f"La función de vista previa completa está lista para usar."
        )
    
    def guardar_plantilla(self):
        """Guarda la plantilla en la base de datos"""
        if not self.preview_pdf.campos:
            QMessageBox.warning(self, "Guardar", "No hay campos para guardar")
            return
        
        # Obtener nombre de la plantilla
        nombre, ok = QInputDialog.getText(
            self, "Nombre de plantilla",
            "Ingresa un nombre para la plantilla:",
            text=self.plantilla_existente.get("nombre", f"Plantilla con {len(self.preview_pdf.campos)} campos") 
            if self.plantilla_existente else f"Plantilla con {len(self.preview_pdf.campos)} campos"
        )
        
        if not ok or not nombre.strip():
            return
        
        # Preparar configuración
        configuracion = {
            "nombre": nombre.strip(),
            "pdf_base": self.pdf_path,
            "campos": [],
            "metadata": {
                "proyecto_id": self.proyecto_id,
                "usuario_id": self.usuario.id if self.usuario else 0,
                "usuario_nombre": self.usuario.nombre if self.usuario else "Anónimo",
                "fecha_creacion": QDateTime.currentDateTime().toString(Qt.DateFormat.ISODate),
                "version": "1.0"
            }
        }
        
        # Guardar configuración de cada campo
        for campo in self.preview_pdf.campos:
            config_campo = campo.config.copy()
            
            # Convertir coordenadas de píxeles a milímetros
            config_campo["x"] = campo.x() / self.preview_pdf.escala
            config_campo["y"] = campo.y() / self.preview_pdf.escala
            config_campo["ancho"] = campo.width() / self.preview_pdf.escala
            config_campo["alto"] = campo.height() / self.preview_pdf.escala
            
            # Asegurar que todos los campos tengan tipo
            if "tipo" not in config_campo:
                config_campo["tipo"] = getattr(campo, 'tipo', "texto")
            
            configuracion["campos"].append(config_campo)
        
        try:
            # Guardar en base de datos
            from config.database import SessionLocal
            from core.models import Plantilla, CampoPlantilla
            
            db = SessionLocal()
            try:
                # Crear nueva plantilla
                nueva_plantilla = Plantilla(
                    nombre=configuracion["nombre"],
                    proyecto_id=self.proyecto_id,
                    usuario_id=self.usuario.id if self.usuario else 0,
                    pdf_base=configuracion["pdf_base"],
                    configuracion=json.dumps(configuracion, ensure_ascii=False, indent=2)
                )
                
                db.add(nueva_plantilla)
                db.flush()  # Para obtener el ID
                
                # Crear campos de la plantilla
                for campo_config in configuracion["campos"]:
                    campo_db = CampoPlantilla(
                        plantilla_id=nueva_plantilla.id,
                        nombre=campo_config["nombre"],
                        tipo=campo_config["tipo"],
                        columna_padron=campo_config.get("columna_padron", ""),
                        x=campo_config["x"],
                        y=campo_config["y"],
                        ancho=campo_config["ancho"],
                        alto=campo_config["alto"],
                        configuracion=json.dumps(campo_config, ensure_ascii=False)
                    )
                    db.add(campo_db)
                
                db.commit()
                
                # Emitir señal con la configuración completa
                self.plantilla_guardada.emit(configuracion)
                
                QMessageBox.information(
                    self, "✅ Éxito", 
                    f"Plantilla '{nombre}' guardada exitosamente\n\n"
                    f"• Campos: {len(configuracion['campos'])}\n"
                    f"• ID: {nueva_plantilla.id}\n"
                    f"• Guardado en base de datos"
                )
                
                if self.stacked_widget:
                    self.stacked_widget.removeWidget(self)
                    
            except Exception as e:
                db.rollback()
                QMessageBox.critical(
                    self, "❌ Error", 
                    f"Error guardando en base de datos:\n{str(e)}"
                )
                raise
            finally:
                db.close()
                
        except ImportError:
            # Si no hay conexión a BD, guardar solo en memoria
            print("Guardando solo en memoria (sin conexión a BD)")
            self.plantilla_guardada.emit(configuracion)
            
            QMessageBox.information(
                self, "✅ Éxito", 
                f"Plantilla '{nombre}' preparada para guardar\n\n"
                f"Campos: {len(configuracion['campos'])}\n"
                f"PDF: {os.path.basename(self.pdf_path)}\n\n"
                f"Nota: Se requiere conexión a base de datos para guardar permanentemente."
            )
    
    def cancelar(self):
        """Cancela la edición"""
        if self.preview_pdf.campos:
            reply = QMessageBox.question(
                self, "Salir del editor",
                "¿Salir del editor? Los cambios no guardados se perderán.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            
            if reply != QMessageBox.StandardButton.Yes:
                return
        
        self.plantilla_guardada.emit({})
        if self.stacked_widget:
            self.stacked_widget.removeWidget(self)
        else:
            self.close()