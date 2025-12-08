# ui/modules/plantillas/editor_mejorado/panel_propiedades.py - VERSIÓN COMPLETA
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QLineEdit, 
                             QComboBox, QSpinBox, QCheckBox, QPushButton,
                             QFormLayout, QGroupBox, QColorDialog, QHBoxLayout,
                             QFrame, QScrollArea, QFontDialog)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QColor
import traceback

class PanelPropiedades(QFrame):
    """Panel de propiedades con ALINEACIÓN COMPLETA"""
    
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
        """Configura UI con alineación completa"""
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
        
        # ===== SECCIÓN: DATOS BÁSICOS =====
        grupo_basico = QGroupBox("📝 Datos básicos")
        grupo_basico.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 1px solid #ddd;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        
        form_basico = QFormLayout()
        
        # Nombre interno
        self.txt_nombre = QLineEdit()
        self.txt_nombre.setPlaceholderText("Nombre del campo...")
        self.txt_nombre.textChanged.connect(self.actualizar_cambios)
        form_basico.addRow("Nombre:", self.txt_nombre)
        
        # Tipo de campo (solo lectura para identificar)
        self.lbl_tipo = QLabel()
        self.lbl_tipo.setStyleSheet("color: #666; font-style: italic;")
        form_basico.addRow("Tipo:", self.lbl_tipo)
        
        grupo_basico.setLayout(form_basico)
        contenido_layout.addWidget(grupo_basico)
        
        # ===== SECCIÓN: CONTENIDO =====
        grupo_contenido = QGroupBox("📊 Contenido")
        grupo_contenido.setStyleSheet(grupo_basico.styleSheet())
        
        form_contenido = QFormLayout()
        
        # Columna del padrón (para campos dinámicos)
        self.combo_columna = QComboBox()
        self.combo_columna.currentTextChanged.connect(self.actualizar_cambios)
        form_contenido.addRow("Columna padrón:", self.combo_columna)
        
        # Texto fijo (para campos estáticos)
        self.txt_texto_fijo = QLineEdit()
        self.txt_texto_fijo.setPlaceholderText("Texto fijo...")
        self.txt_texto_fijo.textChanged.connect(self.actualizar_cambios)
        form_contenido.addRow("Texto fijo:", self.txt_texto_fijo)
        
        grupo_contenido.setLayout(form_contenido)
        contenido_layout.addWidget(grupo_contenido)
        
        # ===== SECCIÓN: ESTILO Y FORMATO =====
        grupo_estilo = QGroupBox("🎨 Estilo")
        grupo_estilo.setStyleSheet(grupo_basico.styleSheet())
        
        form_estilo = QFormLayout()
        
        # ALINEACIÓN COMPLETA - 4 OPCIONES
        self.combo_alineacion = QComboBox()
        self.combo_alineacion.addItems(['left', 'center', 'right', 'justify'])
        self.combo_alineacion.currentTextChanged.connect(self.actualizar_cambios)
        form_estilo.addRow("Alineación:", self.combo_alineacion)
        
        # Tamaño de fuente
        self.spin_tamano = QSpinBox()
        self.spin_tamano.setRange(6, 72)
        self.spin_tamano.setValue(12)
        self.spin_tamano.valueChanged.connect(self.actualizar_cambios)
        form_estilo.addRow("Tamaño fuente:", self.spin_tamano)
        
        grupo_estilo.setLayout(form_estilo)
        contenido_layout.addWidget(grupo_estilo)
        
        # ===== SECCIÓN: OPCIONES DE TEXTO =====
        grupo_opciones = QGroupBox("📐 Opciones de texto")
        grupo_opciones.setStyleSheet(grupo_basico.styleSheet())
        
        opciones_layout = QVBoxLayout()
        
        # Checkboxes en línea
        checks_layout = QHBoxLayout()
        
        self.check_negrita = QCheckBox("Negrita")
        self.check_negrita.stateChanged.connect(self.actualizar_cambios)
        
        self.check_cursiva = QCheckBox("Cursiva")
        self.check_cursiva.stateChanged.connect(self.actualizar_cambios)
        
        checks_layout.addWidget(self.check_negrita)
        checks_layout.addWidget(self.check_cursiva)
        checks_layout.addStretch()
        
        opciones_layout.addLayout(checks_layout)
        
        # Botones de estilo avanzado
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(5)
        
        self.btn_fuente = QPushButton("🔤 Cambiar fuente")
        self.btn_fuente.clicked.connect(self.cambiar_fuente)
        
        self.btn_color = QPushButton("🎨 Cambiar color")
        self.btn_color.clicked.connect(self.cambiar_color)
        
        btn_layout.addWidget(self.btn_fuente)
        btn_layout.addWidget(self.btn_color)
        
        opciones_layout.addLayout(btn_layout)
        grupo_opciones.setLayout(opciones_layout)
        contenido_layout.addWidget(grupo_opciones)
        
        # Información de columna
        self.lbl_info_columna = QLabel("")
        self.lbl_info_columna.setStyleSheet("color: #666; font-size: 9px; font-style: italic;")
        contenido_layout.addWidget(self.lbl_info_columna)
        
        # Espaciador
        contenido_layout.addStretch()
        
        widget_contenido.setLayout(contenido_layout)
        scroll.setWidget(widget_contenido)
        layout.addWidget(scroll)
        
        self.setLayout(layout)
        self.setMinimumWidth(250)
    
    def cargar_columnas_reales(self):
        """Carga columnas del padrón desde la base de datos"""
        try:
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
                print(f"Error cargando columnas: {str(e)}")
                # En caso de error, cargar datos de ejemplo
                self.cargar_columnas_ejemplo()
            finally:
                db.close()
                
        except ImportError as e:
            print(f"Error de importación: {str(e)}")
            self.cargar_columnas_ejemplo()
    
    def cargar_columnas_ejemplo(self):
        """Carga columnas de ejemplo si falla la conexión a BD"""
        self.columnas_padron = [
            {"nombre": "nombre", "tipo": "texto"},
            {"nombre": "apellido", "tipo": "texto"},
            {"nombre": "dni", "tipo": "número"},
            {"nombre": "direccion", "tipo": "texto"},
            {"nombre": "telefono", "tipo": "texto"},
            {"nombre": "email", "tipo": "texto"},
            {"nombre": "fecha_nacimiento", "tipo": "fecha"},
            {"nombre": "monto_adeudo", "tipo": "moneda"}
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
            # Actualizar el spinbox si el campo tiene tamaño de fuente
            if hasattr(self.campo_actual, 'config'):
                self.spin_tamano.setValue(self.campo_actual.config.get('tamano_fuente', 12))
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
                "texto_fijo": self.txt_texto_fijo.text(),
                "alineacion": self.combo_alineacion.currentText(),
                "tamano_fuente": self.spin_tamano.value(),
                "negrita": self.check_negrita.isChecked(),
                "cursiva": self.check_cursiva.isChecked()
            }
            self.propiedades_cambiadas.emit(props)
    
    def mostrar_campo(self, campo):
        """Muestra u oculta el panel según si hay campo seleccionado"""
        self.campo_actual = campo
        
        if campo:
            self.show()
            
            # Configurar controles según tipo de campo
            self.configurar_controles_por_tipo(campo)
            
            # Actualizar título
            tipo_map = {
                'texto': '📝',
                'campo': '🔤',
                'compuesto': '🧩',
                'tabla': '📊'
            }
            icono = tipo_map.get(campo.config.get('tipo', 'texto'), '📝')
            self.lbl_titulo.setText(f"{icono} {campo.config.get('nombre', 'Sin nombre')}")
            
        else:
            self.hide()
            self.lbl_titulo.setText("⚙️ Propiedades")
    
    def configurar_controles_por_tipo(self, campo):
        """Configura controles según el tipo de campo"""
        config = campo.config
        
        # Datos básicos
        self.txt_nombre.setText(config.get('nombre', ''))
        
        tipo = config.get('tipo', 'texto')
        tipo_texto = {
            'texto': 'Texto fijo',
            'campo': 'Campo de BD',
            'compuesto': 'Campo compuesto',
            'tabla': 'Tabla dinámica'
        }.get(tipo, 'Desconocido')
        self.lbl_tipo.setText(tipo_texto)
        
        # Contenido
        if tipo in ['texto', 'campo']:
            # Mostrar columna o texto según tipo
            if tipo == 'texto':
                self.txt_texto_fijo.setText(config.get('texto_fijo', ''))
                self.txt_texto_fijo.setEnabled(True)
                self.combo_columna.setCurrentIndex(0)
                self.combo_columna.setEnabled(False)
            else:  # campo
                columna = config.get('columna_padron', '')
                index = self.combo_columna.findData(columna)
                self.combo_columna.setCurrentIndex(max(0, index))
                self.combo_columna.setEnabled(True)
                self.txt_texto_fijo.clear()
                self.txt_texto_fijo.setEnabled(False)
        else:
            # Para compuestos y tablas, deshabilitar estos controles
            self.txt_texto_fijo.clear()
            self.txt_texto_fijo.setEnabled(False)
            self.combo_columna.setCurrentIndex(0)
            self.combo_columna.setEnabled(False)
        
        # Estilo
        alineacion = config.get('alineacion', 'left')
        index = self.combo_alineacion.findText(alineacion)
        if index >= 0:
            self.combo_alineacion.setCurrentIndex(index)
        
        self.spin_tamano.setValue(config.get('tamano_fuente', 12))
        self.check_negrita.setChecked(config.get('negrita', False))
        self.check_cursiva.setChecked(config.get('cursiva', False))
        
        # Información de columna
        if tipo == 'campo':
            columna = config.get('columna_padron', '')
            if columna:
                for col in self.columnas_padron:
                    if col.get('nombre') == columna:
                        tipo_col = col.get('tipo', 'desconocido')
                        self.lbl_info_columna.setText(f"Tipo: {tipo_col}")
                        break
                else:
                    self.lbl_info_columna.setText("Columna no encontrada en padrón")
            else:
                self.lbl_info_columna.setText("")
        else:
            self.lbl_info_columna.setText("")