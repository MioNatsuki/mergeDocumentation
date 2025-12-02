# ui/modules/plantillas/editor_mejorado/editor_visual.py
from PyQt6.QtWidgets import (QWidget, QHBoxLayout, QVBoxLayout, QLabel, 
                             QPushButton, QMessageBox, QSplitter, QFrame)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
import json
import os

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
        self.columnas_padron = []  # ← NUEVO: columnas del padrón
        self.uuid_padron = None    # ← NUEVO: UUID del padrón del proyecto
        
        self.setup_ui()
        self.cargar_datos_proyecto()  # ← CAMBIADO: cargar proyecto primero
        self.cargar_columnas_padron()  # ← Ahora con UUID real
    
    def setup_ui(self):
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
        
        title_layout.addWidget(lbl_title)
        title_layout.addStretch()
        title_layout.addWidget(self.lbl_pdf)
        title_bar.setLayout(title_layout)
        
        main_layout.addWidget(title_bar)
        
        # Área de trabajo principal (3 paneles)
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Panel izquierdo: Tipos de campos
        self.panel_campos = PanelCampos()
        self.panel_campos.campo_solicitado.connect(self.on_campo_solicitado)
        splitter.addWidget(self.panel_campos)
        
        # Panel central: Preview del PDF
        self.preview_pdf = PreviewPDF(self.pdf_path)
        self.preview_pdf.click_posicion.connect(self.on_click_pdf)
        self.preview_pdf.campo_seleccionado.connect(self.on_campo_seleccionado)
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
        
        bottom_layout.addWidget(btn_preview)
        bottom_layout.addStretch()
        bottom_layout.addWidget(btn_cancelar)
        bottom_layout.addWidget(btn_guardar)
        
        bottom_bar.setLayout(bottom_layout)
        main_layout.addWidget(bottom_bar)
        
        self.setLayout(main_layout)
    
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
                QMessageBox.warning(self, "Advertencia", 
                                  "Este proyecto no tiene un padrón configurado")
        except Exception as e:
            print(f"ERROR cargando proyecto: {e}")
        finally:
            db.close()
    
    def cargar_columnas_padron(self):
        """Carga las columnas del padrón del proyecto"""
        if not self.uuid_padron:
            print("DEBUG: No hay UUID de padrón, usando columnas de ejemplo")
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
                {"nombre": "estatus", "tipo": "texto", "ejemplo": "Activo"},
                {"nombre": "saldo_vencer", "tipo": "numero", "ejemplo": "5000.00"},
                {"nombre": "liquidacion", "tipo": "numero", "ejemplo": "0.00"},
                {"nombre": "ultimo_abono", "tipo": "fecha", "ejemplo": "2024-01-10"},
                {"nombre": "dependencia", "tipo": "texto", "ejemplo": "PENSIONES"},
                {"nombre": "afiliado_calle", "tipo": "texto", "ejemplo": "Calle Principal"},
                {"nombre": "afiliado_colonia", "tipo": "texto", "ejemplo": "Centro"},
                {"nombre": "afiliado_cp", "tipo": "texto", "ejemplo": "01000"},
                {"nombre": "afiliado_telefono", "tipo": "texto", "ejemplo": "5512345678"},
                {"nombre": "aval_nombre", "tipo": "texto", "ejemplo": "María González"},
                {"nombre": "aval_telefono", "tipo": "texto", "ejemplo": "5587654321"},
            ]
            self.columnas_padron = columnas_ejemplo
            self.panel_propiedades.cargar_columnas_padron(columnas_ejemplo)
            return
        
        from config.database import SessionLocal
        from core.padron_service import PadronService
        
        db = SessionLocal()
        try:
            padron_service = PadronService(db)
            self.columnas_padron = padron_service.obtener_columnas_padron(self.uuid_padron)
            
            if not self.columnas_padron:
                QMessageBox.warning(self, "Sin columnas", 
                                  "No se pudieron cargar las columnas del padrón.\n\n"
                                  "Verifica que:\n"
                                  "1. El padrón esté configurado correctamente\n"
                                  "2. Tengas permisos para leer la tabla\n"
                                  "3. La tabla exista en la base de datos")
                return
            
            print(f"DEBUG: Se cargaron {len(self.columnas_padron)} columnas del padrón")
            
            # Pasar columnas al panel de propiedades
            self.panel_propiedades.cargar_columnas_padron(self.columnas_padron)
            
        except Exception as e:
            print(f"ERROR cargando columnas: {e}")
            import traceback
            traceback.print_exc()
            QMessageBox.critical(self, "Error", f"No se pudieron cargar las columnas: {str(e)}")
        finally:
            db.close()

    def cargar_columnas_padron(self):
        """Carga las columnas del padrón del proyecto"""
        # Esto lo implementaremos mañana con la base de datos real
        # Por ahora, datos de ejemplo
        columnas_ejemplo = [
            {"nombre": "cuenta", "tipo": "texto"},
            {"nombre": "nombre", "tipo": "texto"},
            {"nombre": "adeudo", "tipo": "decimal"},
            {"nombre": "fecha_convenio", "tipo": "date"},
            {"nombre": "telefono", "tipo": "texto"},
            {"nombre": "direccion", "tipo": "texto"},
            {"nombre": "codigo_afiliado", "tipo": "texto"}
        ]
        
        self.panel_propiedades.cargar_columnas_padron(columnas_ejemplo)
    
    def on_campo_solicitado(self, tipo_campo):
        """Cuando se selecciona un tipo de campo en el panel izquierdo"""
        self.tipo_campo_actual = tipo_campo
        QMessageBox.information(self, "Listo", 
                              f"Ahora haz clic en el PDF donde quieres el campo '{tipo_campo}'")
    
    def on_click_pdf(self, x_mm, y_mm):
        """Cuando se hace clic en el PDF"""
        print(f"Agregando campo en: {x_mm}mm, {y_mm}mm")
        
        # Crear campo del tipo actual
        campo = CampoWidget(
            tipo=self.tipo_campo_actual,
            x_mm=x_mm,
            y_mm=y_mm,
            ancho_mm=50 if self.tipo_campo_actual != "tabla" else 150,
            alto_mm=10 if self.tipo_campo_actual != "tabla" else 60
        )
        
        # Conectar señales
        campo.campo_seleccionado.connect(self.on_campo_seleccionado)
        campo.campo_modificado.connect(self.on_campo_modificado)
        
        # Agregar al preview
        self.preview_pdf.agregar_campo_visual(campo)
        self.campos.append(campo)
        
        # Seleccionar automáticamente
        self.on_campo_seleccionado(campo)
    
    def on_campo_seleccionado(self, campo):
        """Cuando se selecciona un campo"""
        # Actualizar panel de propiedades
        self.panel_propiedades.mostrar_campo(campo)
    
    def on_campo_modificado(self, cambios):
        """Cuando se modifica un campo (arrastre, etc.)"""
        # Actualizar propiedades si están visibles
        if self.panel_propiedades.campo_actual:
            self.panel_propiedades.mostrar_campo(self.panel_propiedades.campo_actual)
    
    def on_propiedades_cambiadas(self, propiedades):
        """Cuando cambian las propiedades en el panel derecho"""
        if self.panel_propiedades.campo_actual:
            self.panel_propiedades.campo_actual.actualizar_config(propiedades)
    
    def previsualizar(self):
        """Genera una previsualización del PDF con datos de ejemplo"""
        QMessageBox.information(self, "Previsualizar", 
                              "Función de previsualización en desarrollo")
        # Aquí generaremos un PDF de prueba con datos mock
    
    def guardar_plantilla(self):
        """Guarda la configuración de la plantilla"""
        # Validar que haya campos
        if not self.campos:
            QMessageBox.warning(self, "Sin campos", 
                            "Debes agregar al menos un campo a la plantilla")
            return
        
        # Validar campos sin mapear
        campos_sin_mapear = []
        for campo in self.campos:
            config = campo.config
            if not config.get("columna_padron") and not config.get("campo_especial"):
                campos_sin_mapear.append(config.get("nombre", "Campo sin nombre"))
        
        if campos_sin_mapear:
            reply = QMessageBox.question(
                self, "Campos sin mapear",
                f"{len(campos_sin_mapear)} campo(s) no están mapeados a columnas:\n\n" +
                "\n".join(f"• {nombre}" for nombre in campos_sin_mapear[:5]) +
                ("\n..." if len(campos_sin_mapear) > 5 else "") +
                "\n\n¿Deseas continuar de todas formas?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.No:
                return
        
        # Recopilar configuración completa
        configuracion = {
            "version": "2.0",
            "pdf_base": self.pdf_path,
            "uuid_padron": self.uuid_padron,  # ← NUEVO: UUID del padrón
            "columnas_disponibles": self.columnas_padron,  # ← NUEVO: columnas cargadas
            "campos": {},
            "metadata": {
                "proyecto_id": self.proyecto_id,
                "usuario_creador": self.usuario.id,
                "fecha_creacion": "auto"
            }
        }
        
        for campo in self.campos:
            # Determinar si es campo especial
            columna = campo.config.get("columna_padron", "")
            es_especial = columna.startswith("especial:") if columna else False
            
            if es_especial:
                tipo_especial = columna.replace("especial:", "")
                campo.config["campo_especial"] = tipo_especial
                campo.config["columna_padron"] = ""  # Limpiar columna
            
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
        
        # Pedir nombre para la plantilla
        from PyQt6.QtWidgets import QInputDialog
        
        nombre, ok = QInputDialog.getText(
            self, 
            "Nombre de la plantilla",
            "Ingresa un nombre para la plantilla:",
            text=f"Plantilla con {len(self.campos)} campos"
        )
        
        if not ok or not nombre.strip():
            return
        
        configuracion["metadata"]["nombre_plantilla"] = nombre.strip()
        
        # Emitir señal con la configuración completa
        self.plantilla_guardada.emit(configuracion)
        
        print(f"DEBUG: Configuración lista para guardar:")
        print(f"  - Campos: {len(self.campos)}")
        print(f"  - UUID padrón: {self.uuid_padron}")
        print(f"  - Columnas disponibles: {len(self.columnas_padron)}")
    
    def cancelar(self):
        """Cancela la edición"""
        reply = QMessageBox.question(
            self, "Cancelar",
            "¿Está seguro de cancelar? Los cambios no guardados se perderán.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.plantilla_guardada.emit({})  # Diccionario vacío indica cancelación