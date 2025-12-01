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
        self.proyectos_filtrados = []
        self.stacked_widget = stacked_widget
        self.setup_ui()
        self.cargar_proyectos()
    
    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(20)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Header
        header_container = QFrame()
        header_container.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #99b898, stop:0.5 #fecea8, stop:1 #ff847c);
                border-radius: 12px;
                padding: 15px;
            }
        """)
        
        header_layout = QVBoxLayout()
        
        title = QLabel("Selección de Proyectos")
        title.setFont(QFont("Jura", 20, QFont.Weight.Bold))
        title.setStyleSheet("color: #2a363b;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_layout.addWidget(title)
        
        #header_layout.addStretch()

        subtitle = QLabel(f"Bienvenido, {self.usuario.nombre} - {self.usuario.rol.capitalize()}")
        subtitle.setFont(QFont("Jura", 12))
        subtitle.setStyleSheet("color: #2a363b; opacity: 0.9;")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_layout.addWidget(subtitle)

        header_container.setLayout(header_layout)
        layout.addWidget(header_container)
        
        # BARRA DE HERRAMIENTAS
        toolbar = QFrame()
        toolbar_layout = QHBoxLayout()

        # Búsqueda
        search_container = QFrame()
        search_container.setStyleSheet("""
            QFrame {
                background-color: #ffffff;
                border: 2px solid #99b898;
                border-radius: 8px;
                padding: 5px;
            }
        """)
        search_layout = QHBoxLayout()
        
        self.txt_buscar = QLineEdit()
        self.txt_buscar.setPlaceholderText("🔍 Buscar proyectos...")
        self.txt_buscar.setFont(QFont("Jura", 10))
        self.txt_buscar.textChanged.connect(self.filtrar_proyectos)
        self.txt_buscar.setStyleSheet("""
            QLineEdit {
                border: none;
                background: transparent;
                font-family: 'Jura';
                font-size: 12px;
            }
            QLineEdit:focus {
                border: none;
            }
        """)
        
        search_layout.addWidget(self.txt_buscar)
        search_container.setLayout(search_layout)
        toolbar_layout.addWidget(search_container)
        
        toolbar_layout.addStretch()
        
        # Filtros
        filter_layout = QHBoxLayout()
        
        filter_layout.addWidget(QLabel("Orden:"))
        self.combo_orden = QComboBox()
        self.combo_orden.addItems(["Nombre A-Z", "Nombre Z-A", "Más recientes", "Más antiguos"])
        self.combo_orden.setFont(QFont("Jura", 10))
        self.combo_orden.currentTextChanged.connect(self.ordenar_proyectos)
        self.combo_orden.setStyleSheet("""
            QComboBox {
                background-color: #ffffff;
                border: 2px solid #fecea8;
                border-radius: 6px;
                padding: 5px 10px;
                font-family: 'Jura';
            }
        """)
        filter_layout.addWidget(self.combo_orden)
        
        toolbar_layout.addLayout(filter_layout)
        
        if self.usuario.rol in ["superadmin", "admin"]:
            btn_nuevo = QPushButton("➕ Nuevo Proyecto")
            btn_nuevo.clicked.connect(self.crear_nuevo_proyecto)
            btn_nuevo.setFont(QFont("Jura", 11, QFont.Weight.Bold))
            btn_nuevo.setStyleSheet("""
                QPushButton {
                    background-color: #ff847c;
                    color: white;
                    border: none;
                    padding: 10px 20px;
                    border-radius: 8px;
                }
                QPushButton:hover {
                    background-color: #e84a5f;
                }
            """)
            toolbar_layout.addWidget(btn_nuevo)
        
        toolbar.setLayout(toolbar_layout)
        layout.addWidget(toolbar)
        
        # CONTADOR DE RESULTADOS
        self.lbl_contador = QLabel()
        self.lbl_contador.setFont(QFont("Jura", 10))
        self.lbl_contador.setStyleSheet("color: #5a6b70;")
        layout.addWidget(self.lbl_contador)
        
        # ÁREA DE PROYECTOS
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        scroll_area.setStyleSheet("background-color: transparent;")
        
        self.projects_container = QWidget()
        self.grid_layout = QGridLayout()
        self.grid_layout.setSpacing(20)
        self.grid_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.grid_layout.setContentsMargins(10, 10, 10, 10)
        
        self.projects_container.setLayout(self.grid_layout)
        scroll_area.setWidget(self.projects_container)
        
        layout.addWidget(scroll_area)
        
        # MENSAJES DE ESTADO
        self.lbl_sin_proyectos = QLabel("No hay proyectos disponibles")
        self.lbl_sin_proyectos.setFont(QFont("Jura", 14))
        self.lbl_sin_proyectos.setStyleSheet("color: #99b898; padding: 60px;")
        self.lbl_sin_proyectos.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.lbl_sin_proyectos)
        self.lbl_sin_proyectos.hide()
        
        self.lbl_sin_resultados = QLabel("No se encontraron proyectos que coincidan con la búsqueda")
        self.lbl_sin_resultados.setFont(QFont("Jura", 12))
        self.lbl_sin_resultados.setStyleSheet("color: #fecea8; padding: 40px;")
        self.lbl_sin_resultados.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.lbl_sin_resultados)
        self.lbl_sin_resultados.hide()
        
        self.setLayout(layout)

    def filtrar_proyectos(self, texto):
        """Filtra proyectos por texto de búsqueda"""
        texto = texto.lower().strip()
        
        if not texto:
            self.proyectos_filtrados = self.proyectos.copy()
        else:
            self.proyectos_filtrados = [
                p for p in self.proyectos 
                if texto in p.nombre.lower() or 
                   (p.descripcion and texto in p.descripcion.lower()) or
                   texto in p.tabla_padron.lower()
            ]
        
        self.ordenar_proyectos()
        self.actualizar_contador()

    def ordenar_proyectos(self, criterio=None):
        """Ordena proyectos según criterio seleccionado"""
        if not criterio:
            criterio = self.combo_orden.currentText()
        
        if criterio == "Nombre A-Z":
            self.proyectos_filtrados.sort(key=lambda x: x.nombre.lower())
        elif criterio == "Nombre Z-A":
            self.proyectos_filtrados.sort(key=lambda x: x.nombre.lower(), reverse=True)
        elif criterio == "Más recientes":
            self.proyectos_filtrados.sort(key=lambda x: x.fecha_creacion, reverse=True)
        elif criterio == "Más antiguos":
            self.proyectos_filtrados.sort(key=lambda x: x.fecha_creacion)
        
        self.mostrar_proyectos()
    
    def cargar_proyectos(self):
        """Carga proyectos con nombres de padrones"""
        db = SessionLocal()
        try:
            project_service = ProjectService(db)
            self.proyectos = project_service.obtener_proyectos_usuario(self.usuario)
            
            # Obtener nombres de padrones para cada proyecto
            padron_service = PadronService(db)
            self.padrones_cache = {}  # Cache de UUID -> Nombre
            
            for proyecto in self.proyectos:
                if proyecto.tabla_padron and proyecto.tabla_padron not in self.padrones_cache:
                    padron = padron_service.obtener_padron_por_uuid(proyecto.tabla_padron)
                    if padron:
                        self.padrones_cache[proyecto.tabla_padron] = padron.nombre
                    else:
                        self.padrones_cache[proyecto.tabla_padron] = f"UUID: {proyecto.tabla_padron[:8]}..."
            
            self.mostrar_proyectos()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error cargando proyectos: {str(e)}")
        finally:
            db.close()
    
    def mostrar_proyectos(self):
        """Muestra los proyectos en la grid"""
        # Limpiar layout
        for i in reversed(range(self.grid_layout.count())): 
            self.grid_layout.itemAt(i).widget().setParent(None)
        
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