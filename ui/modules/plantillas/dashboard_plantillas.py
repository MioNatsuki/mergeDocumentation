from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTableWidget,
    QTableWidgetItem, QHeaderView, QMessageBox, QComboBox, QFrame, QLineEdit,
    QFileDialog, QProgressBar, QTextEdit, QGroupBox, QFormLayout, QCheckBox
)
from PyQt6.QtCore import Qt, pyqtSignal, QThread
from PyQt6.QtGui import QFont
from config.database import SessionLocal
from core.template_service import TemplateService
from core.padron_service import PadronService
from core.models import Plantilla, Proyecto
import os
import tempfile
import json
from typing import Dict

class ProcesarWordThread(QThread):
    """Hilo para procesar archivo Word en segundo plano"""
    procesamiento_completado = pyqtSignal(list, list)  # placeholders, errores
    
    def __init__(self, word_path: str):
        super().__init__()
        self.word_path = word_path
    
    def run(self):
        try:
            placeholders = TemplateService.extraer_placeholders(self.word_path)
            self.procesamiento_completado.emit(placeholders, [])
        except Exception as e:
            self.procesamiento_completado.emit([], [str(e)])

class GenerarPreviewThread(QThread):
    """Hilo para generar preview en segundo plano"""
    preview_generado = pyqtSignal(bool, str)  # éxito, mensaje/ruta
    
    def __init__(self, word_path: str, mapeo: dict, datos_ejemplo: dict, output_dir: str):
        super().__init__()
        self.word_path = word_path
        self.mapeo = mapeo
        self.datos_ejemplo = datos_ejemplo
        self.output_dir = output_dir
    
    def run(self):
        try:
            # Generar PDF
            exito, ruta_pdf, mensaje = TemplateService.generar_pdf_directo(
                self.word_path,
                self.mapeo,
                self.datos_ejemplo,
                os.path.join(self.output_dir, "preview.pdf")
            )
            self.preview_generado.emit(exito, ruta_pdf if exito else mensaje)
        except Exception as e:
            self.preview_generado.emit(False, str(e))

class DashboardPlantillas(QWidget):
    """Dashboard para gestión de plantillas Word"""
    
    plantilla_guardada = pyqtSignal()
    
    def __init__(self, usuario, proyecto_id, stacked_widget=None):
        super().__init__()
        self.usuario = usuario
        self.proyecto_id = proyecto_id
        self.stacked_widget = stacked_widget
        self.word_path = None
        self.placeholders = []
        self.columnas_padron = []
        self.plantilla_existente = None
        
        self.setup_ui()
        self.cargar_columnas_padron()
        self.cargar_plantillas_existentes()
    
    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(20)
        
        # Header
        header = QLabel("Gestión de Plantillas Word")
        header.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(header)
        
        # Sección 1: Subir plantilla
        upload_group = QGroupBox("1. Subir plantilla Word (.docx)")
        upload_group.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        upload_layout = QVBoxLayout()
        
        # Selección de plantilla existente
        form_layout = QFormLayout()
        
        self.combo_plantillas = QComboBox()
        self.combo_plantillas.addItem("-- Crear nueva plantilla --", None)
        self.combo_plantillas.currentIndexChanged.connect(self.on_plantilla_seleccionada)
        form_layout.addRow("Plantillas existentes:", self.combo_plantillas)
        
        upload_layout.addLayout(form_layout)
        
        # Upload manual
        upload_manual_layout = QHBoxLayout()
        
        self.txt_ruta_word = QLineEdit()
        self.txt_ruta_word.setPlaceholderText("Ruta del archivo Word...")
        self.txt_ruta_word.setReadOnly(True)
        
        btn_examinar = QPushButton("Examinar...")
        btn_examinar.clicked.connect(self.examinar_archivo)
        
        btn_cargar = QPushButton("📁 Cargar Word")
        btn_cargar.clicked.connect(self.cargar_archivo_manual)
        btn_cargar.setStyleSheet("background-color: #17a2b8; color: white; padding: 8px;")
        
        upload_manual_layout.addWidget(QLabel("O subir nuevo:"))
        upload_manual_layout.addWidget(self.txt_ruta_word)
        upload_manual_layout.addWidget(btn_examinar)
        upload_manual_layout.addWidget(btn_cargar)
        upload_manual_layout.addStretch()
        
        upload_layout.addLayout(upload_manual_layout)
        
        # Info
        lbl_info = QLabel("⚠️ El documento debe contener placeholders como {{nombre}}, {{direccion}}, etc.")
        lbl_info.setStyleSheet("color: #856404; background-color: #fff3cd; padding: 8px; border-radius: 4px;")
        upload_layout.addWidget(lbl_info)
        
        upload_group.setLayout(upload_layout)
        layout.addWidget(upload_group)
        
        # Sección 2: Mapeo de campos (inicialmente oculta)
        self.mapeo_group = QGroupBox("2. Mapear placeholders a columnas del padrón")
        self.mapeo_group.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        self.mapeo_group.setVisible(False)
        mapeo_layout = QVBoxLayout()
        
        # Estadísticas
        self.lbl_estadisticas = QLabel("")
        self.lbl_estadisticas.setStyleSheet("font-weight: bold; color: #495057;")
        mapeo_layout.addWidget(self.lbl_estadisticas)
        
        # Tabla de mapeo
        self.tabla_mapeo = QTableWidget()
        self.tabla_mapeo.setColumnCount(3)
        self.tabla_mapeo.setHorizontalHeaderLabels(["Placeholder", "Columna Padrón", "Valor de Ejemplo"])
        self.tabla_mapeo.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tabla_mapeo.setAlternatingRowColors(True)
        mapeo_layout.addWidget(self.tabla_mapeo)
        
        # Botones de acción en mapeo
        btn_mapeo_layout = QHBoxLayout()
        
        self.btn_auto_mapear = QPushButton("🔍 Mapeo Automático")
        self.btn_auto_mapear.clicked.connect(self.mapeo_automatico)
        self.btn_auto_mapear.setToolTip("Intenta mapear automáticamente por nombre similar")
        
        self.btn_limpiar_mapeo = QPushButton("🗑️ Limpiar Todo")
        self.btn_limpiar_mapeo.clicked.connect(self.limpiar_mapeo)
        
        btn_mapeo_layout.addWidget(self.btn_auto_mapear)
        btn_mapeo_layout.addWidget(self.btn_limpiar_mapeo)
        btn_mapeo_layout.addStretch()
        
        mapeo_layout.addLayout(btn_mapeo_layout)
        self.mapeo_group.setLayout(mapeo_layout)
        layout.addWidget(self.mapeo_group)
        
        # Sección 3: Configuración
        self.config_group = QGroupBox("3. Configuración de plantilla")
        self.config_group.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        self.config_group.setVisible(False)
        config_layout = QFormLayout()
        
        self.txt_nombre = QLineEdit()
        self.txt_nombre.setPlaceholderText("Nombre de la plantilla")
        config_layout.addRow("Nombre:", self.txt_nombre)
        
        self.txt_descripcion = QLineEdit()
        self.txt_descripcion.setPlaceholderText("Descripción opcional")
        config_layout.addRow("Descripción:", self.txt_descripcion)
        
        self.check_activa = QCheckBox("Plantilla activa")
        self.check_activa.setChecked(True)
        config_layout.addRow("", self.check_activa)
        
        self.config_group.setLayout(config_layout)
        layout.addWidget(self.config_group)
        
        # Área de progreso para preview
        self.preview_group = QGroupBox("Vista Previa")
        self.preview_group.setVisible(False)
        preview_layout = QVBoxLayout()
        
        self.progress_preview = QProgressBar()
        self.progress_preview.setTextVisible(True)
        self.progress_preview.setVisible(False)
        
        self.texto_log = QTextEdit()
        self.texto_log.setMaximumHeight(100)
        self.texto_log.setReadOnly(True)
        self.texto_log.setStyleSheet("font-family: monospace; font-size: 10px;")
        
        preview_layout.addWidget(self.progress_preview)
        preview_layout.addWidget(self.texto_log)
        self.preview_group.setLayout(preview_layout)
        layout.addWidget(self.preview_group)
        
        # Botones principales
        button_layout = QHBoxLayout()
        
        self.btn_guardar = QPushButton("💾 Guardar Plantilla")
        self.btn_guardar.clicked.connect(self.guardar_plantilla)
        self.btn_guardar.setEnabled(False)
        self.btn_guardar.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                border: none;
                padding: 12px 24px;
                border-radius: 6px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:disabled {
                background-color: #6c757d;
            }
        """)
        
        self.btn_preview = QPushButton("👁️ Generar Preview")
        self.btn_preview.clicked.connect(self.generar_preview)
        self.btn_preview.setEnabled(False)
        self.btn_preview.setStyleSheet("""
            QPushButton {
                background-color: #17a2b8;
                color: white;
                border: none;
                padding: 12px 24px;
                border-radius: 6px;
            }
            QPushButton:disabled {
                background-color: #6c757d;
            }
        """)
        
        self.btn_cancelar = QPushButton("❌ Cancelar")
        self.btn_cancelar.clicked.connect(self.cancelar)
        self.btn_cancelar.setStyleSheet("""
            QPushButton {
                background-color: #6c757d;
                color: white;
                border: none;
                padding: 12px 24px;
                border-radius: 6px;
            }
        """)
        
        button_layout.addWidget(self.btn_guardar)
        button_layout.addWidget(self.btn_preview)
        button_layout.addStretch()
        button_layout.addWidget(self.btn_cancelar)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
    
    def cargar_columnas_padron(self):
        """Carga columnas del padrón del proyecto"""
        db = SessionLocal()
        try:
            # Obtener UUID del padrón del proyecto
            proyecto = db.query(Proyecto).filter(Proyecto.id == self.proyecto_id).first()
            
            if proyecto and proyecto.tabla_padron:
                padron_service = PadronService(db)
                self.columnas_padron = padron_service.obtener_columnas_padron(proyecto.tabla_padron)
                
                # También obtener datos de ejemplo para preview
                self.datos_ejemplo = padron_service.obtener_datos_ejemplo_real(proyecto.tabla_padron, limit=1)
                if self.datos_ejemplo:
                    self.datos_ejemplo = self.datos_ejemplo[0]
                else:
                    self.datos_ejemplo = {}
        except Exception as e:
            print(f"Error cargando columnas padrón: {e}")
            self.columnas_padron = []
            self.datos_ejemplo = {}
        finally:
            db.close()
    
    def cargar_plantillas_existentes(self):
        """Carga plantillas existentes del proyecto"""
        db = SessionLocal()
        try:
            plantillas = db.query(Plantilla).filter(
                Plantilla.proyecto_id == self.proyecto_id,
                Plantilla.is_deleted == False
            ).all()
            
            for plantilla in plantillas:
                self.combo_plantillas.addItem(plantilla.nombre, plantilla.id)
                
        except Exception as e:
            print(f"Error cargando plantillas: {e}")
        finally:
            db.close()
    
    def on_plantilla_seleccionada(self):
        """Cuando se selecciona una plantilla existente"""
        plantilla_id = self.combo_plantillas.currentData()
        
        if plantilla_id:
            # Cargar plantilla existente
            db = SessionLocal()
            try:
                plantilla = db.query(Plantilla).filter(Plantilla.id == plantilla_id).first()
                if plantilla:
                    self.plantilla_existente = plantilla
                    
                    # Cargar datos en la UI
                    self.txt_nombre.setText(plantilla.nombre)
                    self.txt_descripcion.setText(plantilla.descripcion or "")
                    self.check_activa.setChecked(plantilla.activa)
                    
                    # Si tiene archivo Word, cargarlo
                    if plantilla.ruta_archivo_docx and os.path.exists(plantilla.ruta_archivo_docx):
                        self.word_path = plantilla.ruta_archivo_docx
                        self.txt_ruta_word.setText(plantilla.ruta_archivo_docx)
                        
                        # Extraer placeholders
                        self.procesar_word(plantilla.ruta_archivo_docx)
                        
                        # Cargar mapeo existente
                        if plantilla.campos_mapeo:
                            self.cargar_mapeo_existente(plantilla.campos_mapeo)
                    
                    self.btn_guardar.setText("💾 Actualizar Plantilla")
                    
            finally:
                db.close()
        else:
            # Nueva plantilla
            self.plantilla_existente = None
            self.limpiar_formulario()
            self.btn_guardar.setText("💾 Guardar Plantilla")
    
    def cargar_mapeo_existente(self, campos_mapeo: dict):
        """Carga un mapeo existente en la tabla"""
        if not campos_mapeo:
            return
        
        # Buscar cada placeholder en la tabla y asignar columna
        for row in range(self.tabla_mapeo.rowCount()):
            placeholder_item = self.tabla_mapeo.item(row, 0)
            if placeholder_item:
                placeholder = placeholder_item.text().replace('{', '').replace('}', '')
                
                # Buscar en el mapeo
                for key, value in campos_mapeo.items():
                    if key == placeholder and value:
                        # Encontrar el combo y asignar valor
                        combo = self.tabla_mapeo.cellWidget(row, 1)
                        if combo:
                            index = combo.findData(value)
                            if index >= 0:
                                combo.setCurrentIndex(index)
    
    def examinar_archivo(self):
        """Abre diálogo para seleccionar archivo Word"""
        archivo, _ = QFileDialog.getOpenFileName(
            self,
            "Seleccionar plantilla Word",
            "",
            "Documentos Word (*.docx);;Todos los archivos (*)"
        )
        
        if archivo:
            self.txt_ruta_word.setText(archivo)
    
    def cargar_archivo_manual(self):
        """Carga archivo Word desde la ruta especificada"""
        ruta = self.txt_ruta_word.text().strip()
        
        if not ruta:
            QMessageBox.warning(self, "Error", "Por favor seleccione un archivo Word")
            return
        
        if not os.path.exists(ruta):
            QMessageBox.warning(self, "Error", f"El archivo no existe:\n{ruta}")
            return
        
        if not ruta.lower().endswith('.docx'):
            QMessageBox.warning(self, "Error", "El archivo debe ser .docx")
            return
        
        # Procesar el archivo
        self.procesar_word(ruta)
    
    def procesar_word(self, word_path: str):
        """Procesa archivo Word y extrae placeholders"""
        self.word_path = word_path
        
        # Mostrar progreso
        self.texto_log.clear()
        self.agregar_log(f"📄 Procesando: {os.path.basename(word_path)}...")
        
        # Ejecutar en hilo para no bloquear UI
        self.thread_procesar = ProcesarWordThread(word_path)
        self.thread_procesar.procesamiento_completado.connect(self.on_procesamiento_completado)
        self.thread_procesar.start()
    
    def on_procesamiento_completado(self, placeholders: list, errores: list):
        """Cuando termina el procesamiento del Word"""
        if errores:
            QMessageBox.critical(self, "Error", f"Error procesando Word:\n{errores[0]}")
            return
        
        if not placeholders:
            QMessageBox.warning(self, "Sin placeholders", 
                              "No se encontraron placeholders {{...}} en el documento.\n\n"
                              "Asegúrese de usar el formato: {{nombre}}, {{direccion}}, etc.")
            return
        
        self.placeholders = placeholders
        self.agregar_log(f"✅ Encontrados {len(placeholders)} placeholders")
        
        # Mostrar secciones de mapeo y configuración
        self.mapeo_group.setVisible(True)
        self.config_group.setVisible(True)
        self.preview_group.setVisible(True)
        
        # Actualizar estadísticas
        self.lbl_estadisticas.setText(
            f"📊 {len(placeholders)} placeholders encontrados | "
            f"{len(self.columnas_padron)} columnas en padrón"
        )
        
        # Mostrar tabla de mapeo
        self.mostrar_tabla_mapeo()
        
        # Habilitar botones
        self.btn_guardar.setEnabled(True)
        self.btn_preview.setEnabled(True)
        
        # Si es nueva plantilla, sugerir nombre basado en archivo
        if not self.plantilla_existente:
            nombre_base = os.path.splitext(os.path.basename(self.word_path))[0]
            self.txt_nombre.setText(f"Plantilla {nombre_base}")
    
    def mostrar_tabla_mapeo(self):
        """Muestra tabla con placeholders y dropdowns para mapeo"""
        self.tabla_mapeo.setRowCount(len(self.placeholders))
        
        for i, placeholder in enumerate(self.placeholders):
            # Columna 1: Placeholder
            item = QTableWidgetItem(f"{{{{{placeholder}}}}}")
            item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            item.setToolTip(f"Placeholder: {placeholder}")
            self.tabla_mapeo.setItem(i, 0, item)
            
            # Columna 2: Dropdown con columnas del padrón
            combo = QComboBox()
            combo.addItem("-- No asignar --", None)
            
            # Agrupar columnas por tipo
            comboTipos = {}
            for col in self.columnas_padron:
                tipo = col.get('tipo', 'texto')
                if tipo not in comboTipos:
                    comboTipos[tipo] = QComboBox()
                    comboTipos[tipo].addItem(f"-- {tipo.upper()} --", None)
                
                comboTipos[tipo].addItem(f"{col['nombre']} ({col['tipo_db']})", col['nombre'])
            
            # Crear combo principal con grupos
            combo.addItem("═════ TEXTOS ═════", None)
            for col in self.columnas_padron:
                if col['tipo'] == 'texto':
                    combo.addItem(f"📝 {col['nombre']}", col['nombre'])
            
            combo.addItem("═════ NÚMEROS ════", None)
            for col in self.columnas_padron:
                if col['tipo'] == 'numero':
                    combo.addItem(f"🔢 {col['nombre']}", col['nombre'])
            
            combo.addItem("═════ FECHAS ═════", None)
            for col in self.columnas_padron:
                if col['tipo'] == 'fecha':
                    combo.addItem(f"📅 {col['nombre']}", col['nombre'])
            
            # Buscar match automático
            placeholder_lower = placeholder.lower()
            mejor_match = None
            mejor_puntaje = 0
            
            for col in self.columnas_padron:
                columna_lower = col['nombre'].lower()
                
                # Calcular puntaje de similitud
                puntaje = 0
                if placeholder_lower == columna_lower:
                    puntaje = 100
                elif placeholder_lower in columna_lower:
                    puntaje = 80
                elif columna_lower in placeholder_lower:
                    puntaje = 70
                elif any(palabra in columna_lower for palabra in placeholder_lower.split('_')):
                    puntaje = 50
                
                if puntaje > mejor_puntaje:
                    mejor_puntaje = puntaje
                    mejor_match = col['nombre']
            
            # Seleccionar mejor match si hay
            if mejor_match and mejor_puntaje > 40:
                index = combo.findData(mejor_match)
                if index >= 0:
                    combo.setCurrentIndex(index)
            
            self.tabla_mapeo.setCellWidget(i, 1, combo)
            
            # Columna 3: Valor de ejemplo (se llena después)
            item_ejemplo = QTableWidgetItem("")
            item_ejemplo.setFlags(item_ejemplo.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.tabla_mapeo.setItem(i, 2, item_ejemplo)
        
        # Actualizar valores de ejemplo
        self.actualizar_valores_ejemplo()
    
    def actualizar_valores_ejemplo(self):
        """Actualiza la columna de valores de ejemplo basado en el mapeo actual"""
        if not self.datos_ejemplo:
            return
        
        for i in range(self.tabla_mapeo.rowCount()):
            combo = self.tabla_mapeo.cellWidget(i, 1)
            if combo:
                columna = combo.currentData()
                if columna and columna in self.datos_ejemplo:
                    valor = self.datos_ejemplo[columna]
                    if valor is None:
                        valor = "(vacío)"
                    elif len(str(valor)) > 30:
                        valor = str(valor)[:27] + "..."
                    
                    item = self.tabla_mapeo.item(i, 2)
                    if item:
                        item.setText(str(valor))
    
    def mapeo_automatico(self):
        """Intenta mapear automáticamente todos los placeholders"""
        for i in range(self.tabla_mapeo.rowCount()):
            placeholder_item = self.tabla_mapeo.item(i, 0)
            if placeholder_item:
                placeholder = placeholder_item.text().replace('{', '').replace('}', '')
                
                # Si ya tiene asignación, saltar
                combo = self.tabla_mapeo.cellWidget(i, 1)
                if combo and combo.currentData():
                    continue
                
                # Buscar mejor match
                placeholder_lower = placeholder.lower()
                mejor_match = None
                mejor_puntaje = 0
                
                for col in self.columnas_padron:
                    columna_lower = col['nombre'].lower()
                    
                    # Calcular similitud
                    if placeholder_lower == columna_lower:
                        mejor_match = col['nombre']
                        mejor_puntaje = 100
                        break
                    elif placeholder_lower in columna_lower or columna_lower in placeholder_lower:
                        puntaje = 70
                        if puntaje > mejor_puntaje:
                            mejor_puntaje = puntaje
                            mejor_match = col['nombre']
                
                # Asignar si encontramos buen match
                if mejor_match and mejor_puntaje > 60:
                    index = combo.findData(mejor_match)
                    if index >= 0:
                        combo.setCurrentIndex(index)
        
        # Actualizar valores de ejemplo
        self.actualizar_valores_ejemplo()
        QMessageBox.information(self, "Mapeo Automático", "Mapeo automático completado")
    
    def limpiar_mapeo(self):
        """Limpia todas las asignaciones"""
        for i in range(self.tabla_mapeo.rowCount()):
            combo = self.tabla_mapeo.cellWidget(i, 1)
            if combo:
                combo.setCurrentIndex(0)  # "-- No asignar --"
        
        self.actualizar_valores_ejemplo()
    
    def obtener_mapeo(self) -> Dict:
        """Obtiene el mapeo actual de la tabla"""
        mapeo = {}
        for i in range(self.tabla_mapeo.rowCount()):
            placeholder_item = self.tabla_mapeo.item(i, 0)
            if placeholder_item:
                placeholder = placeholder_item.text().replace('{', '').replace('}', '')
                combo = self.tabla_mapeo.cellWidget(i, 1)
                if combo:
                    columna = combo.currentData()
                    if columna:
                        mapeo[placeholder] = columna
        return mapeo
    
    def generar_preview(self):
        """Genera un PDF de preview con datos de ejemplo"""
        mapeo = self.obtener_mapeo()
        
        if not mapeo:
            QMessageBox.warning(self, "Error", 
                              "Debe asignar al menos un placeholder a una columna del padrón")
            return
        
        if not self.datos_ejemplo:
            QMessageBox.warning(self, "Error", 
                              "No hay datos de ejemplo disponibles del padrón")
            return
        
        # Crear directorio temporal para preview
        temp_dir = tempfile.gettempdir()
        preview_dir = os.path.join(temp_dir, "preview_plantillas")
        os.makedirs(preview_dir, exist_ok=True)
        
        # Configurar UI para preview
        self.progress_preview.setVisible(True)
        self.progress_preview.setRange(0, 0)  # Progress bar indeterminado
        self.texto_log.clear()
        self.agregar_log("🔄 Generando preview...")
        
        # Ejecutar en hilo
        self.thread_preview = GenerarPreviewThread(
            self.word_path,
            mapeo,
            self.datos_ejemplo,
            preview_dir
        )
        self.thread_preview.preview_generado.connect(self.on_preview_generado)
        self.thread_preview.start()
    
    def on_preview_generado(self, exito: bool, resultado: str):
        """Cuando termina la generación del preview"""
        self.progress_preview.setVisible(False)
        
        if exito:
            self.agregar_log(f"✅ Preview generado: {resultado}")
            
            # Preguntar si quiere abrir el PDF
            reply = QMessageBox.question(
                self, "Preview Listo",
                "✅ Preview generado exitosamente.\n\n¿Desea abrir el archivo PDF?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                import subprocess
                try:
                    if os.name == 'nt':  # Windows
                        os.startfile(resultado)
                    elif os.name == 'posix':  # Linux/macOS
                        subprocess.run(['xdg-open', resultado])
                except:
                    QMessageBox.information(self, "Abrir PDF", 
                                          f"PDF generado en:\n{resultado}")
        else:
            self.agregar_log(f"❌ Error: {resultado}")
            QMessageBox.critical(self, "Error en Preview", 
                               f"No se pudo generar el preview:\n\n{resultado}")
    
    def guardar_plantilla(self):
        """Guarda o actualiza la plantilla en la base de datos"""
        # Validaciones
        nombre = self.txt_nombre.text().strip()
        if not nombre:
            QMessageBox.warning(self, "Error", "El nombre de la plantilla es obligatorio")
            return
        
        mapeo = self.obtener_mapeo()
        if not mapeo:
            QMessageBox.warning(self, "Error", 
                              "Debe asignar al menos un placeholder a una columna del padrón")
            return
        
        # Preparar directorio de plantillas
        from config.settings import settings
        plantillas_dir = os.path.join(os.path.dirname(__file__), "..", "..", "..", "plantillas")
        os.makedirs(plantillas_dir, exist_ok=True)
        
        db = SessionLocal()
        try:
            # Copiar archivo Word a directorio de plantillas
            nombre_archivo = f"{nombre.replace(' ', '_')}_{self.proyecto_id}.docx"
            ruta_final = TemplateService.copiar_plantilla_a_destino(
                self.word_path,
                plantillas_dir,
                nombre_archivo
            )
            
            if self.plantilla_existente:
                # Actualizar plantilla existente
                plantilla = self.plantilla_existente
                plantilla.nombre = nombre
                plantilla.descripcion = self.txt_descripcion.text().strip()
                plantilla.ruta_archivo_docx = ruta_final
                plantilla.campos_mapeo = mapeo
                plantilla.configuracion = {"fuente": "Calibri", "tamano": 11}
                plantilla.activa = self.check_activa.isChecked()
                
                mensaje = "✅ Plantilla actualizada"
            else:
                # Crear nueva plantilla
                plantilla = Plantilla(
                    proyecto_id=self.proyecto_id,
                    nombre=nombre,
                    descripcion=self.txt_descripcion.text().strip(),
                    ruta_archivo_docx=ruta_final,
                    campos_mapeo=mapeo,
                    configuracion={"fuente": "Calibri", "tamano": 11},
                    activa=self.check_activa.isChecked(),
                    usuario_creador=self.usuario.id
                )
                db.add(plantilla)
                mensaje = "✅ Plantilla creada"
            
            db.commit()
            
            QMessageBox.information(self, "Éxito", 
                                  f"{mensaje}\n\n"
                                  f"• {len(mapeo)} campos mapeados\n"
                                  f"• Archivo: {os.path.basename(ruta_final)}")
            
            self.plantilla_guardada.emit()
            
        except Exception as e:
            db.rollback()
            QMessageBox.critical(self, "Error", f"Error guardando plantilla:\n{str(e)}")
            print(f"Error guardando plantilla: {e}")
        finally:
            db.close()
    
    def cancelar(self):
        """Cancela y regresa al dashboard de proyectos"""
        if self.stacked_widget:
            # Buscar y mostrar dashboard de proyectos
            for i in range(self.stacked_widget.count()):
                widget = self.stacked_widget.widget(i)
                if widget.__class__.__name__ == "DashboardProyectos":
                    self.stacked_widget.setCurrentWidget(widget)
                    break
    
    def limpiar_formulario(self):
        """Limpia todo el formulario"""
        self.word_path = None
        self.placeholders = []
        self.plantilla_existente = None
        
        self.txt_ruta_word.clear()
        self.txt_nombre.clear()
        self.txt_descripcion.clear()
        self.check_activa.setChecked(True)
        
        self.mapeo_group.setVisible(False)
        self.config_group.setVisible(False)
        self.preview_group.setVisible(False)
        
        self.btn_guardar.setEnabled(False)
        self.btn_preview.setEnabled(False)
        
        self.tabla_mapeo.setRowCount(0)
        self.texto_log.clear()
    
    def agregar_log(self, mensaje: str):
        """Agrega mensaje al log"""
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.texto_log.append(f"[{timestamp}] {mensaje}")
        
        # Auto-scroll al final
        cursor = self.texto_log.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        self.texto_log.setTextCursor(cursor)