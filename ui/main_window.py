from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLabel, QPushButton, QStackedWidget, QMessageBox)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QAction
from core.models import Usuario
from utils.logger import auditoria

# Importar módulos nuevos
from ui.modules.proyectos.dashboard_proyectos import DashboardProyectos
from ui.modules.plantillas.dashboard_plantillas import DashboardPlantillas

class MainWindow(QMainWindow):
    def __init__(self, usuario: Usuario):
        super().__init__()
        self.usuario = usuario
        self.setWindowTitle(f"Sistema de Correspondencia - {usuario.nombre}")
        self.setMinimumSize(1200, 800)
        self.setup_ui()
        self.setup_menu()
    
    def setup_ui(self):
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
        
        # Inicializar dashboard de proyectos
        self.dashboard_proyectos = DashboardProyectos(self.usuario, self.stacked_widget)
        self.dashboard_proyectos.project_selected.connect(self.on_proyecto_seleccionado)
        self.stacked_widget.addWidget(self.dashboard_proyectos)
        
        # Mostrar dashboard de proyectos por defecto
        self.stacked_widget.setCurrentWidget(self.dashboard_proyectos)
    
    def setup_menu(self):
        menubar = self.menuBar()
        
        # Menú Proyectos
        menu_proyectos = menubar.addMenu("&Proyectos")
        action_seleccionar = QAction("Seleccionar Proyecto", self)
        action_seleccionar.triggered.connect(self.mostrar_dashboard_proyectos)
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
    
    def mostrar_dashboard_proyectos(self):
        """Muestra el dashboard de proyectos"""
        self.stacked_widget.setCurrentWidget(self.dashboard_proyectos)
        self.dashboard_proyectos.cargar_proyectos()
    
    def show_plantillas(self):
        QMessageBox.information(self, "Plantillas", "Módulo de plantillas en desarrollo")
    
    def show_gestion_usuarios(self):
        QMessageBox.information(self, "Usuarios", "Módulo de usuarios en desarrollo")
    
    def show_auditoria(self):
        QMessageBox.information(self, "Auditoría", "Módulo de auditoría en desarrollo")
    
    def show_estadisticas(self):
        QMessageBox.information(self, "Estadísticas", "Módulo de estadísticas en desarrollo")
    
    def show_perfil(self):
        QMessageBox.information(self, "Perfil", f"Perfil de {self.usuario.nombre}\nRol: {self.usuario.rol}")

    def on_proyecto_seleccionado(self, proyecto_id):
        """Cuando se selecciona un proyecto desde el dashboard"""
        print(f"DEBUG: Navegando al proyecto {proyecto_id}")
        
        # Crear dashboard de plantillas para el proyecto seleccionado
        dashboard_plantillas = DashboardPlantillas(self.usuario, proyecto_id, self.stacked_widget)
        dashboard_plantillas.volver_a_proyectos.connect(self.mostrar_dashboard_proyectos)
        
        # Agregar al stacked widget y mostrar
        self.stacked_widget.addWidget(dashboard_plantillas)
        self.stacked_widget.setCurrentWidget(dashboard_plantillas)
        print(f"DEBUG: Dashboard de plantillas creado y mostrado")
    
    def logout(self):
        reply = QMessageBox.question(
            self, "Cerrar Sesión",
            "¿Está seguro que desea cerrar sesión?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
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
