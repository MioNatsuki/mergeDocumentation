# ui/modules/plantillas/editor_mejorado/editor_visual.py - MEJORADO CON PREVISUALIZACIÓN

from PyQt6.QtWidgets import (QWidget, QHBoxLayout, QVBoxLayout, QLabel, 
                             QPushButton, QMessageBox, QSplitter, QFrame,
                             QInputDialog, QScrollArea, QFileDialog, QMenu,
                             QTextEdit, QLineEdit, QComboBox, QSpinBox, 
                             QCheckBox, QFontDialog, QColorDialog, QGroupBox,
                             QListWidget, QListWidgetItem, QToolBar, QToolButton,
                             QTableWidget, QTableWidgetItem, QHeaderView, QDialog)
from PyQt6.QtCore import Qt, pyqtSignal, QRect, QPoint, QTimer
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
    """Widget de campo de texto SIN fondo, SIN placeholder"""
    
    campo_modificado = pyqtSignal(dict)
    campo_seleccionado = pyqtSignal(object)
    solicita_eliminar = pyqtSignal(object)
    
    def __init__(self, nombre: str = "Nuevo Campo", tipo: str = "texto", parent=None):
        super().__init__(parent)
        self.nombre = nombre
        self.tipo = tipo
        self.columna_padron = ""  # ← NUEVO: Cada campo tendrá su propia columna
        
        self.config = {
            "nombre": nombre,
            "tipo": tipo,
            "columna_padron": "",  # ← INICIALIZAR VACÍO
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
            "borde": False  # ← SIN BORDE POR DEFECTO
        }
        
        self.seleccionado = False
        self.drag_pos = None
        self.redimensionando = False
        self.resize_corner = None
        
        self.setup_ui()
        self.actualizar_estilo()
    
    def setup_ui(self):
        """Configura SIN fondo, SIN borde"""
        self.setFrameStyle(QFrame.Shape.NoFrame)  # ← SIN BORDE
        self.setCursor(Qt.CursorShape.SizeAllCursor)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)  # ← SIN MÁRGENES
        
        self.label = QLabel()
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.actualizar_texto()  # ← NUEVO MÉTODO
        layout.addWidget(self.label)
        
        self.setLayout(layout)
        self.setFixedSize(self.config["ancho"], self.config["alto"])
    
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
            
            # Areas de redimensionamiento
            handles = {
                "top-left": QRect(0, 0, 8, 8),
                "top-right": QRect(rect.width() - 8, 0, 8, 8),
                "bottom-left": QRect(0, rect.height() - 8, 8, 8),
                "bottom-right": QRect(rect.width() - 8, rect.height() - 8, 8, 8),
            }
            
            # Verificar si es redimensionamiento
            for corner_name, handle_rect in handles.items():
                if handle_rect.contains(pos):
                    self.redimensionando = True
                    self.resize_corner = corner_name
                    self.resize_start_pos = event.globalPosition().toPoint()
                    self.resize_start_size = self.size()
                    self.resize_start_pos_widget = self.pos()
                    return
            
            # Si no, es arrastre normal
            self.drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            self.campo_seleccionado.emit(self)
            event.accept()
    
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
    
    def paintEvent(self, event):
        """Dibuja solo cuando está seleccionado"""
        super().paintEvent(event)
        
        if self.seleccionado:
            painter = QPainter(self)
            painter.setPen(QPen(QColor(255, 0, 0), 1, Qt.PenStyle.DashLine))
            painter.drawRect(0, 0, self.width()-1, self.height()-1)
    
    def mouseDoubleClickEvent(self, event):
        """NO hacer nada - eliminamos edición de placeholder"""
        pass
    
    def contextMenuEvent(self, event):
        """Menú contextual SIMPLIFICADO - solo eliminar"""
        menu = QMenu(self)
        
        action_eliminar = QAction("🗑️ Eliminar campo", self)
        action_eliminar.triggered.connect(self.eliminar_campo)
        
        menu.addAction(action_eliminar)
        menu.exec(event.globalPos())
    
    def eliminar_campo(self):
        """Emitir señal para eliminar este campo"""
        self.solicita_eliminar.emit(self)
    
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
        """Estilo SIN fondo, solo texto"""
        if self.seleccionado:
            borde = "1px dashed #ff0000"
        else:
            borde = "none"
        
        # Color del texto según si tiene columna asignada
        if self.columna_padron:
            color_texto = "#0066cc"  # Azul cuando tiene columna
        else:
            color_texto = "#666666"  # Gris cuando no tiene
        
        estilo = f"""
            CampoTextoWidget {{
                background-color: transparent;
                border: {borde};
                padding: 0px;
            }}
            QLabel {{
                background-color: transparent;
                color: {color_texto};
                font-family: '{self.config['fuente']}';
                font-size: {self.config['tamano']}pt;
                font-weight: {'bold' if self.config['negrita'] else 'normal'};
                font-style: {'italic' if self.config['cursiva'] else 'normal'};
                padding: 2px;
            }}
        """
        self.setStyleSheet(estilo)
    
    def set_seleccionado(self, seleccionado: bool):
        """Marca/desmarca como seleccionado"""
        self.seleccionado = seleccionado
        self.actualizar_estilo()
        self.update()

# ================== CLASE CAMPO TABLA (SIN CAMBIOS MAYORES) ==================
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
        
        self.tabla = QTableWidget(self.config["filas_ejemplo"], len(self.config["columnas"]))
        self.tabla.setHorizontalHeaderLabels(self.config["columnas"])
        self.tabla.verticalHeader().setVisible(False)
        self.tabla.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        
        for row in range(self.config["filas_ejemplo"]):
            for col in range(len(self.config["columnas"])):
                self.tabla.setItem(row, col, QTableWidgetItem(f"Dato {row+1}-{col+1}"))
        
        layout.addWidget(self.tabla)
        self.setLayout(layout)
        self.setFixedSize(self.config["ancho"], self.config["alto"])
    
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            pos = event.pos()
            rect = self.rect()
            handles = {
                "top-left": QRect(0, 0, 8, 8),
                "top-right": QRect(rect.width() - 8, 0, 8, 8),
                "bottom-left": QRect(0, rect.height() - 8, 8, 8),
                "bottom-right": QRect(rect.width() - 8, rect.height() - 8, 8, 8)
            }
            
            for corner_name, handle_rect in handles.items():
                if handle_rect.contains(pos):
                    self.redimensionando = True
                    self.resize_corner = corner_name
                    self.resize_start_pos = event.globalPosition().toPoint()
                    self.resize_start_size = self.size()
                    self.resize_start_pos_widget = self.pos()
                    return
            
            self.drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            self.campo_seleccionado.emit(self)
            event.accept()
    
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
    
    def contextMenuEvent(self, event):
        menu = QMenu(self)
        action_config_columnas = QAction("⚙️ Configurar columnas", self)
        action_config_columnas.triggered.connect(self.configurar_columnas)
        action_eliminar = QAction("🗑️ Eliminar tabla", self)
        action_eliminar.triggered.connect(lambda: self.solicita_eliminar.emit(self))
        menu.addAction(action_config_columnas)
        menu.addSeparator()
        menu.addAction(action_eliminar)
        # Usar globalPos() en lugar de globalPosition()
        menu.exec(event.globalPos())
    
    def configurar_columnas(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Configurar Columnas")
        dialog.setFixedSize(400, 300)
        layout = QVBoxLayout()
        list_widget = QListWidget()
        for columna in self.config["columnas"]:
            list_widget.addItem(columna)
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
        nombre, ok = QInputDialog.getText(self, "Nueva Columna", "Nombre de la columna:")
        if ok and nombre:
            list_widget.addItem(nombre)
    
    def eliminar_columna(self, list_widget):
        current_item = list_widget.currentItem()
        if current_item:
            list_widget.takeItem(list_widget.row(current_item))
    
    def guardar_columnas(self, list_widget, dialog):
        nuevas_columnas = []
        for i in range(list_widget.count()):
            nuevas_columnas.append(list_widget.item(i).text())
        self.config["columnas"] = nuevas_columnas
        self.tabla.setColumnCount(len(nuevas_columnas))
        self.tabla.setHorizontalHeaderLabels(nuevas_columnas)
        dialog.accept()
        self.campo_modificado.emit({"columnas": nuevas_columnas})
    
    def actualizar_estilo(self):
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
        self.seleccionado = seleccionado
        self.actualizar_estilo()
        self.update()

# ================== PREVIEW PDF MEJORADO ==================
class PreviewPDF(QFrame):
    """Área para previsualizar PDF con campos"""
    
    click_posicion = pyqtSignal(float, float)
    campo_seleccionado = pyqtSignal(object)
    solicita_agregar_campo = pyqtSignal(str, float, float)
    
    def __init__(self, parent=None):
        super().__init__()
        self.pdf_path = None
        self.campos = []
        self.campo_seleccionado_actual = None
        self.imagen_pdf = None
        self.escala = 2.0
        self.modo_actual = "seleccion"
        self.setup_ui()
        
    def setup_ui(self):
        self.setFrameStyle(QFrame.Shape.StyledPanel)
        self.setStyleSheet("PreviewPDF { background-color: #f0f0f0; border: 1px solid #ccc; }")
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        
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
        if not PDF_SUPPORT:
            self.mostrar_error("PyMuPDF no está instalado. Instala con: pip install PyMuPDF")
            return
        self.pdf_path = pdf_path
        try:
            doc = fitz.open(pdf_path)
            pagina = doc[0]
            zoom = 1.5
            mat = fitz.Matrix(zoom, zoom)
            pix = pagina.get_pixmap(matrix=mat, alpha=False)
            img_format = QImage.Format.Format_RGB888
            qimage = QImage(pix.samples, pix.width, pix.height, pix.stride, img_format)
            self.imagen_pdf = QPixmap.fromImage(qimage)
            ancho_px = pix.width
            alto_px = pix.height
            ancho_mm = 210 * zoom
            self.escala = ancho_px / ancho_mm
            self.lbl_imagen.setPixmap(self.imagen_pdf)
            self.lbl_imagen.setFixedSize(ancho_px, alto_px)
            self.lbl_imagen.setStyleSheet("background-color: white;")
            doc.close()
        except Exception as e:
            self.mostrar_error(f"Error cargando PDF: {str(e)}")
            traceback.print_exc()
    
    def mostrar_error(self, mensaje: str):
        self.lbl_imagen.setText(f"❌ Error\n\n{mensaje}")
        self.lbl_imagen.setStyleSheet("""
            QLabel {
                background-color: #ffe6e6;
                color: #cc0000;
                font-size: 14px;
                padding: 50px;
                border: 2px solid #ff9999;
                border-radius: 10px;
            }
        """)
    
    def on_click_imagen(self, event):
        if not self.imagen_pdf:
            return
        pos = event.pos()
        if self.modo_actual == "seleccion":
            for campo in self.campos:
                if campo.geometry().contains(pos):
                    self.seleccionar_campo(campo)
                    return
        elif self.modo_actual == "agregar_texto":
            x_mm = pos.x() / self.escala
            y_mm = pos.y() / self.escala
            self.solicita_agregar_campo.emit("texto", x_mm, y_mm)
        elif self.modo_actual == "agregar_tabla":
            x_mm = pos.x() / self.escala
            y_mm = pos.y() / self.escala
            self.solicita_agregar_campo.emit("tabla", x_mm, y_mm)
    
    def seleccionar_campo(self, campo):
        if self.campo_seleccionado_actual:
            self.campo_seleccionado_actual.set_seleccionado(False)
        self.campo_seleccionado_actual = campo
        campo.set_seleccionado(True)
        self.campo_seleccionado.emit(campo)
    
    def agregar_campo_visual(self, campo_widget, x_mm: float, y_mm: float):
        self.campos.append(campo_widget)
        campo_widget.setParent(self.lbl_imagen)
        x_px = int(x_mm * self.escala)
        y_px = int(y_mm * self.escala)
        campo_widget.move(x_px, y_px)
        campo_widget.show()
        self.seleccionar_campo(campo_widget)
    
    def eliminar_campo(self, campo):
        if campo in self.campos:
            self.campos.remove(campo)
            campo.deleteLater()
            if self.campo_seleccionado_actual == campo:
                self.campo_seleccionado_actual = None

# ================== PANEL PROPIEDADES MEJORADO ==================
class PanelPropiedades(QFrame):
    """Panel de propiedades con columnas REALES del padrón"""
    propiedades_cambiadas = pyqtSignal(dict)
    
    def __init__(self, proyecto_id):
        super().__init__()
        self.proyecto_id = proyecto_id
        self.campo_actual = None
        self.columnas_padron = []
        self.setup_ui()
        self.cargar_columnas_reales()
        self.hide()  # ← OCULTAR por defecto
    
    def setup_ui(self):
        self.setFrameStyle(QFrame.Shape.StyledPanel)
        self.setStyleSheet("PanelPropiedades { background-color: white; border: 1px solid #ddd; padding: 10px; }")
        layout = QVBoxLayout()
        self.lbl_titulo = QLabel("⚙️ Propiedades del Campo")
        self.lbl_titulo.setStyleSheet("font-size: 14px; font-weight: bold;")
        layout.addWidget(self.lbl_titulo)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        widget_contenido = QWidget()
        contenido_layout = QVBoxLayout()
        
        # Nombre interno
        contenido_layout.addWidget(QLabel("Nombre interno:"))
        self.txt_nombre = QLineEdit()
        self.txt_nombre.setPlaceholderText("Nombre para identificar el campo...")
        self.txt_nombre.textChanged.connect(self.actualizar_cambios)  # ← CAMBIÉ el nombre
        contenido_layout.addWidget(self.txt_nombre)
        
        # Columna del padrón
        contenido_layout.addWidget(QLabel("📊 Columna del Padrón:"))
        self.combo_columna = QComboBox()
        self.combo_columna.currentTextChanged.connect(self.actualizar_cambios)  # ← CAMBIÉ el nombre
        contenido_layout.addWidget(self.combo_columna)
        
        self.lbl_info_columna = QLabel("")
        self.lbl_info_columna.setStyleSheet("color: #666; font-size: 10px;")
        contenido_layout.addWidget(self.lbl_info_columna)
        
        # Botones de estilo (mantenemos por ahora)
        layout_botones = QHBoxLayout()
        self.btn_fuente = QPushButton("🔤 Fuente")
        self.btn_fuente.clicked.connect(self.cambiar_fuente)
        self.btn_color = QPushButton("🎨 Color")
        self.btn_color.clicked.connect(self.cambiar_color)
        layout_botones.addWidget(self.btn_fuente)
        layout_botones.addWidget(self.btn_color)
        contenido_layout.addLayout(layout_botones)
        
        self.check_negrita = QCheckBox("Negrita")
        self.check_negrita.stateChanged.connect(self.actualizar_cambios)  # ← CAMBIÉ el nombre
        self.check_cursiva = QCheckBox("Cursiva")
        self.check_cursiva.stateChanged.connect(self.actualizar_cambios)  # ← CAMBIÉ el nombre
        contenido_layout.addWidget(self.check_negrita)
        contenido_layout.addWidget(self.check_cursiva)
        
        widget_contenido.setLayout(contenido_layout)
        scroll.setWidget(widget_contenido)
        layout.addWidget(scroll)
        self.setLayout(layout)
    
    def cargar_columnas_reales(self):
        """Carga columnas del padrón"""
        from config.database import SessionLocal
        from core.models import Proyecto
        from core.padron_service import PadronService
        
        db = SessionLocal()
        try:
            proyecto = db.query(Proyecto).filter(Proyecto.id == self.proyecto_id).first()
            if not proyecto or not proyecto.tabla_padron:
                return
            
            padron_service = PadronService(db)
            self.columnas_padron = padron_service.obtener_columnas_padron(proyecto.tabla_padron)
            
            self.combo_columna.clear()
            self.combo_columna.addItem("-- Sin columna asignada --", "")
            
            for columna in self.columnas_padron:
                nombre = columna["nombre"]
                tipo = columna["tipo"]
                self.combo_columna.addItem(f"{nombre} ({tipo})", nombre)
                
        except Exception as e:
            print(f"ERROR cargando columnas: {e}")
        finally:
            db.close()
    
    def cambiar_fuente(self):
        """Diálogo para cambiar fuente"""
        if self.campo_actual and hasattr(self.campo_actual, 'cambiar_fuente'):
            self.campo_actual.cambiar_fuente()
            self.actualizar_cambios()
    
    def cambiar_color(self):
        """Diálogo para cambiar color"""
        if self.campo_actual and hasattr(self.campo_actual, 'cambiar_color'):
            self.campo_actual.cambiar_color()
            self.actualizar_cambios()
    
    def actualizar_cambios(self):  # ← NUEVO MÉTODO CON NOMBRE CORRECTO
        """Emitir cambios cuando se modifica algo"""
        if self.campo_actual:
            props = {
                "nombre": self.txt_nombre.text(),
                "columna_padron": self.combo_columna.currentData(),
                "negrita": self.check_negrita.isChecked(),
                "cursiva": self.check_cursiva.isChecked()
            }
            self.propiedades_cambiadas.emit(props)
    
    def mostrar_campo(self, campo):
        """Muestra u oculta el panel según si hay campo seleccionado"""
        self.campo_actual = campo
        
        if campo:
            self.show()  # ← MOSTRAR cuando hay campo
            
            self.txt_nombre.setText(campo.nombre)
            
            # Configurar combo
            columna = campo.config.get("columna_padron", "")
            index = self.combo_columna.findData(columna)
            self.combo_columna.setCurrentIndex(max(0, index))
            
            # Actualizar info de columna
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
            
            # Configurar checks
            self.check_negrita.setChecked(campo.config.get("negrita", False))
            self.check_cursiva.setChecked(campo.config.get("cursiva", False))
            
            self.lbl_titulo.setText(f"⚙️ {campo.nombre} ({campo.tipo})")
        else:
            self.hide()  # ← OCULTAR cuando no hay campo
            self.lbl_titulo.setText("⚙️ Propiedades del Campo")
            self.txt_nombre.setText("")
            self.combo_columna.setCurrentIndex(0)
            self.check_negrita.setChecked(False)
            self.check_cursiva.setChecked(False)
            self.lbl_info_columna.setText("")

# ================== DIÁLOGO DE PREVISUALIZACIÓN ==================
class DialogoPreview(QDialog):

    def __init__(self, proyecto_id, pdf_path, campos, parent=None):  # ← YA ESTÁ BIEN
        super().__init__(parent)  # ← parent va al final
        self.proyecto_id = proyecto_id
        self.pdf_path = pdf_path
        self.campos = campos
        self.registro_actual = None
        self.registros = []
        self.indice_actual = 0
        self.setup_ui()
        self.cargar_registros()  # ← Esto falla porque el método no existe en PadronService

    def cargar_registros(self):
        """Carga registros del padrón - CORREGIDO"""
        from config.database import SessionLocal
        from core.models import Proyecto
        from core.padron_service import PadronService
        
        db = SessionLocal()
        try:
            # 1. Obtener el proyecto
            proyecto = db.query(Proyecto).filter(Proyecto.id == self.proyecto_id).first()
            if not proyecto or not proyecto.tabla_padron:
                QMessageBox.warning(self, "Error", "No hay padrón configurado para este proyecto")
                return
            
            # 2. Obtener el UUID del padrón
            uuid_padron = proyecto.tabla_padron
            
            # 3. Usar PadronService para obtener registros
            padron_service = PadronService(db)
            
            # Obtener algunos registros de ejemplo (máximo 10 para preview)
            self.registros = padron_service.obtener_datos_ejemplo_real(uuid_padron, limit=10)
            
            if self.registros:
                self.indice_actual = 0
                self.mostrar_registro_actual()
            else:
                QMessageBox.information(self, "Sin datos", 
                                    "No hay registros en el padrón para mostrar")
                    
        except Exception as e:
            error_msg = f"Error cargando datos: {str(e)}"
            print(f"DEBUG - {error_msg}")
            QMessageBox.critical(self, "Error", error_msg)
        finally:
            db.close()

# ================== EDITOR VISUAL MEJORADO ==================
class EditorVisual(QWidget):
    """Editor visual principal - CON PREVISUALIZACIÓN"""
    plantilla_guardada = pyqtSignal(dict)
    
    def __init__(self, usuario, proyecto_id, pdf_path=None, stacked_widget=None):
        super().__init__()
        self.usuario = usuario
        self.proyecto_id = proyecto_id
        self.pdf_path = pdf_path
        self.stacked_widget = stacked_widget
        self.campos = []
        self.setup_ui()
        if pdf_path and os.path.exists(pdf_path):
            self.cargar_pdf(pdf_path)
    
    def setup_ui(self):
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
        
        # ← NUEVO BOTÓN DE PREVISUALIZACIÓN
        btn_preview = QPushButton("👁️ Vista Previa")
        btn_preview.clicked.connect(self.mostrar_preview)
        btn_preview.setStyleSheet("background-color: #3498db; color: white; font-weight: bold;")
        
        btn_guardar = QPushButton("💾 Guardar")
        btn_guardar.clicked.connect(self.guardar_plantilla)
        btn_guardar.setStyleSheet("background-color: #27ae60; color: white;")
        btn_cancelar = QPushButton("❌ Cancelar")
        btn_cancelar.clicked.connect(self.cancelar)
        btn_cancelar.setStyleSheet("background-color: #e74c3c; color: white;")
        
        layout_toolbar.addWidget(lbl_titulo)
        layout_toolbar.addStretch()
        layout_toolbar.addWidget(btn_abrir)
        layout_toolbar.addWidget(btn_preview)  # ← Añadir botón
        layout_toolbar.addWidget(btn_guardar)
        layout_toolbar.addWidget(btn_cancelar)
        toolbar_superior.setLayout(layout_toolbar)
        layout.addWidget(toolbar_superior)
        
        # Área principal
        splitter = QSplitter(Qt.Orientation.Horizontal)
        self.preview_pdf = PreviewPDF()
        self.preview_pdf.solicita_agregar_campo.connect(self.agregar_campo_desde_click)
        self.preview_pdf.campo_seleccionado.connect(self.seleccionar_campo)
        splitter.addWidget(self.preview_pdf)
        
        self.panel_propiedades = PanelPropiedades(self.proyecto_id)
        self.panel_propiedades.propiedades_cambiadas.connect(self.on_propiedades_cambiadas)
        splitter.addWidget(self.panel_propiedades)
        splitter.setSizes([700, 300])
        layout.addWidget(splitter)
        
        # Barra inferior
        barra_inferior = QFrame()
        barra_inferior.setStyleSheet("background-color: #34495e; padding: 5px;")
        layout_inferior = QHBoxLayout()
        self.lbl_estado = QLabel("Listo")
        self.lbl_estado.setStyleSheet("color: white;")
        self.lbl_info = QLabel("Haz clic en el PDF para agregar campos")
        self.lbl_info.setStyleSheet("color: #bdc3c7; font-size: 12px;")
        layout_inferior.addWidget(self.lbl_estado)
        layout_inferior.addStretch()
        layout_inferior.addWidget(self.lbl_info)
        barra_inferior.setLayout(layout_inferior)
        layout.addWidget(barra_inferior)
        
        self.setLayout(layout)
        self.resize(1200, 800)
    
    def cargar_pdf(self, pdf_path: str):
        self.pdf_path = pdf_path
        self.lbl_estado.setText(f"Cargando PDF: {os.path.basename(pdf_path)}")
        QTimer.singleShot(100, lambda: self.preview_pdf.cargar_pdf(pdf_path))
        self.lbl_info.setText("PDF cargado. Usa los botones para crear campos")
    
    def abrir_pdf(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Seleccionar PDF", "", "Archivos PDF (*.pdf)")
        if file_path:
            self.cargar_pdf(file_path)
    
    def agregar_campo_desde_click(self, tipo_campo: str, x_mm: float, y_mm: float):
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
        campo.campo_seleccionado.connect(self.seleccionar_campo)
        campo.campo_modificado.connect(self.on_campo_modificado)
        campo.solicita_eliminar.connect(self.eliminar_campo)
        self.preview_pdf.agregar_campo_visual(campo, x_mm, y_mm)
        self.campos.append(campo)
        self.panel_propiedades.mostrar_campo(campo)
        self.lbl_estado.setText(f"Campo {tipo_campo} agregado")
    
    def seleccionar_campo(self, campo):
        self.panel_propiedades.mostrar_campo(campo)
    
    def eliminar_campo(self, campo):
        reply = QMessageBox.question(self, "Eliminar campo", 
                                    f"¿Eliminar el campo '{campo.nombre}'?",
                                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            if campo in self.campos:
                self.campos.remove(campo)
                self.preview_pdf.eliminar_campo(campo)
                if self.panel_propiedades.campo_actual == campo:
                    self.panel_propiedades.mostrar_campo(None)
                self.lbl_estado.setText(f"Campo '{campo.nombre}' eliminado")
    
    def on_campo_modificado(self, cambios):
        pass

    def cargar_plantilla_existente(self):
        """Carga una plantilla existente para edición"""
        if not hasattr(self, 'plantilla_existente') or not self.plantilla_existente:
            return
        
        # Cargar campos existentes
        campos_config = self.plantilla_existente.get("campos", [])
        
        for config in campos_config:
            # Crear campo desde configuración
            campo = CampoTextoWidget(
                config.get("nombre", "Campo"), 
                "texto", 
                self.preview_pdf.lbl_imagen
            )
            
            # Aplicar configuración
            campo.config = config.copy()
            campo.nombre = config.get("nombre", "Campo")
            
            # Asignar columna del padrón si existe
            if "columna_padron" in config:
                campo.set_columna_padron(config["columna_padron"])
            
            # Conectar señales
            campo.campo_seleccionado.connect(self.seleccionar_campo)
            campo.campo_modificado.connect(self.on_campo_modificado)
            campo.solicita_eliminar.connect(self.eliminar_campo)
            
            # Posicionar (convertir mm a píxeles si es necesario)
            if hasattr(self.preview_pdf, 'escala'):
                x_px = int(config.get("x", 50) * self.preview_pdf.escala)
                y_px = int(config.get("y", 50) * self.preview_pdf.escala)
                ancho_px = int(config.get("ancho", 100) * self.preview_pdf.escala)
                alto_px = int(config.get("alto", 30) * self.preview_pdf.escala)
            else:
                x_px = config.get("x", 50)
                y_px = config.get("y", 50)
                ancho_px = config.get("ancho", 100)
                alto_px = config.get("alto", 30)
            
            campo.move(x_px, y_px)
            campo.setFixedSize(ancho_px, alto_px)
            campo.show()
            
            # Agregar a lista
            self.campos.append(campo)
        
        QMessageBox.information(self, "Cargado", 
                            f"Plantilla cargada con {len(campos_config)} campos")
    
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
        
        # Actualizar columna del padrón - SOLO para CampoTextoWidget
        if "columna_padron" in propiedades:
            campo.config["columna_padron"] = propiedades["columna_padron"]
            
            # Si el campo tiene método set_columna_padron, usarlo
            if hasattr(campo, 'set_columna_padron'):
                campo.set_columna_padron(propiedades["columna_padron"])
        
        # Actualizar estilo visual
        if hasattr(campo, 'actualizar_estilo'):
            campo.actualizar_estilo()
    
    # ← NUEVA FUNCIÓN DE PREVISUALIZACIÓN
    def mostrar_preview(self):
        """Muestra diálogo de previsualización con datos reales"""
        if not self.preview_pdf.campos:
            QMessageBox.warning(self, "Vista Previa", "No hay campos para previsualizar")
            return
        if not self.pdf_path:
            QMessageBox.warning(self, "Vista Previa", "No hay PDF cargado")
            return
        
        # Preparar configuración de campos
        configs_campos = []
        for campo in self.preview_pdf.campos:
            config = campo.config.copy()
            config["x"] = campo.x() / self.preview_pdf.escala
            config["y"] = campo.y() / self.preview_pdf.escala
            config["ancho"] = campo.width() / self.preview_pdf.escala
            config["alto"] = campo.height() / self.preview_pdf.escala
            configs_campos.append(config)
        
        # Abrir diálogo
        dialogo = DialogoPreview(self.proyecto_id, self.pdf_path, configs_campos, self)
        dialogo.exec()
    
    def guardar_plantilla(self):
        if not self.preview_pdf.campos:
            QMessageBox.warning(self, "Guardar", "No hay campos para guardar")
            return
        nombre, ok = QInputDialog.getText(self, "Nombre de plantilla",
                                         "Ingresa un nombre:",
                                         text=f"Plantilla con {len(self.preview_pdf.campos)} campos")
        if not ok or not nombre.strip():
            return
        configuracion = {
            "nombre": nombre.strip(),
            "pdf_base": self.pdf_path,
            "campos": [],
            "metadata": {
                "proyecto_id": self.proyecto_id,
                "usuario": self.usuario.id if self.usuario else 0
            }
        }
        for campo in self.preview_pdf.campos:
            config_campo = campo.config.copy()
            config_campo["x"] = campo.x() / self.preview_pdf.escala
            config_campo["y"] = campo.y() / self.preview_pdf.escala
            config_campo["ancho"] = campo.width() / self.preview_pdf.escala
            config_campo["alto"] = campo.height() / self.preview_pdf.escala
            configuracion["campos"].append(config_campo)
        self.plantilla_guardada.emit(configuracion)
        QMessageBox.information(self, "Éxito", 
                              f"✅ Plantilla '{nombre}' guardada con {len(configuracion['campos'])} campos")
        if self.stacked_widget:
            self.stacked_widget.removeWidget(self)
    
    def cancelar(self):
        reply = QMessageBox.question(self, "Cancelar",
                                    "¿Cancelar? Los cambios no guardados se perderán.",
                                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            self.plantilla_guardada.emit({})
            if self.stacked_widget:
                self.stacked_widget.removeWidget(self)
    
    def closeEvent(self, event):
        self.cancelar()
        event.accept()