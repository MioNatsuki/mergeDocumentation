# ui/modules/plantillas/editor_mejorado/panel_propiedades.py
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QLineEdit, 
                             QComboBox, QSpinBox, QCheckBox, QPushButton,
                             QFormLayout, QGroupBox, QColorDialog, QHBoxLayout)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QColor

class PanelPropiedades(QWidget):
    """Panel derecho para configurar propiedades del campo seleccionado"""
    
    propiedades_cambiadas = pyqtSignal(dict)  # Nuevas propiedades
    
    def __init__(self):
        super().__init__()
        self.campo_actual = None
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(15)
        
        # Título
        self.lbl_titulo = QLabel("⚙️ Propiedades del Campo")
        self.lbl_titulo.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        layout.addWidget(self.lbl_titulo)
        
        # Mensaje cuando no hay campo seleccionado
        self.lbl_sin_campo = QLabel("Selecciona un campo en el PDF para configurarlo")
        self.lbl_sin_campo.setStyleSheet("color: #666; font-style: italic; padding: 20px;")
        layout.addWidget(self.lbl_sin_campo)
        
        # Grupo de propiedades (oculto inicialmente)
        self.grupo_propiedades = QGroupBox()
        self.grupo_propiedades.hide()
        
        form_layout = QFormLayout()
        form_layout.setSpacing(10)
        
        # Nombre del campo
        self.txt_nombre = QLineEdit()
        self.txt_nombre.textChanged.connect(self.actualizar_propiedades)
        
        # Columna del padrón
        self.combo_columna = QComboBox()
        self.combo_columna.addItem("-- Selecciona columna --", "")
        self.combo_columna.currentTextChanged.connect(self.actualizar_propiedades)
        
        # Tipo de fuente
        self.combo_fuente = QComboBox()
        self.combo_fuente.addItems(["Arial", "Times New Roman", "Helvetica", "Courier", "Verdana"])
        self.combo_fuente.currentTextChanged.connect(self.actualizar_propiedades)
        
        # Tamaño de fuente
        self.spin_tamano = QSpinBox()
        self.spin_tamano.setRange(6, 72)
        self.spin_tamano.setValue(12)
        self.spin_tamano.valueChanged.connect(self.actualizar_propiedades)
        
        # Color
        self.btn_color = QPushButton("Color")
        self.btn_color.clicked.connect(self.seleccionar_color)
        self.color_actual = QColor("#000000")
        
        # Negrita y cursiva
        self.check_negrita = QCheckBox("Negrita")
        self.check_negrita.stateChanged.connect(self.actualizar_propiedades)
        
        self.check_cursiva = QCheckBox("Cursiva")
        self.check_cursiva.stateChanged.connect(self.actualizar_propiedades)
        
        # Alineación
        self.combo_alineacion = QComboBox()
        self.combo_alineacion.addItems(["Izquierda", "Centro", "Derecha", "Justificado"])
        self.combo_alineacion.currentTextChanged.connect(self.actualizar_propiedades)
        
        # Formato
        self.combo_formato = QComboBox()
        self.combo_formato.addItems([
            "Texto simple",
            "Mayúsculas",
            "Minúsculas",
            "Capitalizar",
            "Moneda ($1,234.56)",
            "Porcentaje (12.34%)",
            "Fecha (dd/mm/yyyy)"
        ])
        self.combo_formato.currentTextChanged.connect(self.actualizar_propiedades)
        
        # Posición y tamaño
        hbox_pos = QHBoxLayout()
        self.spin_x = QSpinBox()
        self.spin_x.setRange(0, 500)
        self.spin_x.setSuffix(" mm")
        self.spin_x.valueChanged.connect(self.actualizar_propiedades)
        
        self.spin_y = QSpinBox()
        self.spin_y.setRange(0, 500)
        self.spin_y.setSuffix(" mm")
        self.spin_y.valueChanged.connect(self.actualizar_propiedades)
        
        hbox_pos.addWidget(QLabel("X:"))
        hbox_pos.addWidget(self.spin_x)
        hbox_pos.addWidget(QLabel("Y:"))
        hbox_pos.addWidget(self.spin_y)
        
        hbox_tam = QHBoxLayout()
        self.spin_ancho = QSpinBox()
        self.spin_ancho.setRange(10, 500)
        self.spin_ancho.setSuffix(" mm")
        self.spin_ancho.setValue(50)
        self.spin_ancho.valueChanged.connect(self.actualizar_propiedades)
        
        self.spin_alto = QSpinBox()
        self.spin_alto.setRange(5, 200)
        self.spin_alto.setSuffix(" mm")
        self.spin_alto.setValue(10)
        self.spin_alto.valueChanged.connect(self.actualizar_propiedades)
        
        hbox_tam.addWidget(QLabel("Ancho:"))
        hbox_tam.addWidget(self.spin_ancho)
        hbox_tam.addWidget(QLabel("Alto:"))
        hbox_tam.addWidget(self.spin_alto)
        
        # Agregar al formulario
        form_layout.addRow("Nombre:", self.txt_nombre)
        form_layout.addRow("Columna padrón:", self.combo_columna)
        form_layout.addRow("Fuente:", self.combo_fuente)
        form_layout.addRow("Tamaño:", self.spin_tamano)
        form_layout.addRow("Color:", self.btn_color)
        form_layout.addRow("", self.check_negrita)
        form_layout.addRow("", self.check_cursiva)
        form_layout.addRow("Alineación:", self.combo_alineacion)
        form_layout.addRow("Formato:", self.combo_formato)
        form_layout.addRow("Posición:", hbox_pos)
        form_layout.addRow("Tamaño:", hbox_tam)
        
        self.grupo_propiedades.setLayout(form_layout)
        layout.addWidget(self.grupo_propiedades)
        
        layout.addStretch()
        self.setLayout(layout)
    
    def seleccionar_color(self):
        """Abre diálogo para seleccionar color"""
        color = QColorDialog.getColor(self.color_actual, self, "Seleccionar color")
        if color.isValid():
            self.color_actual = color
            self.btn_color.setStyleSheet(f"background-color: {color.name()}; color: white;")
            self.actualizar_propiedades()
    
    def actualizar_propiedades(self):
        """Emitir propiedades actualizadas"""
        if self.campo_actual:
            props = {
                "nombre": self.txt_nombre.text(),
                "columna_padron": self.combo_columna.currentData(),
                "fuente": self.combo_fuente.currentText(),
                "tamano": self.spin_tamano.value(),
                "color": self.color_actual.name(),
                "negrita": self.check_negrita.isChecked(),
                "cursiva": self.check_cursiva.isChecked(),
                "alineacion": self.combo_alineacion.currentText().lower(),
                "formato": self.combo_formato.currentText(),
                "x": self.spin_x.value(),
                "y": self.spin_y.value(),
                "ancho": self.spin_ancho.value(),
                "alto": self.spin_alto.value()
            }
            self.propiedades_cambiadas.emit(props)
    
    def cargar_columnas_padron(self, columnas):
        """Carga las columnas disponibles del padrón con filtros por tipo"""
        self.combo_columna.clear()
        self.combo_columna.addItem("-- Selecciona columna --", "")
        
        # Agrupar columnas por tipo para mejor organización
        columnas_por_tipo = {}
        for columna in columnas:
            tipo = columna.get("tipo", "texto")
            if tipo not in columnas_por_tipo:
                columnas_por_tipo[tipo] = []
            columnas_por_tipo[tipo].append(columna)
        
        # Agregar separador por tipos
        for tipo, cols in columnas_por_tipo.items():
            # Nombre amigable del tipo
            nombres_tipo = {
                "texto": "📝 Texto",
                "numero": "🔢 Números",
                "fecha": "📅 Fechas",
                "booleano": "✅ Booleanos"
            }
            nombre_tipo = nombres_tipo.get(tipo, f"📌 {tipo.title()}")
            
            # Separador
            self.combo_columna.addItem(f"─ {nombre_tipo} ─")
            self.combo_columna.setItemData(self.combo_columna.count()-1, None)
            
            # Columnas de este tipo
            for columna in cols:
                nombre = columna["nombre"]
                ejemplo = columna.get("ejemplo", "")
                display_text = f"{nombre}"
                if ejemplo:
                    display_text += f" (ej: {ejemplo})"
                
                self.combo_columna.addItem(display_text, nombre)
        
        # Agregar campos especiales (no del padrón)
        self.combo_columna.addItem("─ 🎯 Campos Especiales ─")
        self.combo_columna.setItemData(self.combo_columna.count()-1, None)
        
        campos_especiales = [
            ("fecha_actual", "📅 Fecha actual (automática)"),
            ("hora_actual", "⏰ Hora actual (automática)"),
            ("codigo_barras", "📊 Código de barras (generado)"),
            ("numero_pagina", "📄 Número de página"),
            ("total_paginas", "📚 Total de páginas"),
            ("texto_fijo", "📋 Texto fijo (ingresar manual)")
        ]
        
        for valor, texto in campos_especiales:
            self.combo_columna.addItem(texto, f"especial:{valor}")
    
    def mostrar_campo(self, campo_widget):
        """Muestra propiedades del campo seleccionado"""
        self.campo_actual = campo_widget
        
        # Ocultar mensaje, mostrar propiedades
        self.lbl_sin_campo.hide()
        self.grupo_propiedades.show()
        
        # Actualizar título
        self.lbl_titulo.setText(f"⚙️ {campo_widget.tipo.title()}")
        
        # Cargar valores actuales
        config = campo_widget.config
        self.txt_nombre.setText(config.get("nombre", ""))
        
        # Buscar columna en el combo
        columna = config.get("columna_padron", "")
        index = self.combo_columna.findData(columna)
        if index >= 0:
            self.combo_columna.setCurrentIndex(index)
        
        self.combo_fuente.setCurrentText(config.get("fuente", "Arial"))
        self.spin_tamano.setValue(config.get("tamano", 12))
        
        # Color
        color = QColor(config.get("color", "#000000"))
        if color.isValid():
            self.color_actual = color
            self.btn_color.setStyleSheet(f"background-color: {color.name()}; color: white;")
        
        self.check_negrita.setChecked(config.get("negrita", False))
        self.check_cursiva.setChecked(config.get("cursiva", False))
        
        alineacion = config.get("alineacion", "left").title()
        self.combo_alineacion.setCurrentText(alineacion)
        
        self.combo_formato.setCurrentText(config.get("formato", "Texto simple"))
        
        # Posición y tamaño del widget
        self.spin_x.setValue(int(campo_widget.x_mm))
        self.spin_y.setValue(int(campo_widget.y_mm))
        self.spin_ancho.setValue(int(campo_widget.ancho_mm))
        self.spin_alto.setValue(int(campo_widget.alto_mm))
    
    def limpiar(self):
        """Limpia el panel cuando no hay campo seleccionado"""
        self.campo_actual = None
        self.lbl_sin_campo.show()
        self.grupo_propiedades.hide()
        self.lbl_titulo.setText("⚙️ Propiedades del Campo")