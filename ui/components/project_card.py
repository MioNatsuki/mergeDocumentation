from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QFrame)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QPalette, QColor

class ProjectCard(QFrame):
    """Componente de tarjeta para mostrar proyectos"""
    project_selected = pyqtSignal(int)  # Emite ID del proyecto
    project_edit = pyqtSignal(int)     # Emite ID para editar
    project_delete = pyqtSignal(int)   # Emite ID para eliminar
    
    def __init__(self, proyecto, usuario_rol, parent=None):
        super().__init__(parent)
        self.proyecto = proyecto
        self.usuario_rol = usuario_rol
        self.setup_ui()
    
    def setup_ui(self):
        self.setFrameStyle(QFrame.Shape.StyledPanel)
        self.setLineWidth(1)
        self.setFixedSize(280, 180)
        
        layout = QVBoxLayout()
        layout.setSpacing(10)
        
        # Header con nombre
        header_layout = QHBoxLayout()
        
        name_label = QLabel(self.proyecto.nombre)
        name_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        name_label.setWordWrap(True)
        header_layout.addWidget(name_label)
        
        # Badge de estado
        status_label = QLabel("ACTIVO" if self.proyecto.activo else "INACTIVO")
        status_label.setStyleSheet(
            "background-color: #4CAF50; color: white; padding: 2px 6px; border-radius: 3px; font-size: 10px;" 
            if self.proyecto.activo else
            "background-color: #f44336; color: white; padding: 2px 6px; border-radius: 3px; font-size: 10px;"
        )
        header_layout.addWidget(status_label)
        
        layout.addLayout(header_layout)
        
        # Descripción
        desc_label = QLabel(self.proyecto.descripcion or "Sin descripción")
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("color: #666; font-size: 11px;")
        layout.addWidget(desc_label)
        
        # Info adicional
        info_layout = QVBoxLayout()
        
        padron_label = QLabel(f"Padrón: {self.proyecto.tabla_padron or 'No definido'}")
        padron_label.setStyleSheet("color: #888; font-size: 10px;")
        info_layout.addWidget(padron_label)
        
        fecha_label = QLabel(f"Creado: {self.proyecto.fecha_creacion.strftime('%d/%m/%Y')}")
        fecha_label.setStyleSheet("color: #888; font-size: 10px;")
        info_layout.addWidget(fecha_label)
        
        layout.addLayout(info_layout)
        layout.addStretch()
        
        # Botones de acción
        button_layout = QHBoxLayout()
        
        btn_seleccionar = QPushButton("Seleccionar")
        btn_seleccionar.clicked.connect(lambda: self.project_selected.emit(self.proyecto.id))
        btn_seleccionar.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                padding: 5px 10px;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)
        button_layout.addWidget(btn_seleccionar)
        
        # Solo superadmin/admin pueden editar/eliminar
        if self.usuario_rol in ["superadmin", "admin"]:
            btn_editar = QPushButton("Editar")
            btn_editar.clicked.connect(lambda: self.project_edit.emit(self.proyecto.id))
            btn_editar.setStyleSheet("""
                QPushButton {
                    background-color: #FF9800;
                    color: white;
                    border: none;
                    padding: 5px 10px;
                    border-radius: 3px;
                }
                QPushButton:hover {
                    background-color: #F57C00;
                }
            """)
            button_layout.addWidget(btn_editar)
            
            if self.usuario_rol == "superadmin":
                btn_eliminar = QPushButton("Eliminar")
                btn_eliminar.clicked.connect(lambda: self.project_delete.emit(self.proyecto.id))
                btn_eliminar.setStyleSheet("""
                    QPushButton {
                        background-color: #f44336;
                        color: white;
                        border: none;
                        padding: 5px 10px;
                        border-radius: 3px;
                    }
                    QPushButton:hover {
                        background-color: #D32F2F;
                    }
                """)
                button_layout.addWidget(btn_eliminar)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
        
        # Efecto hover
        self.setStyleSheet("""
            ProjectCard {
                background-color: white;
                border: 1px solid #ddd;
                border-radius: 8px;
                padding: 12px;
            }
            ProjectCard:hover {
                border-color: #2196F3;
                background-color: #f8fdff;
            }
        """)