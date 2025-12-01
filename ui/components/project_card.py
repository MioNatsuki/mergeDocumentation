# ui/components/project_card.py - VERSIÓN REDISEÑADA
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QFrame)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QPixmap, QPainter
from PyQt6.QtCore import QSize
import os

class ProjectCard(QFrame):
    def __init__(self, proyecto, usuario_rol, padron_nombre=None, parent=None):
        super().__init__(parent)
        self.proyecto = proyecto
        self.usuario_rol = usuario_rol
        self.padron_nombre = padron_nombre  # ← Nombre humano del padrón
        self.setup_ui()
    
    def setup_ui(self):
        # Configuración de la card
        self.setFixedSize(320, 280)  # Tamaño aumentado para logo
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        
        # Layout principal
        layout = QVBoxLayout()
        layout.setSpacing(8)
        layout.setContentsMargins(12, 12, 12, 12)
        
        # ÁREA DEL LOGO (NUEVO)
        self.logo_container = QFrame()
        self.logo_container.setFixedHeight(120)
        self.logo_container.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #99b898, stop:1 #88a786);
                border-radius: 8px;
                border: 2px solid #99b898;
            }
        """)
        
        logo_layout = QVBoxLayout()
        logo_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Logo del proyecto
        self.lbl_logo = QLabel()
        self.lbl_logo.setFixedSize(80, 80)
        self.lbl_logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_logo.setStyleSheet("""
            QLabel {
                background-color: rgba(255,255,255,0.9);
                border-radius: 40px;
                border: 2px solid #2a363b;
            }
        """)
        
        # Cargar logo si existe
        self.cargar_logo()
        
        # Icono por defecto si no hay logo
        if not self.proyecto.logo or not os.path.exists(self.proyecto.logo):
            self.lbl_logo.setText("📁")
            self.lbl_logo.setStyleSheet(self.lbl_logo.styleSheet() + """
                QLabel {
                    font-size: 32px;
                    color: #2a363b;
                }
            """)
        
        logo_layout.addWidget(self.lbl_logo)
        self.logo_container.setLayout(logo_layout)
        layout.addWidget(self.logo_container)
        
        # INFORMACIÓN DEL PROYECTO
        info_layout = QVBoxLayout()
        info_layout.setSpacing(6)
        if self.padron_nombre:
            padron_text = f"📊 {self.padron_nombre}"
        else:
            # Mostrar UUID truncado si no tenemos nombre
            uuid_truncado = self.proyecto.tabla_padron[:8] + "..." if self.proyecto.tabla_padron else "Sin padrón"
            padron_text = f"📊 {uuid_truncado}"
        
        padron_label = QLabel(padron_text)
        padron_label.setFont(QFont("Jura", 8))
        padron_label.setStyleSheet("color: #7a8b90;")
        
        # Nombre del proyecto
        name_label = QLabel(self.proyecto.nombre)
        name_label.setFont(QFont("Jura", 13, QFont.Weight.Bold))
        name_label.setStyleSheet("color: #2a363b;")
        name_label.setWordWrap(True)
        name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        info_layout.addWidget(name_label)
        
        # Descripción
        desc_text = self.proyecto.descripcion or "Sin descripción"
        desc_label = QLabel(desc_text)
        desc_label.setFont(QFont("Jura", 9))
        desc_label.setStyleSheet("color: #5a6b70;")
        desc_label.setWordWrap(True)
        desc_label.setMaximumHeight(40)
        info_layout.addWidget(desc_label)
        
        # Línea separadora
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setStyleSheet("background-color: #fecea8; margin: 5px 0px;")
        info_layout.addWidget(separator)
        
        # Info adicional
        meta_layout = QVBoxLayout()
        
        padron_label = QLabel(f"📊 {self.proyecto.tabla_padron or 'Sin padrón'}")
        padron_label.setFont(QFont("Jura", 8))
        padron_label.setStyleSheet("color: #7a8b90;")
        meta_layout.addWidget(padron_label)
        
        fecha_label = QLabel(f"📅 {self.proyecto.fecha_creacion.strftime('%d/%m/%Y')}")
        fecha_label.setFont(QFont("Jura", 8))
        fecha_label.setStyleSheet("color: #7a8b90;")
        meta_layout.addWidget(fecha_label)
        
        info_layout.addLayout(meta_layout)
        layout.addLayout(info_layout)
        
        # BOTONES DE ACCIÓN
        button_layout = QHBoxLayout()
        button_layout.setSpacing(8)
        
        # Botón Seleccionar
        btn_seleccionar = QPushButton("Abrir")
        btn_seleccionar.setFixedHeight(32)
        btn_seleccionar.clicked.connect(lambda: self.project_selected.emit(self.proyecto.id))
        btn_seleccionar.setStyleSheet("""
            QPushButton {
                background-color: #99b898;
                color: #2a363b;
                border: none;
                border-radius: 6px;
                font-family: 'Jura';
                font-weight: bold;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #88a786;
                transform: scale(1.05);
            }
            QPushButton:pressed {
                background-color: #7a9978;
            }
        """)
        button_layout.addWidget(btn_seleccionar)
        
        # Solo admin/superadmin pueden editar/eliminar
        if self.usuario_rol in ["superadmin", "admin"]:
            btn_editar = QPushButton("Editar")
            btn_editar.setFixedHeight(32)
            btn_editar.clicked.connect(lambda: self.project_edit.emit(self.proyecto.id))
            btn_editar.setStyleSheet("""
                QPushButton {
                    background-color: #fecea8;
                    color: #2a363b;
                    border: none;
                    border-radius: 6px;
                    font-family: 'Jura';
                    font-weight: bold;
                    font-size: 11px;
                }
                QPushButton:hover {
                    background-color: #eebd97;
                }
            """)
            button_layout.addWidget(btn_editar)
            
            if self.usuario_rol == "superadmin":
                btn_eliminar = QPushButton("Eliminar")
                btn_eliminar.setFixedHeight(32)
                btn_eliminar.clicked.connect(lambda: self.project_delete.emit(self.proyecto.id))
                btn_eliminar.setStyleSheet("""
                    QPushButton {
                        background-color: #ff847c;
                        color: white;
                        border: none;
                        border-radius: 6px;
                        font-family: 'Jura';
                        font-weight: bold;
                        font-size: 11px;
                    }
                    QPushButton:hover {
                        background-color: #e84a5f;
                    }
                """)
                button_layout.addWidget(btn_eliminar)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
        
        # ESTILOS DE LA CARD
        self.setStyleSheet("""
            ProjectCard {
                background-color: #ffffff;
                border: 2px solid #e0e0e0;
                border-radius: 12px;
            }
            ProjectCard:hover {
                border-color: #99b898;
                background-color: #f8fbf8;
                transform: translateY(-2px);
            }
        """)
    
    def cargar_logo(self):
        """Carga el logo del proyecto si existe"""
        if self.proyecto.logo and os.path.exists(self.proyecto.logo):
            try:
                pixmap = QPixmap(self.proyecto.logo)
                if not pixmap.isNull():
                    # Redimensionar manteniendo aspect ratio
                    pixmap = pixmap.scaled(70, 70, Qt.AspectRatioMode.KeepAspectRatio, 
                                         Qt.TransformationMode.SmoothTransformation)
                    self.lbl_logo.setPixmap(pixmap)
            except Exception as e:
                print(f"Error cargando logo: {e}")
                self.lbl_logo.setText("📁")