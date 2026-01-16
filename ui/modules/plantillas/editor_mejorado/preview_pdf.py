# ui/modules/plantillas/editor_mejorado/preview_pdf.py - VERSIÓN CORREGIDA
from PyQt6.QtWidgets import (QFrame, QLabel, QVBoxLayout, QHBoxLayout,
                             QPushButton, QScrollArea, QWidget, QStackedWidget,
                             QGroupBox, QComboBox, QSpinBox, QMessageBox, QSizePolicy,
                             QApplication)
from PyQt6.QtCore import Qt, pyqtSignal, QPoint, QTimer, QSize
from PyQt6.QtGui import QPixmap, QImage, QMouseEvent, QWheelEvent, QPainter, QPen, QColor, QFont, QBrush
import fitz  # PyMuPDF
import traceback
from typing import List, Dict
from config.database import SessionLocal
from core.padron_service import PadronService
from core.models import Proyecto
import os

class PreviewPDF(QFrame):
    """Preview de PDF con datos REALES del padrón"""
    
    click_posicion = pyqtSignal(float, float)
    campo_seleccionado = pyqtSignal(object)
    solicita_agregar_campo = pyqtSignal(str, float, float)
    solicita_crear_campo_por_arrastre = pyqtSignal(str, float, float, float, float)
    solicita_terminar_arrastre = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__()
        self.pdf_path = None
        self.campos = []
        self.campo_seleccionado_actual = None
        self.imagenes_paginas = []
        self.pagina_actual = 0
        self.total_paginas = 0
        self.escala = 1.0
        self.arrastrando = False
        self.punto_inicio_arrastre = None
        self.punto_fin_arrastre = None
        self.rect_arrastre = None
        
        # Modos y datos REALES
        self.modo = 'seleccion'
        self.modo_vista = 'plantilla'  # 'plantilla' o 'preview'
        self.registros_reales = []  # ← Datos REALES del padrón
        self.registro_actual_idx = 0
        self.proyecto_id = None
        self.tipo_campo_a_agregar = None  # ← ¡NUEVO! Tipo de campo a agregar
        
        # UI para navegación
        self.barra_navegacion = None
        self.btn_anterior = None
        self.btn_siguiente = None
        self.lbl_registro = None
        
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
        
        # ===== BARRA SUPERIOR: Modos =====
        barra_modos = QFrame()
        barra_modos.setFixedHeight(40)
        barra_modos.setStyleSheet("""
            QFrame {
                background-color: #ffffff;
                border-bottom: 1px solid #e0e0e0;
            }
            QPushButton {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 4px;
                padding: 5px 15px;
                font-size: 11px;
                margin: 0 2px;
            }
            QPushButton:hover {
                background-color: #e9ecef;
            }
            QPushButton:checked {
                background-color: #007bff;
                color: white;
                font-weight: bold;
            }
        """)
        
        layout_modos = QHBoxLayout()
        layout_modos.setContentsMargins(10, 5, 10, 5)
        
        # Botones de modo vista
        self.btn_modo_plantilla = QPushButton("📝 Modo Edición")
        self.btn_modo_plantilla.setCheckable(True)
        self.btn_modo_plantilla.setChecked(True)
        self.btn_modo_plantilla.clicked.connect(lambda: self.cambiar_modo_vista('plantilla'))
        
        self.btn_modo_preview = QPushButton("👁️ Vista Previa")
        self.btn_modo_preview.setCheckable(True)
        self.btn_modo_preview.clicked.connect(lambda: self.cambiar_modo_vista('preview'))
        
        layout_modos.addWidget(self.btn_modo_plantilla)
        layout_modos.addWidget(self.btn_modo_preview)
        layout_modos.addStretch()
        
        # Información de proyecto
        self.lbl_info = QLabel("Sin PDF cargado")
        self.lbl_info.setStyleSheet("color: #666; font-size: 11px;")
        layout_modos.addWidget(self.lbl_info)
        
        barra_modos.setLayout(layout_modos)
        layout.addWidget(barra_modos)
        
        # ===== BARRA DE NAVEGACIÓN (sólo en preview) =====
        self.barra_navegacion = QFrame()
        self.barra_navegacion.setFixedHeight(40)
        self.barra_navegacion.setStyleSheet("""
            QFrame {
                background-color: #e3f2fd;
                border: 1px solid #bbdefb;
                border-radius: 4px;
                margin: 2px;
            }
            QPushButton {
                background-color: #2196f3;
                color: white;
                border: none;
                border-radius: 3px;
                padding: 5px 10px;
                font-size: 11px;
                min-width: 30px;
            }
            QPushButton:hover {
                background-color: #1976d2;
            }
            QPushButton:disabled {
                background-color: #90caf9;
                color: #e3f2fd;
            }
        """)
        
        layout_nav = QHBoxLayout()
        layout_nav.setContentsMargins(10, 5, 10, 5)
        
        self.btn_anterior = QPushButton("◀ Anterior")
        self.btn_anterior.clicked.connect(self.registro_anterior)
        
        self.lbl_registro = QLabel("Registro 0/0")
        self.lbl_registro.setStyleSheet("font-weight: bold; color: #0d47a1;")
        self.lbl_registro.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.btn_siguiente = QPushButton("Siguiente ▶")
        self.btn_siguiente.clicked.connect(self.registro_siguiente)
        
        layout_nav.addWidget(self.btn_anterior)
        layout_nav.addWidget(self.lbl_registro)
        layout_nav.addWidget(self.btn_siguiente)
        
        self.barra_navegacion.setLayout(layout_nav)
        self.barra_navegacion.hide()  # Ocultar inicialmente
        layout.addWidget(self.barra_navegacion)
        
        # ===== ÁREA DEL PDF =====
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll_area.setStyleSheet("background-color: #e8e8e8;")
        
        self.container_paginas = QStackedWidget()
        self.scroll_area.setWidget(self.container_paginas)
        layout.addWidget(self.scroll_area, 1)  # Factor de expansión 1
        
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
    
    def set_proyecto_id(self, proyecto_id: int):
        """Establece el proyecto para cargar datos del padrón"""
        self.proyecto_id = proyecto_id
    
    def mousePressEvent(self, event: QMouseEvent):
        """Inicia arrastre para crear campo"""
        # Si estamos en modo agregar y es clic izquierdo
        if (hasattr(self, 'tipo_campo_a_agregar') and self.tipo_campo_a_agregar and
            event.button() == Qt.MouseButton.LeftButton and
            self.modo_vista == 'plantilla'):
            
            # Obtener posición en mm
            lbl_imagen = self.get_current_image_label()
            if lbl_imagen:
                pos = event.pos()
                x_mm = pos.x() / lbl_imagen.escala
                y_mm = pos.y() / lbl_imagen.escala
                
                # Iniciar arrastre
                self.arrastrando = True
                self.punto_inicio_arrastre = (x_mm, y_mm)
                self.punto_fin_arrastre = (x_mm, y_mm)
                
                print(f"📐 Iniciando arrastre en: ({x_mm:.1f}, {y_mm:.1f})")
        else:
            super().mousePressEvent(event)

    def cambiar_modo_vista(self, modo: str):
        """Cambia entre modo plantilla y preview"""
        self.modo_vista = modo
        
        if modo == 'plantilla':
            self.btn_modo_plantilla.setChecked(True)
            self.btn_modo_preview.setChecked(False)
            self.barra_navegacion.hide()
            self.actualizar_vista_plantilla()
            
        else:  # preview
            self.btn_modo_plantilla.setChecked(False)
            self.btn_modo_preview.setChecked(True)
            
            # Intentar cargar datos si no los tenemos
            if not self.registros_reales:
                self.cargar_datos_reales()
            
            if self.registros_reales:
                self.barra_navegacion.show()
                self.actualizar_vista_preview()
            else:
                QMessageBox.warning(self, "Sin datos", 
                                  "No hay datos en el padrón para vista previa")
                self.cambiar_modo_vista('plantilla')

    def cambiar_modo_agregar(self, tipo_campo: str = None):
        """Cambia al modo agregar campo específico"""
        if tipo_campo:
            self.modo = 'agregar_campo'
            self.tipo_campo_a_agregar = tipo_campo  # ← NUEVA VARIABLE
            self.barra_estado.setText(f"➕ Agregar {tipo_campo} - Haz clic en el PDF")
        else:
            self.modo = 'seleccion'
            self.tipo_campo_a_agregar = None
            self.barra_estado.setText("👆 Modo selección")

    def cargar_datos_reales(self):
        """Carga datos REALES del padrón desde la base de datos"""
        if not self.proyecto_id:
            return
        
        db = SessionLocal()
        try:
            # 1. Obtener el proyecto
            proyecto = db.query(Proyecto).filter(Proyecto.id == self.proyecto_id).first()
            if not proyecto or not proyecto.tabla_padron:
                QMessageBox.warning(self, "Sin padrón", 
                                  "Este proyecto no tiene una tabla de padrón configurada")
                return
            
            # 2. Obtener datos del padrón
            padron_service = PadronService(db)
            self.registros_reales = padron_service.obtener_todos_registros(
                proyecto.tabla_padron, 
                limit=50  # Primeros 50 registros para preview
            )
            
            if not self.registros_reales:
                QMessageBox.information(self, "Sin datos", 
                                      "No hay datos en el padrón. Usando datos de ejemplo...")
                # Crear datos de ejemplo
                self.registros_reales = self.crear_datos_ejemplo()
            
            # 3. Resetear índice
            self.registro_actual_idx = 0
            
            # 4. Actualizar UI
            self.actualizar_barra_navegacion()
            
            print(f"✅ Cargados {len(self.registros_reales)} registros REALES del padrón")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error cargando datos: {str(e)}")
            traceback.print_exc()
            # Usar datos de ejemplo como fallback
            self.registros_reales = self.crear_datos_ejemplo()
        finally:
            db.close()
    
    def crear_datos_ejemplo(self):
        """Crea datos de ejemplo si no hay padrón"""
        datos = []
        for i in range(10):
            registro = {
                'nombre': f'Nombre {i+1}',
                'apellido': f'Apellido {i+1}',
                'dni': f'{10000000 + i}',
                'direccion': f'Calle {i+1} #123',
                'telefono': f'555-{1000 + i}',
                'email': f'usuario{i+1}@ejemplo.com',
                'fecha_nacimiento': f'198{min(i, 9)}-01-{i+1:02d}',
                'monto_adeudo': f'${(i+1) * 1000}'
            }
            datos.append(registro)
        return datos
    
    def actualizar_barra_navegacion(self):
        """Actualiza la barra de navegación"""
        total = len(self.registros_reales)
        actual = self.registro_actual_idx + 1
        
        self.lbl_registro.setText(f"Registro {actual}/{total}")
        
        # Habilitar/deshabilitar botones
        self.btn_anterior.setEnabled(self.registro_actual_idx > 0)
        self.btn_siguiente.setEnabled(self.registro_actual_idx < total - 1)
    
    def registro_anterior(self):
        """Muestra el registro anterior"""
        if self.registro_actual_idx > 0:
            self.registro_actual_idx -= 1
            self.actualizar_vista_preview()
    
    def registro_siguiente(self):
        """Muestra el siguiente registro"""
        if self.registro_actual_idx < len(self.registros_reales) - 1:
            self.registro_actual_idx += 1
            self.actualizar_vista_preview()
    
    def actualizar_vista_plantilla(self):
        """Vuelve a mostrar placeholders {columna}"""
        for campo in self.campos:
            if hasattr(campo, 'set_modo'):
                campo.set_modo('plantilla')
            # No necesitas llamar a actualizar_texto() si usas actualizar_vista_completa()
        
        if self.total_paginas > 0:
            self.barra_estado.setText(f"📝 Modo Edición - Página {self.pagina_actual + 1}/{self.total_paginas}")
    
    def actualizar_vista_preview(self):
        """Muestra datos REALES del registro actual"""
        if not self.registros_reales or self.registro_actual_idx >= len(self.registros_reales):
            self.barra_estado.setText("⚠️ No hay datos para vista previa")
            return
        
        try:
            datos_actuales = self.registros_reales[self.registro_actual_idx]
            
            print(f"📊 Mostrando registro {self.registro_actual_idx + 1}")
            
            # ACTUALIZAR CADA CAMPO
            for campo in self.campos:
                try:
                    # Cambiar a modo preview
                    if hasattr(campo, 'set_modo'):
                        campo.set_modo('preview')
                    
                    # Pasar datos reales
                    if hasattr(campo, 'set_datos_preview'):
                        campo.set_datos_preview(datos_actuales)
                    
                except Exception as e:
                    print(f"Error actualizando campo: {e}")
            
            # Actualizar UI
            self.actualizar_barra_navegacion()
            
            total = len(self.registros_reales)
            actual = self.registro_actual_idx + 1
            
            # Mostrar datos del registro actual
            muestra = ""
            for key in list(datos_actuales.keys())[:2]:
                if key in datos_actuales:
                    valor = str(datos_actuales[key])
                    if len(valor) > 20:
                        valor = valor[:20] + "..."
                    muestra += f"{key}: {valor}  "
            
            self.barra_estado.setText(
                f"👁️ Vista Previa - Registro {actual}/{total} | {muestra}"
            )
            
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
    
    def cargar_pdf(self, pdf_path: str):
        """Carga un PDF"""
        if not os.path.exists(pdf_path):
            self.mostrar_error(f"Archivo no encontrado: {pdf_path}")
            return
        
        try:
            self.pdf_path = pdf_path
            
            # Limpiar widgets anteriores
            self.limpiar_paginas()
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
                pagina_widget = self.crear_pagina_widget(doc, page_num)
                self.container_paginas.addWidget(pagina_widget)
            
            doc.close()
            
            # Mostrar primera página
            self.pagina_actual = 0
            self.container_paginas.setCurrentIndex(0)
            
            self.barra_estado.setText(f"✅ PDF cargado: {os.path.basename(pdf_path)} - {self.total_paginas} página(s)")
            
        except Exception as e:
            self.mostrar_error(f"Error cargando PDF: {str(e)}")
            traceback.print_exc()
    
    def crear_pagina_widget(self, doc, page_num):
        """Crea widget para una página del PDF"""
        pagina_widget = QWidget()
        pagina_layout = QVBoxLayout()
        pagina_layout.setContentsMargins(0, 0, 0, 0)
        pagina_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Renderizar página
        pagina = doc[page_num]
        zoom = 1.8  # Zoom para buena visualización
        mat = fitz.Matrix(zoom, zoom)
        pix = pagina.get_pixmap(matrix=mat, alpha=False)
        
        # Crear imagen
        img = QImage(pix.samples, pix.width, pix.height, pix.stride, QImage.Format.Format_RGB888)
        pixmap = QPixmap.fromImage(img)
        
        # Crear label para la imagen
        lbl_imagen = QLabel()
        lbl_imagen.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_imagen.setPixmap(pixmap)
        lbl_imagen.setFixedSize(pix.width, pix.height)
        
        # Guardar escala (píxeles por mm)
        # A4 = 210x297mm, asumimos que es A4
        self.escala = pix.width / 210  # pixeles por mm (ancho A4)
        lbl_imagen.escala = self.escala
        lbl_imagen.page_num = page_num
        
        # Conectar eventos
        lbl_imagen.mousePressEvent = lambda e, p=page_num: self.on_click_pagina(e, p)
        lbl_imagen.mouseMoveEvent = self.on_mouse_move_pagina
        lbl_imagen.setMouseTracking(True)
        
        # Guardar referencia
        self.imagenes_paginas.append({
            'pixmap': pixmap,
            'width': pix.width,
            'height': pix.height,
            'escala': self.escala
        })
        
        pagina_layout.addWidget(lbl_imagen)
        pagina_widget.setLayout(pagina_layout)
        
        return pagina_widget
    def mouseMoveEvent(self, event: QMouseEvent):
        """Dibuja rectángulo de arrastre"""
        if self.arrastrando:
            lbl_imagen = self.get_current_image_label()
            if lbl_imagen:
                pos = event.pos()
                x_mm = pos.x() / lbl_imagen.escala
                y_mm = pos.y() / lbl_imagen.escala
                
                self.punto_fin_arrastre = (x_mm, y_mm)
                
                # Forzar redibujado para mostrar rectángulo
                self.update()
        
        super().mouseMoveEvent(event)
    
    def mouseReleaseEvent(self, event: QMouseEvent):
        """Termina arrastre y crea campo"""
        if self.arrastrando and event.button() == Qt.MouseButton.LeftButton:
            lbl_imagen = self.get_current_image_label()
            if lbl_imagen:
                pos = event.pos()
                x_mm = pos.x() / lbl_imagen.escala
                y_mm = pos.y() / lbl_imagen.escala
                
                self.punto_fin_arrastre = (x_mm, y_mm)
                
                # Crear campo con el rectángulo
                if (self.punto_inicio_arrastre and self.punto_fin_arrastre and
                    hasattr(self, 'tipo_campo_a_agregar') and self.tipo_campo_a_agregar):
                    
                    x1, y1 = self.punto_inicio_arrastre
                    x2, y2 = self.punto_fin_arrastre
                    
                    print(f"📐 Creando campo {self.tipo_campo_a_agregar}: "
                          f"({x1:.1f},{y1:.1f}) → ({x2:.1f},{y2:.1f})")
                    
                    # Emitir señal para crear campo
                    self.solicita_crear_campo_por_arrastre.emit(
                        self.tipo_campo_a_agregar, x1, y1, x2, y2
                    )
                
                # Resetear
                self.arrastrando = False
                self.punto_inicio_arrastre = None
                self.punto_fin_arrastre = None
                self.update()
                
                # Volver a modo selección
                self.cambiar_modo_agregar(None)
            
            self.solicita_terminar_arrastre.emit()
        
        super().mouseReleaseEvent(event)
    
    def paintEvent(self, event):
        """Dibuja rectángulo de arrastre"""
        super().paintEvent(event)
        
        if self.arrastrando and self.punto_inicio_arrastre and self.punto_fin_arrastre:
            lbl_imagen = self.get_current_image_label()
            if lbl_imagen:
                painter = QPainter(self)
                painter.setPen(QPen(QColor(0, 120, 255), 2, Qt.PenStyle.DashLine))
                painter.setBrush(QBrush(QColor(0, 120, 255, 30)))
                
                # Convertir mm a píxeles
                x1 = int(self.punto_inicio_arrastre[0] * lbl_imagen.escala)
                y1 = int(self.punto_inicio_arrastre[1] * lbl_imagen.escala)
                x2 = int(self.punto_fin_arrastre[0] * lbl_imagen.escala)
                y2 = int(self.punto_fin_arrastre[1] * lbl_imagen.escala)
                
                # Dibujar rectángulo
                x = min(x1, x2)
                y = min(y1, y2)
                w = abs(x2 - x1)
                h = abs(y2 - y1)
                
                painter.drawRect(x, y, w, h)
                
                # Dibujar texto del tipo
                painter.setPen(QPen(QColor(0, 0, 0), 1))
                painter.drawText(x + 5, y + 15, 
                               f"{self.tipo_campo_a_agregar.upper()}: {w/lbl_imagen.escala:.1f}×{h/lbl_imagen.escala:.1f} mm")
    
    def get_current_image_label(self):
        """Obtiene el QLabel de la imagen actual"""
        pagina_widget = self.container_paginas.currentWidget()
        if pagina_widget:
            return pagina_widget.findChild(QLabel)
        return None

    def limpiar_paginas(self):
        """Limpia todas las páginas"""
        while self.container_paginas.count():
            widget = self.container_paginas.widget(0)
            self.container_paginas.removeWidget(widget)
            widget.deleteLater()
        
        self.imagenes_paginas = []
    
    def deseleccionar_todos_los_campos(self):
        """Deselecciona ABSOLUTAMENTE TODOS los campos"""
        if self.campo_seleccionado_actual:
            if hasattr(self.campo_seleccionado_actual, 'set_seleccionado'):
                self.campo_seleccionado_actual.set_seleccionado(False)
            self.campo_seleccionado_actual = None
        
        # Asegurarnos de deseleccionar cualquier campo que se haya quedado marcado
        for campo in self.campos:
            if hasattr(campo, 'config') and campo.config.get('seleccionado', False):
                if hasattr(campo, 'set_seleccionado'):
                    campo.set_seleccionado(False)

    def on_click_pagina(self, event: QMouseEvent, pagina_num: int):
        """Maneja clic en la página - VERSIÓN CORREGIDA Y FUNCIONAL"""
        lbl_imagen = self.sender()
        if not lbl_imagen:
            return
        
        pos = event.pos()
        
        print(f"\n🔍 CLICK en página:")
        print(f"  Modo: '{self.modo}'")
        print(f"  Tipo campo a agregar: '{getattr(self, 'tipo_campo_a_agregar', 'NO DEFINIDO')}'")
        print(f"  Posición: ({pos.x()}, {pos.y()})")
        
        # 1. Verificar si estamos en modo AGREGAR CAMPO
        if hasattr(self, 'tipo_campo_a_agregar') and self.tipo_campo_a_agregar:
            if self.modo_vista == 'plantilla':  # Solo en modo edición
                # Convertir coordenadas a mm
                x_mm = pos.x() / lbl_imagen.escala
                y_mm = pos.y() / lbl_imagen.escala
                
                print(f"  🎯 AGREGANDO NUEVO CAMPO:")
                print(f"     Tipo: {self.tipo_campo_a_agregar}")
                print(f"     Posición mm: ({x_mm:.1f}, {y_mm:.1f})")
                
                # ¡EMITIR SEÑAL PARA AGREGAR CAMPO!
                self.solicita_agregar_campo.emit(self.tipo_campo_a_agregar, x_mm, y_mm)
                
                # Volver a modo selección automáticamente
                self.cambiar_modo_agregar(None)
                print("  🔄 Volviendo a modo selección")
                return
        
        # 2. Si NO estamos en modo agregar, verificar si clickeamos un campo existente
        campo_clicado = None
        for campo in self.campos:
            try:
                if campo.geometry().contains(pos) and campo.isVisible():
                    campo_clicado = campo
                    break
            except:
                continue
        
        if campo_clicado:
            # Seleccionar el campo clickeado
            self.seleccionar_campo(campo_clicado)
            print(f"  ✅ Seleccionado campo: {campo_clicado.config.get('nombre', 'sin nombre')}")
        else:
            # Click fuera de campos → deseleccionar todo
            print("  🖱️ Click fuera de campos - Deseleccionando")
            self.deseleccionar_todos_los_campos()
    
    def on_mouse_move_pagina(self, event: QMouseEvent):
        """Muestra coordenadas al mover el mouse"""
        lbl_imagen = self.sender()
        if lbl_imagen and hasattr(lbl_imagen, 'escala'):
            x_mm = event.pos().x() / lbl_imagen.escala
            y_mm = event.pos().y() / lbl_imagen.escala
            
            if self.modo_vista == 'preview' and self.registros_reales:
                registro_actual = self.registro_actual_idx + 1
                total = len(self.registros_reales)
                info = f"📊 Vista Previa - Registro {registro_actual}/{total} | X={x_mm:.1f}mm, Y={y_mm:.1f}mm"
            else:
                info = f"📝 Modo Edición - Página {self.pagina_actual + 1}/{self.total_paginas} | X={x_mm:.1f}mm, Y={y_mm:.1f}mm"
            
            self.barra_estado.setText(info)
    
    def agregar_campo_visual(self, campo_widget, x_mm: float, y_mm: float):
        """Agrega un campo visualmente"""
        pagina_widget = self.container_paginas.widget(self.pagina_actual)
        if not pagina_widget:
            return
        
        lbl_imagen = pagina_widget.findChild(QLabel)
        if not lbl_imagen:
            return
        
        # Configurar campo
        campo_widget.setParent(lbl_imagen)
        campo_widget.config['pagina'] = self.pagina_actual
        
        # Convertir mm a píxeles
        x_px = int(x_mm * lbl_imagen.escala)
        y_px = int(y_mm * lbl_imagen.escala)
        
        campo_widget.move(x_px, y_px)
        
        # Configurar tamaño
        if 'ancho' in campo_widget.config and 'alto' in campo_widget.config:
            ancho_px = int(campo_widget.config['ancho'] * lbl_imagen.escala)
            alto_px = int(campo_widget.config['alto'] * lbl_imagen.escala)
            campo_widget.setFixedSize(ancho_px, alto_px)
        
        campo_widget.show()
        self.campos.append(campo_widget)
        self.seleccionar_campo(campo_widget)
        
        # Actualizar vista según modo actual
        if self.modo_vista == 'preview' and self.registros_reales:
            datos_actuales = self.registros_reales[self.registro_actual_idx]
            if hasattr(campo_widget, 'set_datos_preview_real'):
                campo_widget.set_datos_preview_real(datos_actuales)
        
        campo_widget.show()
        self.campos.append(campo_widget)
        self.seleccionar_campo(campo_widget)
    
    def seleccionar_campo(self, campo):
        """Selecciona un campo - VERSIÓN MEJORADA CON DESELECCIÓN GLOBAL"""
        # 1. Deseleccionar TODOS los campos primero
        self.deseleccionar_todos_los_campos()
        
        # 2. Seleccionar el nuevo campo
        self.campo_seleccionado_actual = campo
        
        if hasattr(campo, 'set_seleccionado'):
            campo.set_seleccionado(True)
        
        # 3. Emitir señal para que panel de propiedades se actualice
        self.campo_seleccionado.emit(campo)
        
        # 4. Feedback visual
        print(f"✅ Campo seleccionado: {campo.config.get('nombre', 'sin nombre')}")
    
    def eliminar_campo(self, campo):
        """Elimina un campo - CON LIMPIEZA DE SELECCIÓN"""
        if campo in self.campos:
            self.campos.remove(campo)
            
            # Si el campo eliminado estaba seleccionado, limpiar
            if self.campo_seleccionado_actual == campo:
                self.deseleccionar_todos_los_campos()
        
        campo.deleteLater()
    
    def mostrar_error(self, mensaje: str):
        """Muestra error en la UI"""
        self.barra_estado.setText(f"❌ {mensaje}")
        
        # Limpiar y mostrar mensaje de error
        self.limpiar_paginas()
        
        widget_error = QWidget()
        layout = QVBoxLayout()
        lbl_error = QLabel(f"❌ Error\n\n{mensaje}")
        lbl_error.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_error.setStyleSheet("color: #cc0000; font-size: 14px; padding: 40px;")
        layout.addWidget(lbl_error)
        widget_error.setLayout(layout)
        
        self.container_paginas.addWidget(widget_error)
    
    def mostrar_registro(self, registro_idx: int):
        """Muestra un registro específico"""
        if 0 <= registro_idx < len(self.registros_reales):
            self.registro_actual_idx = registro_idx
            self.actualizar_vista_preview()
            return True
        return False

    def ir_a_registro(self, numero: int):
        """Va a un registro por número (1-based)"""
        if 1 <= numero <= len(self.registros_reales):
            self.mostrar_registro(numero - 1)

    def siguiente_registro(self):
        """Muestra el siguiente registro"""
        if self.registro_actual_idx < len(self.registros_reales) - 1:
            self.registro_actual_idx += 1
            self.actualizar_vista_preview()
            return True
        return False

    def anterior_registro(self):
        """Muestra el registro anterior"""
        if self.registro_actual_idx > 0:
            self.registro_actual_idx -= 1
            self.actualizar_vista_preview()
            return True
        return False

    def actualizar_vista_preview(self):
        """Muestra datos REALES del registro actual - VERSIÓN MEJORADA"""
        if not self.registros_reales or self.registro_actual_idx >= len(self.registros_reales):
            self.barra_estado.setText("⚠️ No hay datos para vista previa")
            return
        
        try:
            # Obtener datos del registro actual
            datos_actuales = self.registros_reales[self.registro_actual_idx]
            
            print(f"📊 Mostrando registro {self.registro_actual_idx + 1}: {list(datos_actuales.keys())[:3]}...")
            
            # Actualizar cada campo con los datos REALES
            campos_actualizados = 0
            for campo in self.campos:
                try:
                    # Para campos simples
                    if hasattr(campo, 'set_modo_preview'):
                        campo.set_modo_preview(datos_actuales)
                        campos_actualizados += 1
                    
                    # Para campos compuestos (si existen)
                    elif hasattr(campo, 'get_texto_preview'):
                        texto = campo.get_texto_preview(datos_actuales)
                        # Buscar labels dentro del campo
                        for child in campo.findChildren(QLabel):
                            child.setText(texto)
                        campos_actualizados += 1
                    
                    # Para campos con método antiguo (backward compatibility)
                    elif hasattr(campo, 'set_datos_preview'):
                        campo.set_datos_preview(datos_actuales)
                        campos_actualizados += 1
                        
                except Exception as e:
                    print(f"Error actualizando campo {campo.config.get('nombre', 'sin nombre')}: {e}")
            
            print(f"✅ Actualizados {campos_actualizados} campos")
            
            # Actualizar barra de navegación
            self.actualizar_barra_navegacion()
            
            # Actualizar barra de estado con información útil
            total = len(self.registros_reales)
            actual = self.registro_actual_idx + 1
            
            # Mostrar algunos datos del registro actual (para debug)
            muestra = ""
            for key in list(datos_actuales.keys())[:2]:  # Primeros 2 campos
                if key in datos_actuales:
                    valor = str(datos_actuales[key])[:20]  # Limitar longitud
                    muestra += f"{key}: {valor}... "
            
            self.barra_estado.setText(
                f"👁️ Vista Previa - Registro {actual}/{total} | {muestra}"
            )
            
        except Exception as e:
            print(f"❌ Error en actualizar_vista_preview: {e}")
            import traceback
            traceback.print_exc()
            self.barra_estado.setText(f"⚠️ Error cargando registro: {str(e)}")

    def setup_barra_navegacion_mejorada(self):
        """Configura barra de navegación con más controles"""
        # Si ya existe, limpiarla
        if self.barra_navegacion:
            self.barra_navegacion.deleteLater()
        
        self.barra_navegacion = QFrame()
        self.barra_navegacion.setFixedHeight(50)
        self.barra_navegacion.setStyleSheet("""
            QFrame {
                background-color: #e3f2fd;
                border: 1px solid #bbdefb;
                border-radius: 4px;
                margin: 2px;
            }
            QPushButton {
                background-color: #2196f3;
                color: white;
                border: none;
                border-radius: 3px;
                padding: 6px 12px;
                font-size: 11px;
                min-width: 40px;
                margin: 0 2px;
            }
            QPushButton:hover {
                background-color: #1976d2;
            }
            QPushButton:disabled {
                background-color: #90caf9;
                color: #e3f2fd;
            }
            QSpinBox {
                background-color: white;
                border: 1px solid #90caf9;
                border-radius: 3px;
                padding: 4px;
                font-size: 11px;
                min-width: 50px;
            }
        """)
        
        layout_nav = QHBoxLayout()
        layout_nav.setContentsMargins(10, 5, 10, 5)
        layout_nav.setSpacing(5)
        
        # Botón Ir al primero
        self.btn_primero = QPushButton("⏮️ Primero")
        self.btn_primero.clicked.connect(lambda: self.ir_a_registro(1))
        self.btn_primero.setToolTip("Ir al primer registro")
        
        # Botón Anterior
        self.btn_anterior = QPushButton("◀ Anterior")
        self.btn_anterior.clicked.connect(self.anterior_registro)
        
        # Contador y selector
        contador_layout = QHBoxLayout()
        contador_layout.setSpacing(5)
        
        self.lbl_registro = QLabel("Registro")
        self.lbl_registro.setStyleSheet("font-weight: bold; color: #0d47a1;")
        
        self.spin_registro = QSpinBox()
        self.spin_registro.setMinimum(1)
        self.spin_registro.setMaximum(1)  # Se actualizará dinámicamente
        self.spin_registro.valueChanged.connect(self.ir_a_registro)
        
        self.lbl_total = QLabel("/ 0")
        self.lbl_total.setStyleSheet("color: #666;")
        
        contador_layout.addWidget(self.lbl_registro)
        contador_layout.addWidget(self.spin_registro)
        contador_layout.addWidget(self.lbl_total)
        
        # Botón Siguiente
        self.btn_siguiente = QPushButton("Siguiente ▶")
        self.btn_siguiente.clicked.connect(self.siguiente_registro)
        
        # Botón Ir al último
        self.btn_ultimo = QPushButton("Último ⏭️")
        self.btn_ultimo.clicked.connect(lambda: self.ir_a_registro(len(self.registros_reales)))
        self.btn_ultimo.setToolTip("Ir al último registro")
        
        # Botón Actualizar datos
        self.btn_actualizar = QPushButton("🔄 Actualizar")
        self.btn_actualizar.clicked.connect(self.recargar_datos)
        self.btn_actualizar.setToolTip("Recargar datos del padrón")
        
        layout_nav.addWidget(self.btn_primero)
        layout_nav.addWidget(self.btn_anterior)
        layout_nav.addLayout(contador_layout)
        layout_nav.addWidget(self.btn_siguiente)
        layout_nav.addWidget(self.btn_ultimo)
        layout_nav.addStretch()
        layout_nav.addWidget(self.btn_actualizar)
        
        self.barra_navegacion.setLayout(layout_nav)
        
        # Insertar después de la barra de modos
        self.layout().insertWidget(2, self.barra_navegacion)
        self.barra_navegacion.hide()

    def actualizar_barra_navegacion(self):
        """Actualiza la barra de navegación con los datos actuales"""
        if not hasattr(self, 'spin_registro'):
            return
        
        total = len(self.registros_reales)
        actual = self.registro_actual_idx + 1
        
        # Actualizar controles
        self.spin_registro.blockSignals(True)  # Evitar señal durante actualización
        self.spin_registro.setMaximum(max(1, total))
        self.spin_registro.setValue(actual)
        self.spin_registro.blockSignals(False)
        
        self.lbl_total.setText(f"/ {total}")
        
        # Actualizar estado de botones
        self.btn_primero.setEnabled(actual > 1)
        self.btn_anterior.setEnabled(actual > 1)
        self.btn_siguiente.setEnabled(actual < total)
        self.btn_ultimo.setEnabled(actual < total)
        
        # Actualizar tooltips
        self.btn_actualizar.setToolTip(f"Recargar datos ({total} registros cargados)")

    def recargar_datos(self):
        """Recarga los datos del padrón"""
        if self.proyecto_id:
            # Limpiar datos actuales
            self.registros_reales = []
            self.registro_actual_idx = 0
            
            # Mostrar mensaje de carga
            self.barra_estado.setText("🔄 Cargando datos del padrón...")
            QApplication.processEvents()  # Actualizar UI
            
            # Recargar
            self.cargar_datos_reales()
            
            # Si hay datos, mostrar el primero
            if self.registros_reales:
                self.mostrar_registro(0)
                self.barra_estado.setText(f"✅ {len(self.registros_reales)} registros recargados")
            else:
                self.barra_estado.setText("⚠️ No hay datos en el padrón")

    def cambiar_modo_vista(self, modo: str):
        """Cambia entre modo plantilla y preview"""
        self.modo_vista = modo
        
        if modo == 'plantilla':
            self.btn_modo_plantilla.setChecked(True)
            self.btn_modo_preview.setChecked(False)
            
            if hasattr(self, 'barra_navegacion'):
                self.barra_navegacion.hide()
            
            # IMPORTANTE: Cambiar TODOS los campos a modo plantilla
            self.actualizar_vista_plantilla()
            
        else:  # preview
            self.btn_modo_plantilla.setChecked(False)
            self.btn_modo_preview.setChecked(True)
            
            # Inicializar navegación
            if not hasattr(self, 'spin_registro'):
                self.setup_barra_navegacion_mejorada()
            
            # Cargar datos si no los tenemos
            if not self.registros_reales:
                self.cargar_datos_reales()
            
            if self.registros_reales:
                self.barra_navegacion.show()
                self.mostrar_registro(0)
            else:
                QMessageBox.warning(self, "Sin datos", 
                                "No hay datos en el padrón para vista previa")
                self.cambiar_modo_vista('plantilla')