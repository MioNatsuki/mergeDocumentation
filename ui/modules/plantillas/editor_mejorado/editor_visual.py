# ui/modules/plantillas/editor_mejorado/editor_visual.py (VERSIÓN CORREGIDA)
from PyQt6.QtWidgets import (QWidget, QHBoxLayout, QVBoxLayout, QLabel, 
                             QPushButton, QMessageBox, QSplitter, QFrame,
                             QInputDialog, QScrollArea, QFileDialog, QMenu,
                             QTextEdit, QLineEdit, QComboBox, QSpinBox, 
                             QCheckBox, QFontDialog, QColorDialog, QGroupBox,
                             QListWidget, QListWidgetItem, QToolBar, QToolButton)
from PyQt6.QtCore import Qt, pyqtSignal, QRect, QPoint
from PyQt6.QtGui import QFont, QColor, QPixmap, QImage, QPainter, QPen, QBrush, QAction
import json
import os
import traceback
from typing import Dict, List, Optional
import fitz

# Importar con try/except para mejor manejo de errores
try:
    import fitz  # PyMuPDF
    PDF_SUPPORT = True
except ImportError:
    PDF_SUPPORT = False
    print("Advertencia: PyMuPDF (fitz) no está instalado. Usando placeholder.")

try:
    from PIL import Image
    IMAGE_SUPPORT = True
except ImportError:
    IMAGE_SUPPORT = False
    print("Advertencia: Pillow no está instalado.")

# ================== CLASE CAMPO DE TEXTO ==================
class CampoTextoWidget(QFrame):
    """Widget de campo de texto arrastrable y redimensionable"""
    
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
            "alineacion": "izquierda",
            "formato": "texto",
            "columna_padron": "",
            "x": 50,
            "y": 50,
            "ancho": 100,
            "alto": 30,
            "margen": 2,
            "fondo": "transparente",
            "borde": True
        }
        
        self.seleccionado = False
        self.drag_pos = None
        self.redimensionando = False
        self.resize_corner = None
        
        self.setup_ui()
        self.actualizar_estilo()
        
    def setup_ui(self):
        """Configura la interfaz del campo"""
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
        """Maneja clic en el campo"""
        if event.button() == Qt.MouseButton.LeftButton:
            # Verificar si es clic en esquina para redimensionar
            rect = self.rect()
            corner_size = 10
            corners = {
                "top-left": QRect(0, 0, corner_size, corner_size),
                "top-right": QRect(rect.width() - corner_size, 0, corner_size, corner_size),
                "bottom-left": QRect(0, rect.height() - corner_size, corner_size, corner_size),
                "bottom-right": QRect(rect.width() - corner_size, rect.height() - corner_size, corner_size, corner_size)
            }
            
            for corner_name, corner_rect in corners.items():
                if corner_rect.contains(event.pos()):
                    self.redimensionando = True
                    self.resize_corner = corner_name
                    self.resize_start_pos = event.globalPosition().toPoint()
                    self.resize_start_size = self.size()
                    return
            
            # Si no es redimensionar, es arrastre
            self.drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            self.campo_seleccionado.emit(self)
            event.accept()
            
    def mouseMoveEvent(self, event):
        """Maneja movimiento del mouse"""
        if event.buttons() & Qt.MouseButton.LeftButton:
            if self.redimensionando:
                # Redimensionar
                delta = event.globalPosition().toPoint() - self.resize_start_pos
                
                new_width = self.resize_start_size.width()
                new_height = self.resize_start_size.height()
                
                if self.resize_corner in ["top-right", "bottom-right"]:
                    new_width = max(50, self.resize_start_size.width() + delta.x())
                elif self.resize_corner in ["top-left", "bottom-left"]:
                    new_width = max(50, self.resize_start_size.width() - delta.x())
                    if new_width > 50:
                        self.move(self.x() + delta.x(), self.y())
                
                if self.resize_corner in ["bottom-left", "bottom-right"]:
                    new_height = max(30, self.resize_start_size.height() + delta.y())
                elif self.resize_corner in ["top-left", "top-right"]:
                    new_height = max(30, self.resize_start_size.height() - delta.y())
                    if new_height > 30:
                        self.move(self.x(), self.y() + delta.y())
                
                self.setFixedSize(new_width, new_height)
                self.config["ancho"] = new_width
                self.config["alto"] = new_height
                self.campo_modificado.emit({"ancho": new_width, "alto": new_height})
                
            elif self.drag_pos:
                # Arrastrar
                new_pos = event.globalPosition().toPoint() - self.drag_pos
                self.move(new_pos)
                
                # Actualizar posición en mm (asumiendo escala)
                if hasattr(self.parent(), 'escala'):
                    escala = self.parent().escala
                    self.config["x"] = self.x() / escala
                    self.config["y"] = self.y() / escala
                    self.campo_modificado.emit({"x": self.config["x"], "y": self.config["y"]})
    
    def mouseReleaseEvent(self, event):
        """Maneja liberación del mouse"""
        self.redimensionando = False
        self.drag_pos = None
        self.resize_corner = None
    
    def mouseDoubleClickEvent(self, event):
        """Doble clic para editar texto"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.editar_texto()
    
    def contextMenuEvent(self, event):
        """Menú contextual con opciones"""
        menu = QMenu(self)
        
        action_editar = QAction("✏️ Editar texto", self)
        action_editar.triggered.connect(self.editar_texto)
        
        action_fuente = QAction("🔤 Cambiar fuente", self)
        action_fuente.triggered.connect(self.cambiar_fuente)
        
        action_color = QAction("🎨 Cambiar color", self)
        action_color.triggered.connect(self.cambiar_color)
        
        action_eliminar = QAction("🗑️ Eliminar", self)
        action_eliminar.triggered.connect(lambda: self.solicita_eliminar.emit(self))
        
        menu.addAction(action_editar)
        menu.addAction(action_fuente)
        menu.addAction(action_color)
        menu.addSeparator()
        menu.addAction(action_eliminar)
        
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
        """Actualiza el estilo visual del campo"""
        estilo = f"""
            CampoTextoWidget {{
                background-color: {'rgba(173, 216, 230, 0.7)' if self.seleccionado else 'rgba(255, 255, 255, 0.3)'};
                border: { '2px solid #ff0000' if self.seleccionado else '1px solid #000000'};
                border-radius: 3px;
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

# ================== CLASE PREVIEW PDF ==================
class PreviewPDF(QFrame):
    """Área para previsualizar PDF con campos"""
    
    click_posicion = pyqtSignal(float, float)  # x, y en mm
    campo_agregado = pyqtSignal(dict)  # Configuración del campo
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.pdf_path = None
        self.campos = []  # Lista de campos en el PDF
        self.campo_seleccionado = None
        self.imagen_pdf = None
        self.escala = 2.0  # px por mm
        self.modo_actual = "seleccion"  # seleccion, agregar_texto
        
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
        
        # Barra de herramientas simple
        toolbar = QFrame()
        toolbar.setStyleSheet("background-color: #e0e0e0; padding: 5px;")
        toolbar_layout = QHBoxLayout()
        
        self.lbl_modo = QLabel("👆 Modo: Selección")
        
        self.btn_texto = QPushButton("📝 Agregar Texto")
        self.btn_texto.clicked.connect(lambda: self.cambiar_modo("agregar_texto"))
        
        self.btn_seleccion = QPushButton("👆 Seleccionar")
        self.btn_seleccion.clicked.connect(lambda: self.cambiar_modo("seleccion"))
        
        toolbar_layout.addWidget(self.lbl_modo)
        toolbar_layout.addWidget(self.btn_seleccion)
        toolbar_layout.addWidget(self.btn_texto)
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
            
            # Crear campo
            campo = CampoTextoWidget("Nuevo Campo", "texto", self.lbl_imagen)
            campo.move(pos.x() - 50, pos.y() - 15)  # Centrar en el clic
            campo.show()
            
            # Conectar señales
            campo.campo_seleccionado.connect(self.seleccionar_campo)
            campo.campo_modificado.connect(self.on_campo_modificado)
            campo.solicita_eliminar.connect(self.eliminar_campo)
            
            self.campos.append(campo)
            self.seleccionar_campo(campo)
            
            # Emitir señal
            self.campo_agregado.emit({
                "tipo": "texto",
                "x": x_mm,
                "y": y_mm,
                "nombre": "Nuevo Campo"
            })
    
    def seleccionar_campo(self, campo):
        """Selecciona un campo"""
        if self.campo_seleccionado:
            self.campo_seleccionado.set_seleccionado(False)
        
        self.campo_seleccionado = campo
        campo.set_seleccionado(True)
    
    def on_campo_modificado(self, cambios):
        """Cuando se modifica un campo"""
        if self.campo_seleccionado:
            print(f"Campo modificado: {cambios}")
    
    def eliminar_campo(self, campo):
        """Elimina un campo"""
        if campo in self.campos:
            self.campos.remove(campo)
            campo.deleteLater()
            
            if self.campo_seleccionado == campo:
                self.campo_seleccionado = None

# ================== PANEL PROPIEDADES SIMPLIFICADO ==================
class PanelPropiedades(QFrame):
    """Panel de propiedades simplificado"""
    
    propiedades_cambiadas = pyqtSignal(dict)
    
    def __init__(self):
        super().__init__()
        self.campo_actual = None
        self.setup_ui()
    
    def setup_ui(self):
        """Configura la interfaz"""
        self.setFrameStyle(QFrame.Shape.StyledPanel)
        self.setStyleSheet("""
            PanelPropiedades {
                background-color: white;
                border: 1px solid #ddd;
                padding: 10px;
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
        
        # Columna CSV
        self.combo_columna = QComboBox()
        self.combo_columna.addItems(["", "cuenta", "nombre", "direccion", "telefono", "monto"])
        self.combo_columna.currentTextChanged.connect(self.emitir_cambios)
        contenido_layout.addWidget(QLabel("Columna CSV:"))
        contenido_layout.addWidget(self.combo_columna)
        
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
                "columna_csv": self.combo_columna.currentText(),
                "negrita": self.check_negrita.isChecked(),
                "cursiva": self.check_cursiva.isChecked()
            }
            self.propiedades_cambiadas.emit(props)
    
    def mostrar_campo(self, campo):
        """Muestra propiedades de un campo"""
        self.campo_actual = campo
        
        if campo:
            self.txt_nombre.setText(campo.nombre)
            self.txt_texto.setText(campo.config["texto"])
            self.combo_columna.setCurrentText(campo.config.get("columna_padron", ""))
            self.check_negrita.setChecked(campo.config.get("negrita", False))
            self.check_cursiva.setChecked(campo.config.get("cursiva", False))
            
            self.lbl_titulo.setText(f"⚙️ {campo.nombre}")
        else:
            self.lbl_titulo.setText("⚙️ Propiedades del Campo")

# ================== EDITOR VISUAL PRINCIPAL ==================
class EditorVisual(QWidget):
    """Editor visual principal"""
    
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
        
        # Panel izquierdo - Preview PDF
        self.preview_pdf = PreviewPDF()
        self.preview_pdf.campo_agregado.connect(self.on_campo_agregado)
        splitter.addWidget(self.preview_pdf)
        
        # Panel derecho - Propiedades
        self.panel_propiedades = PanelPropiedades()
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
        
        self.lbl_info = QLabel("Haz clic en el PDF para agregar campos de texto")
        self.lbl_info.setStyleSheet("color: #bdc3c7; font-size: 12px;")
        
        layout_inferior.addWidget(self.lbl_estado)
        layout_inferior.addStretch()
        layout_inferior.addWidget(self.lbl_info)
        
        barra_inferior.setLayout(layout_inferior)
        layout.addWidget(barra_inferior)
        
        self.setLayout(layout)
        self.resize(1000, 700)
    
    def cargar_pdf(self, pdf_path: str):
        """Carga un PDF en el preview"""
        print(f"EditorVisual.cargar_pdf llamado con: {pdf_path}")
        self.pdf_path = pdf_path
        self.lbl_estado.setText(f"Cargando PDF: {os.path.basename(pdf_path)}")
        
        # Usar QTimer para procesar en el siguiente ciclo de eventos
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(100, lambda: self.preview_pdf.cargar_pdf(pdf_path))
        
        self.lbl_info.setText(f"PDF cargado. Usa el botón '📝 Agregar Texto' para crear campos.")
    
    def abrir_pdf(self):
        """Abre diálogo para seleccionar PDF"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Seleccionar PDF", "", "Archivos PDF (*.pdf)"
        )
        
        if file_path:
            self.cargar_pdf(file_path)
    
    def on_campo_agregado(self, config):
        """Cuando se agrega un nuevo campo"""
        self.campos.append(config)
        self.panel_propiedades.campo_actual = self.preview_pdf.campo_seleccionado
        self.lbl_estado.setText(f"Campo agregado: {config.get('nombre', 'Nuevo')}")
    
    def on_propiedades_cambiadas(self, propiedades):
        """Cuando cambian las propiedades de un campo"""
        campo = self.preview_pdf.campo_seleccionado
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
        for campo_widget in self.preview_pdf.campos:
            if isinstance(campo_widget, CampoTextoWidget):
                configuracion["campos"].append(campo_widget.config)
        
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