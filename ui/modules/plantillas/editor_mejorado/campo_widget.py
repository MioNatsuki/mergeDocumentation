# ui/modules/plantillas/editor_mejorado/campo_widget.py
from PyQt6.QtWidgets import QFrame, QLabel, QVBoxLayout, QSizeGrip
from PyQt6.QtCore import Qt, pyqtSignal, QPoint, QRect
from PyQt6.QtGui import QMouseEvent, QPainter, QColor, QBrush, QFont

class CampoWidget(QFrame):
    """Widget arrastrable y redimensionable para campos en el PDF"""
    
    campo_modificado = pyqtSignal(dict)  # Nueva configuración
    campo_seleccionado = pyqtSignal(object)
    
    def __init__(self, tipo="texto", x_mm=50, y_mm=50, ancho_mm=50, alto_mm=10):
        super().__init__()
        self.tipo = tipo
        self.x_mm = x_mm
        self.y_mm = y_mm
        self.ancho_mm = ancho_mm
        self.alto_mm = alto_mm
        
        # Configuración del campo
        self.config = {
            "nombre": f"campo_{tipo}",
            "columna_padron": "",
            "campo_especial": "",  # ← NUEVO: para campos especiales
            "fuente": "Arial",
            "tamano": 12,
            "color": "#000000",
            "negrita": False,
            "cursiva": False,
            "alineacion": "left",
            "formato": "texto",
            "valor_fijo": "",  # ← Para texto fijo
            "formato_fecha": "dd/mm/yyyy",  # ← Para fechas
            "incluir_hora": False,  # ← Para fechas con hora
        }
        
        self.setup_ui()
        self.drag_pos = None
    
    def setup_ui(self):
        """Configura la apariencia del campo"""
        self.setFrameStyle(QFrame.Shape.Box)
        
        # Colores según tipo
        colores = {
            "texto": QColor(173, 216, 230, 180),  # Azul claro
            "tabla": QColor(144, 238, 144, 180),  # Verde claro
            "imagen": QColor(255, 218, 185, 180), # Melocotón
            "fecha": QColor(221, 160, 221, 180),  # Ciruela
            "moneda": QColor(255, 255, 153, 180), # Amarillo claro
            "codigo_barras": QColor(192, 192, 192, 180)  # Gris
        }
        
        color = colores.get(self.tipo, QColor(200, 200, 200, 180))
        
        self.setStyleSheet(f"""
            CampoWidget {{
                background-color: rgba({color.red()}, {color.green()}, {color.blue()}, 0.7);
                border: 2px solid rgba({color.red()//2}, {color.green()//2}, {color.blue()//2}, 0.9);
                border-radius: 3px;
            }}
            CampoWidget:hover {{
                border: 2px solid #ff0000;
            }}
        """)
        
        # Label con información del campo
        layout = QVBoxLayout()
        self.lbl_info = QLabel(self.get_icono() + " " + self.tipo.title())
        self.lbl_info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_info.setStyleSheet("font-size: 10px; font-weight: bold;")
        layout.addWidget(self.lbl_info)
        self.actualizar_texto_label()
        self.setLayout(layout)
        
        # Hacer arrastrable
        self.setCursor(Qt.CursorShape.SizeAllCursor)
    
    def get_icono(self):
        """Devuelve icono según tipo"""
        iconos = {
            "texto": "📝",
            "tabla": "📊",
            "imagen": "🖼️",
            "fecha": "📅",
            "moneda": "💰",
            "codigo_barras": "📊"
        }
        return iconos.get(self.tipo, "❓")
    
    def mousePressEvent(self, event: QMouseEvent):
        """Inicia arrastre"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            self.campo_seleccionado.emit(self)
            event.accept()
    
    def mouseMoveEvent(self, event: QMouseEvent):
        """Arrastra el campo"""
        if event.buttons() == Qt.MouseButton.LeftButton and self.drag_pos:
            self.move(event.globalPosition().toPoint() - self.drag_pos)
            
            # Actualizar posición en mm (asumiendo que parent tiene escala)
            if hasattr(self.parent(), 'escala'):
                escala = self.parent().escala
                self.x_mm = self.x() / escala
                self.y_mm = self.y() / escala
                
                # Emitir cambios
                self.campo_modificado.emit({
                    "x": self.x_mm,
                    "y": self.y_mm
                })
    
    def mouseReleaseEvent(self, event: QMouseEvent):
        """Termina arrastre"""
        self.drag_pos = None
    
    def actualizar_config(self, nueva_config):
        """Actualiza configuración del campo"""
        self.config.update(nueva_config)
        self.actualizar_texto_label()
        self.actualizar_estilo()
        self.update()

    def resizeEvent(self, event):
        """Cuando se redimensiona el campo"""
        super().resizeEvent(event)
        
        # Actualizar tamaño en mm (si hay escala disponible)
        if hasattr(self.parent(), 'escala'):
            escala = self.parent().escala
            self.ancho_mm = self.width() / escala
            self.alto_mm = self.height() / escala
            
            self.campo_modificado.emit({
                "ancho": self.ancho_mm,
                "alto": self.alto_mm
            })
    
    def actualizar_texto_label(self):
        """Actualiza el texto del label basado en configuración"""
        nombre = self.config.get("nombre", f"campo_{self.tipo}")
        
        # Si tiene columna del padrón, mostrarlo
        columna = self.config.get("columna_padron", "")
        if columna:
            if columna.startswith("especial:"):
                # Campo especial
                especial = columna.replace("especial:", "")
                self.lbl_info.setText(f"{self.get_icono()} {especial}")
            else:
                # Columna del padrón
                self.lbl_info.setText(f"{self.get_icono()} {columna}")
        else:
            # Sin mapeo aún
            self.lbl_info.setText(f"{self.get_icono()} {nombre}")
        
        # Tooltip con detalles
        tooltip = f"Tipo: {self.tipo.title()}\n"
        if columna:
            tooltip += f"Mapeado a: {columna}\n"
        tooltip += f"Posición: {self.x_mm:.0f}mm, {self.y_mm:.0f}mm\n"
        tooltip += f"Tamaño: {self.ancho_mm:.0f}mm × {self.alto_mm:.0f}mm"
        
        self.setToolTip(tooltip)

    def actualizar_estilo(self):
        """Actualiza el estilo visual según configuración"""
        # Colores base según tipo
        colores_base = {
            "texto": QColor(173, 216, 230),  # Azul claro
            "tabla": QColor(144, 238, 144),  # Verde claro
            "fecha": QColor(221, 160, 221),  # Ciruela
            "moneda": QColor(255, 255, 153), # Amarillo claro
            "numero": QColor(255, 218, 185), # Melocotón
            "codigo_barras": QColor(192, 192, 192)  # Gris
        }
        
        color_base = colores_base.get(self.tipo, QColor(200, 200, 200))
        
        # Intensidad según si está mapeado
        columna = self.config.get("columna_padron", "")
        if columna:
            # Mapeado - color más intenso
            r, g, b = color_base.red(), color_base.green(), color_base.blue()
        else:
            # No mapeado - color más tenue
            r, g, b = color_base.red()//2, color_base.green()//2, color_base.blue()//2
        
        self.setStyleSheet(f"""
            CampoWidget {{
                background-color: rgba({r}, {g}, {b}, 0.7);
                border: 2px solid rgba({r//2}, {g//2}, {b//2}, 0.9);
                border-radius: 3px;
            }}
            CampoWidget:hover {{
                border: 2px solid #ff0000;
            }}
        """)