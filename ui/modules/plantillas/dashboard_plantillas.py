from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QScrollArea, QGridLayout, 
                             QMessageBox, QFrame)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
from config.database import SessionLocal
from core.models import Proyecto, Plantilla
from core.project_service import ProjectService

from ui.modules.plantillas.formulario_plantilla import FormularioPlantilla

class DashboardPlantillas(QWidget):
    """Dashboard de plantillas para un proyecto específico"""
    volver_a_proyectos = pyqtSignal()
    
    def __init__(self, usuario, proyecto_id, stacked_widget=None):
        super().__init__()
        self.usuario = usuario
        self.proyecto_id = proyecto_id
        self.proyecto = None
        self.plantillas = []
        self.stacked_widget = stacked_widget
        self.setup_ui()
        self.cargar_datos_proyecto()
        self.cargar_plantillas()
    
    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(20)
        
        # Header con navegación
        header_layout = QHBoxLayout()
        
        btn_volver = QPushButton("← Volver a Proyectos")
        btn_volver.clicked.connect(self.volver_a_proyectos.emit)
        btn_volver.setStyleSheet("""
            QPushButton {
                background-color: #6c757d;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #5a6268;
            }
        """)
        header_layout.addWidget(btn_volver)
        
        header_layout.addStretch()
        
        # Botón nueva plantilla (solo admin/superadmin)
        if self.usuario.rol in ["superadmin", "admin"]:
            btn_nueva = QPushButton("+ Nueva Plantilla")
            btn_nueva.clicked.connect(self.crear_nueva_plantilla)
            btn_nueva.setStyleSheet("""
                QPushButton {
                    background-color: #4CAF50;
                    color: white;
                    border: none;
                    padding: 8px 16px;
                    border-radius: 4px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #45a049;
                }
            """)
            header_layout.addWidget(btn_nueva)
        
        layout.addLayout(header_layout)
        
        # Información del proyecto
        self.lbl_titulo = QLabel("Cargando proyecto...")
        self.lbl_titulo.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        self.lbl_titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.lbl_titulo)
        
        self.lbl_descripcion = QLabel()
        self.lbl_descripcion.setStyleSheet("color: #666; font-size: 12px;")
        self.lbl_descripcion.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_descripcion.setWordWrap(True)
        layout.addWidget(self.lbl_descripcion)
        
        # Separador
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(separator)
        
        # Subtítulo
        subtitle = QLabel("Plantillas Disponibles")
        subtitle.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        layout.addWidget(subtitle)
        
        # Área de plantillas
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        
        self.plantillas_container = QWidget()
        self.grid_layout = QGridLayout()
        self.grid_layout.setSpacing(15)
        self.grid_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        self.plantillas_container.setLayout(self.grid_layout)
        scroll_area.setWidget(self.plantillas_container)
        
        layout.addWidget(scroll_area)
        
        # Mensaje cuando no hay plantillas
        self.lbl_sin_plantillas = QLabel("No hay plantillas disponibles para este proyecto")
        self.lbl_sin_plantillas.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_sin_plantillas.setFont(QFont("Arial", 12))
        self.lbl_sin_plantillas.setStyleSheet("color: #666; padding: 40px;")
        layout.addWidget(self.lbl_sin_plantillas)
        self.lbl_sin_plantillas.hide()
        
        # Mensaje de error
        self.lbl_error = QLabel()
        self.lbl_error.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_error.setStyleSheet("color: #dc3545; padding: 20px;")
        self.lbl_error.setWordWrap(True)
        layout.addWidget(self.lbl_error)
        self.lbl_error.hide()
        
        self.setLayout(layout)
    
    def cargar_datos_proyecto(self):
        """Carga la información del proyecto con manejo robusto de errores"""
        db = SessionLocal()
        try:
            # Consulta DIRECTA y SIMPLE
            self.proyecto = db.query(Proyecto).filter(Proyecto.id == self.proyecto_id).first()
            
            if self.proyecto:
                self.lbl_titulo.setText(f"Proyecto: {self.proyecto.nombre}")
                self.lbl_descripcion.setText(self.proyecto.descripcion or "Sin descripción")
                self.lbl_error.hide()
            else:
                self.lbl_titulo.setText("Proyecto no encontrado")
                self.lbl_error.setText(f"El proyecto con ID {self.proyecto_id} no existe en la base de datos")
                self.lbl_error.show()
                
        except Exception as e:
            error_msg = f"Error cargando proyecto: {str(e)}"
            print(f"DEBUG - {error_msg}")  # Para debugging
            self.lbl_titulo.setText("Error al cargar proyecto")
            self.lbl_error.setText(error_msg)
            self.lbl_error.show()
        finally:
            db.close()
    
    def cargar_plantillas(self):
        """Carga las plantillas del proyecto"""
        # Primero verificar que el proyecto se cargó correctamente
        if not self.proyecto:
            return
            
        db = SessionLocal()
        try:
            # Método DIRECTO sin usar ProjectService para evitar problemas
            self.plantillas = db.query(Plantilla).filter(
                Plantilla.proyecto_id == self.proyecto_id,
                Plantilla.activa == True
            ).all()
            
            self.mostrar_plantillas()
            
        except Exception as e:
            error_msg = f"Error cargando plantillas: {str(e)}"
            print(f"DEBUG - {error_msg}")  # Para debugging
            self.lbl_error.setText(f"{self.lbl_error.text()}\n{error_msg}" if self.lbl_error.text() else error_msg)
            self.lbl_error.show()
        finally:
            db.close()
    
    def mostrar_plantillas(self):
        """Muestra las plantillas en la grid"""
        # Limpiar layout
        for i in reversed(range(self.grid_layout.count())): 
            widget = self.grid_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)
        
        if not self.plantillas:
            self.lbl_sin_plantillas.show()
            return
        
        self.lbl_sin_plantillas.hide()
        
        # Crear tarjetas de plantillas
        for i, plantilla in enumerate(self.plantillas):
            card = self.crear_tarjeta_plantilla(plantilla)
            row = i // 3
            col = i % 3
            self.grid_layout.addWidget(card, row, col)
    
    def crear_tarjeta_plantilla(self, plantilla):
        """Crea una tarjeta para una plantilla"""
        card = QFrame()
        card.setFrameStyle(QFrame.Shape.StyledPanel)
        card.setFixedSize(250, 150)
        card.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 1px solid #ddd;
                border-radius: 8px;
                padding: 12px;
            }
            QFrame:hover {
                border-color: #2196F3;
                background-color: #f8fdff;
            }
        """)
        
        layout = QVBoxLayout()
        
        # Nombre
        name_label = QLabel(plantilla.nombre)
        name_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        name_label.setWordWrap(True)
        layout.addWidget(name_label)
        
        # Descripción
        desc_label = QLabel(plantilla.descripcion or "Sin descripción")
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("color: #666; font-size: 11px;")
        layout.addWidget(desc_label)
        
        layout.addStretch()
        
        # Estado
        status_label = QLabel("ACTIVA" if plantilla.activa else "INACTIVA")
        status_label.setStyleSheet(
            "background-color: #4CAF50; color: white; padding: 2px 6px; border-radius: 3px; font-size: 10px;" 
            if plantilla.activa else
            "background-color: #f44336; color: white; padding: 2px 6px; border-radius: 3px; font-size: 10px;"
        )
        layout.addWidget(status_label)
        
        # Botones de acción
        button_layout = QHBoxLayout()
        
        btn_usar = QPushButton("Usar Plantilla")
        btn_usar.clicked.connect(lambda: self.usar_plantilla(plantilla.id))
        btn_usar.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                padding: 5px 10px;
                border-radius: 3px;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)
        button_layout.addWidget(btn_usar)
        
        # Solo admin/superadmin pueden editar
        if self.usuario.rol in ["superadmin", "admin"]:
            btn_editar = QPushButton("Editar")
            btn_editar.clicked.connect(lambda: self.editar_plantilla(plantilla.id))
            btn_editar.setStyleSheet("""
                QPushButton {
                    background-color: #FF9800;
                    color: white;
                    border: none;
                    padding: 5px 10px;
                    border-radius: 3px;
                    font-size: 11px;
                }
                QPushButton:hover {
                    background-color: #F57C00;
                }
            """)
            button_layout.addWidget(btn_editar)
        
        layout.addLayout(button_layout)
        card.setLayout(layout)
        
        return card
    
    def usar_plantilla(self, plantilla_id):
        """Usa la plantilla seleccionada"""
        QMessageBox.information(self, "Usar Plantilla", 
                              f"Plantilla {plantilla_id} seleccionada. Preparando emisor de documentos...")
        
    def crear_nueva_plantilla(self):
        """Crea una nueva plantilla"""
        print(f"DEBUG: crear_nueva_plantilla() llamado")
        print(f"DEBUG: stacked_widget = {self.stacked_widget}")
        print(f"DEBUG: usuario.rol = {self.usuario.rol}")
        
        if self.stacked_widget:
            print("DEBUG: Creando FormularioPlantilla...")
            formulario = FormularioPlantilla(self.usuario, self.proyecto_id)
            formulario.plantilla_guardada.connect(self.on_plantilla_guardada)
            
            self.stacked_widget.addWidget(formulario)
            self.stacked_widget.setCurrentWidget(formulario)
            print("DEBUG: Formulario mostrado correctamente")
        else:
            print("DEBUG: stacked_widget es None, mostrando fallback")
            QMessageBox.information(self, "Nueva Plantilla", 
                                "Formulario de nueva plantilla listo para implementar")

    def editar_plantilla(self, plantilla_id):
        """Edita la plantilla seleccionada"""
        if self.stacked_widget:
            formulario = FormularioPlantilla(self.usuario, self.proyecto_id, plantilla_id)
            formulario.plantilla_guardada.connect(self.on_plantilla_guardada)
            
            self.stacked_widget.addWidget(formulario)
            self.stacked_widget.setCurrentWidget(formulario)
        else:
            QMessageBox.information(self, "Editar Plantilla", 
                                f"Editando plantilla {plantilla_id}")

    def on_plantilla_guardada(self):
        """Cuando se guarda una plantilla"""
        self.cargar_plantillas()
        if self.stacked_widget:
            self.stacked_widget.setCurrentWidget(self)