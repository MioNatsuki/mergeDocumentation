from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QFrame, QLineEdit, QTextEdit, QMessageBox, QStackedWidget,
    QTableWidget, QTableWidgetItem, QHeaderView, QFileDialog,
    QProgressBar, QComboBox, QCheckBox, QSpinBox, QGroupBox
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QPixmap
from core.project_service import ProjectService
from core.padron_service import PadronService
from config.database import SessionLocal
import os
import pandas as pd
import tempfile

class FormularioProyecto(QWidget):
    """Wizard de 3 pasos para crear/editar proyectos con padrón dinámico"""
    proyecto_guardado = pyqtSignal()
    
    def __init__(self, usuario, proyecto_id=None, stacked_widget=None):
        super().__init__()
        self.usuario = usuario
        self.proyecto_id = proyecto_id
        self.stacked_widget = stacked_widget
        self.proyecto = None
        self.paso_actual = 1
        self.csv_path = None
        self.estructura_columnas = []
        self.uuid_padron = None
        self.nombre_tabla = None
        
        # Cargar proyecto si estamos editando
        if proyecto_id:
            self.cargar_proyecto_existente()
        
        self.setup_ui()
    
    def setup_ui(self):
        """Configura el wizard de 3 pasos"""
        self.setWindowTitle("Nuevo Proyecto" if not self.proyecto_id else "Editar Proyecto")
        self.setMinimumSize(900, 700)
        
        layout = QVBoxLayout()
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)
        
        # CABECERA CON PASOS
        header = QFrame()
        header.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #ffabab, stop:0.5 #ddffab, stop:1 #abe4ff);
                border-radius: 12px;
                padding: 15px;
            }
        """)
        
        header_layout = QHBoxLayout()
        
        # Paso 1: Información Básica
        self.paso1_frame = self.crear_paso_indicator(1, "📝 Información Básica")
        header_layout.addWidget(self.paso1_frame)
        
        # Flecha
        flecha1 = QLabel("➡")
        flecha1.setFont(QFont("Arial", 20))
        flecha1.setStyleSheet("color: #2a363b;")
        flecha1.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_layout.addWidget(flecha1)
        
        # Paso 2: Configuración del Padrón
        self.paso2_frame = self.crear_paso_indicator(2, "📊 Estructura del Padrón")
        self.paso2_frame.setEnabled(False)
        header_layout.addWidget(self.paso2_frame)
        
        # Flecha
        flecha2 = QLabel("➡")
        flecha2.setFont(QFont("Arial", 20))
        flecha2.setStyleSheet("color: #2a363b;")
        flecha2.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_layout.addWidget(flecha2)
        
        # Paso 3: Carga Inicial
        self.paso3_frame = self.crear_paso_indicator(3, "📂 Carga de Datos")
        self.paso3_frame.setEnabled(False)
        header_layout.addWidget(self.paso3_frame)
        
        header_layout.addStretch()
        header.setLayout(header_layout)
        layout.addWidget(header)
        
        # WIDGET STACK PARA PASOS
        self.stacked_widget_pasos = QStackedWidget()
        
        # Paso 1: Información Básica
        self.widget_paso1 = self.crear_paso1()
        self.stacked_widget_pasos.addWidget(self.widget_paso1)
        
        # Paso 2: Configuración del Padrón
        self.widget_paso2 = self.crear_paso2()
        self.stacked_widget_pasos.addWidget(self.widget_paso2)
        
        # Paso 3: Carga Inicial
        self.widget_paso3 = self.crear_paso3()
        self.stacked_widget_pasos.addWidget(self.widget_paso3)
        
        layout.addWidget(self.stacked_widget_pasos)
        
        # BOTONES DE NAVEGACIÓN
        botones_layout = QHBoxLayout()
        botones_layout.setSpacing(15)
        
        self.btn_anterior = QPushButton("⬅ Anterior")
        self.btn_anterior.clicked.connect(self.anterior_paso)
        self.btn_anterior.setEnabled(False)
        self.btn_anterior.setStyleSheet(self.get_button_style("#ffdaab"))
        
        self.btn_siguiente = QPushButton("Siguiente ➡")
        self.btn_siguiente.clicked.connect(self.siguiente_paso)
        self.btn_siguiente.setStyleSheet(self.get_button_style("#ddffab"))
        
        self.btn_cancelar = QPushButton("Cancelar")
        self.btn_cancelar.clicked.connect(self.cancelar)
        self.btn_cancelar.setStyleSheet(self.get_button_style("#ffabab"))
        
        botones_layout.addWidget(self.btn_anterior)
        botones_layout.addStretch()
        botones_layout.addWidget(self.btn_cancelar)
        botones_layout.addWidget(self.btn_siguiente)
        
        layout.addLayout(botones_layout)
        self.setLayout(layout)
        
        # Mostrar paso actual
        self.mostrar_paso_actual()
    
    def crear_paso_indicator(self, numero, texto):
        """Crea un indicador de paso"""
        frame = QFrame()
        frame.setFixedHeight(80)
        frame.setStyleSheet("""
            QFrame {
                background-color: rgba(255, 255, 255, 0.7);
                border-radius: 8px;
                border: 2px solid #2a363b;
            }
            QFrame[enabled="false"] {
                background-color: rgba(255, 255, 255, 0.3);
                border-color: #aaaaaa;
            }
        """)
        
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Número del paso
        lbl_numero = QLabel(f"{numero}")
        lbl_numero.setFont(QFont("Jura", 24, QFont.Weight.Bold))
        lbl_numero.setStyleSheet("color: #2a363b;")
        lbl_numero.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Texto del paso
        lbl_texto = QLabel(texto)
        lbl_texto.setFont(QFont("Jura", 10))
        lbl_texto.setStyleSheet("color: #2a363b;")
        lbl_texto.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        layout.addWidget(lbl_numero)
        layout.addWidget(lbl_texto)
        frame.setLayout(layout)
        
        return frame
    
    def get_button_style(self, color):
        """Devuelve estilo CSS para botones"""
        return f"""
            QPushButton {{
                background-color: {color};
                color: #2a363b;
                border: 2px solid {color};
                border-radius: 8px;
                padding: 12px 24px;
                font-family: 'Jura';
                font-weight: bold;
                font-size: 12px;
                min-width: 100px;
            }}
            QPushButton:hover {{
                background-color: #ffffff;
                border-color: #2a363b;
            }}
            QPushButton:disabled {{
                background-color: #cccccc;
                color: #666666;
                border-color: #aaaaaa;
            }}
        """
    
    def crear_paso1(self):
        """Paso 1: Información básica del proyecto"""
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(25)
        
        # Título
        titulo = QLabel("Información Básica del Proyecto")
        titulo.setFont(QFont("Jura", 16, QFont.Weight.Bold))
        titulo.setStyleSheet("color: #2a363b; border-bottom: 2px solid #99b898; padding-bottom: 10px;")
        titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(titulo)
        
        # FORMULARIO
        form_layout = QVBoxLayout()
        form_layout.setSpacing(15)
        
        # Nombre del proyecto
        grupo_nombre = QGroupBox("Nombre del Proyecto *")
        grupo_nombre.setFont(QFont("Jura", 11))
        layout_nombre = QVBoxLayout()
        
        self.txt_nombre = QLineEdit()
        self.txt_nombre.setPlaceholderText("Ej: Cobranza Enero 2024")
        self.txt_nombre.setFont(QFont("Jura", 11))
        self.txt_nombre.setStyleSheet("""
            QLineEdit {
                padding: 10px;
                border: 2px solid #99b898;
                border-radius: 6px;
                font-family: 'Jura';
            }
            QLineEdit:focus {
                border-color: #ff847c;
                outline: none;
            }
        """)
        layout_nombre.addWidget(self.txt_nombre)
        grupo_nombre.setLayout(layout_nombre)
        form_layout.addWidget(grupo_nombre)
        
        # Descripción
        grupo_desc = QGroupBox("Descripción (Opcional)")
        grupo_desc.setFont(QFont("Jura", 11))
        layout_desc = QVBoxLayout()
        
        self.txt_descripcion = QTextEdit()
        self.txt_descripcion.setPlaceholderText("Describe el propósito de este proyecto...")
        self.txt_descripcion.setMaximumHeight(100)
        self.txt_descripcion.setFont(QFont("Jura", 10))
        self.txt_descripcion.setStyleSheet("""
            QTextEdit {
                border: 2px solid #fecea8;
                border-radius: 6px;
                padding: 8px;
                font-family: 'Jura';
            }
            QTextEdit:focus {
                border-color: #ff847c;
            }
        """)
        layout_desc.addWidget(self.txt_descripcion)
        grupo_desc.setLayout(layout_desc)
        form_layout.addWidget(grupo_desc)
        
        # Logo
        grupo_logo = QGroupBox("Logo del Proyecto (Opcional)")
        grupo_logo.setFont(QFont("Jura", 11))
        layout_logo = QVBoxLayout()
        
        # Contenedor para logo
        self.logo_container = QFrame()
        self.logo_container.setFixedSize(150, 150)
        self.logo_container.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border: 3px dashed #dee2e6;
                border-radius: 12px;
            }
            QFrame:hover {
                border-color: #99b898;
            }
        """)
        self.logo_container.mousePressEvent = self.seleccionar_logo
        
        logo_layout = QVBoxLayout()
        logo_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.lbl_logo_preview = QLabel("📷")
        self.lbl_logo_preview.setFont(QFont("Arial", 36))
        self.lbl_logo_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.lbl_logo_texto = QLabel("Haz clic para seleccionar logo")
        self.lbl_logo_texto.setFont(QFont("Jura", 9))
        self.lbl_logo_texto.setStyleSheet("color: #6c757d;")
        self.lbl_logo_texto.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_logo_texto.setWordWrap(True)
        
        logo_layout.addWidget(self.lbl_logo_preview)
        logo_layout.addWidget(self.lbl_logo_texto)
        self.logo_container.setLayout(logo_layout)
        
        layout_logo.addWidget(self.logo_container, alignment=Qt.AlignmentFlag.AlignCenter)
        
        # Info de logo
        lbl_info_logo = QLabel("Formatos: PNG, JPG (Máx. 2MB)")
        lbl_info_logo.setFont(QFont("Jura", 8))
        lbl_info_logo.setStyleSheet("color: #6c757d; font-style: italic;")
        lbl_info_logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout_logo.addWidget(lbl_info_logo)
        
        grupo_logo.setLayout(layout_logo)
        form_layout.addWidget(grupo_logo)
        
        layout.addLayout(form_layout)
        
        # NOTA
        nota = QLabel("💡 * Campos obligatorios")
        nota.setFont(QFont("Jura", 9))
        nota.setStyleSheet("color: #ff847c; padding: 10px; background-color: #fff5f5; border-radius: 6px;")
        nota.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(nota)
        
        widget.setLayout(layout)
        return widget
    
    def crear_paso2(self):
        """Paso 2: Configuración del padrón"""
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(25)
        
        # Título
        titulo = QLabel("Configuración de la Estructura del Padrón")
        titulo.setFont(QFont("Jura", 16, QFont.Weight.Bold))
        titulo.setStyleSheet("color: #2a363b; border-bottom: 2px solid #fecea8; padding-bottom: 10px;")
        titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(titulo)
        
        # SUBIDA DE CSV
        grupo_csv = QGroupBox("1. Subir archivo CSV para análisis")
        grupo_csv.setFont(QFont("Jura", 11))
        layout_csv = QVBoxLayout()
        
        # Área de drop
        self.drop_area_csv = QFrame()
        self.drop_area_csv.setMinimumHeight(120)
        self.drop_area_csv.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border: 3px dashed #99b898;
                border-radius: 10px;
            }
            QFrame:hover {
                background-color: #f0f9f0;
                border-color: #88a786;
            }
        """)
        self.drop_area_csv.mousePressEvent = self.seleccionar_csv
        
        drop_layout = QVBoxLayout()
        drop_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.lbl_csv_icono = QLabel("📁")
        self.lbl_csv_icono.setFont(QFont("Arial", 32))
        self.lbl_csv_icono.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.lbl_csv_titulo = QLabel("Arrastra o haz clic para seleccionar CSV")
        self.lbl_csv_titulo.setFont(QFont("Jura", 11, QFont.Weight.Bold))
        self.lbl_csv_titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.lbl_csv_info = QLabel("")
        self.lbl_csv_info.setFont(QFont("Jura", 9))
        self.lbl_csv_info.setStyleSheet("color: #28a745;")
        self.lbl_csv_info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_csv_info.hide()
        
        drop_layout.addWidget(self.lbl_csv_icono)
        drop_layout.addWidget(self.lbl_csv_titulo)
        drop_layout.addWidget(self.lbl_csv_info)
        self.drop_area_csv.setLayout(drop_layout)
        
        layout_csv.addWidget(self.drop_area_csv)
        
        # Info de formato
        lbl_csv_format = QLabel("""
            <div style='background-color: #e7f3ff; padding: 10px; border-radius: 6px;'>
            <b>Requisitos del CSV:</b><br>
            • Codificación: UTF-8 (recomendado)<br>
            • Separador: Coma (,)<br>
            • <b>Columnas obligatorias:</b> <span style='color: #dc3545;'>cuenta</span> y <span style='color: #dc3545;'>codigo_afiliado</span><br>
            • Tamaño máximo: 50MB
            </div>
        """)
        lbl_csv_format.setFont(QFont("Jura", 9))
        
        layout_csv.addWidget(lbl_csv_format)
        grupo_csv.setLayout(layout_csv)
        layout.addWidget(grupo_csv)
        
        # TABLA DE COLUMNAS DETECTADAS
        grupo_columnas = QGroupBox("2. Columnas Detectadas y Configuración")
        grupo_columnas.setFont(QFont("Jura", 11))
        layout_columnas = QVBoxLayout()
        
        self.tabla_columnas = QTableWidget()
        self.tabla_columnas.setColumnCount(6)
        self.tabla_columnas.setHorizontalHeaderLabels([
            "Columna Original", "Columna SQL", "Tipo Detected", "Tipo SQL", "Nulo", "Ejemplo"
        ])
        
        header = self.tabla_columnas.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        header.setStyleSheet("""
            QHeaderView::section {
                background-color: #99b898;
                color: white;
                font-weight: bold;
                padding: 8px;
                font-family: 'Jura';
                border: 1px solid #88a786;
            }
        """)
        
        self.tabla_columnas.setStyleSheet("""
            QTableWidget {
                border: 2px solid #dee2e6;
                border-radius: 6px;
                background-color: white;
                alternate-background-color: #f8f9fa;
                font-family: 'Jura';
            }
            QTableWidget::item {
                padding: 8px;
            }
            QTableWidget::item:selected {
                background-color: #d1ecf1;
                color: #0c5460;
            }
        """)
        
        self.tabla_columnas.setAlternatingRowColors(True)
        self.tabla_columnas.setMinimumHeight(300)
        
        layout_columnas.addWidget(self.tabla_columnas)
        
        # Botón para agregar columna manual
        btn_add_col = QPushButton("➕ Agregar Columna Manualmente")
        btn_add_col.clicked.connect(self.agregar_columna_manual)
        btn_add_col.setStyleSheet(self.get_button_style("#d9abff"))
        layout_columnas.addWidget(btn_add_col, alignment=Qt.AlignmentFlag.AlignRight)
        
        grupo_columnas.setLayout(layout_columnas)
        layout.addWidget(grupo_columnas)
        
        widget.setLayout(layout)
        return widget
    
    def crear_paso3(self):
        """Paso 3: Carga inicial de datos"""
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(25)
        
        # Título
        titulo = QLabel("Carga Inicial de Datos al Padrón")
        titulo.setFont(QFont("Jura", 16, QFont.Weight.Bold))
        titulo.setStyleSheet("color: #2a363b; border-bottom: 2px solid #abe4ff; padding-bottom: 10px;")
        titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(titulo)
        
        # OPCIONES DE CARGA
        grupo_opciones = QGroupBox("Opciones de Carga")
        grupo_opciones.setFont(QFont("Jura", 11))
        layout_opciones = QVBoxLayout()
        
        # Opción 1: Reutilizar CSV
        self.radio_reutilizar = QCheckBox("Reutilizar el CSV del paso anterior (recomendado)")
        self.radio_reutilizar.setFont(QFont("Jura", 10))
        self.radio_reutilizar.setChecked(True)
        self.radio_reutilizar.toggled.connect(self.on_opcion_carga_cambiada)
        
        # Opción 2: Nuevo CSV
        self.radio_nuevo = QCheckBox("Subir un nuevo archivo CSV")
        self.radio_nuevo.setFont(QFont("Jura", 10))
        self.radio_nuevo.toggled.connect(self.on_opcion_carga_cambiada)
        
        layout_opciones.addWidget(self.radio_reutilizar)
        layout_opciones.addWidget(self.radio_nuevo)
        
        # Área para nuevo CSV
        self.frame_nuevo_csv = QFrame()
        self.frame_nuevo_csv.setStyleSheet("background-color: #f8f9fa; padding: 15px; border-radius: 6px;")
        self.frame_nuevo_csv.hide()
        
        layout_nuevo_csv = QVBoxLayout()
        
        lbl_subir_nuevo = QLabel("Seleccionar nuevo archivo CSV:")
        lbl_subir_nuevo.setFont(QFont("Jura", 10))
        
        btn_seleccionar_nuevo = QPushButton("📂 Buscar Archivo CSV")
        btn_seleccionar_nuevo.clicked.connect(self.seleccionar_nuevo_csv)
        btn_seleccionar_nuevo.setStyleSheet(self.get_button_style("#ffdaab"))
        
        self.lbl_nuevo_csv_info = QLabel("")
        self.lbl_nuevo_csv_info.setFont(QFont("Jura", 9))
        self.lbl_nuevo_csv_info.setStyleSheet("color: #28a745;")
        
        layout_nuevo_csv.addWidget(lbl_subir_nuevo)
        layout_nuevo_csv.addWidget(btn_seleccionar_nuevo)
        layout_nuevo_csv.addWidget(self.lbl_nuevo_csv_info)
        self.frame_nuevo_csv.setLayout(layout_nuevo_csv)
        
        layout_opciones.addWidget(self.frame_nuevo_csv)
        grupo_opciones.setLayout(layout_opciones)
        layout.addWidget(grupo_opciones)
        
        # PREVIEW DE DATOS
        grupo_preview = QGroupBox("Previsualización de Datos")
        grupo_preview.setFont(QFont("Jura", 11))
        layout_preview = QVBoxLayout()
        
        self.tabla_preview = QTableWidget()
        self.tabla_preview.setColumnCount(0)
        self.tabla_preview.setRowCount(0)
        
        self.tabla_preview.setStyleSheet("""
            QTableWidget {
                border: 2px solid #dee2e6;
                border-radius: 6px;
                background-color: white;
                font-family: 'Jura';
            }
            QTableWidget::item {
                padding: 6px;
            }
        """)
        
        self.tabla_preview.setMinimumHeight(200)
        
        lbl_preview_info = QLabel("Mostrando primeras 10 filas del CSV")
        lbl_preview_info.setFont(QFont("Jura", 9))
        lbl_preview_info.setStyleSheet("color: #6c757d; font-style: italic;")
        
        layout_preview.addWidget(self.tabla_preview)
        layout_preview.addWidget(lbl_preview_info)
        grupo_preview.setLayout(layout_preview)
        layout.addWidget(grupo_preview)
        
        # BARRA DE PROGRESO
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid #99b898;
                border-radius: 6px;
                text-align: center;
                font-family: 'Jura';
                height: 25px;
            }
            QProgressBar::chunk {
                background-color: #99b898;
                border-radius: 4px;
            }
        """)
        layout.addWidget(self.progress_bar)
        
        # ESTADO
        self.lbl_estado = QLabel("")
        self.lbl_estado.setFont(QFont("Jura", 10))
        self.lbl_estado.setStyleSheet("padding: 10px; border-radius: 6px;")
        self.lbl_estado.hide()
        
        layout.addWidget(self.lbl_estado)
        
        widget.setLayout(layout)
        return widget
    
    def mostrar_paso_actual(self):
        """Muestra el paso actual y actualiza botones"""
        self.stacked_widget_pasos.setCurrentIndex(self.paso_actual - 1)
        
        # Actualizar indicadores de pasos
        self.paso1_frame.setEnabled(True)
        self.paso2_frame.setEnabled(self.paso_actual >= 2)
        self.paso3_frame.setEnabled(self.paso_actual == 3)
        
        # Actualizar botones
        self.btn_anterior.setEnabled(self.paso_actual > 1)
        
        if self.paso_actual == 3:
            self.btn_siguiente.setText("✅ Finalizar y Crear Proyecto")
            self.btn_siguiente.setStyleSheet(self.get_button_style("#99b898"))
            # Actualizar preview si hay CSV
            if self.csv_path:
                self.actualizar_preview_datos()
        else:
            self.btn_siguiente.setText("Siguiente ➡")
            self.btn_siguiente.setStyleSheet(self.get_button_style("#ddffab"))
    
    def anterior_paso(self):
        """Retrocede un paso"""
        if self.paso_actual > 1:
            self.paso_actual -= 1
            self.mostrar_paso_actual()
    
    def siguiente_paso(self):
        """Avanza al siguiente paso o finaliza"""
        if self.paso_actual == 1:
            if not self.validar_paso1():
                return
            self.paso_actual = 2
            self.mostrar_paso_actual()
            
        elif self.paso_actual == 2:
            if not self.validar_paso2():
                return
            self.paso_actual = 3
            self.mostrar_paso_actual()
            
        elif self.paso_actual == 3:
            self.finalizar_proyecto()
    
    def validar_paso1(self):
        """Valida el paso 1: Información básica"""
        nombre = self.txt_nombre.text().strip()
        
        if not nombre:
            self.mostrar_error("El nombre del proyecto es obligatorio")
            self.txt_nombre.setFocus()
            return False
        
        # Validar que el nombre no exista
        db = SessionLocal()
        try:
            project_service = ProjectService(db)
            proyectos = project_service.obtener_proyectos_usuario(self.usuario)
            
            for proyecto in proyectos:
                if proyecto.nombre.lower() == nombre.lower() and proyecto.id != self.proyecto_id:
                    self.mostrar_error(f"Ya existe un proyecto con el nombre: '{nombre}'")
                    return False
        finally:
            db.close()
        
        return True
    
    def validar_paso2(self):
        """Valida el paso 2: Configuración del padrón"""
        if not self.estructura_columnas:
            self.mostrar_error("Debes subir un CSV para analizar la estructura del padrón")
            return False
        
        # Validar columnas obligatorias
        columnas_obligatorias = ['cuenta', 'codigo_afiliado']
        columnas_encontradas = [col['nombre_limpio'].lower() for col in self.estructura_columnas]
        
        faltantes = []
        for obligatoria in columnas_obligatorias:
            if obligatoria not in columnas_encontradas:
                faltantes.append(obligatoria)
        
        if faltantes:
            self.mostrar_error(f"Columnas obligatorias faltantes: {', '.join(faltantes)}")
            return False
        
        return True
    
    def mostrar_error(self, mensaje):
        """Muestra un mensaje de error"""
        QMessageBox.critical(self, "Error de Validación", mensaje)
    
    def mostrar_exito(self, mensaje):
        """Muestra un mensaje de éxito"""
        QMessageBox.information(self, "Éxito", mensaje)
    
    def seleccionar_logo(self, event):
        """Selecciona un logo para el proyecto"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Seleccionar Logo",
            "",
            "Imágenes (*.png *.jpg *.jpeg *.bmp);;Todos los archivos (*)"
        )
        
        if file_path:
            # Validar tamaño (max 2MB)
            tamano = os.path.getsize(file_path) / (1024 * 1024)  # MB
            if tamano > 2:
                QMessageBox.warning(self, "Archivo muy grande", 
                                  "El logo no debe superar los 2MB")
                return
            
            # Copiar logo a carpeta de logos
            logos_dir = "logos"
            os.makedirs(logos_dir, exist_ok=True)
            
            nombre_archivo = f"logo_{os.path.basename(file_path)}"
            destino = os.path.join(logos_dir, nombre_archivo)
            
            try:
                import shutil
                shutil.copy2(file_path, destino)
                
                # Mostrar preview
                pixmap = QPixmap(destino)
                if not pixmap.isNull():
                    pixmap = pixmap.scaled(120, 120, 
                                         Qt.AspectRatioMode.KeepAspectRatio,
                                         Qt.TransformationMode.SmoothTransformation)
                    self.lbl_logo_preview.setPixmap(pixmap)
                    self.lbl_logo_preview.setText("")
                    self.lbl_logo_texto.setText(os.path.basename(file_path))
                
                self.logo_path = destino
                
            except Exception as e:
                QMessageBox.critical(self, "Error", f"No se pudo copiar el logo: {str(e)}")
    
    def seleccionar_csv(self, event):
        """Selecciona un CSV para análisis"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Seleccionar Archivo CSV",
            "",
            "Archivos CSV (*.csv);;Todos los archivos (*)"
        )
        
        if file_path:
            self.procesar_csv(file_path)
    
    def procesar_csv(self, file_path):
        """Procesa el CSV para extraer estructura"""
        try:
            # Mostrar estado
            self.lbl_csv_icono.setText("⏳")
            self.lbl_csv_titulo.setText("Analizando CSV...")
            self.lbl_csv_info.show()
            self.lbl_csv_info.setText("Procesando, por favor espere...")
            
            # Usar el servicio de padrón para analizar
            db = SessionLocal()
            try:
                padron_service = PadronService(db)
                exito, columnas, errores = padron_service.analizar_estructura_csv(file_path)
                
                if not exito:
                    self.mostrar_error(f"Error analizando CSV:\n" + "\n".join(errores))
                    self.resetear_csv_ui()
                    return
                
                # Guardar CSV y estructura
                self.csv_path = file_path
                self.estructura_columnas = columnas
                
                # Actualizar UI
                self.lbl_csv_icono.setText("✅")
                self.lbl_csv_titulo.setText("CSV Analizado Correctamente")
                self.lbl_csv_info.setText(f"{len(columnas)} columnas detectadas")
                
                # Mostrar columnas en tabla
                self.mostrar_columnas_en_tabla(columnas)
                
                self.mostrar_exito(f"CSV analizado correctamente.\n{len(columnas)} columnas detectadas.")
                
            finally:
                db.close()
                
        except Exception as e:
            self.mostrar_error(f"Error procesando CSV: {str(e)}")
            self.resetear_csv_ui()
    
    def mostrar_columnas_en_tabla(self, columnas):
        """Muestra las columnas detectadas en la tabla"""
        self.tabla_columnas.setRowCount(len(columnas))
        
        for i, columna in enumerate(columnas):
            # Columna original
            item_original = QTableWidgetItem(columna['nombre_original'])
            self.tabla_columnas.setItem(i, 0, item_original)
            
            # Columna limpia (editable)
            item_limpia = QTableWidgetItem(columna['nombre_limpio'])
            self.tabla_columnas.setItem(i, 1, item_limpia)
            
            # Tipo detectado
            item_tipo_det = QTableWidgetItem(columna['tipo_sugerido'])
            self.tabla_columnas.setItem(i, 2, item_tipo_det)
            
            # Tipo SQL (editable)
            item_tipo_sql = QTableWidgetItem(columna['tipo_sql'])
            self.tabla_columnas.setItem(i, 3, item_tipo_sql)
            
            # Nulo
            item_nulo = QTableWidgetItem("SÍ" if columna['nullable'] else "NO")
            self.tabla_columnas.setItem(i, 4, item_nulo)
            
            # Ejemplo
            ejemplos = columna['ejemplos'][:3] if columna['ejemplos'] else []
            item_ejemplo = QTableWidgetItem(", ".join(map(str, ejemplos))[:50])
            self.tabla_columnas.setItem(i, 5, item_ejemplo)
    
    def agregar_columna_manual(self):
        """Agrega una columna manualmente a la tabla"""
        dialog = QWidget()
        dialog.setWindowTitle("Agregar Columna Manual")
        dialog.setFixedSize(400, 300)
        
        layout = QVBoxLayout()
        
        lbl_titulo = QLabel("Agregar Nueva Columna")
        lbl_titulo.setFont(QFont("Jura", 12, QFont.Weight.Bold))
        layout.addWidget(lbl_titulo)
        
        # Nombre
        layout.addWidget(QLabel("Nombre de la columna:"))
        txt_nombre = QLineEdit()
        txt_nombre.setPlaceholderText("ej: telefono")
        layout.addWidget(txt_nombre)
        
        # Tipo
        layout.addWidget(QLabel("Tipo de dato:"))
        combo_tipo = QComboBox()
        combo_tipo.addItems(["texto", "entero", "decimal", "fecha", "booleano"])
        layout.addWidget(combo_tipo)
        
        # Nulo
        check_nulo = QCheckBox("Permitir valores nulos")
        check_nulo.setChecked(True)
        layout.addWidget(check_nulo)
        
        layout.addStretch()
        
        # Botones
        btn_layout = QHBoxLayout()
        btn_cancelar = QPushButton("Cancelar")
        btn_agregar = QPushButton("Agregar")
        
        btn_cancelar.clicked.connect(dialog.close)
        btn_agregar.clicked.connect(lambda: self.agregar_columna_manual_confirm(
            txt_nombre.text().strip(), combo_tipo.currentText(), check_nulo.isChecked(), dialog
        ))
        
        btn_layout.addWidget(btn_cancelar)
        btn_layout.addWidget(btn_agregar)
        layout.addLayout(btn_layout)
        
        dialog.setLayout(layout)
        dialog.show()
    
    def agregar_columna_manual_confirm(self, nombre, tipo, nullable, dialog):
        """Confirma la adición de columna manual"""
        if not nombre:
            QMessageBox.warning(dialog, "Error", "El nombre de la columna es obligatorio")
            return
        
        # Agregar a estructura
        nueva_columna = {
            'nombre_original': nombre,
            'nombre_limpio': nombre.lower().replace(' ', '_'),
            'tipo_sugerido': tipo,
            'tipo_sql': self.convertir_tipo_a_sql(tipo),
            'nullable': nullable,
            'ejemplos': []
        }
        
        self.estructura_columnas.append(nueva_columna)
        
        # Actualizar tabla
        self.mostrar_columnas_en_tabla(self.estructura_columnas)
        
        dialog.close()
        self.mostrar_exito(f"Columna '{nombre}' agregada correctamente")
    
    def convertir_tipo_a_sql(self, tipo):
        """Convierte tipo amigable a SQL"""
        tipos = {
            'texto': 'VARCHAR(255)',
            'entero': 'INTEGER',
            'decimal': 'NUMERIC(15,2)',
            'fecha': 'DATE',
            'booleano': 'BOOLEAN'
        }
        return tipos.get(tipo, 'TEXT')
    
    def on_opcion_carga_cambiada(self):
        """Cuando cambia la opción de carga"""
        if self.radio_nuevo.isChecked():
            self.frame_nuevo_csv.show()
        else:
            self.frame_nuevo_csv.hide()
    
    def seleccionar_nuevo_csv(self):
        """Selecciona un nuevo CSV para carga"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Seleccionar Archivo CSV para Carga",
            "",
            "Archivos CSV (*.csv);;Todos los archivos (*)"
        )
        
        if file_path:
            # Validar que coincida con estructura
            if not self.validar_csv_con_estructura(file_path):
                return
            
            self.csv_carga_path = file_path
            nombre = os.path.basename(file_path)
            tamano = os.path.getsize(file_path) / 1024  # KB
            self.lbl_nuevo_csv_info.setText(f"{nombre} ({tamano:.1f} KB)")
            
            # Actualizar preview
            self.actualizar_preview_datos(file_path)
    
    def validar_csv_con_estructura(self, csv_path):
        """Valida que el CSV tenga las mismas columnas que la estructura"""
        try:
            import pandas as pd
            
            # Leer encabezados del CSV
            df = pd.read_csv(csv_path, nrows=0)
            columnas_csv = [str(col).strip().lower() for col in df.columns]
            
            # Columnas esperadas (nombres limpios)
            columnas_esperadas = [col['nombre_limpio'].lower() for col in self.estructura_columnas]
            
            # Verificar que todas las columnas esperadas estén en el CSV
            faltantes = []
            for esperada in columnas_esperadas:
                if esperada not in columnas_csv:
                    # Buscar coincidencias aproximadas
                    coincidencia = False
                    for csv_col in columnas_csv:
                        if esperada in csv_col or csv_col in esperada:
                            coincidencia = True
                            break
                    
                    if not coincidencia:
                        faltantes.append(esperada)
            
            if faltantes:
                QMessageBox.warning(
                    self, "Estructura Incorrecta",
                    f"El CSV no contiene las columnas esperadas:\n" +
                    "\n".join(f"• {col}" for col in faltantes)
                )
                return False
            
            return True
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error validando CSV: {str(e)}")
            return False
    
    def actualizar_preview_datos(self, csv_path=None):
        """Actualiza la previsualización de datos en la tabla"""
        if not csv_path:
            csv_path = self.csv_carga_path if hasattr(self, 'csv_carga_path') else self.csv_path
        
        if not csv_path or not os.path.exists(csv_path):
            return
        
        try:
            # Leer primeras 10 filas del CSV
            import pandas as pd
            df = pd.read_csv(csv_path, nrows=10)
            
            # Configurar tabla
            self.tabla_preview.setColumnCount(len(df.columns))
            self.tabla_preview.setHorizontalHeaderLabels(df.columns)
            self.tabla_preview.setRowCount(min(10, len(df)))
            
            # Llenar datos
            for i in range(min(10, len(df))):
                for j in range(len(df.columns)):
                    valor = str(df.iat[i, j])
                    item = QTableWidgetItem(valor[:100])  # Limitar longitud
                    self.tabla_preview.setItem(i, j, item)
            
        except Exception as e:
            print(f"Error mostrando preview: {e}")
    
    def finalizar_proyecto(self):
        """Crea el proyecto con la tabla de padrón y carga los datos"""
        if not self.validar_paso3():
            return
        
        # Confirmación final
        reply = QMessageBox.question(
            self, "Confirmar Creación",
            "¿Está seguro que desea crear el proyecto?\n\n"
            f"📁 Nombre: {self.txt_nombre.text()}\n"
            f"📊 Columnas: {len(self.estructura_columnas)}\n"
            f"📂 Tabla: padron_completo_{self.txt_nombre.text().lower().replace(' ', '_')[:30]}\n\n"
            "Esta acción creará la tabla de padrón en la base de datos y cargará los datos iniciales.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        # Mostrar progreso
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        
        # Crear proyecto en un hilo o con temporizador
        QTimer.singleShot(100, self.ejecutar_creacion_proyecto)
    
    def validar_paso3(self):
        """Valida el paso 3: Carga de datos"""
        # Determinar qué CSV usar
        if self.radio_reutilizar.isChecked():
            csv_path = self.csv_path
        else:
            csv_path = getattr(self, 'csv_carga_path', None)
        
        if not csv_path or not os.path.exists(csv_path):
            self.mostrar_error("Debe seleccionar un archivo CSV para la carga inicial")
            return False
        
        return True
    
    def ejecutar_creacion_proyecto(self):
        """Ejecuta la creación del proyecto paso a paso"""
        try:
            db = SessionLocal()
            
            # PASO 1: Crear tabla de padrón dinámica
            self.progress_bar.setValue(10)
            self.lbl_estado.show()
            self.lbl_estado.setText("🚀 Creando tabla de padrón en la base de datos...")
            self.lbl_estado.setStyleSheet("background-color: #d1ecf1; color: #0c5460;")
            
            padron_service = PadronService(db)
            
            nombre_proyecto = self.txt_nombre.text().strip()
            
            # Crear tabla dinámica
            exito, uuid_padron, nombre_tabla, errores = padron_service.crear_tabla_padron_dinamica(
                nombre_proyecto, self.estructura_columnas
            )
            
            if not exito:
                raise Exception(f"Error creando tabla: {' '.join(errores)}")
            
            self.uuid_padron = uuid_padron
            self.nombre_tabla = nombre_tabla
            
            self.progress_bar.setValue(30)
            self.lbl_estado.setText(f"✅ Tabla creada: {nombre_tabla}")
            
            # PASO 2: Cargar datos iniciales
            self.progress_bar.setValue(40)
            self.lbl_estado.setText("📥 Cargando datos iniciales al padrón...")
            
            # Determinar CSV a usar
            if self.radio_reutilizar.isChecked():
                csv_path = self.csv_path
            else:
                csv_path = self.csv_carga_path
            
            # Crear mapeo de columnas
            mapeo_columnas = {}
            for col in self.estructura_columnas:
                # Para columnas del CSV original, usar nombre original
                if col['nombre_original'] in mapeo_columnas.values():
                    continue
                mapeo_columnas[col['nombre_original']] = col['nombre_limpio']
            
            # Cargar datos
            exito, registros, errores = padron_service.cargar_datos_csv_a_padron(
                uuid_padron, csv_path, mapeo_columnas
            )
            
            if not exito:
                raise Exception(f"Error cargando datos: {' '.join(errores)}")
            
            self.progress_bar.setValue(70)
            self.lbl_estado.setText(f"✅ {registros} registros cargados al padrón")
            
            # PASO 3: Crear proyecto en la base de datos
            self.progress_bar.setValue(80)
            self.lbl_estado.setText("📋 Creando registro del proyecto...")
            
            project_service = ProjectService(db)
            
            # Logo path si existe
            logo_path = getattr(self, 'logo_path', None)
            
            proyecto = project_service.crear_proyecto(
                nombre=nombre_proyecto,
                descripcion=self.txt_descripcion.toPlainText().strip(),
                tabla_padron=uuid_padron,  # Guardamos el UUID
                usuario=self.usuario,
                logo=logo_path
            )
            
            self.proyecto = proyecto
            
            self.progress_bar.setValue(100)
            self.lbl_estado.setText("🎉 ¡Proyecto creado exitosamente!")
            self.lbl_estado.setStyleSheet("background-color: #d4edda; color: #155724;")
            
            db.commit()
            
            # Éxito
            QTimer.singleShot(1000, self.on_proyecto_creado_exito)
            
        except Exception as e:
            db.rollback()
            self.lbl_estado.setText(f"❌ Error: {str(e)}")
            self.lbl_estado.setStyleSheet("background-color: #f8d7da; color: #721c24;")
            print(f"ERROR creando proyecto: {e}")
            import traceback
            traceback.print_exc()
            
        finally:
            db.close()
    
    def on_proyecto_creado_exito(self):
        """Cuando el proyecto se crea exitosamente"""
        self.proyecto_guardado.emit()
        
        if self.stacked_widget:
            # Buscar y mostrar dashboard de proyectos
            for i in range(self.stacked_widget.count()):
                widget = self.stacked_widget.widget(i)
                if widget.__class__.__name__ == 'DashboardProyectos':
                    self.stacked_widget.setCurrentWidget(widget)
                    break
    
    def cargar_proyecto_existente(self):
        """Carga un proyecto existente para edición"""
        db = SessionLocal()
        try:
            project_service = ProjectService(db)
            proyectos = project_service.obtener_proyectos_usuario(self.usuario)
            
            for proyecto in proyectos:
                if proyecto.id == self.proyecto_id:
                    self.proyecto = proyecto
                    
                    # Cargar datos en UI
                    self.txt_nombre.setText(proyecto.nombre)
                    if proyecto.descripcion:
                        self.txt_descripcion.setText(proyecto.descripcion)
                    
                    if proyecto.logo:
                        self.logo_path = proyecto.logo
                        pixmap = QPixmap(proyecto.logo)
                        if not pixmap.isNull():
                            pixmap = pixmap.scaled(120, 120, 
                                                 Qt.AspectRatioMode.KeepAspectRatio,
                                                 Qt.TransformationMode.SmoothTransformation)
                            self.lbl_logo_preview.setPixmap(pixmap)
                            self.lbl_logo_preview.setText("")
                            self.lbl_logo_texto.setText(os.path.basename(proyecto.logo))
                    
                    break
                    
        finally:
            db.close()
    
    def resetear_csv_ui(self):
        """Resetea la UI de CSV"""
        self.lbl_csv_icono.setText("📁")
        self.lbl_csv_titulo.setText("Arrastra o haz clic para seleccionar CSV")
        self.lbl_csv_info.hide()
        self.csv_path = None
        self.estructura_columnas = []
        self.tabla_columnas.setRowCount(0)
    
    def cancelar(self):
        """Cancela la creación/edición del proyecto"""
        reply = QMessageBox.question(
            self, "Confirmar Cancelación",
            "¿Está seguro que desea cancelar? Los cambios no guardados se perderán.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            if self.stacked_widget:
                # Volver al dashboard de proyectos
                for i in range(self.stacked_widget.count()):
                    widget = self.stacked_widget.widget(i)
                    if widget.__class__.__name__ == 'DashboardProyectos':
                        self.stacked_widget.setCurrentWidget(widget)
                        break