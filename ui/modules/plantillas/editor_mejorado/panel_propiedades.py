# ui/modules/plantillas/editor_mejorado/panel_propiedades.py
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QLineEdit, 
                             QComboBox, QSpinBox, QCheckBox, QPushButton,
                             QFormLayout, QGroupBox, QColorDialog, QHBoxLayout,
                             QFrame, QScrollArea)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QColor
import traceback

class PanelPropiedades(QFrame):
    """Panel de propiedades con conexión REAL a base de datos"""
    
    propiedades_cambiadas = pyqtSignal(dict)
    
    def __init__(self, proyecto_id):
        super().__init__()
        self.proyecto_id = proyecto_id
        self.campo_actual = None
        self.columnas_padron = []
        self.setup_ui()
        self.cargar_columnas_reales()
        self.hide()
    
    def setup_ui(self):
        self.setFrameStyle(QFrame.Shape.StyledPanel)
        self.setStyleSheet("""
            PanelPropiedades { 
                background-color: #ffffff; 
                border: 1px solid #ddd;
                border-radius: 4px;
            }
            QLabel {
                color: #333;
                font-size: 11px;
                font-weight: bold;
            }
            QLineEdit, QComboBox, QSpinBox {
                background-color: #f9f9f9;
                border: 1px solid #ddd;
                border-radius: 3px;
                padding: 4px;
                font-size: 11px;
                min-height: 25px;
            }
            QLineEdit:focus, QComboBox:focus, QSpinBox:focus {
                border-color: #007bff;
                background-color: #ffffff;
            }
            QPushButton {
                background-color: #f8f9fa;
                border: 1px solid #ddd;
                border-radius: 3px;
                padding: 5px 10px;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #e9ecef;
                border-color: #007bff;
            }
            QCheckBox {
                font-size: 11px;
                spacing: 5px;
            }
        """)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)
        
        # Título
        self.lbl_titulo = QLabel("⚙️ Propiedades")
        self.lbl_titulo.setStyleSheet("font-size: 12px; font-weight: bold; color: #2c3e50;")
        layout.addWidget(self.lbl_titulo)
        
        # Línea separadora
        separador = QFrame()
        separador.setFrameShape(QFrame.Shape.HLine)
        separador.setStyleSheet("background-color: #e0e0e0;")
        layout.addWidget(separador)
        
        # Scroll area para contenido
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("border: none;")
        
        widget_contenido = QWidget()
        contenido_layout = QVBoxLayout()
        contenido_layout.setContentsMargins(5, 5, 5, 5)
        contenido_layout.setSpacing(8)
        
        # Nombre interno
        lbl_nombre = QLabel("Nombre:")
        contenido_layout.addWidget(lbl_nombre)
        self.txt_nombre = QLineEdit()
        self.txt_nombre.setPlaceholderText("Nombre del campo...")
        self.txt_nombre.textChanged.connect(self.actualizar_cambios)
        contenido_layout.addWidget(self.txt_nombre)
        
        # Columna del padrón
        lbl_columna = QLabel("📊 Columna del Padrón:")
        contenido_layout.addWidget(lbl_columna)
        self.combo_columna = QComboBox()
        self.combo_columna.currentTextChanged.connect(self.actualizar_cambios)
        contenido_layout.addWidget(self.combo_columna)
        
        # Información de columna
        self.lbl_info_columna = QLabel("")
        self.lbl_info_columna.setStyleSheet("color: #666; font-size: 9px; font-style: italic;")
        contenido_layout.addWidget(self.lbl_info_columna)
        
        # Botones de estilo
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(5)
        self.btn_fuente = QPushButton("🔤 Fuente")
        self.btn_fuente.clicked.connect(self.cambiar_fuente)
        self.btn_color = QPushButton("🎨 Color")
        self.btn_color.clicked.connect(self.cambiar_color)
        btn_layout.addWidget(self.btn_fuente)
        btn_layout.addWidget(self.btn_color)
        contenido_layout.addLayout(btn_layout)
        
        # Opciones de formato
        formato_layout = QHBoxLayout()
        self.check_negrita = QCheckBox("B")
        self.check_negrita.setStyleSheet("font-weight: bold;")
        self.check_negrita.stateChanged.connect(self.actualizar_cambios)
        
        self.check_cursiva = QCheckBox("I")
        self.check_cursiva.setStyleSheet("font-style: italic;")
        self.check_cursiva.stateChanged.connect(self.actualizar_cambios)
        
        formato_layout.addWidget(self.check_negrita)
        formato_layout.addWidget(self.check_cursiva)
        formato_layout.addStretch()
        contenido_layout.addLayout(formato_layout)
        
        # Espaciador
        contenido_layout.addStretch()
        
        widget_contenido.setLayout(contenido_layout)
        scroll.setWidget(widget_contenido)
        layout.addWidget(scroll)
        
        self.setLayout(layout)
        self.setMinimumWidth(200)
    
    def cargar_columnas_reales(self):
        """Carga columnas del padrón DESDE LA BASE DE DATOS REAL"""
        try:
            # Importar dentro del método para evitar dependencias circulares
            from config.database import SessionLocal
            from core.models import Proyecto
            from core.padron_service import PadronService
            
            db = SessionLocal()
            try:
                # Obtener el proyecto
                proyecto = db.query(Proyecto).filter(Proyecto.id == self.proyecto_id).first()
                if not proyecto or not proyecto.tabla_padron:
                    print(f"Proyecto {self.proyecto_id} no encontrado o sin padrón")
                    self.columnas_padron = []
                    return
                
                # Obtener columnas del padrón
                padron_service = PadronService(db)
                self.columnas_padron = padron_service.obtener_columnas_padron(proyecto.tabla_padron)
                
                # Limpiar y cargar combo
                self.combo_columna.clear()
                self.combo_columna.addItem("-- Sin columna asignada --", "")
                
                for columna in self.columnas_padron:
                    nombre = columna["nombre"]
                    tipo = columna["tipo"]
                    self.combo_columna.addItem(f"{nombre} ({tipo})", nombre)
                    
                print(f"Cargadas {len(self.columnas_padron)} columnas del padrón")
                
            except Exception as e:
                print(f"Error cargando columnas REALES: {str(e)}")
                traceback.print_exc()
                # En caso de error, cargar datos de ejemplo
                self.cargar_columnas_ejemplo()
            finally:
                db.close()
                
        except ImportError as e:
            print(f"Error de importación: {str(e)}")
            # Para demo, cargar datos de ejemplo
            self.cargar_columnas_ejemplo()
    
    def cargar_columnas_ejemplo(self):
        """Carga columnas de ejemplo si falla la conexión a BD"""
        print("Cargando columnas de ejemplo...")
        self.columnas_padron = [
            {"nombre": "nombre", "tipo": "varchar", "nullable": False},
            {"nombre": "apellido", "tipo": "varchar", "nullable": False},
            {"nombre": "dni", "tipo": "integer", "nullable": False},
            {"nombre": "direccion", "tipo": "varchar", "nullable": True},
            {"nombre": "telefono", "tipo": "varchar", "nullable": True},
            {"nombre": "email", "tipo": "varchar", "nullable": True},
            {"nombre": "fecha_nacimiento", "tipo": "date", "nullable": True},
            {"nombre": "edad", "tipo": "integer", "nullable": True}
        ]
        
        self.combo_columna.clear()
        self.combo_columna.addItem("-- Sin columna asignada --", "")
        
        for columna in self.columnas_padron:
            nombre = columna["nombre"]
            tipo = columna["tipo"]
            self.combo_columna.addItem(f"{nombre} ({tipo})", nombre)
    
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
    
    def actualizar_cambios(self):
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
            self.show()
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
                    self.lbl_info_columna.setText("Columna no encontrada")
            else:
                self.lbl_info_columna.setText("")
            
            # Configurar checks
            self.check_negrita.setChecked(campo.config.get("negrita", False))
            self.check_cursiva.setChecked(campo.config.get("cursiva", False))
            
            # Actualizar título
            if campo.tipo == "tabla":
                self.lbl_titulo.setText(f"📊 {campo.nombre}")
            else:
                self.lbl_titulo.setText(f"📝 {campo.nombre}")
        else:
            self.hide()
            self.lbl_titulo.setText("⚙️ Propiedades")