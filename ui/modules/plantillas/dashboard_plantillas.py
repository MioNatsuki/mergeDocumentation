from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QScrollArea, QGridLayout, 
                             QMessageBox, QFrame)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
from config.database import SessionLocal
from core.project_service import ProjectService

class DashboardPlantillas(QWidget):
    """Dashboard de plantillas para un proyecto específico"""
    volver_a_proyectos = pyqtSignal()
    
    def __init__(self, usuario, proyecto_id):
        super().__init__()
        self.usuario = usuario
        self.proyecto_id = proyecto_id
        self.proyecto = None
        self.plantillas = []
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
        self.lbl_titulo = QLabel()
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
        
        self.setLayout(layout)
    
    def cargar_datos_proyecto(self):
        """Carga la información del proyecto"""
        db = SessionLocal()
        try:
            self.proyecto = db.query(ProjectService.Proyecto).filter(
                ProjectService.Proyecto.id == self.proyecto_id
            ).first()
            
            if self.proyecto:
                self.lbl_titulo.setText(f"Proyecto: {self.proyecto.nombre}")
                self.lbl_descripcion.setText(self.proyecto.descripcion or "Sin descripción")
            else:
                self.lbl_titulo.setText("Proyecto no encontrado")
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error cargando proyecto: {str(e)}")
        finally:
            db.close()
    
    def cargar_plantillas(self):
        """Carga las plantillas del proyecto"""
        db = SessionLocal()
        try:
            project_service = ProjectService(db)
            self.plantillas = project_service.obtener_plantillas_proyecto(self.proyecto_id, self.usuario)
            self.mostrar_plantillas()
            
        except PermissionError as e:
            QMessageBox.warning(self, "Permisos Insuficientes", str(e))
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error cargando plantillas: {str(e)}")
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
        # TODO: Implementar navegación al emisor de documentos
    
    def editar_plantilla(self, plantilla_id):
        """Edita la plantilla seleccionada"""
        QMessageBox.information(self, "Editar Plantilla", 
                              f"Editando plantilla {plantilla_id}. Abriendo editor...")
        # TODO: Implementar editor de plantillas
    
    def crear_nueva_plantilla(self):
        """Crea una nueva plantilla"""
        QMessageBox.information(self, "Nueva Plantilla", 
                              "Formulario de nueva plantilla en desarrollo")
        # TODO: Implementar creación de plantillas