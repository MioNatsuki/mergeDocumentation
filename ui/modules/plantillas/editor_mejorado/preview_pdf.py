# ui/modules/plantillas/editor_mejorado/preview_pdf.py - VERSIÓN CORREGIDA CON ZOOM
from PyQt6.QtWidgets import QWidget, QLabel, QFrame, QVBoxLayout, QHBoxLayout, QPushButton, QSlider, QScrollArea
from PyQt6.QtCore import Qt, pyqtSignal, QPoint, QRect, QTimer
from PyQt6.QtGui import QPixmap, QMouseEvent, QPainter, QPen, QColor, QWheelEvent, QImage, QBrush
import fitz  # PyMuPDF
import tempfile
import os
from PIL import Image

class PreviewPDF(QFrame):
    """Widget que muestra PDF con zoom y detecta clicks para agregar campos"""
    
    click_posicion = pyqtSignal(int, int)  # x, y en mm
    campo_seleccionado = pyqtSignal(object)
    zoom_cambiado = pyqtSignal(float)  # Nueva señal para zoom
    
    def __init__(self, pdf_path=None):
        super().__init__()
        self.pdf_path = pdf_path
        self.campos = []  # Lista de campos visibles
        self.campo_activo = None
        self.imagen_pdf = None
        self.escala = 2.0  # px por mm
        self.zoom_level = 1.0  # Nivel de zoom (1.0 = 100%)
        self.pan_enabled = False
        self.pan_start = QPoint()
        self.setup_ui()
        
        if pdf_path and os.path.exists(pdf_path):
            self.cargar_pdf(pdf_path)
        else:
            self.mostrar_placeholder()
    
    def setup_ui(self):
        self.setFrameStyle(QFrame.Shape.StyledPanel)
        self.setStyleSheet("""
            PreviewPDF {
                background-color: #2b2b2b;
                border: 2px solid #444;
            }
        """)
        
        # Layout principal
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Barra de herramientas (zoom)
        toolbar = QFrame()
        toolbar.setStyleSheet("""
            QFrame {
                background-color: #3c3c3c;
                padding: 5px;
                border-bottom: 1px solid #555;
            }
        """)
        
        toolbar_layout = QHBoxLayout()
        toolbar_layout.setContentsMargins(5, 2, 5, 2)
        
        # Botón zoom out
        btn_zoom_out = QPushButton("➖")
        btn_zoom_out.setToolTip("Alejar (Ctrl -)")
        btn_zoom_out.clicked.connect(self.zoom_out)
        btn_zoom_out.setFixedSize(30, 25)
        
        # Slider de zoom
        self.slider_zoom = QSlider(Qt.Orientation.Horizontal)
        self.slider_zoom.setRange(10, 300)  # 10% a 300%
        self.slider_zoom.setValue(100)
        self.slider_zoom.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.slider_zoom.valueChanged.connect(self.cambiar_zoom_slider)
        
        # Botón zoom in
        btn_zoom_in = QPushButton("➕")
        btn_zoom_in.setToolTip("Acercar (Ctrl +)")
        btn_zoom_in.clicked.connect(self.zoom_in)
        btn_zoom_in.setFixedSize(30, 25)
        
        # Botón reset zoom
        btn_reset = QPushButton("⟲ 100%")
        btn_reset.setToolTip("Restaurar zoom al 100%")
        btn_reset.clicked.connect(self.reset_zoom)
        btn_reset.setFixedSize(60, 25)
        
        # Botón pan (arrastrar)
        self.btn_pan = QPushButton("✋ Pan")
        self.btn_pan.setToolTip("Activar/desactivarr arrastre (Espacio)")
        self.btn_pan.setCheckable(True)
        self.btn_pan.clicked.connect(self.toggle_pan)
        self.btn_pan.setFixedSize(60, 25)
        
        # Label de zoom actual
        self.lbl_zoom = QLabel("100%")
        self.lbl_zoom.setStyleSheet("color: #aaa; font-size: 12px;")
        self.lbl_zoom.setFixedWidth(50)
        
        # Agregar a toolbar
        toolbar_layout.addWidget(btn_zoom_out)
        toolbar_layout.addWidget(self.slider_zoom)
        toolbar_layout.addWidget(btn_zoom_in)
        toolbar_layout.addWidget(btn_reset)
        toolbar_layout.addWidget(self.btn_pan)
        toolbar_layout.addStretch()
        toolbar_layout.addWidget(self.lbl_zoom)
        
        toolbar.setLayout(toolbar_layout)
        main_layout.addWidget(toolbar)
        
        # Área scrollable para el PDF
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll_area.setStyleSheet("""
            QScrollArea {
                background-color: #2b2b2b;
            }
            QScrollBar:vertical, QScrollBar:horizontal {
                background-color: #3c3c3c;
                width: 12px;
                height: 12px;
            }
            QScrollBar::handle:vertical, QScrollBar::handle:horizontal {
                background-color: #666;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical:hover, QScrollBar::handle:horizontal:hover {
                background-color: #888;
            }
        """)
        
        # Widget contenedor para la imagen
        self.container = QWidget()
        self.container_layout = QVBoxLayout()
        self.container_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Label para mostrar la imagen
        self.lbl_imagen = QLabel()
        self.lbl_imagen.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_imagen.setStyleSheet("background-color: white;")
        self.lbl_imagen.setCursor(Qt.CursorShape.CrossCursor)
        
        self.container_layout.addWidget(self.lbl_imagen)
        self.container.setLayout(self.container_layout)
        self.scroll_area.setWidget(self.container)
        
        main_layout.addWidget(self.scroll_area)
        self.setLayout(main_layout)
        
        # Tooltips
        self.setToolTip("Haz clic para agregar campos | Rueda del mouse para zoom | Espacio para arrastrar")
    
    def mostrar_placeholder(self):
        """Muestra un placeholder cuando no hay PDF"""
        self.lbl_imagen.setText("📄 Arrastra un PDF aquí\n\nO usa el botón 'Nueva Plantilla'")
        self.lbl_imagen.setStyleSheet("""
            QLabel {
                background-color: #3c3c3c;
                color: #aaa;
                font-size: 14px;
                padding: 40px;
                border: 2px dashed #666;
                border-radius: 10px;
            }
        """)
        self.lbl_imagen.setAlignment(Qt.AlignmentFlag.AlignCenter)
    
    def cargar_pdf(self, pdf_path):
        """Convierte primera página del PDF a imagen"""
        try:
            print(f"DEBUG: Cargando PDF: {pdf_path}")
            
            # Abrir PDF con PyMuPDF
            doc = fitz.open(pdf_path)
            pagina = doc[0]
            
            # Calcular matriz para buena calidad (150 DPI)
            zoom = 150 / 72  # 150 DPI
            mat = fitz.Matrix(zoom, zoom)
            
            # Renderizar a pixmap
            pix = pagina.get_pixmap(matrix=mat, alpha=False)
            
            # Convertir a QImage
            img_format = QImage.Format.Format_RGB888
            qimage = QImage(pix.samples, pix.width, pix.height, pix.stride, img_format)
            
            # Guardar referencia
            self.imagen_original = QPixmap.fromImage(qimage)
            self.pdf_width_mm = 210  # Ancho A4 en mm
            self.pdf_height_mm = 297  # Alto A4 en mm
            
            # Calcular escala inicial
            self.escala_base = self.imagen_original.width() / self.pdf_width_mm
            
            print(f"DEBUG: Imagen cargada: {pix.width}x{pix.height}px, "
                  f"Escala base: {self.escala_base:.2f} px/mm")
            
            # Aplicar zoom inicial
            self.aplicar_zoom()
            
            doc.close()
            
        except Exception as e:
            print(f"ERROR cargando PDF: {e}")
            import traceback
            traceback.print_exc()
            self.lbl_imagen.setText(f"❌ Error cargando PDF\n\n{str(e)[:100]}...")
    
    def aplicar_zoom(self):
        """Aplica el nivel de zoom actual a la imagen"""
        if hasattr(self, 'imagen_original'):
            # Calcular nuevo tamaño
            nuevo_ancho = int(self.imagen_original.width() * self.zoom_level)
            nuevo_alto = int(self.imagen_original.height() * self.zoom_level)
            
            # Escalar la imagen
            pixmap = self.imagen_original.scaled(
                nuevo_ancho, nuevo_alto,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            
            # Actualizar escala (px por mm)
            self.escala = self.escala_base * self.zoom_level
            
            # Mostrar imagen
            self.lbl_imagen.setPixmap(pixmap)
            self.lbl_imagen.resize(pixmap.size())
            
            # Actualizar label de zoom
            self.lbl_zoom.setText(f"{int(self.zoom_level * 100)}%")
            self.slider_zoom.setValue(int(self.zoom_level * 100))
            
            print(f"DEBUG: Zoom aplicado: {self.zoom_level:.2f}x, "
                  f"Escala: {self.escala:.2f} px/mm")
    
    # --- FUNCIONES DE ZOOM ---
    
    def zoom_in(self):
        """Aumenta el zoom en 25%"""
        self.zoom_level = min(3.0, self.zoom_level + 0.25)
        self.aplicar_zoom()
        self.zoom_cambiado.emit(self.zoom_level)
    
    def zoom_out(self):
        """Disminuye el zoom en 25%"""
        self.zoom_level = max(0.25, self.zoom_level - 0.25)
        self.aplicar_zoom()
        self.zoom_cambiado.emit(self.zoom_level)
    
    def reset_zoom(self):
        """Restaura el zoom al 100%"""
        self.zoom_level = 1.0
        self.aplicar_zoom()
        self.zoom_cambiado.emit(self.zoom_level)
    
    def cambiar_zoom_slider(self, value):
        """Cambia zoom según slider"""
        self.zoom_level = value / 100.0
        self.aplicar_zoom()
        self.zoom_cambiado.emit(self.zoom_level)
    
    def toggle_pan(self):
        """Activa/desactiva el modo pan (arrastre)"""
        self.pan_enabled = self.btn_pan.isChecked()
        if self.pan_enabled:
            self.lbl_imagen.setCursor(Qt.CursorShape.OpenHandCursor)
            self.btn_pan.setStyleSheet("background-color: #4CAF50; color: white;")
        else:
            self.lbl_imagen.setCursor(Qt.CursorShape.CrossCursor)
            self.btn_pan.setStyleSheet("")
    
    # --- EVENTOS DEL MOUSE ---
    
    def wheelEvent(self, event: QWheelEvent):
        """Zoom con rueda del mouse + Ctrl"""
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            # Zoom con Ctrl + rueda
            delta = event.angleDelta().y()
            if delta > 0:
                self.zoom_in()
            else:
                self.zoom_out()
            event.accept()
        else:
            # Scroll normal
            super().wheelEvent(event)
    
    def mousePressEvent(self, event: QMouseEvent):
        """Maneja clics del mouse"""
        if event.button() == Qt.MouseButton.LeftButton:
            if self.pan_enabled:
                # Iniciar pan (arrastre)
                self.pan_start = event.pos()
                self.lbl_imagen.setCursor(Qt.CursorShape.ClosedHandCursor)
            else:
                # Click normal para agregar campo
                self.procesar_click(event.pos())
    
    def mouseMoveEvent(self, event: QMouseEvent):
        """Maneja movimiento del mouse"""
        if self.pan_enabled and event.buttons() & Qt.MouseButton.LeftButton:
            # Arrastrar (pan)
            delta = event.pos() - self.pan_start
            self.pan_start = event.pos()
            
            # Mover scrollbars
            h_scroll = self.scroll_area.horizontalScrollBar()
            v_scroll = self.scroll_area.verticalScrollBar()
            h_scroll.setValue(h_scroll.value() - delta.x())
            v_scroll.setValue(v_scroll.value() - delta.y())
    
    def mouseReleaseEvent(self, event: QMouseEvent):
        """Maneja liberación del mouse"""
        if event.button() == Qt.MouseButton.LeftButton and self.pan_enabled:
            self.lbl_imagen.setCursor(Qt.CursorShape.OpenHandCursor)
    
    def procesar_click(self, pos_global):
        """Procesa un click para agregar campo"""
        # Convertir posición global a posición en el label
        pos_label = self.lbl_imagen.mapFromGlobal(pos_global)
        
        # Verificar que el click fue dentro de la imagen
        if (0 <= pos_label.x() <= self.lbl_imagen.width() and 
            0 <= pos_label.y() <= self.lbl_imagen.height()):
            
            # Convertir píxeles a milímetros
            x_mm = pos_label.x() / self.escala
            y_mm = pos_label.y() / self.escala
            
            print(f"DEBUG: Click en posición: "
                  f"({pos_label.x()}, {pos_label.y()}) px = "
                  f"({x_mm:.1f}, {y_mm:.1f}) mm")
            
            # Emitir señal con posición en mm
            self.click_posicion.emit(int(x_mm), int(y_mm))
            
            # También verificar si se hizo clic en un campo existente
            self.verificar_clic_campo(pos_label.x(), pos_label.y())
    
    def verificar_clic_campo(self, x, y):
        """Verifica si se hizo clic en un campo existente"""
        for campo in self.campos:
            if campo.geometry().contains(x, y):
                self.campo_activo = campo
                self.campo_seleccionado.emit(campo)
                self.update()
                break
    
    def agregar_campo_visual(self, campo_widget):
        """Agrega un campo visual al preview"""
        self.campos.append(campo_widget)
        campo_widget.setParent(self.lbl_imagen)
        
        # Convertir mm a píxeles (usando escala actual con zoom)
        x_px = int(campo_widget.x_mm * self.escala)
        y_px = int(campo_widget.y_mm * self.escala)
        
        campo_widget.move(x_px, y_px)
        campo_widget.show()
        
        print(f"DEBUG: Campo agregado en posición: "
              f"({campo_widget.x_mm}mm, {campo_widget.y_mm}mm) = "
              f"({x_px}px, {y_px}px)")
    
    def keyPressEvent(self, event):
        """Maneja teclas rápidas"""
        # Espacio para activar/desactivar pan
        if event.key() == Qt.Key.Key_Space:
            self.btn_pan.toggle()
            self.toggle_pan()
            event.accept()
        # Ctrl + para zoom in
        elif event.key() == Qt.Key.Key_Plus and event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            self.zoom_in()
            event.accept()
        # Ctrl - para zoom out
        elif event.key() == Qt.Key.Key_Minus and event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            self.zoom_out()
            event.accept()
        # Ctrl 0 para reset zoom
        elif event.key() == Qt.Key.Key_0 and event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            self.reset_zoom()
            event.accept()
        else:
            super().keyPressEvent(event)
    
    def paintEvent(self, event):
        """Dibuja guías y selección"""
        super().paintEvent(event)
        
        # Dibujar borde rojo alrededor del campo activo
        if self.campo_activo:
            painter = QPainter(self.lbl_imagen)
            painter.setPen(QPen(QColor(255, 0, 0), 2, Qt.PenStyle.DashLine))
            
            rect = self.campo_activo.geometry()
            painter.drawRect(rect)
            
            # Dibujar handles de redimensionamiento (opcional)
            tamaño_handle = 6
            painter.setBrush(QBrush(QColor(255, 0, 0)))
            
            # Esquinas
            painter.drawRect(rect.left() - tamaño_handle//2, rect.top() - tamaño_handle//2, 
                           tamaño_handle, tamaño_handle)
            painter.drawRect(rect.right() - tamaño_handle//2, rect.top() - tamaño_handle//2, 
                           tamaño_handle, tamaño_handle)
            painter.drawRect(rect.left() - tamaño_handle//2, rect.bottom() - tamaño_handle//2, 
                           tamaño_handle, tamaño_handle)
            painter.drawRect(rect.right() - tamaño_handle//2, rect.bottom() - tamaño_handle//2, 
                           tamaño_handle, tamaño_handle)