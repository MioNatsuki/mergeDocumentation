from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QScrollArea, QGridLayout, 
                             QMessageBox, QFrame, QLineEdit, QComboBox, QStackedWidget)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QIcon
from ui.components.project_card import ProjectCard
from ui.modules.proyectos.formulario_proyecto import FormularioProyecto
from core.project_service import ProjectService
from config.database import SessionLocal

class DashboardProyectos(QWidget):
    """Dashboard principal de selección de proyectos"""
    project_selected = pyqtSignal(int)  # Emite cuando se selecciona un proyecto
    navegar_a_formulario = pyqtSignal(object)  # Nuevo: para navegar a formularios
    
    def __init__(self, usuario, stacked_widget=None):
        super().__init__()
        self.usuario = usuario
        self.proyectos = []
        self.stacked_widget = stacked_widget  # Recibir referencia al stacked_widget
        self.setup_ui()
        self.cargar_proyectos()
    
    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(20)
        
        # Header
        header_layout = QHBoxLayout()
        
        title = QLabel("Selección de Proyectos")
        title.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        # Botón nuevo proyecto (solo admin/superadmin)
        if self.usuario.rol in ["superadmin", "admin"]:
            btn_nuevo = QPushButton("Nuevo Proyecto")
            btn_nuevo.clicked.connect(self.crear_nuevo_proyecto)
            btn_nuevo.setStyleSheet("""
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
            header_layout.addWidget(btn_nuevo)
        
        layout.addLayout(header_layout)
        
        # Filtros
        filter_layout = QHBoxLayout()
        
        filter_layout.addWidget(QLabel("Buscar:"))
        self.txt_buscar = QLineEdit()
        self.txt_buscar.setPlaceholderText("Buscar proyectos...")
        self.txt_buscar.textChanged.connect(self.filtrar_proyectos)
        filter_layout.addWidget(self.txt_buscar)
        
        filter_layout.addWidget(QLabel("Ordenar por:"))
        self.combo_orden = QComboBox()
        self.combo_orden.addItems(["Nombre A-Z", "Nombre Z-A", "Más recientes", "Más antiguos"])
        self.combo_orden.currentTextChanged.connect(self.ordenar_proyectos)
        filter_layout.addWidget(self.combo_orden)
        
        filter_layout.addStretch()
        layout.addLayout(filter_layout)
        
        # Área de proyectos
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        
        self.projects_container = QWidget()
        self.grid_layout = QGridLayout()
        self.grid_layout.setSpacing(15)
        self.grid_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        self.projects_container.setLayout(self.grid_layout)
        scroll_area.setWidget(self.projects_container)
        
        layout.addWidget(scroll_area)
        
        # Mensaje cuando no hay proyectos
        self.lbl_sin_proyectos = QLabel("No hay proyectos disponibles para tu usuario")
        self.lbl_sin_proyectos.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_sin_proyectos.setFont(QFont("Arial", 12))
        self.lbl_sin_proyectos.setStyleSheet("color: #666; padding: 40px;")
        layout.addWidget(self.lbl_sin_proyectos)
        self.lbl_sin_proyectos.hide()
        
        self.setLayout(layout)
    
    def cargar_proyectos(self):
        """Carga los proyectos desde la base de datos"""
        db = SessionLocal()
        try:
            project_service = ProjectService(db)
            self.proyectos = project_service.obtener_proyectos_usuario(self.usuario)
            self.mostrar_proyectos()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error cargando proyectos: {str(e)}")
        finally:
            db.close()
    
    def mostrar_proyectos(self):
        """Muestra los proyectos en la grid"""
        # Limpiar layout
        for i in reversed(range(self.grid_layout.count())): 
            widget = self.grid_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)
        
        if not self.proyectos:
            self.lbl_sin_proyectos.show()
            return
        
        self.lbl_sin_proyectos.hide()
        
        # Mostrar proyectos en grid 3 columnas
        for i, proyecto in enumerate(self.proyectos):
            card = ProjectCard(proyecto, self.usuario.rol)
            card.project_selected.connect(self.on_project_selected)
            card.project_edit.connect(self.on_project_edit)
            card.project_delete.connect(self.on_project_delete)
            
            row = i // 3
            col = i % 3
            self.grid_layout.addWidget(card, row, col)
    
    def on_project_selected(self, proyecto_id):
        """Cuando se selecciona un proyecto"""
        self.project_selected.emit(proyecto_id)
    
    def on_project_edit(self, proyecto_id):
        """Cuando se solicita editar un proyecto"""
        if self.stacked_widget:
            formulario = FormularioProyecto(self.usuario, proyecto_id)
            formulario.proyecto_guardado.connect(self.on_proyecto_guardado)
            
            self.stacked_widget.addWidget(formulario)
            self.stacked_widget.setCurrentWidget(formulario)
        else:
            # Fallback: usar señal
            self.navegar_a_formulario.emit(proyecto_id)
    
    def on_project_delete(self, proyecto_id):
        """Cuando se solicita eliminar un proyecto"""
        reply = QMessageBox.question(
            self, "Confirmar Eliminación",
            "¿Está seguro que desea eliminar este proyecto?\n\nEsta acción no se puede deshacer.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.eliminar_proyecto(proyecto_id)
    
    def eliminar_proyecto(self, proyecto_id):
        """Elimina un proyecto"""
        db = SessionLocal()
        try:
            project_service = ProjectService(db)
            project_service.eliminar_proyecto(proyecto_id, self.usuario)
            
            # Recargar proyectos
            self.cargar_proyectos()
            
            QMessageBox.information(self, "Éxito", "Proyecto eliminado correctamente")
            
        except PermissionError as e:
            QMessageBox.warning(self, "Permisos Insuficientes", str(e))
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error eliminando proyecto: {str(e)}")
        finally:
            db.close()
    
    def crear_nuevo_proyecto(self):
        """Abre formulario para nuevo proyecto"""
        if self.stacked_widget:
            formulario = FormularioProyecto(self.usuario)
            formulario.proyecto_guardado.connect(self.on_proyecto_guardado)
            
            self.stacked_widget.addWidget(formulario)
            self.stacked_widget.setCurrentWidget(formulario)
        else:
            # Fallback
            self.navegar_a_formulario.emit(None)
    
    def on_proyecto_guardado(self):
        """Cuando se guarda un proyecto (creación o edición)"""
        self.cargar_proyectos()
        # Si estamos en un stacked_widget, volver a este dashboard
        if self.stacked_widget:
            self.stacked_widget.setCurrentWidget(self)
    
    def filtrar_proyectos(self, texto):
        """Filtra proyectos por texto"""
        # TODO: Implementar filtrado
        pass
    
    def ordenar_proyectos(self, criterio):
        """Ordena proyectos según criterio"""
        # TODO: Implementar ordenamiento
        pass