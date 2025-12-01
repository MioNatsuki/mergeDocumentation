# ui/modules/proyectos/formulario_proyecto.py - VERSIÓN COMPLETA REDISEÑADA
import os
import shutil
import uuid
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QTextEdit, QPushButton, QMessageBox,
                             QFrame, QComboBox, QFileDialog, QProgressBar,
                             QGroupBox, QScrollArea)
from PyQt6.QtCore import Qt, pyqtSignal, QThread
from PyQt6.QtGui import QFont, QPixmap, QPainter, QColor
from config.database import SessionLocal
from core.project_service import ProjectService
from core.padron_service import PadronService
from core.models import Proyecto
import json

class LogoUploadThread(QThread):
    """Hilo para procesar upload de logos en segundo plano"""
    upload_complete = pyqtSignal(str, str)  # ruta_temporal, ruta_final
    upload_error = pyqtSignal(str)
    progress = pyqtSignal(int)
    
    def __init__(self, file_path, proyecto_id=None):
        super().__init__()
        self.file_path = file_path
        self.proyecto_id = proyecto_id
        self.app_data_dir = self.get_app_data_dir()
    
    def get_app_data_dir(self):
        """Obtiene directorio AppData/Local del usuario"""
        app_data = os.getenv('LOCALAPPDATA')
        if not app_data:
            # Fallback para otros sistemas
            app_data = os.path.expanduser('~/.local/share')
        
        app_dir = os.path.join(app_data, "SistemaCorrespondencia")
        os.makedirs(os.path.join(app_dir, "logos", "proyectos"), exist_ok=True)
        os.makedirs(os.path.join(app_dir, "temp"), exist_ok=True)
        
        return app_dir
    
    def run(self):
        try:
            self.progress.emit(10)
            
            # Verificar que el archivo existe
            if not os.path.exists(self.file_path):
                self.upload_error.emit("El archivo no existe")
                return
            
            # Generar nombre único para el logo
            ext = os.path.splitext(self.file_path)[1].lower()
            if self.proyecto_id:
                logo_name = f"proyecto_{self.proyecto_id}_logo{ext}"
            else:
                logo_name = f"temp_{uuid.uuid4().hex[:8]}{ext}"
            
            # Ruta temporal (para preview)
            temp_path = os.path.join(self.app_data_dir, "temp", logo_name)
            
            self.progress.emit(30)
            
            # Copiar a temp para preview inmediato
            shutil.copy2(self.file_path, temp_path)
            
            self.progress.emit(50)
            
            # Ruta final (en logos/proyectos)
            final_path = os.path.join(self.app_data_dir, "logos", "proyectos", logo_name)
            
            # Si ya existe un logo para este proyecto, eliminarlo
            if self.proyecto_id and os.path.exists(final_path):
                os.remove(final_path)
            
            self.progress.emit(70)
            
            # Redimensionar si es muy grande (máx 345x170)
            self.redimensionar_logo(self.file_path, final_path, max_width=345, max_height=170)
            
            self.progress.emit(100)
            self.upload_complete.emit(temp_path, final_path)
            
        except Exception as e:
            self.upload_error.emit(f"Error procesando logo: {str(e)}")
    
    def redimensionar_logo(self, src_path, dst_path, max_width=345, max_height=170):
        """Redimensiona logo manteniendo aspect ratio"""
        from PIL import Image
        
        with Image.open(src_path) as img:
            # Convertir a RGB si es necesario
            if img.mode in ('RGBA', 'LA', 'P'):
                img = img.convert('RGB')
            
            # Calcular nuevo tamaño manteniendo aspect ratio
            original_width, original_height = img.size
            ratio = min(max_width/original_width, max_height/original_height)
            
            if ratio < 1:  # Solo redimensionar si es más grande
                new_size = (int(original_width * ratio), int(original_height * ratio))
                img = img.resize(new_size, Image.Resampling.LANCZOS)
            
            # Guardar
            img.save(dst_path, 'PNG' if dst_path.lower().endswith('.png') else 'JPEG', quality=85)

class LogoPreview(QFrame):
    """Widget de preview de logo con estilos"""
    def __init__(self):
        super().__init__()
        self.setup_ui()
        self.logo_path = None
    
    def setup_ui(self):
        self.setFixedSize(180, 100)
        self.setStyleSheet("""
            LogoPreview {
                background-color: #f8f9fa;
                border: 3px dashed #99b898;
                border-radius: 12px;
            }
            LogoPreview:hover {
                border-color: #ff847c;
                background-color: #fff5f5;
            }
        """)
        
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.lbl_preview = QLabel("📁 Sin logo")
        self.lbl_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_preview.setStyleSheet("""
            QLabel {
                font-family: 'Jura';
                font-size: 14px;
                color: #7a8b90;
            }
        """)
        
        self.lbl_tamano = QLabel("")
        self.lbl_tamano.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_tamano.setStyleSheet("""
            QLabel {
                font-family: 'Jura';
                font-size: 10px;
                color: #99b898;
            }
        """)
        
        layout.addWidget(self.lbl_preview)
        layout.addWidget(self.lbl_tamano)
        self.setLayout(layout)
    
    def cargar_logo(self, logo_path):
        """Carga un logo en el preview"""
        self.logo_path = logo_path
        if logo_path and os.path.exists(logo_path):
            try:
                pixmap = QPixmap(logo_path)
                if not pixmap.isNull():
                    # Escalar manteniendo aspect ratio
                    pixmap = pixmap.scaled(150, 70, 
                                         Qt.AspectRatioMode.KeepAspectRatio,
                                         Qt.TransformationMode.SmoothTransformation)
                    self.lbl_preview.setPixmap(pixmap)
                    
                    # Mostrar tamaño
                    tamano = os.path.getsize(logo_path) / 1024  # KB
                    self.lbl_tamano.setText(f"{tamano:.1f} KB")
                else:
                    self.lbl_preview.setText("❌ Error")
            except Exception as e:
                self.lbl_preview.setText("❌ Error")
                print(f"Error cargando preview: {e}")
        else:
            self.lbl_preview.setText("📁 Sin logo")
            self.lbl_tamano.setText("")

class FormularioProyecto(QWidget):
    """Formulario para crear/editar proyectos - REDISEÑADO"""
    proyecto_guardado = pyqtSignal()
    
    def __init__(self, usuario, proyecto_id=None, stacked_widget=None):
        super().__init__()
        self.usuario = usuario
        self.proyecto_id = proyecto_id
        self.proyecto = None
        self.stacked_widget = stacked_widget
        self.logo_temp_path = None
        self.logo_final_path = None
        self.thread_upload = None
        self.setup_ui()
        self.cargar_datos_existentes()
        self.cargar_padrones()
    
    def setup_ui(self):
        # Layout principal con scroll
        main_layout = QVBoxLayout()
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Área scrollable
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        scroll_area.setStyleSheet("background-color: #f5f7fa;")
        
        # Widget contenedor
        container = QWidget()
        container_layout = QVBoxLayout()
        container_layout.setSpacing(25)
        container_layout.setContentsMargins(40, 30, 40, 40)
        
        # HEADER CON DEGRADADO
        header = QFrame()
        header.setFixedHeight(120)
        header.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #99b898, stop:0.3 #fecea8, stop:0.6 #ff847c, stop:1 #e84a5f);
                border-radius: 0px 0px 20px 20px;
            }
        """)
        
        header_layout = QVBoxLayout()
        header_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        titulo = QLabel("Nuevo Proyecto" if not self.proyecto_id else "Editar Proyecto")
        titulo.setFont(QFont("Jura", 24, QFont.Weight.Bold))
        titulo.setStyleSheet("color: #2a363b;")
        
        subtitulo = QLabel("Complete los datos del proyecto")
        subtitulo.setFont(QFont("Jura", 12))
        subtitulo.setStyleSheet("color: #2a363b; opacity: 0.9;")
        
        header_layout.addWidget(titulo)
        header_layout.addWidget(subtitulo)
        header.setLayout(header_layout)
        container_layout.addWidget(header)
        
        # FORMULARIO EN DOS COLUMNAS
        form_container = QFrame()
        form_container.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 20px;
                border: 2px solid #e0e6ed;
            }
        """)
        
        form_layout = QHBoxLayout()
        form_layout.setSpacing(40)
        form_layout.setContentsMargins(30, 30, 30, 30)
        
        # COLUMNA IZQUIERDA - Campos del formulario
        col_izq = QFrame()
        col_izq_layout = QVBoxLayout()
        col_izq_layout.setSpacing(20)
        
        # Campo: Nombre
        grupo_nombre = QGroupBox("Nombre del Proyecto *")
        grupo_nombre.setFont(QFont("Jura", 11, QFont.Weight.Bold))
        grupo_nombre.setStyleSheet("""
            QGroupBox {
                border: 2px solid #99b898;
                border-radius: 10px;
                margin-top: 12px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 10px 0 10px;
                color: #2a363b;
            }
        """)
        
        grupo_layout = QVBoxLayout()
        self.txt_nombre = QLineEdit()
        self.txt_nombre.setPlaceholderText("Ej: Proyecto Pensiones 2024")
        self.txt_nombre.setFont(QFont("Jura", 11))
        self.txt_nombre.setStyleSheet("""
            QLineEdit {
                padding: 12px;
                border: 2px solid #e0e6ed;
                border-radius: 8px;
                font-family: 'Jura';
            }
            QLineEdit:focus {
                border-color: #99b898;
                background-color: #f8fbf8;
            }
        """)
        grupo_layout.addWidget(self.txt_nombre)
        grupo_nombre.setLayout(grupo_layout)
        col_izq_layout.addWidget(grupo_nombre)
        
        # Campo: Descripción
        grupo_desc = QGroupBox("Descripción")
        grupo_desc.setFont(QFont("Jura", 11, QFont.Weight.Bold))
        grupo_desc.setStyleSheet(grupo_nombre.styleSheet().replace("#99b898", "#fecea8"))
        
        desc_layout = QVBoxLayout()
        self.txt_descripcion = QTextEdit()
        self.txt_descripcion.setPlaceholderText("Describa el propósito de este proyecto...")
        self.txt_descripcion.setFont(QFont("Jura", 10))
        self.txt_descripcion.setMaximumHeight(120)
        self.txt_descripcion.setStyleSheet("""
            QTextEdit {
                padding: 12px;
                border: 2px solid #e0e6ed;
                border-radius: 8px;
                font-family: 'Jura';
            }
            QTextEdit:focus {
                border-color: #fecea8;
            }
        """)
        desc_layout.addWidget(self.txt_descripcion)
        grupo_desc.setLayout(desc_layout)
        col_izq_layout.addWidget(grupo_desc)
        
        # Campo: Tabla Padrón
        grupo_padron = QGroupBox("Tabla de Padrón *")
        grupo_padron.setFont(QFont("Jura", 11, QFont.Weight.Bold))
        grupo_padron.setStyleSheet(grupo_nombre.styleSheet().replace("#99b898", "#ff847c"))
        
        padron_layout = QVBoxLayout()
        self.combo_padron = QComboBox()
        self.combo_padron.setFont(QFont("Jura", 11))
        self.combo_padron.setStyleSheet("""
            QComboBox {
                padding: 12px;
                border: 2px solid #e0e6ed;
                border-radius: 8px;
                font-family: 'Jura';
                background-color: white;
            }
            QComboBox:focus {
                border-color: #ff847c;
            }
            QComboBox::drop-down {
                border: none;
                padding-right: 15px;
            }
            QComboBox::down-arrow {
                image: url(down_arrow.png);
                width: 12px;
                height: 12px;
            }
        """)
        self.combo_padron.setPlaceholderText("Seleccione una tabla de padrón...")
        padron_layout.addWidget(self.combo_padron)
        grupo_padron.setLayout(padron_layout)
        col_izq_layout.addWidget(grupo_padron)
        
        col_izq.setLayout(col_izq_layout)
        form_layout.addWidget(col_izq, 2)  # 2/3 del espacio
        
        # COLUMNA DERECHA - Logo y acciones
        col_der = QFrame()
        col_der_layout = QVBoxLayout()
        col_der_layout.setSpacing(25)
        
        # Sección Logo
        grupo_logo = QGroupBox("Logo del Proyecto *")
        grupo_logo.setFont(QFont("Jura", 11, QFont.Weight.Bold))
        grupo_logo.setStyleSheet(grupo_nombre.styleSheet().replace("#99b898", "#e84a5f"))
        
        logo_layout = QVBoxLayout()
        logo_layout.setSpacing(15)
        logo_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Preview del logo
        self.logo_preview = LogoPreview()
        logo_layout.addWidget(self.logo_preview)
        
        # Botones de upload
        btn_logo_layout = QHBoxLayout()
        
        self.btn_seleccionar_logo = QPushButton("📁 Seleccionar Logo")
        self.btn_seleccionar_logo.clicked.connect(self.seleccionar_logo)
        self.btn_seleccionar_logo.setFont(QFont("Jura", 10))
        self.btn_seleccionar_logo.setStyleSheet("""
            QPushButton {
                background-color: #99b898;
                color: #2a363b;
                border: none;
                padding: 10px 15px;
                border-radius: 8px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #88a786;
            }
        """)
        
        self.btn_eliminar_logo = QPushButton("🗑️ Quitar Logo")
        self.btn_eliminar_logo.clicked.connect(self.eliminar_logo)
        self.btn_eliminar_logo.setFont(QFont("Jura", 10))
        self.btn_eliminar_logo.setEnabled(False)
        self.btn_eliminar_logo.setStyleSheet("""
            QPushButton {
                background-color: #e0e6ed;
                color: #5a6b70;
                border: none;
                padding: 10px 15px;
                border-radius: 8px;
            }
            QPushButton:hover:enabled {
                background-color: #ff847c;
                color: white;
            }
            QPushButton:disabled {
                color: #a0aec0;
            }
        """)
        
        btn_logo_layout.addWidget(self.btn_seleccionar_logo)
        btn_logo_layout.addWidget(self.btn_eliminar_logo)
        logo_layout.addLayout(btn_logo_layout)
        
        # Info del logo
        self.lbl_info_logo = QLabel("Formatos: PNG, JPG, JPEG | Máx: 345x170px")
        self.lbl_info_logo.setFont(QFont("Jura", 9))
        self.lbl_info_logo.setStyleSheet("color: #7a8b90;")
        self.lbl_info_logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo_layout.addWidget(self.lbl_info_logo)
        
        # Progress bar para upload
        self.progress_logo = QProgressBar()
        self.progress_logo.setVisible(False)
        self.progress_logo.setTextVisible(True)
        self.progress_logo.setStyleSheet("""
            QProgressBar {
                border: 1px solid #99b898;
                border-radius: 6px;
                text-align: center;
                font-family: 'Jura';
                font-size: 10px;
            }
            QProgressBar::chunk {
                background-color: #99b898;
                border-radius: 6px;
            }
        """)
        logo_layout.addWidget(self.progress_logo)
        
        grupo_logo.setLayout(logo_layout)
        col_der_layout.addWidget(grupo_logo)
        
        col_der_layout.addStretch()
        
        # Botones de acción
        acciones_layout = QVBoxLayout()
        acciones_layout.setSpacing(12)
        
        self.btn_guardar = QPushButton("💾 Guardar Proyecto")
        self.btn_guardar.clicked.connect(self.guardar_proyecto)
        self.btn_guardar.setFont(QFont("Jura", 12, QFont.Weight.Bold))
        self.btn_guardar.setStyleSheet("""
            QPushButton {
                background-color: #2a363b;
                color: white;
                border: none;
                padding: 15px;
                border-radius: 10px;
            }
            QPushButton:hover:enabled {
                background-color: #1a262b;
                transform: translateY(-2px);
            }
            QPushButton:disabled {
                background-color: #a0aec0;
                color: #e2e8f0;
            }
        """)
        
        self.btn_cancelar = QPushButton("❌ Cancelar")
        self.btn_cancelar.clicked.connect(self.cancelar)
        self.btn_cancelar.setFont(QFont("Jura", 11))
        self.btn_cancelar.setStyleSheet("""
            QPushButton {
                background-color: #e0e6ed;
                color: #4a5568;
                border: none;
                padding: 12px;
                border-radius: 10px;
            }
            QPushButton:hover {
                background-color: #cbd5e0;
            }
        """)
        
        acciones_layout.addWidget(self.btn_guardar)
        acciones_layout.addWidget(self.btn_cancelar)
        col_der_layout.addLayout(acciones_layout)
        
        col_der.setLayout(col_der_layout)
        form_layout.addWidget(col_der, 1)  # 1/3 del espacio
        
        form_container.setLayout(form_layout)
        container_layout.addWidget(form_container)
        
        container.setLayout(container_layout)
        scroll_area.setWidget(container)
        main_layout.addWidget(scroll_area)
        
        self.setLayout(main_layout)
    
    def cargar_padrones(self):
        """Carga los padrones - dropdown muestra nombre pero guarda UUID"""
        db = SessionLocal()
        try:
            padron_service = PadronService(db)
            padrones = padron_service.obtener_padrones_activos()
            
            self.combo_padron.clear()
            self.combo_padron.addItem("-- Seleccione un padrón --", None)
            
            for padron in padrones:
                # Mostrar nombre al usuario
                display_text = padron['nombre']
                if padron['descripcion']:
                    desc_corta = padron['descripcion'][:40] + '...' if len(padron['descripcion']) > 40 else padron['descripcion']
                    display_text += f" - {desc_corta}"
                
                # Guardar UUID como dato (para tabla_padron)
                self.combo_padron.addItem(display_text, padron['uuid_padron'])
            
            # Si estamos editando, seleccionar el padrón actual por UUID
            if self.proyecto and self.proyecto.tabla_padron:
                for i in range(self.combo_padron.count()):
                    if self.combo_padron.itemData(i) == self.proyecto.tabla_padron:
                        self.combo_padron.setCurrentIndex(i)
                        break
                        
        except Exception as e:
            print(f"Error cargando padrones: {e}")
            QMessageBox.warning(self, "Error", f"No se pudieron cargar los padrones: {e}")
        finally:
            db.close()
    
    def seleccionar_logo(self):
        """Abre diálogo para seleccionar logo"""
        archivo, _ = QFileDialog.getOpenFileName(
            self,
            "Seleccionar Logo del Proyecto",
            "",
            "Imágenes (*.png *.jpg *.jpeg *.bmp *.gif);;Todos los archivos (*)"
        )
        
        if archivo:
            self.procesar_logo(archivo)
    
    def procesar_logo(self, logo_path):
        """Procesa el logo seleccionado"""
        # Mostrar progreso
        self.progress_logo.setVisible(True)
        self.progress_logo.setValue(10)
        self.btn_seleccionar_logo.setEnabled(False)
        
        # Crear y ejecutar hilo de upload
        self.thread_upload = LogoUploadThread(logo_path, self.proyecto_id)
        self.thread_upload.upload_complete.connect(self.on_logo_upload_complete)
        self.thread_upload.upload_error.connect(self.on_logo_upload_error)
        self.thread_upload.progress.connect(self.progress_logo.setValue)
        self.thread_upload.start()
    
    def on_logo_upload_complete(self, temp_path, final_path):
        """Cuando se completa el upload del logo"""
        self.logo_temp_path = temp_path
        self.logo_final_path = final_path
        
        # Mostrar preview
        self.logo_preview.cargar_logo(temp_path)
        self.btn_eliminar_logo.setEnabled(True)
        
        # Ocultar progreso
        self.progress_logo.setVisible(False)
        self.btn_seleccionar_logo.setEnabled(True)
        
        # Mostrar mensaje
        nombre_archivo = os.path.basename(final_path)
        self.lbl_info_logo.setText(f"✓ Logo cargado: {nombre_archivo}")
        self.lbl_info_logo.setStyleSheet("color: #99b898; font-weight: bold;")
    
    def on_logo_upload_error(self, error_msg):
        """Cuando hay error en el upload del logo"""
        self.progress_logo.setVisible(False)
        self.btn_seleccionar_logo.setEnabled(True)
        
        QMessageBox.warning(self, "Error al cargar logo", error_msg)
    
    def eliminar_logo(self):
        """Elimina el logo seleccionado"""
        reply = QMessageBox.question(
            self, "Eliminar Logo",
            "¿Está seguro que desea eliminar el logo seleccionado?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.logo_temp_path = None
            self.logo_final_path = None
            self.logo_preview.cargar_logo(None)
            self.btn_eliminar_logo.setEnabled(False)
            self.lbl_info_logo.setText("Formatos: PNG, JPG, JPEG | Máx: 345x170px")
            self.lbl_info_logo.setStyleSheet("color: #7a8b90;")
    
    def cargar_datos_existentes(self):
        """Carga datos del proyecto si es edición"""
        if not self.proyecto_id:
            return
        
        db = SessionLocal()
        try:
            self.proyecto = db.query(Proyecto).filter(Proyecto.id == self.proyecto_id).first()
            
            if self.proyecto:
                # Cargar datos básicos
                self.txt_nombre.setText(self.proyecto.nombre)
                self.txt_descripcion.setText(self.proyecto.descripcion or "")
                
                # Cargar logo si existe
                if self.proyecto.logo_path and os.path.exists(self.proyecto.logo_path):
                    self.logo_final_path = self.proyecto.logo_path
                    self.logo_preview.cargar_logo(self.proyecto.logo_path)
                    self.btn_eliminar_logo.setEnabled(True)
                    
                    nombre_archivo = os.path.basename(self.proyecto.logo_path)
                    self.lbl_info_logo.setText(f"✓ Logo actual: {nombre_archivo}")
                    self.lbl_info_logo.setStyleSheet("color: #99b898; font-weight: bold;")
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error cargando proyecto: {str(e)}")
        finally:
            db.close()
    
    def validar_formulario(self):
        """Valida todos los campos del formulario"""
        errores = []
        
        # Nombre
        nombre = self.txt_nombre.text().strip()
        if not nombre:
            errores.append("El nombre del proyecto es obligatorio")
        
        # Padrón
        padron_id = self.combo_padron.currentData()
        if not padron_id:
            errores.append("Debe seleccionar una tabla de padrón")
        
        # Logo
        if not self.logo_final_path:
            errores.append("Debe seleccionar un logo para el proyecto")
        
        # Mostrar errores si hay
        if errores:
            QMessageBox.warning(self, "Validación", "\n".join(errores))
            return False
        
        return True
    
    def obtener_uuid_padron(self, padron_id):
        """Obtiene el UUID del padrón seleccionado"""
        db = SessionLocal()
        try:
            padron_service = PadronService(db)
            padron = padron_service.obtener_padron_por_id(padron_id)
            return padron.uuid if hasattr(padron, 'uuid') else None
        finally:
            db.close()
    
    def guardar_proyecto(self):
        """Guarda el proyecto usando UUID del padrón"""
        if not self.validar_formulario():
            return
        
        self.btn_guardar.setEnabled(False)
        self.btn_guardar.setText("Guardando...")
        
        db = SessionLocal()
        try:
            # Obtener UUID del padrón seleccionado
            uuid_padron = self.combo_padron.currentData()
            
            if not uuid_padron:
                raise ValueError("Debe seleccionar un padrón")
            
            # Obtener nombre del padrón para mostrar/información
            padron_service = PadronService(db)
            padron = padron_service.obtener_padron_por_uuid(uuid_padron)
            
            if not padron:
                raise ValueError(f"No se encontró el padrón con UUID {uuid_padron}")
            
            datos = {
                'nombre': self.txt_nombre.text().strip(),
                'descripcion': self.txt_descripcion.toPlainText().strip(),
                'tabla_padron': uuid_padron,  # ← GUARDAMOS EL UUID
                'logo': self.logo_final_path
            }
            
            project_service = ProjectService(db)
            
            if self.proyecto_id:
                # Edición
                project_service.actualizar_proyecto(self.proyecto_id, datos, self.usuario)
                mensaje = f"✅ Proyecto actualizado\nPadrón: {padron.nombre}"
            else:
                # Creación
                project_service.crear_proyecto(
                    datos['nombre'],
                    datos['descripcion'], 
                    datos['tabla_padron'],  # ← Pasar UUID
                    self.usuario,
                    datos['logo']
                )
                mensaje = f"✅ Proyecto creado\nPadrón: {padron.nombre}"
            
            db.commit()
            
            # Limpiar temp files
            if self.logo_temp_path and os.path.exists(self.logo_temp_path):
                os.remove(self.logo_temp_path)
            
            QMessageBox.information(self, "Éxito", mensaje)
            self.proyecto_guardado.emit()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error guardando proyecto:\n{str(e)}")
            print(f"DEBUG - Error: {e}")
            import traceback
            traceback.print_exc()
            db.rollback()
        finally:
            db.close()
            self.btn_guardar.setEnabled(True)
            self.btn_guardar.setText("💾 Guardar Proyecto")
    
    def cancelar(self):
        """Cancela la operación"""
        # Limpiar temp files
        if self.logo_temp_path and os.path.exists(self.logo_temp_path):
            os.remove(self.logo_temp_path)
        
        self.proyecto_guardado.emit()