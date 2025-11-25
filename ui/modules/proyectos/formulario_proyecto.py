from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QTextEdit, QPushButton, QMessageBox,
                             QFrame, QComboBox)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
from config.database import SessionLocal
from core.project_service import ProjectService
from core.models import Proyecto  # ← IMPORTAR DIRECTAMENTE

class FormularioProyecto(QWidget):
    """Formulario para crear/editar proyectos"""
    proyecto_guardado = pyqtSignal()
    
    def __init__(self, usuario, proyecto_id=None):
        super().__init__()
        self.usuario = usuario
        self.proyecto_id = proyecto_id
        self.proyecto = None
        self.setup_ui()
        self.cargar_datos_existentes()
    
    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(20)
        
        # Header
        titulo = QLabel("Nuevo Proyecto" if not self.proyecto_id else "Editar Proyecto")
        titulo.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(titulo)
        
        # Form container
        form_frame = QFrame()
        form_frame.setFrameStyle(QFrame.Shape.StyledPanel)
        form_layout = QVBoxLayout()
        form_layout.setSpacing(15)
        
        # Campo: Nombre
        lbl_nombre = QLabel("Nombre del Proyecto *")
        self.txt_nombre = QLineEdit()
        self.txt_nombre.setPlaceholderText("Ingrese el nombre del proyecto")
        self.txt_nombre.setMaxLength(100)
        
        # Campo: Descripción
        lbl_descripcion = QLabel("Descripción")
        self.txt_descripcion = QTextEdit()
        self.txt_descripcion.setPlaceholderText("Descripción del proyecto...")
        self.txt_descripcion.setMaximumHeight(80)
        
        # Campo: Tabla Padrón
        lbl_padron = QLabel("Tabla de Padrón *")
        self.combo_padron = QComboBox()
        self.combo_padron.addItems([
            "padron_completo_pensiones",
            "padron_activos", 
            "padron_historicos"
        ])
        self.combo_padron.setEditable(True)
        self.combo_padron.setPlaceholderText("Seleccione o ingrese nombre de tabla")
        
        # Botones
        button_layout = QHBoxLayout()
        
        self.btn_guardar = QPushButton("Guardar Proyecto")
        self.btn_guardar.clicked.connect(self.guardar_proyecto)
        self.btn_guardar.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
        """)
        
        self.btn_cancelar = QPushButton("Cancelar")
        self.btn_cancelar.clicked.connect(self.cancelar)
        self.btn_cancelar.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #d32f2f;
            }
        """)
        
        button_layout.addWidget(self.btn_guardar)
        button_layout.addWidget(self.btn_cancelar)
        
        # Agregar al form
        form_layout.addWidget(lbl_nombre)
        form_layout.addWidget(self.txt_nombre)
        form_layout.addWidget(lbl_descripcion)
        form_layout.addWidget(self.txt_descripcion)
        form_layout.addWidget(lbl_padron)
        form_layout.addWidget(self.combo_padron)
        form_layout.addLayout(button_layout)
        
        form_frame.setLayout(form_layout)
        layout.addWidget(form_frame)
        
        self.setLayout(layout)
    
    def cargar_datos_existentes(self):
        """Carga datos existentes si es edición - VERSIÓN CORREGIDA"""
        if not self.proyecto_id:
            return  # No hay nada que cargar para nuevo proyecto
        
        db = SessionLocal()
        try:
            # CONSULTA DIRECTA Y SIMPLE - CORREGIDA
            self.proyecto = db.query(Proyecto).filter(Proyecto.id == self.proyecto_id).first()
            
            if self.proyecto:
                self.txt_nombre.setText(self.proyecto.nombre)
                self.txt_descripcion.setText(self.proyecto.descripcion or "")
                
                if self.proyecto.tabla_padron:
                    index = self.combo_padron.findText(self.proyecto.tabla_padron)
                    if index >= 0:
                        self.combo_padron.setCurrentIndex(index)
                    else:
                        self.combo_padron.setEditText(self.proyecto.tabla_padron)
            else:
                QMessageBox.warning(self, "Advertencia", f"No se encontró el proyecto con ID {self.proyecto_id}")
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error cargando proyecto: {str(e)}")
            print(f"DEBUG - Error en cargar_datos_existentes: {e}")  # Para debugging
        finally:
            db.close()
    
    def validar_formulario(self):
        """Valida los datos del formulario"""
        nombre = self.txt_nombre.text().strip()
        tabla_padron = self.combo_padron.currentText().strip()
        
        if not nombre:
            QMessageBox.warning(self, "Validación", "El nombre del proyecto es obligatorio")
            self.txt_nombre.setFocus()
            return False
        
        if not tabla_padron:
            QMessageBox.warning(self, "Validación", "La tabla de padrón es obligatoria")
            self.combo_padron.setFocus()
            return False
        
        return True
    
    def guardar_proyecto(self):
        """Guarda el proyecto en la base de datos"""
        if not self.validar_formulario():
            return
        
        self.btn_guardar.setEnabled(False)
        self.btn_guardar.setText("Guardando...")
        
        db = SessionLocal()
        try:
            project_service = ProjectService(db)
            
            datos = {
                'nombre': self.txt_nombre.text().strip(),
                'descripcion': self.txt_descripcion.toPlainText().strip(),
                'tabla_padron': self.combo_padron.currentText().strip()
            }
            
            if self.proyecto_id:
                # Edición
                project_service.actualizar_proyecto(self.proyecto_id, datos, self.usuario)
                mensaje = "Proyecto actualizado correctamente"
            else:
                # Creación
                project_service.crear_proyecto(
                    datos['nombre'],
                    datos['descripcion'], 
                    datos['tabla_padron'],
                    self.usuario
                )
                mensaje = "Proyecto creado correctamente"
            
            db.commit()
            QMessageBox.information(self, "Éxito", mensaje)
            self.proyecto_guardado.emit()
            
        except PermissionError as e:
            QMessageBox.warning(self, "Permisos Insuficientes", str(e))
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error guardando proyecto: {str(e)}")
            print(f"DEBUG - Error en guardar_proyecto: {e}")  # Para debugging
            db.rollback()
        finally:
            db.close()
            self.btn_guardar.setEnabled(True)
            self.btn_guardar.setText("Guardar Proyecto")
    
    def cancelar(self):
        """Cancela la operación"""
        self.proyecto_guardado.emit()