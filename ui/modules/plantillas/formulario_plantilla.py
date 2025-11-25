from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QTextEdit, QPushButton, QMessageBox,
                             QFrame, QComboBox, QCheckBox, QFileDialog)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
from config.database import SessionLocal
from core.models import Plantilla, Proyecto
import os

class FormularioPlantilla(QWidget):
    """Formulario para crear/editar plantillas"""
    plantilla_guardada = pyqtSignal()
    
    def __init__(self, usuario, proyecto_id, plantilla_id=None):
        super().__init__()
        self.usuario = usuario
        self.proyecto_id = proyecto_id
        self.plantilla_id = plantilla_id
        self.plantilla = None
        self.setup_ui()
        self.cargar_datos_existentes()
    
    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(20)
        
        # Header
        titulo = QLabel("Nueva Plantilla" if not self.plantilla_id else "Editar Plantilla")
        titulo.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(titulo)
        
        # Form container
        form_frame = QFrame()
        form_frame.setFrameStyle(QFrame.Shape.StyledPanel)
        form_layout = QVBoxLayout()
        form_layout.setSpacing(15)
        
        # Campo: Nombre
        lbl_nombre = QLabel("Nombre de Plantilla *")
        self.txt_nombre = QLineEdit()
        self.txt_nombre.setPlaceholderText("Ingrese nombre de la plantilla")
        self.txt_nombre.setMaxLength(100)
        
        # Campo: Descripción
        lbl_descripcion = QLabel("Descripción")
        self.txt_descripcion = QTextEdit()
        self.txt_descripcion.setPlaceholderText("Descripción de la plantilla...")
        self.txt_descripcion.setMaximumHeight(60)
        
        # Campo: Tipo de plantilla
        lbl_tipo = QLabel("Tipo de Plantilla")
        self.combo_tipo = QComboBox()
        self.combo_tipo.addItems(["carta", "comunicado", "notificacion", "oficio"])
        
        # Campo: Archivo PDF
        lbl_archivo = QLabel("Archivo PDF Base *")
        file_layout = QHBoxLayout()
        
        self.txt_archivo = QLineEdit()
        self.txt_archivo.setPlaceholderText("Ruta del archivo PDF...")
        self.txt_archivo.setReadOnly(True)
        
        btn_explorar = QPushButton("Examinar...")
        btn_explorar.clicked.connect(self.explorar_archivo)
        btn_explorar.setStyleSheet("""
            QPushButton {
                background-color: #17a2b8;
                color: white;
                border: none;
                padding: 8px 15px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #138496;
            }
        """)
        
        file_layout.addWidget(self.txt_archivo)
        file_layout.addWidget(btn_explorar)
        
        # Campo: Estado
        self.check_activa = QCheckBox("Plantilla activa")
        self.check_activa.setChecked(True)
        
        # Información del proyecto
        info_frame = QFrame()
        info_frame.setStyleSheet("background-color: #f8f9fa; padding: 10px; border-radius: 5px;")
        info_layout = QVBoxLayout()
        
        lbl_info = QLabel("Información del Proyecto")
        lbl_info.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        info_layout.addWidget(lbl_info)
        
        self.lbl_proyecto_info = QLabel()
        self.lbl_proyecto_info.setStyleSheet("color: #666; font-size: 11px;")
        info_layout.addWidget(self.lbl_proyecto_info)
        
        info_frame.setLayout(info_layout)
        
        # Botones
        button_layout = QHBoxLayout()
        
        self.btn_guardar = QPushButton("💾 Guardar Plantilla")
        self.btn_guardar.clicked.connect(self.guardar_plantilla)
        self.btn_guardar.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #218838;
            }
            QPushButton:disabled {
                background-color: #6c757d;
            }
        """)
        
        self.btn_editor = QPushButton("🎨 Abrir Editor Visual")
        self.btn_editor.clicked.connect(self.abrir_editor_visual)
        self.btn_editor.setStyleSheet("""
            QPushButton {
                background-color: #17a2b8;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #138496;
            }
            QPushButton:disabled {
                background-color: #6c757d;
            }
        """)
        self.btn_editor.setEnabled(False)
        
        self.btn_cancelar = QPushButton("❌ Cancelar")
        self.btn_cancelar.clicked.connect(self.cancelar)
        self.btn_cancelar.setStyleSheet("""
            QPushButton {
                background-color: #6c757d;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #5a6268;
            }
        """)
        
        button_layout.addWidget(self.btn_guardar)
        button_layout.addWidget(self.btn_editor)
        button_layout.addStretch()
        button_layout.addWidget(self.btn_cancelar)
        
        # Agregar al form
        form_layout.addWidget(lbl_nombre)
        form_layout.addWidget(self.txt_nombre)
        form_layout.addWidget(lbl_descripcion)
        form_layout.addWidget(self.txt_descripcion)
        form_layout.addWidget(lbl_tipo)
        form_layout.addWidget(self.combo_tipo)
        form_layout.addWidget(lbl_archivo)
        form_layout.addLayout(file_layout)
        form_layout.addWidget(self.check_activa)
        form_layout.addWidget(info_frame)
        form_layout.addLayout(button_layout)
        
        form_frame.setLayout(form_layout)
        layout.addWidget(form_frame)
        
        self.setLayout(layout)
        
        # Cargar información del proyecto
        self.cargar_info_proyecto()
    
    def cargar_info_proyecto(self):
        """Carga la información del proyecto actual"""
        db = SessionLocal()
        try:
            proyecto = db.query(Proyecto).filter(Proyecto.id == self.proyecto_id).first()
            if proyecto:
                self.lbl_proyecto_info.setText(
                    f"Proyecto: {proyecto.nombre}\n"
                    f"Tabla de padrón: {proyecto.tabla_padron or 'No definida'}"
                )
        except Exception as e:
            print(f"Error cargando info proyecto: {e}")
        finally:
            db.close()
    
    def explorar_archivo(self):
        """Abre diálogo para seleccionar archivo PDF"""
        archivo, _ = QFileDialog.getOpenFileName(
            self, 
            "Seleccionar archivo PDF", 
            "", 
            "Archivos PDF (*.pdf);;Todos los archivos (*)"
        )
        
        if archivo:
            self.txt_archivo.setText(archivo)
            self.btn_editor.setEnabled(True)
    
    def cargar_datos_existentes(self):
        """Carga datos existentes si es edición"""
        if not self.plantilla_id:
            return
        
        db = SessionLocal()
        try:
            self.plantilla = db.query(Plantilla).filter(Plantilla.id == self.plantilla_id).first()
            
            if self.plantilla:
                self.txt_nombre.setText(self.plantilla.nombre)
                self.txt_descripcion.setText(self.plantilla.descripcion or "")
                
                if self.plantilla.tipo_plantilla:
                    index = self.combo_tipo.findText(self.plantilla.tipo_plantilla)
                    if index >= 0:
                        self.combo_tipo.setCurrentIndex(index)
                
                if self.plantilla.ruta_archivo:
                    self.txt_archivo.setText(self.plantilla.ruta_archivo)
                    self.btn_editor.setEnabled(True)
                
                self.check_activa.setChecked(self.plantilla.activa)
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error cargando plantilla: {str(e)}")
        finally:
            db.close()
    
    def validar_formulario(self):
        """Valida los datos del formulario"""
        nombre = self.txt_nombre.text().strip()
        archivo = self.txt_archivo.text().strip()
        
        if not nombre:
            QMessageBox.warning(self, "Validación", "El nombre de la plantilla es obligatorio")
            self.txt_nombre.setFocus()
            return False
        
        if not archivo:
            QMessageBox.warning(self, "Validación", "Debe seleccionar un archivo PDF base")
            return False
        
        if not archivo.lower().endswith('.pdf'):
            QMessageBox.warning(self, "Validación", "El archivo debe ser un PDF (.pdf)")
            return False
        
        if not os.path.exists(archivo):
            QMessageBox.warning(self, "Validación", "El archivo seleccionado no existe")
            return False
        
        return True
    
    def guardar_plantilla(self):
        """Guarda la plantilla en la base de datos"""
        if not self.validar_formulario():
            return
        
        self.btn_guardar.setEnabled(False)
        self.btn_guardar.setText("Guardando...")
        
        db = SessionLocal()
        try:
            datos = {
                'nombre': self.txt_nombre.text().strip(),
                'descripcion': self.txt_descripcion.toPlainText().strip(),
                'tipo_plantilla': self.combo_tipo.currentText(),
                'ruta_archivo': self.txt_archivo.text().strip(),
                'activa': self.check_activa.isChecked(),
                'campos_json': {}  # Por defecto vacío, se llenará en el editor visual
            }
            
            if self.plantilla_id:
                # Actualizar existente
                plantilla = db.query(Plantilla).filter(Plantilla.id == self.plantilla_id).first()
                if plantilla:
                    for key, value in datos.items():
                        if hasattr(plantilla, key):
                            setattr(plantilla, key, value)
                    mensaje = "✅ Plantilla actualizada correctamente"
                else:
                    QMessageBox.warning(self, "Error", "Plantilla no encontrada")
                    return
            else:
                # Crear nueva
                plantilla = Plantilla(
                    proyecto_id=self.proyecto_id,
                    usuario_creador=self.usuario.id,
                    **datos
                )
                db.add(plantilla)
                mensaje = "✅ Plantilla creada correctamente"
            
            db.commit()
            QMessageBox.information(self, "Éxito", mensaje)
            self.plantilla_guardada.emit()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error guardando plantilla: {str(e)}")
            db.rollback()
        finally:
            db.close()
            self.btn_guardar.setEnabled(True)
            self.btn_guardar.setText("💾 Guardar Plantilla")
    
    def abrir_editor_visual(self):
        """Abre el editor visual de plantillas"""
        archivo_pdf = self.txt_archivo.text().strip()
        if not archivo_pdf or not os.path.exists(archivo_pdf):
            QMessageBox.warning(self, "Error", "Primero debe seleccionar un archivo PDF válido")
            return
        
        QMessageBox.information(
            self, 
            "Editor Visual de Plantillas", 
            f"🎨 Editor visual en desarrollo...\n\n"
            f"📄 Archivo: {os.path.basename(archivo_pdf)}\n"
            f"📍 Funcionalidades próximas:\n"
            f"   • Posicionamiento por coordenadas\n"
            f"   • Campos dinámicos arrastrables\n"
            f"   • Previsualización en tiempo real\n"
            f"   • Validación de campos vs CSV\n\n"
            f"Esta funcionalidad se implementará en la Semana 5-6."
        )
    
    def cancelar(self):
        """Cancela la operación"""
        reply = QMessageBox.question(
            self,
            "Confirmar cancelación",
            "¿Está seguro de que desea cancelar? Los cambios no guardados se perderán.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.plantilla_guardada.emit()