# ui/modules/plantillas/editor_mejorado/preview_pdf.py - VERSIÓN CORREGIDA CON ZOOM
from PyQt6.QtWidgets import QWidget, QLabel, QFrame, QVBoxLayout, QHBoxLayout, QPushButton, QSlider, QScrollArea
from PyQt6.QtCore import Qt, pyqtSignal, QPoint, QRect, QTimer
from PyQt6.QtGui import QPixmap, QMouseEvent, QPainter, QPen, QColor, QWheelEvent, QImage, QBrush
import fitz  # PyMuPDF
import tempfile
import os
from PIL import Image
import traceback

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

class PreviewPDF(QFrame):
    """Área para previsualizar PDF con campos - MEJORADO"""
    
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
        self.setup_ui()
        
    def setup_ui(self):
        self.setFrameStyle(QFrame.Shape.StyledPanel)
        self.setStyleSheet("""
            PreviewPDF { 
                background-color: #f5f5f5; 
                border: 1px solid #ddd;
                border-radius: 4px;
            }
        """)
        layout = QVBoxLayout()
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)
        
        # Barra de herramientas compacta y moderna
        toolbar = QFrame()
        toolbar.setFixedHeight(40)
        toolbar.setStyleSheet("""
            QFrame {
                background-color: #ffffff;
                border: 1px solid #e0e0e0;
                border-radius: 4px;
                padding: 5px;
            }
            QPushButton {
                background-color: #f8f9fa;
                border: 1px solid #ddd;
                border-radius: 3px;
                padding: 5px 10px;
                margin: 0 2px;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #e9ecef;
                border-color: #007bff;
            }
            QPushButton:pressed {
                background-color: #007bff;
                color: white;
            }
            QPushButton:checked {
                background-color: #007bff;
                color: white;
                border-color: #0056b3;
            }
            QLabel {
                color: #495057;
                font-weight: bold;
                font-size: 12px;
            }
        """)
        
        toolbar_layout = QHBoxLayout()
        toolbar_layout.setContentsMargins(5, 0, 5, 0)
        
        self.lbl_modo = QLabel("Modo: Selección")
        
        # Botones compactos
        self.btn_seleccion = QPushButton("👆 Seleccionar")
        self.btn_seleccion.setCheckable(True)
        self.btn_seleccion.setChecked(True)
        self.btn_seleccion.clicked.connect(self.activar_modo_seleccion)
        
        self.btn_texto = QPushButton("📝 Texto")
        self.btn_texto.setCheckable(True)
        self.btn_texto.clicked.connect(self.activar_modo_texto)
        
        self.btn_tabla = QPushButton("📊 Tabla")
        self.btn_tabla.setCheckable(True)
        self.btn_tabla.clicked.connect(self.activar_modo_tabla)
        
        # Grupo para botones modo (solo uno seleccionable)
        self.botones_modo = [self.btn_seleccion, self.btn_texto, self.btn_tabla]
        
        toolbar_layout.addWidget(self.lbl_modo)
        toolbar_layout.addStretch()
        toolbar_layout.addWidget(self.btn_seleccion)
        toolbar_layout.addWidget(self.btn_texto)
        toolbar_layout.addWidget(self.btn_tabla)
        
        toolbar.setLayout(toolbar_layout)
        layout.addWidget(toolbar)
        
        # Área del PDF - más grande
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll_area.setStyleSheet("background-color: #e8e8e8;")
        
        self.container = QWidget()
        self.container_layout = QVBoxLayout()
        self.container_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.container_layout.setContentsMargins(20, 20, 20, 20)
        
        self.lbl_imagen = QLabel("📄 Selecciona un PDF para comenzar")
        self.lbl_imagen.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_imagen.setStyleSheet("""
            QLabel {
                background-color: white;
                color: #666;
                font-size: 14px;
                padding: 40px;
                border: 2px dashed #aaa;
                border-radius: 8px;
                min-width: 800px;
                min-height: 600px;
            }
        """)
        self.lbl_imagen.mousePressEvent = self.on_click_imagen
        self.lbl_imagen.mouseMoveEvent = self.on_mouse_move_imagen
        self.lbl_imagen.leaveEvent = self.on_leave_imagen
        
        self.container_layout.addWidget(self.lbl_imagen)
        self.container.setLayout(self.container_layout)
        self.scroll_area.setWidget(self.container)
        layout.addWidget(self.scroll_area)
        
        # Barra de estado pequeña
        self.barra_estado = QLabel("Listo")
        self.barra_estado.setStyleSheet("""
            QLabel {
                background-color: #ffffff;
                border-top: 1px solid #e0e0e0;
                color: #666;
                font-size: 10px;
                padding: 3px 10px;
                min-height: 20px;
            }
        """)
        layout.addWidget(self.barra_estado)
        
        self.setLayout(layout)
        self.modo_actual = "seleccion"
    
    def activar_modo_seleccion(self):
        """Activa modo selección"""
        self.cambiar_modo("seleccion")
        self.actualizar_botones_modo(self.btn_seleccion)
    
    def activar_modo_texto(self):
        """Activa modo agregar texto"""
        self.cambiar_modo("agregar_texto")
        self.actualizar_botones_modo(self.btn_texto)
    
    def activar_modo_tabla(self):
        """Activa modo agregar tabla"""
        self.cambiar_modo("agregar_tabla")
        self.actualizar_botones_modo(self.btn_tabla)
    
    def actualizar_botones_modo(self, boton_activo):
        """Mantiene solo un botón de modo activo a la vez"""
        for btn in self.botones_modo:
            if btn != boton_activo:
                btn.setChecked(False)
        boton_activo.setChecked(True)
    
    def cambiar_modo(self, modo: str):
        """Cambia el modo de interacción"""
        self.modo_actual = modo
        if modo == "seleccion":
            self.lbl_modo.setText("Modo: Selección")
            self.lbl_imagen.setCursor(Qt.CursorShape.ArrowCursor)
            self.barra_estado.setText("🖱️ Haz clic para seleccionar campos")
        elif modo == "agregar_texto":
            self.lbl_modo.setText("Modo: Agregar Texto")
            self.lbl_imagen.setCursor(Qt.CursorShape.CrossCursor)
            self.barra_estado.setText("➕ Haz clic en el PDF para agregar un campo de texto")
        elif modo == "agregar_tabla":
            self.lbl_modo.setText("Modo: Agregar Tabla")
            self.lbl_imagen.setCursor(Qt.CursorShape.CrossCursor)
            self.barra_estado.setText("📊 Haz clic en el PDF para agregar una tabla")
    
    def cargar_pdf(self, pdf_path: str):
        if not PDF_SUPPORT:
            self.mostrar_error("PyMuPDF no está instalado. Instala con: pip install PyMuPDF")
            return
        self.pdf_path = pdf_path
        try:
            doc = fitz.open(pdf_path)
            pagina = doc[0]
            zoom = 1.8  # Zoom más grande para mejor visualización
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
            self.lbl_imagen.setStyleSheet("background-color: white; border: 1px solid #ccc;")
            doc.close()
            self.barra_estado.setText(f"PDF cargado: {os.path.basename(pdf_path)} - Tamaño: {ancho_px}x{alto_px}px")
        except Exception as e:
            self.mostrar_error(f"Error cargando PDF: {str(e)}")
            traceback.print_exc()
    
    def mostrar_error(self, mensaje: str):
        self.lbl_imagen.setText(f"❌ Error\n\n{mensaje}")
        self.lbl_imagen.setStyleSheet("""
            QLabel {
                background-color: #ffe6e6;
                color: #cc0000;
                font-size: 12px;
                padding: 40px;
                border: 2px solid #ff9999;
                border-radius: 8px;
            }
        """)
    
    def on_mouse_move_imagen(self, event):
        """Muestra coordenadas en tiempo real"""
        if self.imagen_pdf:
            x_mm = event.pos().x() / self.escala
            y_mm = event.pos().y() / self.escala
            self.barra_estado.setText(f"Posición: X={x_mm:.1f}mm, Y={y_mm:.1f}mm")
    
    def on_leave_imagen(self, event):
        """Restaura texto de estado al salir del área"""
        if self.imagen_pdf:
            if self.modo_actual == "seleccion":
                self.barra_estado.setText("🖱️ Haz clic para seleccionar campos")
            elif self.modo_actual == "agregar_texto":
                self.barra_estado.setText("➕ Haz clic en el PDF para agregar un campo de texto")
            elif self.modo_actual == "agregar_tabla":
                self.barra_estado.setText("📊 Haz clic en el PDF para agregar una tabla")
    
    def on_click_imagen(self, event):
        if not self.imagen_pdf:
            return
        
        pos = event.pos()
        
        # Siempre permite seleccionar campos primero
        for campo in self.campos:
            if campo.geometry().contains(pos):
                self.seleccionar_campo(campo)
                return
        
        # Si no se clickeó en un campo, entonces agregar según modo
        if self.modo_actual == "agregar_texto":
            x_mm = pos.x() / self.escala
            y_mm = pos.y() / self.escala
            self.solicita_agregar_campo.emit("texto", x_mm, y_mm)
        elif self.modo_actual == "agregar_tabla":
            x_mm = pos.x() / self.escala
            y_mm = pos.y() / self.escala
            self.solicita_agregar_campo.emit("tabla", x_mm, y_mm)
    
    def seleccionar_campo(self, campo):
        """Selecciona un campo"""
        if self.campo_seleccionado_actual:
            self.campo_seleccionado_actual.set_seleccionado(False)
        self.campo_seleccionado_actual = campo
        campo.set_seleccionado(True)
        self.campo_seleccionado.emit(campo)
        
        # Cambiar automáticamente a modo selección
        self.activar_modo_seleccion()
        self.barra_estado.setText(f"✅ Campo seleccionado: {campo.nombre}")
    
    def agregar_campo_visual(self, campo_widget, x_mm: float, y_mm: float):
        """Agrega un campo visualmente"""
        self.campos.append(campo_widget)
        campo_widget.setParent(self.lbl_imagen)
        x_px = int(x_mm * self.escala)
        y_px = int(y_mm * self.escala)
        campo_widget.move(x_px, y_px)
        campo_widget.show()
        self.seleccionar_campo(campo_widget)
    
    def eliminar_campo(self, campo):
        """Elimina un campo"""
        if campo in self.campos:
            self.campos.remove(campo)
            campo.deleteLater()
            if self.campo_seleccionado_actual == campo:
                self.campo_seleccionado_actual = None