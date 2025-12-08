# ui/modules/plantillas/editor_mejorado/preview_pdf.py - VERSIÓN CORREGIDA
from PyQt6.QtWidgets import (QFrame, QLabel, QVBoxLayout, QHBoxLayout,
                             QPushButton, QScrollArea, QWidget, QStackedWidget,
                             QGroupBox, QComboBox, QSpinBox, QMessageBox)
from PyQt6.QtCore import Qt, pyqtSignal, QPoint, QTimer, QSize
from PyQt6.QtGui import QPixmap, QImage, QMouseEvent, QWheelEvent, QPainter, QPen, QColor
import fitz  # PyMuPDF
import tempfile
import os
from PIL import Image
import traceback

class PreviewPDF(QFrame):
    """Preview de PDF - VERSIÓN CORREGIDA"""
    
    click_posicion = pyqtSignal(float, float)
    campo_seleccionado = pyqtSignal(object)
    solicita_agregar_campo = pyqtSignal(str, float, float)
    
    def __init__(self, parent=None):
        super().__init__()
        self.pdf_path = None
        self.campos = []
        self.campo_seleccionado_actual = None
        self.imagenes_paginas = []
        self.pagina_actual = 0
        self.total_paginas = 0
        self.escala = 2.0
        
        # Modos
        self.modo = 'seleccion'
        self.modo_vista = 'plantilla'
        self.registros = []
        self.registro_actual = 0
        
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
        
        # Barra superior será manejada por el editor principal
        # Solo ponemos el área del PDF aquí
        
        # ===== ÁREA DEL PDF =====
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll_area.setStyleSheet("background-color: #e8e8e8;")
        
        self.container_paginas = QStackedWidget()
        self.scroll_area.setWidget(self.container_paginas)
        layout.addWidget(self.scroll_area)
        
        # ===== BARRA INFERIOR: Estado =====
        self.barra_estado = QLabel("📄 Selecciona un PDF para comenzar")
        self.barra_estado.setStyleSheet("""
            QLabel {
                background-color: #ffffff;
                border-top: 1px solid #e0e0e0;
                color: #666;
                font-size: 11px;
                padding: 3px 10px;
                min-height: 20px;
            }
        """)
        layout.addWidget(self.barra_estado)
        
        self.setLayout(layout)
    
    def cambiar_modo(self, modo: str):
        """Cambia el modo de interacción"""
        self.modo = modo
        
        if modo == 'seleccion':
            self.barra_estado.setText("🖱️ Haz clic para seleccionar campos")
            self.actualizar_cursor_seleccion()
        elif modo == 'agregar_texto':
            self.barra_estado.setText("➕ Haz clic para agregar campo de texto")
            self.actualizar_cursor_cruz()
        elif modo == 'agregar_compuesto':
            self.barra_estado.setText("🧩 Haz clic para agregar campo compuesto")
            self.actualizar_cursor_cruz()
        elif modo == 'agregar_tabla':
            self.barra_estado.setText("📊 Haz clic para agregar tabla")
            self.actualizar_cursor_cruz()
    
    def actualizar_cursor_seleccion(self):
        """Cursor para modo selección"""
        current_widget = self.container_paginas.currentWidget()
        if current_widget:
            lbl_imagen = current_widget.findChild(QLabel)
            if lbl_imagen:
                lbl_imagen.setCursor(Qt.CursorShape.ArrowCursor)
    
    def actualizar_cursor_cruz(self):
        """Cursor para modo agregar"""
        current_widget = self.container_paginas.currentWidget()
        if current_widget:
            lbl_imagen = current_widget.findChild(QLabel)
            if lbl_imagen:
                lbl_imagen.setCursor(Qt.CursorShape.CrossCursor)
    
    def cambiar_modo_vista(self, modo: str):
        """Cambia entre modo plantilla y preview"""
        self.modo_vista = modo
        if modo == 'preview':
            self.actualizar_vista_preview()
        else:
            self.actualizar_vista_plantilla()
    
    def actualizar_vista_plantilla(self):
        """Vuelve a mostrar placeholders"""
        for campo in self.campos:
            if hasattr(campo, 'set_modo'):
                campo.set_modo('plantilla')
            if hasattr(campo, 'actualizar_texto'):
                campo.actualizar_texto()
        
        if self.total_paginas > 0:
            self.barra_estado.setText(f"Modo edición - Página {self.pagina_actual + 1}/{self.total_paginas}")
    
    def actualizar_vista_preview(self):
        """Muestra datos reales"""
        if not self.registros:
            self.barra_estado.setText("⚠️ No hay datos para vista previa")
            return
        
        for campo in self.campos:
            if hasattr(campo, 'set_modo'):
                campo.set_modo('preview')
            
            if self.registro_actual < len(self.registros):
                datos = self.registros[self.registro_actual]
                
                if hasattr(campo, 'set_datos_preview'):
                    campo.set_datos_preview(datos)
                elif hasattr(campo, 'get_texto_preview'):
                    texto = campo.get_texto_preview(datos)
                    for child in campo.findChildren(QLabel):
                        child.setText(texto)
        
        # Actualizar barra de estado
        if self.registros:
            paginas_totales = len(self.registros)  # Cada registro es una "página" en preview
            self.barra_estado.setText(f"👁️ Vista Previa - Registro {self.registro_actual + 1}/{len(self.registros)}")
    
    def registro_anterior(self):
        if self.registro_actual > 0:
            self.registro_actual -= 1
            self.actualizar_vista_preview()
    
    def registro_siguiente(self):
        if self.registro_actual < len(self.registros) - 1:
            self.registro_actual += 1
            self.actualizar_vista_preview()
    
    def cargar_pdf(self, pdf_path: str):
        """Carga un PDF - VERSIÓN CORREGIDA"""
        if not os.path.exists(pdf_path):
            self.mostrar_error(f"Archivo no encontrado: {pdf_path}")
            return
        
        try:
            self.pdf_path = pdf_path
            
            # Limpiar widgets anteriores - CORREGIDO
            while self.container_paginas.count():
                widget = self.container_paginas.widget(0)
                if widget:
                    self.container_paginas.removeWidget(widget)
                    widget.deleteLater()
            
            self.imagenes_paginas = []
            self.campos = []
            
            # Abrir PDF
            doc = fitz.open(pdf_path)
            self.total_paginas = len(doc)
            
            if self.total_paginas == 0:
                self.mostrar_error("El PDF no tiene páginas")
                doc.close()
                return
            
            # Renderizar cada página
            for page_num in range(self.total_paginas):
                pagina_widget = QWidget()
                pagina_layout = QVBoxLayout()
                pagina_layout.setContentsMargins(0, 0, 0, 0)
                pagina_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
                
                lbl_imagen = QLabel()
                lbl_imagen.setAlignment(Qt.AlignmentFlag.AlignCenter)
                lbl_imagen.setMouseTracking(True)
                lbl_imagen.mousePressEvent = lambda e, p=page_num: self.on_click_pagina(e, p)
                lbl_imagen.mouseMoveEvent = self.on_mouse_move_pagina
                lbl_imagen.leaveEvent = self.on_leave_pagina
                
                # Renderizar
                pagina = doc[page_num]
                zoom = 1.8
                mat = fitz.Matrix(zoom, zoom)
                pix = pagina.get_pixmap(matrix=mat, alpha=False)
                
                # Convertir
                img = QImage(pix.samples, pix.width, pix.height, pix.stride, QImage.Format.Format_RGB888)
                pixmap = QPixmap.fromImage(img)
                
                lbl_imagen.setPixmap(pixmap)
                lbl_imagen.setFixedSize(pix.width, pix.height)
                
                # Guardar escala
                lbl_imagen.page_num = page_num
                lbl_imagen.escala = pix.width / (210 * zoom)  # 210mm = A4 ancho
                
                pagina_layout.addWidget(lbl_imagen)
                pagina_widget.setLayout(pagina_layout)
                
                self.container_paginas.addWidget(pagina_widget)
                self.imagenes_paginas.append({
                    'pixmap': pixmap,
                    'width': pix.width,
                    'height': pix.height,
                    'escala': lbl_imagen.escala
                })
            
            doc.close()
            
            # Mostrar primera página
            self.pagina_actual = 0
            self.container_paginas.setCurrentIndex(0)
            
            self.barra_estado.setText(f"✅ PDF cargado: {os.path.basename(pdf_path)} - {self.total_paginas} página(s)")
            
        except Exception as e:
            self.mostrar_error(f"Error cargando PDF: {str(e)}")
            traceback.print_exc()
    
    def on_click_pagina(self, event: QMouseEvent, pagina_num: int):
        lbl_imagen = self.sender()
        if not lbl_imagen:
            return
        
        pos = event.pos()
        
        # Primero: verificar si se clickeó en un campo existente
        for campo in self.campos:
            if campo.geometry().contains(pos) and campo.isVisible():
                self.seleccionar_campo(campo)
                return
        
        # Segundo: si estamos en modo "agregar_campo" y el editor tiene un tipo definido
        if self.modo == 'agregar_campo' and self.modo_vista == 'plantilla':
            # Obtener el editor padre para saber qué tipo de campo agregar
            editor = self.parent()
            while editor and not hasattr(editor, 'tipo_campo_a_agregar'):
                editor = editor.parent()
            
            if editor and editor.tipo_campo_a_agregar:
                x_mm = pos.x() / lbl_imagen.escala
                y_mm = pos.y() / lbl_imagen.escala
                
                # Emitir señal con el tipo de campo
                self.solicita_agregar_campo.emit(
                    editor.tipo_campo_a_agregar, 
                    x_mm, 
                    y_mm
                )
                
                # Volver automáticamente a modo selección
                self.cambiar_modo('seleccion')
                if hasattr(editor, 'cambiar_modo'):
                    editor.cambiar_modo('seleccion')
        
    def on_mouse_move_pagina(self, event: QMouseEvent):
        lbl_imagen = self.sender()
        if lbl_imagen and hasattr(lbl_imagen, 'escala'):
            x_mm = event.pos().x() / lbl_imagen.escala
            y_mm = event.pos().y() / lbl_imagen.escala
            
            if self.modo_vista == 'preview' and self.registros:
                info = f"Registro {self.registro_actual + 1}/{len(self.registros)} | X={x_mm:.1f}mm, Y={y_mm:.1f}mm"
            else:
                info = f"Página {self.pagina_actual + 1}/{self.total_paginas} | X={x_mm:.1f}mm, Y={y_mm:.1f}mm"
            
            self.barra_estado.setText(info)
    
    def on_leave_pagina(self, event):
        if self.modo_vista == 'plantilla':
            if self.modo == 'seleccion':
                self.barra_estado.setText(f"Página {self.pagina_actual + 1}/{self.total_paginas} - Modo selección")
            else:
                self.barra_estado.setText(f"Página {self.pagina_actual + 1}/{self.total_paginas} - Haz clic para agregar")
        else:
            if self.registros:
                self.barra_estado.setText(f"Vista previa - Registro {self.registro_actual + 1}/{len(self.registros)}")
    
    def agregar_campo_visual(self, campo_widget, x_mm: float, y_mm: float):
        pagina_widget = self.container_paginas.widget(self.pagina_actual)
        if not pagina_widget:
            return
        
        lbl_imagen = pagina_widget.findChild(QLabel)
        if not lbl_imagen:
            return
        
        campo_widget.setParent(lbl_imagen)
        campo_widget.config['pagina'] = self.pagina_actual
        
        x_px = int(x_mm * lbl_imagen.escala)
        y_px = int(y_mm * lbl_imagen.escala)
        
        campo_widget.move(x_px, y_px)
        
        if hasattr(campo_widget, 'config'):
            if 'ancho' in campo_widget.config and 'alto' in campo_widget.config:
                ancho_px = int(campo_widget.config['ancho'] * lbl_imagen.escala)
                alto_px = int(campo_widget.config['alto'] * lbl_imagen.escala)
                campo_widget.setFixedSize(ancho_px, alto_px)
        
        campo_widget.show()
        self.campos.append(campo_widget)
        self.seleccionar_campo(campo_widget)
    
    def seleccionar_campo(self, campo):
        if self.campo_seleccionado_actual:
            self.campo_seleccionado_actual.set_seleccionado(False)
        
        self.campo_seleccionado_actual = campo
        campo.set_seleccionado(True)
        self.campo_seleccionado.emit(campo)
    
    def eliminar_campo(self, campo):
        if campo in self.campos:
            self.campos.remove(campo)
            campo.deleteLater()
            
            if self.campo_seleccionado_actual == campo:
                self.campo_seleccionado_actual = None
    
    def set_registros_preview(self, registros):
        self.registros = registros
        self.registro_actual = 0
        
        if registros:
            self.barra_estado.setText(f"✅ {len(registros)} registros cargados para vista previa")
    
    def mostrar_error(self, mensaje: str):
        self.barra_estado.setText(f"❌ {mensaje}")
        
        # Limpiar widgets - CORREGIDO
        while self.container_paginas.count():
            widget = self.container_paginas.widget(0)
            if widget:
                self.container_paginas.removeWidget(widget)
                widget.deleteLater()
        
        widget_error = QWidget()
        layout = QVBoxLayout()
        lbl_error = QLabel(f"❌ Error\n\n{mensaje}")
        lbl_error.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_error.setStyleSheet("color: #cc0000; font-size: 14px; padding: 40px;")
        layout.addWidget(lbl_error)
        widget_error.setLayout(layout)
        
        self.container_paginas.addWidget(widget_error)