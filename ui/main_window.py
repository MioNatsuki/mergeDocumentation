from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLabel, QPushButton, QStackedWidget, QMessageBox)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QAction, QIcon
from core.models import Usuario
from utils.logger import auditoria

class MainWindow(QMainWindow):
    def __init__(self, usuario: Usuario):
        super().__init__()
        self.usuario = usuario
        self.setWindowTitle(f"Sistema de Correspondencia - {usuario.nombre}")
        self.setMinimumSize(1200, 800)
        self.setup_ui()
        self.setup_menu()
    
    def setup_ui(self):
        # Widget central y layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout()
        central_widget.setLayout(layout)
        
        # Header
        header = QLabel(f"Bienvenido, {self.usuario.nombre} - Rol: {self.usuario.rol.capitalize()}")
        header.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(header)
        
        # Stacked widget para módulos
        self.stacked_widget = QStackedWidget()
        layout.addWidget(self.stacked_widget)
        
        # Pantallas iniciales
        self.setup_dashboard()
    
    def setup_menu(self):
        menubar = self.menuBar()
        
        # Menú Proyectos
        menu_proyectos = menubar.addMenu("&Proyectos")
        action_seleccionar = QAction("Seleccionar Proyecto", self)
        action_seleccionar.triggered.connect(self.show_proyectos)
        menu_proyectos.addAction(action_seleccionar)
        
        # Menú Plantillas (según rol)
        if self.usuario.rol in ["superadmin", "admin"]:
            menu_plantillas = menubar.addMenu("&Plantillas")
            action_gestionar = QAction("Gestionar Plantillas", self)
            action_gestionar.triggered.connect(self.show_plantillas)
            menu_plantillas.addAction(action_gestionar)
        
        # Menú Configuración (solo superadmin)
        if self.usuario.rol == "superadmin":
            menu_config = menubar.addMenu("&Configuración")
            action_usuarios = QAction("Gestión de Usuarios", self)
            action_auditoria = QAction("Auditoría", self)
            action_estadisticas = QAction("Estadísticas", self)
            
            action_usuarios.triggered.connect(self.show_gestion_usuarios)
            action_auditoria.triggered.connect(self.show_auditoria)
            action_estadisticas.triggered.connect(self.show_estadisticas)
            
            menu_config.addAction(action_usuarios)
            menu_config.addAction(action_auditoria)
            menu_config.addAction(action_estadisticas)
        
        # Menú Perfil
        menu_perfil = menubar.addMenu("&Perfil")
        action_mi_perfil = QAction("Mi Perfil", self)
        action_logout = QAction("Cerrar Sesión", self)
        
        action_mi_perfil.triggered.connect(self.show_perfil)
        action_logout.triggered.connect(self.logout)
        
        menu_perfil.addAction(action_mi_perfil)
        menu_perfil.addAction(action_logout)
    
    def setup_dashboard(self):
        """Pantalla inicial de dashboard según rol"""
        dashboard_widget = QWidget()
        layout = QVBoxLayout()
        
        title = QLabel("Dashboard Principal")
        title.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # Contenido según rol
        if self.usuario.rol == "superadmin":
            content = QLabel("SuperAdmin: Acceso completo al sistema")
        elif self.usuario.rol == "admin":
            content = QLabel("Admin: Gestión de proyectos y plantillas asignadas")
        else:
            content = QLabel("Lector: Generación de documentos en proyectos asignados")
        
        content.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(content)
        
        dashboard_widget.setLayout(layout)
        self.stacked_widget.addWidget(dashboard_widget)
    
    def show_proyectos(self):
        # TODO: Implementar selección de proyectos
        QMessageBox.information(self, "Proyectos", "Módulo de proyectos en desarrollo")
    
    def show_plantillas(self):
        # TODO: Implementar gestión de plantillas
        QMessageBox.information(self, "Plantillas", "Módulo de plantillas en desarrollo")
    
    def show_gestion_usuarios(self):
        # TODO: Implementar gestión de usuarios
        QMessageBox.information(self, "Usuarios", "Módulo de usuarios en desarrollo")
    
    def show_auditoria(self):
        # TODO: Implementar auditoría
        QMessageBox.information(self, "Auditoría", "Módulo de auditoría en desarrollo")
    
    def show_estadisticas(self):
        # TODO: Implementar estadísticas
        QMessageBox.information(self, "Estadísticas", "Módulo de estadísticas en desarrollo")
    
    def show_perfil(self):
        # TODO: Implementar perfil de usuario
        QMessageBox.information(self, "Perfil", f"Perfil de {self.usuario.nombre}\nRol: {self.usuario.rol}")
    
    def logout(self):
        reply = QMessageBox.question(
            self, "Cerrar Sesión",
            "¿Está seguro que desea cerrar sesión?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # Registrar logout en bitácora
            from config.database import SessionLocal
            db = SessionLocal()
            try:
                auditoria(
                    db=db,
                    usuario_id=self.usuario.id,
                    accion="logout",
                    modulo="auth"
                )
            finally:
                db.close()
            
            self.close()