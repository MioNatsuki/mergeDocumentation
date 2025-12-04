# ui/modules/plantillas/editor_mejorado/editor_visual.py - MEJORADO

from PyQt6.QtWidgets import (QWidget, QHBoxLayout, QVBoxLayout, QLabel, 
                             QPushButton, QMessageBox, QSplitter, QFrame,
                             QInputDialog, QScrollArea, QFileDialog, QMenu,
                             QTextEdit, QLineEdit, QComboBox, QSpinBox, 
                             QCheckBox, QFontDialog, QColorDialog, QGroupBox,
                             QListWidget, QListWidgetItem, QToolBar, QToolButton,
                             QTableWidget, QTableWidgetItem, QHeaderView)
from PyQt6.QtCore import Qt, pyqtSignal, QRect, QPoint
from PyQt6.QtGui import QFont, QColor, QPixmap, QImage, QPainter, QPen, QBrush, QAction
import json
import os
import traceback
from typing import Dict, List, Optional

# Importar con try/except para mejor manejo de errores
try:
    import fitz  # PyMuPDF
    PDF_SUPPORT = True
except ImportError:
    PDF_SUPPORT = False

try:
    from PIL import Image
    IMAGE_SUPPORT = True
except ImportError:
    IMAGE_SUPPORT = False

# ================== CLASE CAMPO DE TEXTO MEJORADA ==================
class CampoTextoWidget(QFrame):
    """Widget de campo de texto arrastrable y redimensionable - SIN FONDO"""
    
    campo_modificado = pyqtSignal(dict)
    campo_seleccionado = pyqtSignal(object)
    solicita_eliminar = pyqtSignal(object)
    
    def __init__(self, nombre: str = "Nuevo Campo", tipo: str = "texto", parent=None):
        super().__init__(parent)
        self.nombre = nombre
        self.tipo = tipo
        self.config = {
            "nombre": nombre,
            "tipo": tipo,
            "texto": nombre,
            "fuente": "Arial",
            "tamano": 12,
            "color": "#000000",
            "negrita": False,
            "cursiva": False,
            "alineacion": "left",
            "formato": "texto",
            "columna_padron": "",
            "x": 50,
            "y": 50,
            "ancho": 100,
            "alto": 30,
            "margen": 2,
            "borde": True
        }
        
        self.seleccionado = False
        self.drag_pos = None
        self.redimensionando = False
        self.resize_corner = None
        self.resize_handles = []
        
        self.setup_ui()
        self.actualizar_estilo()
        
    def setup_ui(self):
        """Configura la interfaz del campo - SIN FONDO"""
        self.setFrameStyle(QFrame.Shape.Box)
        self.setCursor(Qt.CursorShape.SizeAllCursor)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(2, 2, 2, 2)
        
        self.label = QLabel(self.config["texto"])
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.label)
        
        self.setLayout(layout)
        self.setFixedSize(self.config["ancho"], self.config["alto"])
    
    def mousePressEvent(self, event):
        """Maneja clic en el campo con mejor detección de redimensionamiento"""
        if event.button() == Qt.MouseButton.LeftButton:
            pos = event.pos()
            
            # Definir áreas de redimensionamiento (esquinas de 8x8px)
            rect = self.rect()
            handles = {
                "top-left": QRect(0, 0, 8, 8),
                "top-right": QRect(rect.width() - 8, 0, 8, 8),
                "bottom-left": QRect(0, rect.height() - 8, 8, 8),
                "bottom-right": QRect(rect.width() - 8, rect.height() - 8, 8, 8),
                "top": QRect(rect.width()//2 - 4, 0, 8, 8),
                "bottom": QRect(rect.width()//2 - 4, rect.height() - 8, 8, 8),
                "left": QRect(0, rect.height()//2 - 4, 8, 8),
                "right": QRect(rect.width() - 8, rect.height()//2 - 4, 8, 8)
            }
            
            # Verificar si el clic fue en un handle
            for corner_name, handle_rect in handles.items():
                if handle_rect.contains(pos):
                    self.redimensionando = True
                    self.resize_corner = corner_name
                    self.resize_start_pos = event.globalPosition().toPoint()
                    self.resize_start_size = self.size()
                    self.resize_start_pos_widget = self.pos()
                    return
            
            # Si no es redimensionar, es arrastre
            self.drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            self.campo_seleccionado.emit(self)
            event.accept()
            
    def mouseMoveEvent(self, event):
        """Maneja movimiento del mouse para arrastre y redimensionamiento"""
        if event.buttons() & Qt.MouseButton.LeftButton:
            if self.redimensionando and self.resize_corner:
                # Redimensionar
                delta = event.globalPosition().toPoint() - self.resize_start_pos
                
                new_width = self.resize_start_size.width()
                new_height = self.resize_start_size.height()
                new_x = self.x()
                new_y = self.y()
                
                # Lógica de redimensionamiento según la esquina
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
                
                # Aplicar cambios
                self.move(new_x, new_y)
                self.setFixedSize(new_width, new_height)
                
                # Actualizar configuración
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
                
                # Actualizar posición
                self.config["x"] = new_pos.x()
                self.config["y"] = new_pos.y()
                self.campo_modificado.emit({"x": new_pos.x(), "y": new_pos.y()})
    
    def mouseReleaseEvent(self, event):
        """Maneja liberación del mouse"""
        self.redimensionando = False
        self.drag_pos = None
        self.resize_corner = None
    
    def paintEvent(self, event):
        """Dibuja bordes y handles de redimensionamiento cuando está seleccionado"""
        super().paintEvent(event)
        
        if self.seleccionado:
            painter = QPainter(self)
            painter.setPen(QPen(QColor(255, 0, 0), 2, Qt.PenStyle.DashLine))
            
            # Dibujar borde rojo discontinuo
            painter.drawRect(1, 1, self.width()-2, self.height()-2)
            
            # Dibujar handles de redimensionamiento (puntos negros)
            painter.setPen(QPen(QColor(0, 0, 0), 1))
            painter.setBrush(QBrush(QColor(0, 0, 0)))
            
            # Esquinas
            handle_size = 6
            rect = self.rect()
            
            # Esquina superior izquierda
            painter.drawRect(0, 0, handle_size, handle_size)
            # Esquina superior derecha
            painter.drawRect(rect.width() - handle_size, 0, handle_size, handle_size)
            # Esquina inferior izquierda
            painter.drawRect(0, rect.height() - handle_size, handle_size, handle_size)
            # Esquina inferior derecha
            painter.drawRect(rect.width() - handle_size, rect.height() - handle_size, handle_size, handle_size)
            
            # Centros de los bordes
            # Centro superior
            painter.drawRect(rect.width()//2 - handle_size//2, 0, handle_size, handle_size)
            # Centro inferior
            painter.drawRect(rect.width()//2 - handle_size//2, rect.height() - handle_size, handle_size, handle_size)
            # Centro izquierdo
            painter.drawRect(0, rect.height()//2 - handle_size//2, handle_size, handle_size)
            # Centro derecho
            painter.drawRect(rect.width() - handle_size, rect.height()//2 - handle_size//2, handle_size, handle_size)
    
    def mouseDoubleClickEvent(self, event):
        """Doble clic para editar texto"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.editar_texto()
    
    def contextMenuEvent(self, event):
        """Menú contextual con opciones - AGREGAR ELIMINAR"""
        menu = QMenu(self)
        
        action_editar = QAction("✏️ Editar texto", self)
        action_editar.triggered.connect(self.editar_texto)
        
        action_fuente = QAction("🔤 Cambiar fuente", self)
        action_fuente.triggered.connect(self.cambiar_fuente)
        
        action_color = QAction("🎨 Cambiar color", self)
        action_color.triggered.connect(self.cambiar_color)
        
        # NUEVA OPCIÓN: Eliminar campo
        action_eliminar = QAction("🗑️ Eliminar campo", self)
        action_eliminar.triggered.connect(lambda: self.solicita_eliminar.emit(self))
        
        menu.addAction(action_editar)
        menu.addAction(action_fuente)
        menu.addAction(action_color)
        menu.addSeparator()
        menu.addAction(action_eliminar)  # Añadir opción eliminar
        
        menu.exec(event.globalPosition().toPoint())
    
    def editar_texto(self):
        """Diálogo para editar texto"""
        texto, ok = QInputDialog.getText(
            self, "Editar texto",
            "Texto del campo:",
            text=self.config["texto"]
        )
        
        if ok and texto:
            self.config["texto"] = texto
            self.label.setText(texto)
            self.campo_modificado.emit({"texto": texto})
    
    def cambiar_fuente(self):
        """Diálogo para cambiar fuente"""
        font, ok = QFontDialog.getFont()
        if ok:
            self.config["fuente"] = font.family()
            self.config["tamano"] = font.pointSize()
            self.config["negrita"] = font.bold()
            self.config["cursiva"] = font.italic()
            
            self.label.setFont(font)
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
        """Actualiza el estilo visual del campo - SIN FONDO"""
        # Sin fondo, solo borde delgado cuando no está seleccionado
        if self.seleccionado:
            borde = "1px solid #ff0000"
        else:
            borde = "1px solid #cccccc"
        
        estilo = f"""
            CampoTextoWidget {{
                background-color: transparent;
                border: {borde};
                border-radius: 2px;
                padding: 2px;
            }}
            QLabel {{
                color: {self.config['color']};
                font-family: '{self.config['fuente']}';
                font-size: {self.config['tamano']}pt;
                font-weight: {'bold' if self.config['negrita'] else 'normal'};
                font-style: {'italic' if self.config['cursiva'] else 'normal'};
            }}
        """
        self.setStyleSheet(estilo)
    
    def set_seleccionado(self, seleccionado: bool):
        """Marca/desmarca el campo como seleccionado"""
        self.seleccionado = seleccionado
        self.actualizar_estilo()
        self.update()  # Forzar repaint para mostrar handles

# ================== CLASE CAMPO TABLA ==================
class CampoTablaWidget(QFrame):
    """Widget de tabla dinámica con columnas configurables"""
    
    campo_modificado = pyqtSignal(dict)
    campo_seleccionado = pyqtSignal(object)
    solicita_eliminar = pyqtSignal(object)
    
    def __init__(self, nombre: str = "Nueva Tabla", parent=None):
        super().__init__(parent)
        self.nombre = nombre
        self.tipo = "tabla"
        self.config = {
            "nombre": nombre,
            "tipo": "tabla",
            "columnas": ["Columna 1", "Columna 2", "Columna 3"],
            "filas_ejemplo": 3,
            "encabezado": True,
            "borde": True,
            "x": 50,
            "y": 50,
            "ancho": 300,
            "alto": 150
        }
        
        self.seleccionado = False
        self.drag_pos = None
        self.redimensionando = False
        self.resize_corner = None
        
        self.setup_ui()
        self.actualizar_estilo()
        
    def setup_ui(self):
        """Configura la interfaz de la tabla"""
        self.setFrameStyle(QFrame.Shape.Box)
        self.setCursor(Qt.CursorShape.SizeAllCursor)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(2, 2, 2, 2)
        
        # Tabla
        self.tabla = QTableWidget(self.config["filas_ejemplo"], len(self.config["columnas"]))
        self.tabla.setHorizontalHeaderLabels(self.config["columnas"])
        self.tabla.verticalHeader().setVisible(False)
        self.tabla.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        
        # Rellenar con datos de ejemplo
        for row in range(self.config["filas_ejemplo"]):
            for col in range(len(self.config["columnas"])):
                self.tabla.setItem(row, col, QTableWidgetItem(f"Dato {row+1}-{col+1}"))
        
        layout.addWidget(self.tabla)
        self.setLayout(layout)
        self.setFixedSize(self.config["ancho"], self.config["alto"])
    
    def mousePressEvent(self, event):
        """Maneja clic en la tabla"""
        if event.button() == Qt.MouseButton.LeftButton:
            pos = event.pos()
            
            # Definir áreas de redimensionamiento
            rect = self.rect()
            handles = {
                "top-left": QRect(0, 0, 8, 8),
                "top-right": QRect(rect.width() - 8, 0, 8, 8),
                "bottom-left": QRect(0, rect.height() - 8, 8, 8),
                "bottom-right": QRect(rect.width() - 8, rect.height() - 8, 8, 8)
            }
            
            # Verificar si el clic fue en un handle
            for corner_name, handle_rect in handles.items():
                if handle_rect.contains(pos):
                    self.redimensionando = True
                    self.resize_corner = corner_name
                    self.resize_start_pos = event.globalPosition().toPoint()
                    self.resize_start_size = self.size()
                    self.resize_start_pos_widget = self.pos()
                    return
            
            # Si no es redimensionar, es arrastre
            self.drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            self.campo_seleccionado.emit(self)
            event.accept()
    
    def mouseMoveEvent(self, event):
        """Maneja movimiento del mouse para arrastre y redimensionamiento"""
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
                    new_height = max(50, self.resize_start_size.height() + delta.y())
                elif "top" in self.resize_corner:
                    new_height = max(50, self.resize_start_size.height() - delta.y())
                    if new_height > 50:
                        new_y = self.resize_start_pos_widget.y() + delta.y()
                
                # Aplicar cambios
                self.move(new_x, new_y)
                self.setFixedSize(new_width, new_height)
                self.tabla.setFixedSize(new_width - 4, new_height - 4)
                
                # Actualizar configuración
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
                
                # Actualizar posición
                self.config["x"] = new_pos.x()
                self.config["y"] = new_pos.y()
                self.campo_modificado.emit({"x": new_pos.x(), "y": new_pos.y()})
    
    def mouseReleaseEvent(self, event):
        """Maneja liberación del mouse"""
        self.redimensionando = False
        self.drag_pos = None
        self.resize_corner = None
    
    def contextMenuEvent(self, event):
        """Menú contextual para tabla"""
        menu = QMenu(self)
        
        action_config_columnas = QAction("⚙️ Configurar columnas", self)
        action_config_columnas.triggered.connect(self.configurar_columnas)
        
        action_eliminar = QAction("🗑️ Eliminar tabla", self)
        action_eliminar.triggered.connect(lambda: self.solicita_eliminar.emit(self))
        
        menu.addAction(action_config_columnas)
        menu.addSeparator()
        menu.addAction(action_eliminar)
        
        menu.exec(event.globalPosition().toPoint())
    
    def configurar_columnas(self):
        """Configura las columnas de la tabla"""
        from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QListWidget, QPushButton
        
        dialog = QDialog(self)
        dialog.setWindowTitle("Configurar Columnas")
        dialog.setFixedSize(400, 300)
        
        layout = QVBoxLayout()
        
        # Lista de columnas actuales
        list_widget = QListWidget()
        for columna in self.config["columnas"]:
            list_widget.addItem(columna)
        
        # Botones para agregar/eliminar columnas
        btn_layout = QHBoxLayout()
        
        btn_agregar = QPushButton("➕ Agregar columna")
        btn_agregar.clicked.connect(lambda: self.agregar_columna(list_widget))
        
        btn_eliminar = QPushButton("➖ Eliminar seleccionada")
        btn_eliminar.clicked.connect(lambda: self.eliminar_columna(list_widget))
        
        btn_guardar = QPushButton("💾 Guardar")
        btn_guardar.clicked.connect(lambda: self.guardar_columnas(list_widget, dialog))
        
        btn_layout.addWidget(btn_agregar)
        btn_layout.addWidget(btn_eliminar)
        btn_layout.addStretch()
        btn_layout.addWidget(btn_guardar)
        
        layout.addWidget(QLabel("Columnas de la tabla:"))
        layout.addWidget(list_widget)
        layout.addLayout(btn_layout)
        
        dialog.setLayout(layout)
        dialog.exec()
    
    def agregar_columna(self, list_widget):
        """Agrega una nueva columna"""
        nombre, ok = QInputDialog.getText(self, "Nueva Columna", "Nombre de la columna:")
        if ok and nombre:
            list_widget.addItem(nombre)
    
    def eliminar_columna(self, list_widget):
        """Elimina la columna seleccionada"""
        current_item = list_widget.currentItem()
        if current_item:
            list_widget.takeItem(list_widget.row(current_item))
    
    def guardar_columnas(self, list_widget, dialog):
        """Guarda las columnas configuradas"""
        nuevas_columnas = []
        for i in range(list_widget.count()):
            nuevas_columnas.append(list_widget.item(i).text())
        
        self.config["columnas"] = nuevas_columnas
        self.tabla.setColumnCount(len(nuevas_columnas))
        self.tabla.setHorizontalHeaderLabels(nuevas_columnas)
        
        dialog.accept()
        self.campo_modificado.emit({"columnas": nuevas_columnas})
    
    def actualizar_estilo(self):
        """Actualiza el estilo de la tabla"""
        if self.seleccionado:
            borde = "2px solid #ff0000"
        else:
            borde = "1px solid #cccccc"
        
        estilo = f"""
            CampoTablaWidget {{
                background-color: transparent;
                border: {borde};
                border-radius: 2px;
                padding: 2px;
            }}
            QTableWidget {{
                background-color: rgba(255, 255, 255, 0.8);
                border: 1px solid #ddd;
            }}
        """
        self.setStyleSheet(estilo)
    
    def set_seleccionado(self, seleccionado: bool):
        """Marca/desmarca la tabla como seleccionada"""
        self.seleccionado = seleccionado
        self.actualizar_estilo()
        self.update()

# ================== PREVIEW PDF MEJORADO ==================
class PreviewPDF(QFrame):
    """Área para previsualizar PDF con campos - MEJORADO"""
    
    click_posicion = pyqtSignal(float, float)  # x, y en mm
    campo_seleccionado = pyqtSignal(object)
    solicita_agregar_campo = pyqtSignal(str, float, float)  # tipo, x, y
    
    def __init__(self, parent=None):
        super().__init__()
        self.pdf_path = None
        self.campos = []  # Lista de campos en el PDF
        self.campo_seleccionado_actual = None
        self.imagen_pdf = None
        self.escala = 2.0  # px por mm
        self.modo_actual = "seleccion"  # seleccion, agregar_texto, agregar_tabla
        
        self.setup_ui()
        
    def setup_ui(self):
        """Configura la interfaz"""
        self.setFrameStyle(QFrame.Shape.StyledPanel)
        self.setStyleSheet("""
            PreviewPDF {
                background-color: #f0f0f0;
                border: 1px solid #ccc;
            }
        """)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Barra de herramientas
        toolbar = QFrame()
        toolbar.setStyleSheet("background-color: #e0e0e0; padding: 5px;")
        toolbar_layout = QHBoxLayout()
        
        self.lbl_modo = QLabel("👆 Modo: Selección")
        
        self.btn_texto = QPushButton("📝 Agregar Texto")
        self.btn_texto.clicked.connect(lambda: self.cambiar_modo("agregar_texto"))
        
        self.btn_tabla = QPushButton("📊 Agregar Tabla")
        self.btn_tabla.clicked.connect(lambda: self.cambiar_modo("agregar_tabla"))
        
        self.btn_seleccion = QPushButton("👆 Seleccionar")
        self.btn_seleccion.clicked.connect(lambda: self.cambiar_modo("seleccion"))
        
        toolbar_layout.addWidget(self.lbl_modo)
        toolbar_layout.addWidget(self.btn_seleccion)
        toolbar_layout.addWidget(self.btn_texto)
        toolbar_layout.addWidget(self.btn_tabla)
        toolbar_layout.addStretch()
        
        toolbar.setLayout(toolbar_layout)
        layout.addWidget(toolbar)
        
        # Área de scroll para el PDF
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        
        self.container = QWidget()
        self.container_layout = QVBoxLayout()
        self.container_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.lbl_imagen = QLabel("📄 Selecciona un PDF para comenzar")
        self.lbl_imagen.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_imagen.setStyleSheet("""
            QLabel {
                background-color: white;
                color: #666;
                font-size: 16px;
                padding: 50px;
                border: 2px dashed #999;
                border-radius: 10px;
                min-width: 600px;
                min-height: 400px;
            }
        """)
        self.lbl_imagen.mousePressEvent = self.on_click_imagen
        
        self.container_layout.addWidget(self.lbl_imagen)
        self.container.setLayout(self.container_layout)
        self.scroll_area.setWidget(self.container)
        
        layout.addWidget(self.scroll_area)
        self.setLayout(layout)
    
    def cambiar_modo(self, modo: str):
        """Cambia el modo de interacción"""
        self.modo_actual = modo
        
        if modo == "seleccion":
            self.lbl_modo.setText("👆 Modo: Selección")
            self.lbl_imagen.setCursor(Qt.CursorShape.ArrowCursor)
        elif modo == "agregar_texto":
            self.lbl_modo.setText("📝 Modo: Agregar Texto")
            self.lbl_imagen.setCursor(Qt.CursorShape.CrossCursor)
        elif modo == "agregar_tabla":
            self.lbl_modo.setText("📊 Modo: Agregar Tabla")
            self.lbl_imagen.setCursor(Qt.CursorShape.CrossCursor)
    
    def cargar_pdf(self, pdf_path: str):
        """Carga y muestra un PDF"""
        if not PDF_SUPPORT:
            self.mostrar_error("PyMuPDF no está instalado. Instala con: pip install PyMuPDF")
            return
        
        self.pdf_path = pdf_path
        
        try:
            doc = fitz.open(pdf_path)
            pagina = doc[0]
            
            # Renderizar a buena resolución
            zoom = 1.5  # 150% para mejor visualización
            mat = fitz.Matrix(zoom, zoom)
            pix = pagina.get_pixmap(matrix=mat, alpha=False)
            
            # Convertir a QImage
            img_format = QImage.Format.Format_RGB888
            qimage = QImage(pix.samples, pix.width, pix.height, pix.stride, img_format)
            
            # Guardar como QPixmap
            self.imagen_pdf = QPixmap.fromImage(qimage)
            
            # Calcular escala (px por mm)
            ancho_px = pix.width
            alto_px = pix.height
            ancho_mm = 210 * zoom  # A4 ancho en mm * zoom
            self.escala = ancho_px / ancho_mm
            
            # Mostrar imagen
            self.lbl_imagen.setPixmap(self.imagen_pdf)
            self.lbl_imagen.setFixedSize(ancho_px, alto_px)
            
            # Limpiar estilo
            self.lbl_imagen.setStyleSheet("background-color: white;")
            
            doc.close()
            
            print(f"PDF cargado: {pdf_path}")
            print(f"Dimensiones: {ancho_px}x{alto_px}px, Escala: {self.escala:.2f}px/mm")
            
        except Exception as e:
            self.mostrar_error(f"Error cargando PDF: {str(e)}")
            traceback.print_exc()
    
    def mostrar_error(self, mensaje: str):
        """Muestra mensaje de error"""
        self.lbl_imagen.setText(f"❌ Error\n\n{mensaje}")
        self.lbl_imagen.setStyleSheet("""
            QLabel {
                background-color: #ffe6e6;
                color: #cc0000;
                font-size: 14px;
                padding: 50px;
                border: 2px solid #ff9999;
                border-radius: 10px;
                min-width: 600px;
                min-height: 400px;
            }
        """)
    
    def on_click_imagen(self, event):
        """Maneja clics en la imagen del PDF"""
        if not self.imagen_pdf:
            return
        
        pos = event.pos()
        
        if self.modo_actual == "seleccion":
            # Seleccionar campo existente
            for campo in self.campos:
                if campo.geometry().contains(pos):
                    self.seleccionar_campo(campo)
                    return
        elif self.modo_actual == "agregar_texto":
            # Agregar nuevo campo de texto
            x_mm = pos.x() / self.escala
            y_mm = pos.y() / self.escala
            
            print(f"DEBUG: Click para agregar texto en ({x_mm}, {y_mm}) mm")
            self.solicita_agregar_campo.emit("texto", x_mm, y_mm)
            
        elif self.modo_actual == "agregar_tabla":
            # Agregar nueva tabla
            x_mm = pos.x() / self.escala
            y_mm = pos.y() / self.escala
            
            print(f"DEBUG: Click para agregar tabla en ({x_mm}, {y_mm}) mm")
            self.solicita_agregar_campo.emit("tabla", x_mm, y_mm)
    
    def seleccionar_campo(self, campo):
        """Selecciona un campo"""
        if self.campo_seleccionado_actual:
            self.campo_seleccionado_actual.set_seleccionado(False)
        
        self.campo_seleccionado_actual = campo
        campo.set_seleccionado(True)
        self.campo_seleccionado.emit(campo)
    
    def agregar_campo_visual(self, campo_widget, x_mm: float, y_mm: float):
        """Agrega un campo visual al preview"""
        self.campos.append(campo_widget)
        campo_widget.setParent(self.lbl_imagen)
        
        # Convertir mm a píxeles
        x_px = int(x_mm * self.escala)
        y_px = int(y_mm * self.escala)
        
        campo_widget.move(x_px, y_px)
        campo_widget.show()
        
        print(f"DEBUG: Campo agregado en posición: "
              f"({x_mm}mm, {y_mm}mm) = ({x_px}px, {y_px}px)")
        
        # Seleccionar automáticamente el nuevo campo
        self.seleccionar_campo(campo_widget)
    
    def eliminar_campo(self, campo):
        """Elimina un campo"""
        if campo in self.campos:
            self.campos.remove(campo)
            campo.deleteLater()
            
            if self.campo_seleccionado_actual == campo:
                self.campo_seleccionado_actual = None

# ================== PANEL PROPIEDADES CON COLUMNAS REALES ==================
class PanelPropiedades(QFrame):  # ← Cambiar de QWidget a QFrame
    """Panel de propiedades con columnas REALES del padrón"""
    
    propiedades_cambiadas = pyqtSignal(dict)
    
    def __init__(self, proyecto_id):
        super().__init__()
        self.proyecto_id = proyecto_id
        self.campo_actual = None
        self.columnas_padron = []
        self.setup_ui()
        self.cargar_columnas_reales()
    
    def setup_ui(self):
        """Configura la interfaz"""
        self.setFrameStyle(QFrame.Shape.StyledPanel)  # ← Ahora sí funciona
        self.setStyleSheet("""
            PanelPropiedades {
                background-color: white;
                border: 1px solid #ddd;
                padding: 10px;
                /* Eliminar transform que no existe en CSS de Qt */
            }
        """)
        
        layout = QVBoxLayout()
        
        # Título
        self.lbl_titulo = QLabel("⚙️ Propiedades del Campo")
        self.lbl_titulo.setStyleSheet("font-size: 14px; font-weight: bold;")
        layout.addWidget(self.lbl_titulo)
        
        # Scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        
        widget_contenido = QWidget()
        contenido_layout = QVBoxLayout()
        
        # Nombre del campo
        self.txt_nombre = QLineEdit()
        self.txt_nombre.setPlaceholderText("Nombre del campo...")
        self.txt_nombre.textChanged.connect(self.emitir_cambios)
        contenido_layout.addWidget(QLabel("Nombre:"))
        contenido_layout.addWidget(self.txt_nombre)
        
        # Texto
        self.txt_texto = QLineEdit()
        self.txt_texto.setPlaceholderText("Texto a mostrar...")
        self.txt_texto.textChanged.connect(self.emitir_cambios)
        contenido_layout.addWidget(QLabel("Texto:"))
        contenido_layout.addWidget(self.txt_texto)
        
        # COLUMNAS REALES DEL PADRÓN
        self.combo_columna = QComboBox()
        self.combo_columna.currentTextChanged.connect(self.emitir_cambios)  # ← Agregar conexión
        contenido_layout.addWidget(QLabel("Columna del Padrón:"))
        contenido_layout.addWidget(self.combo_columna)
        
        # Solo para campos de texto
        self.lbl_info_columna = QLabel("")
        self.lbl_info_columna.setStyleSheet("color: #666; font-size: 10px;")
        contenido_layout.addWidget(self.lbl_info_columna)
        
        # Botones de estilo
        layout_botones = QHBoxLayout()
        
        self.btn_fuente = QPushButton("🔤 Fuente")
        self.btn_fuente.clicked.connect(self.cambiar_fuente)
        
        self.btn_color = QPushButton("🎨 Color")
        self.btn_color.clicked.connect(self.cambiar_color)
        
        layout_botones.addWidget(self.btn_fuente)
        layout_botones.addWidget(self.btn_color)
        contenido_layout.addLayout(layout_botones)
        
        # Checkboxes
        self.check_negrita = QCheckBox("Negrita")
        self.check_negrita.stateChanged.connect(self.emitir_cambios)
        
        self.check_cursiva = QCheckBox("Cursiva")
        self.check_cursiva.stateChanged.connect(self.emitir_cambios)
        
        contenido_layout.addWidget(self.check_negrita)
        contenido_layout.addWidget(self.check_cursiva)
        
        widget_contenido.setLayout(contenido_layout)
        scroll.setWidget(widget_contenido)
        layout.addWidget(scroll)
        
        self.setLayout(layout)
    
    def cargar_columnas_reales(self):
        """Carga las columnas REALES del padrón del proyecto"""
        from config.database import SessionLocal
        from core.models import Proyecto
        from core.padron_service import PadronService
        
        db = SessionLocal()
        try:
            # Obtener el proyecto
            proyecto = db.query(Proyecto).filter(Proyecto.id == self.proyecto_id).first()
            if not proyecto or not proyecto.tabla_padron:
                print("DEBUG: Proyecto no encontrado o sin padrón")
                return
            
            print(f"DEBUG: Proyecto encontrado. UUID padrón: {proyecto.tabla_padron}")
            
            # Obtener las columnas REALES
            padron_service = PadronService(db)
            self.columnas_padron = padron_service.obtener_columnas_padron(proyecto.tabla_padron)
            
            print(f"DEBUG: Se encontraron {len(self.columnas_padron)} columnas reales")
            
            # Cargar en el combo
            self.combo_columna.clear()
            self.combo_columna.addItem("-- Selecciona columna --", None)
            
            for columna in self.columnas_padron:
                nombre = columna["nombre"]
                tipo = columna["tipo"]
                self.combo_columna.addItem(f"{nombre} ({tipo})", nombre)
            
        except Exception as e:
            print(f"ERROR cargando columnas reales: {e}")
            import traceback
            traceback.print_exc()
        finally:
            db.close()
    
    def cambiar_fuente(self):
        """Abre diálogo de fuente"""
        if self.campo_actual:
            self.campo_actual.cambiar_fuente()
    
    def cambiar_color(self):
        """Abre diálogo de color"""
        if self.campo_actual:
            self.campo_actual.cambiar_color()
    
    def emitir_cambios(self):
        """Emitir propiedades cuando cambian"""
        if self.campo_actual:
            props = {
                "nombre": self.txt_nombre.text(),
                "texto": self.txt_texto.text(),
                "columna_padron": self.combo_columna.currentData(),
                "negrita": self.check_negrita.isChecked(),
                "cursiva": self.check_cursiva.isChecked()
            }
            self.propiedades_cambiadas.emit(props)
    
    def mostrar_campo(self, campo):
        """Muestra propiedades de un campo"""
        self.campo_actual = campo
        
        if campo:
            self.txt_nombre.setText(campo.nombre)
            self.txt_texto.setText(campo.config.get("texto", ""))
            
            # Para tablas, ocultar algunos controles
            if campo.tipo == "tabla":
                self.txt_texto.setEnabled(False)
                self.combo_columna.setEnabled(False)
                self.lbl_info_columna.setText("Para tablas, configurar columnas desde el menú contextual")
            else:
                self.txt_texto.setEnabled(True)
                self.combo_columna.setEnabled(True)
                
                # Buscar columna en el combo
                columna = campo.config.get("columna_padron", "")
                index = self.combo_columna.findData(columna)
                if index >= 0:
                    self.combo_columna.setCurrentIndex(index)
                else:
                    self.combo_columna.setCurrentIndex(0)
                
                # Mostrar info de la columna si está seleccionada
                if columna:
                    for col in self.columnas_padron:
                        if col["nombre"] == columna:
                            tipo = col.get("tipo", "texto")
                            nullable = "NULL" if col.get("nullable") else "NOT NULL"
                            self.lbl_info_columna.setText(f"Tipo: {tipo} | {nullable}")
                            break
                    else:
                        self.lbl_info_columna.setText("")
                else:
                    self.lbl_info_columna.setText("")
            
            self.check_negrita.setChecked(campo.config.get("negrita", False))
            self.check_cursiva.setChecked(campo.config.get("cursiva", False))
            
            self.lbl_titulo.setText(f"⚙️ {campo.nombre} ({campo.tipo})")
        else:
            self.lbl_titulo.setText("⚙️ Propiedades del Campo")
            self.txt_nombre.setText("")
            self.txt_texto.setText("")
            self.combo_columna.setCurrentIndex(0)
            self.check_negrita.setChecked(False)
            self.check_cursiva.setChecked(False)
            self.lbl_info_columna.setText("")

# ================== EDITOR VISUAL MEJORADO ==================
class EditorVisual(QWidget):
    """Editor visual principal - MEJORADO"""
    
    plantilla_guardada = pyqtSignal(dict)
    
    def __init__(self, usuario, proyecto_id, pdf_path=None, stacked_widget=None):
        super().__init__()
        self.usuario = usuario
        self.proyecto_id = proyecto_id
        self.pdf_path = pdf_path
        self.stacked_widget = stacked_widget
        self.campos = []
        
        self.setup_ui()
        
        # Si se proporcionó un PDF, cargarlo
        if pdf_path and os.path.exists(pdf_path):
            self.cargar_pdf(pdf_path)
    
    def setup_ui(self):
        """Configura la interfaz del editor"""
        self.setWindowTitle("🎨 Editor de Plantillas")
        
        layout = QVBoxLayout()
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Barra superior
        toolbar_superior = QFrame()
        toolbar_superior.setStyleSheet("background-color: #2c3e50; padding: 10px;")
        layout_toolbar = QHBoxLayout()
        
        lbl_titulo = QLabel("Editor de Plantillas")
        lbl_titulo.setStyleSheet("color: white; font-size: 16px; font-weight: bold;")
        
        btn_abrir = QPushButton("📂 Abrir PDF")
        btn_abrir.clicked.connect(self.abrir_pdf)
        
        btn_guardar = QPushButton("💾 Guardar")
        btn_guardar.clicked.connect(self.guardar_plantilla)
        btn_guardar.setStyleSheet("background-color: #27ae60; color: white;")
        
        btn_cancelar = QPushButton("❌ Cancelar")
        btn_cancelar.clicked.connect(self.cancelar)
        btn_cancelar.setStyleSheet("background-color: #e74c3c; color: white;")
        
        layout_toolbar.addWidget(lbl_titulo)
        layout_toolbar.addStretch()
        layout_toolbar.addWidget(btn_abrir)
        layout_toolbar.addWidget(btn_guardar)
        layout_toolbar.addWidget(btn_cancelar)
        
        toolbar_superior.setLayout(layout_toolbar)
        layout.addWidget(toolbar_superior)
        
        # Área principal
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Panel izquierdo - Preview PDF MEJORADO
        self.preview_pdf = PreviewPDF()
        self.preview_pdf.solicita_agregar_campo.connect(self.agregar_campo_desde_click)
        self.preview_pdf.campo_seleccionado.connect(self.seleccionar_campo)
        splitter.addWidget(self.preview_pdf)
        
        # Panel derecho - Propiedades con columnas REALES
        self.panel_propiedades = PanelPropiedades(self.proyecto_id)
        self.panel_propiedades.propiedades_cambiadas.connect(self.on_propiedades_cambiadas)
        splitter.addWidget(self.panel_propiedades)
        
        # Configurar tamaños
        splitter.setSizes([700, 300])
        layout.addWidget(splitter)
        
        # Barra inferior
        barra_inferior = QFrame()
        barra_inferior.setStyleSheet("background-color: #34495e; padding: 5px;")
        layout_inferior = QHBoxLayout()
        
        self.lbl_estado = QLabel("Listo")
        self.lbl_estado.setStyleSheet("color: white;")
        
        self.lbl_info = QLabel("Haz clic en el PDF para agregar campos de texto o tablas")
        self.lbl_info.setStyleSheet("color: #bdc3c7; font-size: 12px;")
        
        layout_inferior.addWidget(self.lbl_estado)
        layout_inferior.addStretch()
        layout_inferior.addWidget(self.lbl_info)
        
        barra_inferior.setLayout(layout_inferior)
        layout.addWidget(barra_inferior)
        
        self.setLayout(layout)
        self.resize(1200, 800)
    
    def cargar_pdf(self, pdf_path: str):
        """Carga un PDF en el preview"""
        print(f"EditorVisual.cargar_pdf llamado con: {pdf_path}")
        self.pdf_path = pdf_path
        self.lbl_estado.setText(f"Cargando PDF: {os.path.basename(pdf_path)}")
        
        # Usar QTimer para procesar en el siguiente ciclo de eventos
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(100, lambda: self.preview_pdf.cargar_pdf(pdf_path))
        
        self.lbl_info.setText(f"PDF cargado. Usa los botones para crear campos o tablas.")
    
    def abrir_pdf(self):
        """Abre diálogo para seleccionar PDF"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Seleccionar PDF", "", "Archivos PDF (*.pdf)"
        )
        
        if file_path:
            self.cargar_pdf(file_path)
    
    def agregar_campo_desde_click(self, tipo_campo: str, x_mm: float, y_mm: float):
        """Agrega un campo cuando se hace clic en el PDF"""
        print(f"DEBUG: Agregando campo tipo {tipo_campo} en ({x_mm}, {y_mm})")
        
        if tipo_campo == "texto":
            campo = CampoTextoWidget("Nuevo Campo", "texto", self.preview_pdf.lbl_imagen)
            campo.config["x"] = x_mm
            campo.config["y"] = y_mm
        elif tipo_campo == "tabla":
            campo = CampoTablaWidget("Nueva Tabla", self.preview_pdf.lbl_imagen)
            campo.config["x"] = x_mm
            campo.config["y"] = y_mm
        else:
            return
        
        # Conectar señales
        campo.campo_seleccionado.connect(self.seleccionar_campo)
        campo.campo_modificado.connect(self.on_campo_modificado)
        campo.solicita_eliminar.connect(self.eliminar_campo)
        
        # Agregar al preview
        self.preview_pdf.agregar_campo_visual(campo, x_mm, y_mm)
        
        # Agregar a nuestra lista
        self.campos.append(campo)
        
        # Actualizar panel de propiedades
        self.panel_propiedades.mostrar_campo(campo)
        
        self.lbl_estado.setText(f"Campo {tipo_campo} agregado")
    
    def seleccionar_campo(self, campo):
        """Selecciona un campo"""
        self.panel_propiedades.mostrar_campo(campo)
    
    def eliminar_campo(self, campo):
        """Elimina un campo"""
        if campo in self.campos:
            self.campos.remove(campo)
            self.preview_pdf.eliminar_campo(campo)
            
            # Limpiar panel de propiedades si el campo eliminado era el seleccionado
            if self.panel_propiedades.campo_actual == campo:
                self.panel_propiedades.campo_actual = None
                self.panel_propiedades.lbl_titulo.setText("⚙️ Propiedades del Campo")
                self.panel_propiedades.txt_nombre.setText("")
                self.panel_propiedades.txt_texto.setText("")
                self.panel_propiedades.combo_columna.setCurrentIndex(0)
                self.panel_propiedades.check_negrita.setChecked(False)
                self.panel_propiedades.check_cursiva.setChecked(False)
                self.panel_propiedades.lbl_info_columna.setText("")
            
            self.lbl_estado.setText(f"Campo {campo.nombre} eliminado")
    
    def on_campo_modificado(self, cambios):
        """Cuando se modifica un campo"""
        print(f"DEBUG: Campo modificado: {cambios}")
    
    def on_propiedades_cambiadas(self, propiedades):
        """Cuando cambian las propiedades de un campo"""
        campo = self.panel_propiedades.campo_actual
        if campo:
            # Actualizar configuración del campo
            for key, value in propiedades.items():
                campo.config[key] = value
            
            # Actualizar visualmente
            if "texto" in propiedades:
                campo.label.setText(propiedades["texto"])
                campo.config["texto"] = propiedades["texto"]
            
            if "nombre" in propiedades:
                campo.nombre = propiedades["nombre"]
                campo.config["nombre"] = propiedades["nombre"]
            
            # Forzar actualización del campo
            campo.update()
    
    def guardar_plantilla(self):
        """Guarda la plantilla"""
        if not self.preview_pdf.campos:
            QMessageBox.warning(self, "Guardar", "No hay campos para guardar")
            return
        
        # Pedir nombre
        nombre, ok = QInputDialog.getText(
            self, "Nombre de plantilla",
            "Ingresa un nombre para la plantilla:",
            text=f"Plantilla con {len(self.preview_pdf.campos)} campos"
        )
        
        if not ok or not nombre.strip():
            return
        
        # Recopilar configuración
        configuracion = {
            "nombre": nombre.strip(),
            "pdf_base": self.pdf_path,
            "campos": [],
            "metadata": {
                "proyecto_id": self.proyecto_id,
                "usuario": self.usuario.id if self.usuario else 0
            }
        }
        
        # Guardar configuración de cada campo
        for campo in self.preview_pdf.campos:
            # Convertir coordenadas de píxeles a mm
            config_campo = campo.config.copy()
            config_campo["x"] = campo.x() / self.preview_pdf.escala
            config_campo["y"] = campo.y() / self.preview_pdf.escala
            config_campo["ancho"] = campo.width() / self.preview_pdf.escala
            config_campo["alto"] = campo.height() / self.preview_pdf.escala
            
            configuracion["campos"].append(config_campo)
        
        # Emitir señal
        self.plantilla_guardada.emit(configuracion)
        
        QMessageBox.information(
            self, "Éxito",
            f"✅ Plantilla '{nombre}' guardada con {len(configuracion['campos'])} campos"
        )
        
        # Cerrar editor si está en stacked widget
        if self.stacked_widget:
            self.stacked_widget.removeWidget(self)
    
    def cancelar(self):
        """Cancela la edición"""
        reply = QMessageBox.question(
            self, "Cancelar",
            "¿Está seguro de cancelar? Los cambios no guardados se perderán.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # Emitir señal vacía para indicar cancelación
            self.plantilla_guardada.emit({})
            
            # Cerrar editor si está en stacked widget
            if self.stacked_widget:
                self.stacked_widget.removeWidget(self)
    
    def closeEvent(self, event):
        """Maneja cierre de ventana"""
        self.cancelar()
        event.accept()