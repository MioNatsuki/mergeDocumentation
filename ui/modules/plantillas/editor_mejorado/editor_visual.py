# ui/modules/plantillas/editor_mejorado/editor_visual.py - VERSIÓN COMPLETA FUNCIONAL
from PyQt6.QtWidgets import (QWidget, QHBoxLayout, QVBoxLayout, QLabel, 
                             QPushButton, QMessageBox, QSplitter, QFrame,
                             QInputDialog, QScrollArea)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QColor
import json
import os
import traceback

from .preview_pdf import PreviewPDF
from .campo_widget import CampoWidget
from .panel_campos import PanelCampos
from .panel_propiedades import PanelPropiedades

class EditorVisual(QWidget):
    """Editor visual principal (3 paneles como lo describiste)"""
    
    plantilla_guardada = pyqtSignal(dict)  # Configuración completa
    
    def __init__(self, usuario, proyecto_id, pdf_path, plantilla_id=None):
        super().__init__()
        self.usuario = usuario
        self.proyecto_id = proyecto_id
        self.pdf_path = pdf_path
        self.plantilla_id = plantilla_id
        self.campos = []  # Lista de objetos CampoWidget
        self.tipo_campo_actual = "texto"  # Tipo por defecto
        self.columnas_padron = []  # Columnas del padrón
        self.uuid_padron = None    # UUID del padrón del proyecto
        
        self.setup_ui()
        self.cargar_datos_proyecto()  # Cargar proyecto primero
        self.cargar_columnas_padron()  # Obtener columnas del padrón
        
        # Debug
        print(f"DEBUG: EditorVisual inicializado")
        print(f"  PDF: {pdf_path}")
        print(f"  Proyecto ID: {proyecto_id}")
        print(f"  Tipo campo actual: {self.tipo_campo_actual}")
    
    def setup_ui(self):
        """Configura la interfaz de 3 paneles"""
        # Layout principal
        main_layout = QVBoxLayout()
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Barra de título
        title_bar = QFrame()
        title_bar.setStyleSheet("""
            QFrame {
                background-color: #2c3e50;
                padding: 10px;
            }
        """)
        
        title_layout = QHBoxLayout()
        
        lbl_title = QLabel("🎨 Editor de Plantillas")
        lbl_title.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        lbl_title.setStyleSheet("color: white;")
        
        self.lbl_pdf = QLabel(f"PDF: {os.path.basename(self.pdf_path)}")
        self.lbl_pdf.setStyleSheet("color: #bdc3c7; font-size: 12px;")
        
        self.lbl_estado = QLabel("Selecciona un tipo de campo y haz clic en el PDF")
        self.lbl_estado.setStyleSheet("color: #ecf0f1; font-size: 11px; font-style: italic;")
        
        title_layout.addWidget(lbl_title)
        title_layout.addWidget(self.lbl_pdf)
        title_layout.addStretch()
        title_layout.addWidget(self.lbl_estado)
        title_bar.setLayout(title_layout)
        
        main_layout.addWidget(title_bar)
        
        # Área de trabajo principal (3 paneles)
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Panel izquierdo: Tipos de campos
        self.panel_campos = PanelCampos()
        self.panel_campos.campo_solicitado.connect(self.on_campo_solicitado)
        splitter.addWidget(self.panel_campos)
        
        # Panel central: Preview del PDF
        print(f"DEBUG: Creando PreviewPDF con: {self.pdf_path}")
        try:
            self.preview_pdf = PreviewPDF(self.pdf_path)
            
            # ¡CONECTAR LAS SEÑALES! - ESTO ES CRÍTICO
            self.preview_pdf.click_posicion.connect(self.on_click_pdf)
            self.preview_pdf.campo_seleccionado.connect(self.on_campo_seleccionado)
            
            print(f"DEBUG: PreviewPDF creado, señales conectadas")
        except Exception as e:
            print(f"ERROR creando PreviewPDF: {e}")
            traceback.print_exc()
            # Crear placeholder de error
            self.preview_pdf = QFrame()
            self.preview_pdf.setStyleSheet("background-color: #ffcccc;")
            error_label = QLabel(f"❌ Error cargando PDF:\n{str(e)[:100]}")
            error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout_error = QVBoxLayout()
            layout_error.addWidget(error_label)
            self.preview_pdf.setLayout(layout_error)
        
        splitter.addWidget(self.preview_pdf)
        
        # Panel derecho: Propiedades
        self.panel_propiedades = PanelPropiedades()
        self.panel_propiedades.propiedades_cambiadas.connect(self.on_propiedades_cambiadas)
        splitter.addWidget(self.panel_propiedades)
        
        # Configurar tamaños iniciales
        splitter.setSizes([200, 600, 300])
        
        main_layout.addWidget(splitter)
        
        # Barra inferior con botones
        bottom_bar = QFrame()
        bottom_bar.setStyleSheet("""
            QFrame {
                background-color: #ecf0f1;
                padding: 10px;
                border-top: 1px solid #bdc3c7;
            }
        """)
        
        bottom_layout = QHBoxLayout()
        
        # Contador de campos
        self.lbl_contador = QLabel("Campos: 0")
        self.lbl_contador.setStyleSheet("color: #7f8c8d; font-weight: bold;")
        
        # Botón previsualizar
        btn_preview = QPushButton("👁️ Previsualizar")
        btn_preview.clicked.connect(self.previsualizar)
        btn_preview.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                padding: 8px 15px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        
        # Botón guardar
        btn_guardar = QPushButton("💾 Guardar Plantilla")
        btn_guardar.clicked.connect(self.guardar_plantilla)
        btn_guardar.setStyleSheet("""
            QPushButton {
                background-color: #2ecc71;
                color: white;
                border: none;
                padding: 8px 15px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #27ae60;
            }
        """)
        
        # Botón cancelar
        btn_cancelar = QPushButton("❌ Cancelar")
        btn_cancelar.clicked.connect(self.cancelar)
        btn_cancelar.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                border: none;
                padding: 8px 15px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
        """)
        
        bottom_layout.addWidget(self.lbl_contador)
        bottom_layout.addWidget(btn_preview)
        bottom_layout.addStretch()
        bottom_layout.addWidget(btn_cancelar)
        bottom_layout.addWidget(btn_guardar)
        
        bottom_bar.setLayout(bottom_layout)
        main_layout.addWidget(bottom_bar)
        
        self.setLayout(main_layout)
        
        # Establecer foco
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
    
    def cargar_datos_proyecto(self):
        """Carga el proyecto para obtener el UUID del padrón"""
        from config.database import SessionLocal
        from core.models import Proyecto
        
        db = SessionLocal()
        try:
            proyecto = db.query(Proyecto).filter(Proyecto.id == self.proyecto_id).first()
            if proyecto and proyecto.tabla_padron:
                self.uuid_padron = proyecto.tabla_padron
                print(f"DEBUG: Proyecto {self.proyecto_id} - UUID padrón: {self.uuid_padron}")
            else:
                print(f"DEBUG: Proyecto sin padrón configurado")
                self.lbl_estado.setText("⚠️ Proyecto sin padrón configurado - usando datos de ejemplo")
        except Exception as e:
            print(f"ERROR cargando proyecto: {e}")
        finally:
            db.close()
    
    def cargar_columnas_padron(self):
        """Carga las columnas del padrón del proyecto"""
        # Columnas de ejemplo como fallback
        columnas_ejemplo = [
            {"nombre": "cuenta", "tipo": "texto", "ejemplo": "123456"},
            {"nombre": "codigo_afiliado", "tipo": "texto", "ejemplo": "A001"},
            {"nombre": "nombre", "tipo": "texto", "ejemplo": "Juan Pérez"},
            {"nombre": "adeudo", "tipo": "numero", "ejemplo": "12500.50"},
            {"nombre": "fecha_convenio", "tipo": "fecha", "ejemplo": "2024-01-15"},
            {"nombre": "telefono", "tipo": "texto", "ejemplo": "5512345678"},
            {"nombre": "direccion", "tipo": "texto", "ejemplo": "Calle Principal 123"},
            {"nombre": "rfc", "tipo": "texto", "ejemplo": "XAXX010101000"},
        ]
        
        # Intentar cargar columnas reales si hay UUID
        if self.uuid_padron:
            try:
                from config.database import SessionLocal
                from core.padron_service import PadronService
                
                db = SessionLocal()
                padron_service = PadronService(db)
                columnas_reales = padron_service.obtener_columnas_padron(self.uuid_padron)
                
                if columnas_reales:
                    self.columnas_padron = columnas_reales
                    print(f"DEBUG: Se cargaron {len(columnas_reales)} columnas reales del padrón")
                else:
                    self.columnas_padron = columnas_ejemplo
                    print(f"DEBUG: Usando columnas de ejemplo (no se encontraron reales)")
            except Exception as e:
                print(f"ERROR cargando columnas reales: {e}")
                self.columnas_padron = columnas_ejemplo
        else:
            self.columnas_padron = columnas_ejemplo
            print(f"DEBUG: Usando columnas de ejemplo (sin UUID de padrón)")
        
        # Pasar columnas al panel de propiedades
        self.panel_propiedades.cargar_columnas_padron(self.columnas_padron)
    
    # --- MANEJO DE EVENTOS ---
    
    def on_campo_solicitado(self, tipo_campo):
        """Cuando se selecciona un tipo de campo en el panel izquierdo"""
        self.tipo_campo_actual = tipo_campo
        self.lbl_estado.setText(f"✅ Listo: Haz clic en el PDF para agregar campo '{tipo_campo}'")
        print(f"DEBUG: Tipo de campo seleccionado: {tipo_campo}")
        
        # Feedback visual breve
        original_text = self.lbl_estado.text()
        QMessageBox.information(self, "Listo", 
                              f"Ahora haz clic en el PDF donde quieres el campo '{tipo_campo}'")
    
    def on_click_pdf(self, x_mm, y_mm):
        """Cuando se hace clic en el PDF"""
        print(f"DEBUG: on_click_pdf recibido: ({x_mm}, {y_mm})")
        print(f"DEBUG: Click en PDF - Posición: {x_mm}mm, {y_mm}mm")
        print(f"DEBUG: Agregando campo tipo: {self.tipo_campo_actual}")
        
        # Tamaños por defecto según tipo
        tamanos = {
            "texto": {"ancho": 50, "alto": 10},
            "tabla": {"ancho": 150, "alto": 60},
            "imagen": {"ancho": 80, "alto": 80},
            "fecha": {"ancho": 40, "alto": 10},
            "moneda": {"ancho": 60, "alto": 10},
            "codigo_barras": {"ancho": 100, "alto": 30},
            "numero": {"ancho": 40, "alto": 10}
        }
        
        tamano = tamanos.get(self.tipo_campo_actual, {"ancho": 50, "alto": 10})
        
        try:
            # Crear campo del tipo actual
            campo = CampoWidget(
                tipo=self.tipo_campo_actual,
                x_mm=x_mm,
                y_mm=y_mm,
                ancho_mm=tamano["ancho"],
                alto_mm=tamano["alto"]
            )
            
            # Nombre por defecto
            campo.config["nombre"] = f"{self.tipo_campo_actual}_{len(self.campos) + 1}"
            
            # Conectar señales
            campo.campo_seleccionado.connect(self.on_campo_seleccionado)
            campo.campo_modificado.connect(self.on_campo_modificado)
            
            # Agregar al preview
            self.preview_pdf.agregar_campo_visual(campo)
            self.campos.append(campo)
            
            # Seleccionar automáticamente
            self.on_campo_seleccionado(campo)
            
            # Actualizar contador
            self.lbl_contador.setText(f"Campos: {len(self.campos)}")
            
            # Feedback
            self.lbl_estado.setText(f"✅ Campo '{self.tipo_campo_actual}' agregado en ({x_mm}mm, {y_mm}mm)")
            
            print(f"DEBUG: Campo creado exitosamente")
            
        except Exception as e:
            print(f"ERROR creando campo: {e}")
            traceback.print_exc()
            QMessageBox.critical(self, "Error", f"No se pudo crear el campo: {str(e)}")
    
    def on_campo_seleccionado(self, campo):
        """Cuando se selecciona un campo (click en él)"""
        print(f"DEBUG: Campo seleccionado: {campo.config.get('nombre', 'sin nombre')}")
        
        # Actualizar panel de propiedades
        self.panel_propiedades.mostrar_campo(campo)
        
        # Actualizar estado
        nombre = campo.config.get("nombre", "Campo sin nombre")
        self.lbl_estado.setText(f"📌 Campo seleccionado: '{nombre}'")
    
    def on_campo_modificado(self, cambios):
        """Cuando se modifica un campo (arrastre, etc.)"""
        # Actualizar propiedades si están visibles
        if self.panel_propiedades.campo_actual:
            self.panel_propiedades.mostrar_campo(self.panel_propiedades.campo_actual)
    
    def on_propiedades_cambiadas(self, propiedades):
        """Cuando cambian las propiedades en el panel derecho"""
        if self.panel_propiedades.campo_actual:
            print(f"DEBUG: Propiedades cambiadas para campo")
            self.panel_propiedades.campo_actual.actualizar_config(propiedades)
    
    def previsualizar(self):
        """Genera una previsualización del PDF con datos de ejemplo"""
        if not self.campos:
            QMessageBox.warning(self, "Sin campos", "No hay campos para previsualizar")
            return
        
        # Generar datos de ejemplo
        datos_ejemplo = {}
        for columna in self.columnas_padron:
            nombre = columna["nombre"]
            ejemplo = columna.get("ejemplo", "Ejemplo")
            datos_ejemplo[nombre] = ejemplo
        
        # Agregar campos especiales
        datos_ejemplo["fecha_actual"] = "15/01/2024"
        datos_ejemplo["codigo_barras"] = "|123456789|"
        datos_ejemplo["texto_fijo"] = "Texto fijo de ejemplo"
        
        # Mostrar diálogo de previsualización
        from PyQt6.QtWidgets import QDialog, QTextEdit
        
        dialog = QDialog(self)
        dialog.setWindowTitle("📄 Previsualización de Datos")
        dialog.setMinimumSize(500, 400)
        
        layout = QVBoxLayout()
        
        lbl_info = QLabel("Datos que se insertarán en los campos:")
        layout.addWidget(lbl_info)
        
        text_edit = QTextEdit()
        text_edit.setReadOnly(True)
        
        # Formatear datos
        texto = "=== DATOS DE EJEMPLO ===\n\n"
        for campo in self.campos:
            nombre = campo.config.get("nombre", "sin nombre")
            columna = campo.config.get("columna_padron", "no mapeado")
            
            if columna:
                if columna.startswith("especial:"):
                    valor = datos_ejemplo.get(columna.replace("especial:", ""), "N/A")
                else:
                    valor = datos_ejemplo.get(columna, "N/A")
            else:
                valor = "[NO MAPEADO]"
            
            texto += f"• {nombre}: {valor}\n"
        
        text_edit.setText(texto)
        layout.addWidget(text_edit)
        
        btn_cerrar = QPushButton("Cerrar")
        btn_cerrar.clicked.connect(dialog.close)
        layout.addWidget(btn_cerrar)
        
        dialog.setLayout(layout)
        dialog.exec()
    
    def guardar_plantilla(self):
        """Guarda la configuración de la plantilla"""
        # Validar que haya campos
        if not self.campos:
            QMessageBox.warning(self, "Sin campos", 
                              "Debes agregar al menos un campo a la plantilla")
            return
        
        # Recopilar configuración
        configuracion = {
            "version": "2.0",
            "pdf_base": self.pdf_path,
            "uuid_padron": self.uuid_padron,
            "campos": {},
            "metadata": {
                "proyecto_id": self.proyecto_id,
                "usuario_creador": self.usuario.id if self.usuario else 0
            }
        }
        
        for campo in self.campos:
            configuracion["campos"][campo.config["nombre"]] = {
                "tipo": campo.tipo,
                "config": campo.config,
                "posicion": {
                    "x": campo.x_mm,
                    "y": campo.y_mm,
                    "ancho": campo.ancho_mm,
                    "alto": campo.alto_mm
                }
            }
        
        # Pedir nombre
        nombre, ok = QInputDialog.getText(
            self, 
            "Nombre de la plantilla",
            "Ingresa un nombre para la plantilla:",
            text=f"Plantilla con {len(self.campos)} campos"
        )
        
        if not ok or not nombre.strip():
            return
        
        configuracion["metadata"]["nombre_plantilla"] = nombre.strip()
        
        # Emitir señal
        print(f"DEBUG: Emitiendo señal plantilla_guardada con {len(self.campos)} campos")
        self.plantilla_guardada.emit(configuracion)
        
        QMessageBox.information(self, "Éxito", 
                              f"✅ Plantilla '{nombre}' guardada con {len(self.campos)} campos")
    
    def cancelar(self):
        """Cancela la edición"""
        reply = QMessageBox.question(
            self, "Cancelar",
            "¿Está seguro de cancelar? Los cambios no guardados se perderán.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.plantilla_guardada.emit({})  # Diccionario vacío indica cancelación
    
    def keyPressEvent(self, event):
        """Maneja atajos de teclado"""
        # Escape para cancelar
        if event.key() == Qt.Key.Key_Escape:
            self.cancelar()
        # Ctrl+S para guardar
        elif event.key() == Qt.Key.Key_S and event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            self.guardar_plantilla()
        # Ctrl+P para previsualizar
        elif event.key() == Qt.Key.Key_P and event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            self.previsualizar()
        else:
            super().keyPressEvent(event)