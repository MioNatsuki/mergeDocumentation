from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QScrollArea, QGridLayout, 
    QMessageBox, QFrame, QLineEdit, QComboBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QPixmap
from ui.components.project_card import ProjectCard
from ui.modules.proyectos.formulario_proyecto import FormularioProyecto
from core.project_service import ProjectService
from core.padron_service import PadronService
from config.database import SessionLocal
import os

class DashboardProyectos(QWidget):
    """Dashboard principal de selección de proyectos - VERSIÓN COMPLETA"""
    project_selected = pyqtSignal(int)
    
    def __init__(self, usuario, stacked_widget=None):
        super().__init__()
        self.usuario = usuario
        self.proyectos = []
        self.proyectos_filtrados = []
        self.padrones_cache = {}  # Cache UUID -> Nombre del padrón
        self.stacked_widget = stacked_widget
        self.setup_ui()
        self.cargar_proyectos()
    
    def setup_ui(self):
        """Configura la interfaz del dashboard"""
        layout = QVBoxLayout()
        layout.setSpacing(20)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # HEADER CON DEGRADADO
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
        
        # Título principal
        title = QLabel("Selección de Proyectos")
        title.setFont(QFont("Jura", 20, QFont.Weight.Bold))
        title.setStyleSheet("color: #2a363b;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_layout.addWidget(title)
        
        # Subtítulo con información del usuario
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
        toolbar_layout.setSpacing(15)
        
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
                padding: 5px;
            }
            QLineEdit:focus {
                border: none;
                outline: none;
            }
        """)
        
        search_layout.addWidget(self.txt_buscar)
        search_container.setLayout(search_layout)
        toolbar_layout.addWidget(search_container)
        
        toolbar_layout.addStretch()
        
        # Filtros
        filter_layout = QHBoxLayout()
        filter_layout.setSpacing(10)
        
        filter_layout.addWidget(QLabel("Orden:"))
        self.combo_orden = QComboBox()
        self.combo_orden.addItems([
            "Nombre A-Z", 
            "Nombre Z-A", 
            "Más recientes", 
            "Más antiguos",
            "Por padrón A-Z",
            "Por padrón Z-A"
        ])
        self.combo_orden.setFont(QFont("Jura", 10))
        self.combo_orden.currentTextChanged.connect(self.ordenar_proyectos)
        self.combo_orden.setStyleSheet("""
            QComboBox {
                background-color: #ffffff;
                border: 2px solid #fecea8;
                border-radius: 6px;
                padding: 5px 10px;
                font-family: 'Jura';
                min-width: 120px;
            }
            QComboBox:hover {
                border-color: #ff847c;
            }
        """)
        filter_layout.addWidget(self.combo_orden)
        
        toolbar_layout.addLayout(filter_layout)
        
        # Botón nuevo proyecto (solo admin/superadmin)
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
        self.lbl_contador.setStyleSheet("""
            QLabel {
                color: #5a6b70;
                padding: 5px 10px;
                background-color: #f8f9fa;
                border-radius: 6px;
                border-left: 4px solid #99b898;
            }
        """)
        layout.addWidget(self.lbl_contador)
        
        # ÁREA DE PROYECTOS CON SCROLL
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        scroll_area.setStyleSheet("""
            QScrollArea {
                background-color: transparent;
                border: none;
            }
            QScrollBar:vertical {
                background-color: #f0f0f0;
                width: 12px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical {
                background-color: #99b898;
                border-radius: 6px;
                min-height: 30px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #88a786;
            }
        """)
        
        self.projects_container = QWidget()
        self.grid_layout = QGridLayout()
        self.grid_layout.setSpacing(20)
        self.grid_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.grid_layout.setContentsMargins(10, 10, 10, 10)
        
        self.projects_container.setLayout(self.grid_layout)
        scroll_area.setWidget(self.projects_container)
        
        layout.addWidget(scroll_area)
        
        # MENSAJES DE ESTADO
        self.lbl_sin_proyectos = QLabel("📭 No hay proyectos disponibles")
        self.lbl_sin_proyectos.setFont(QFont("Jura", 14))
        self.lbl_sin_proyectos.setStyleSheet("""
            QLabel {
                color: #99b898;
                padding: 60px;
                background-color: #f8fbf8;
                border-radius: 12px;
                border: 2px dashed #99b898;
            }
        """)
        self.lbl_sin_proyectos.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.lbl_sin_proyectos)
        self.lbl_sin_proyectos.hide()
        
        self.lbl_sin_resultados = QLabel("🔍 No se encontraron proyectos que coincidan con la búsqueda")
        self.lbl_sin_resultados.setFont(QFont("Jura", 12))
        self.lbl_sin_resultados.setStyleSheet("""
            QLabel {
                color: #fecea8;
                padding: 40px;
                background-color: #fff9f5;
                border-radius: 12px;
                border: 2px dashed #fecea8;
            }
        """)
        self.lbl_sin_resultados.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.lbl_sin_resultados)
        self.lbl_sin_resultados.hide()
        
        # FOOTER
        footer = QLabel("💡 Selecciona un proyecto para ver sus plantillas y documentos")
        footer.setFont(QFont("Jura", 9))
        footer.setStyleSheet("color: #7a8b90; padding: 10px;")
        footer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(footer)
        
        self.setLayout(layout)
    
    def cargar_proyectos(self):
        """Carga proyectos desde la base de datos con información de padrones"""
        print("DEBUG: Cargando proyectos...")
        
        db = SessionLocal()
        try:
            project_service = ProjectService(db)
            self.proyectos = project_service.obtener_proyectos_usuario(self.usuario)
            
            print(f"DEBUG - Proyectos obtenidos: {len(self.proyectos)}")
            
            # Cargar nombres de padrones para cache
            self.cargar_nombres_padrones(db)
            
            # Inicializar lista filtrada
            self.proyectos_filtrados = self.proyectos.copy()
            
            # Mostrar proyectos
            self.mostrar_proyectos()
            self.actualizar_contador()
            
        except Exception as e:
            print(f"ERROR - Error cargando proyectos: {e}")
            import traceback
            traceback.print_exc()
            QMessageBox.critical(self, "Error", f"Error cargando proyectos: {str(e)}")
        finally:
            db.close()
    
    def cargar_nombres_padrones(self, db):
        """Carga los nombres de padrones para mostrar en las cards"""
        try:
            padron_service = PadronService(db)
            
            for proyecto in self.proyectos:
                if proyecto.tabla_padron and proyecto.tabla_padron not in self.padrones_cache:
                    padron = padron_service.obtener_padron_por_uuid(proyecto.tabla_padron)
                    if padron:
                        # USAR nombre_tabla NO nombre
                        self.padrones_cache[proyecto.tabla_padron] = padron.nombre_tabla
                    else:
                        self.padrones_cache[proyecto.tabla_padron] = f"UUID: {proyecto.tabla_padron[:8]}..."
            
            print(f"DEBUG - Padrones en cache: {len(self.padrones_cache)}")
            
        except Exception as e:
            print(f"ERROR - Error cargando nombres de padrones: {e}")
            import traceback
            traceback.print_exc()
    
    def mostrar_proyectos(self):
        """Muestra los proyectos en la grid con información de padrones"""
        print(f"DEBUG: Mostrando {len(self.proyectos_filtrados)} proyectos")
        
        # Limpiar layout anterior
        for i in reversed(range(self.grid_layout.count())): 
            widget = self.grid_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)
        
        # Verificar si hay proyectos
        if not self.proyectos:
            self.lbl_sin_proyectos.show()
            self.lbl_sin_resultados.hide()
            return
        
        # Verificar si hay resultados después de filtrar
        if not self.proyectos_filtrados:
            self.lbl_sin_proyectos.hide()
            self.lbl_sin_resultados.show()
            return
        
        # Ocultar mensajes de estado
        self.lbl_sin_proyectos.hide()
        self.lbl_sin_resultados.hide()
        
        # Mostrar proyectos en grid responsive (3 columnas)
        for i, proyecto in enumerate(self.proyectos_filtrados):
            # Obtener nombre del padrón para esta card
            padron_nombre = self.padrones_cache.get(
                proyecto.tabla_padron, 
                proyecto.tabla_padron[:8] + "..." if proyecto.tabla_padron else "Sin padrón"
            )
            
            # Crear card del proyecto
            card = ProjectCard(proyecto, self.usuario.rol, padron_nombre)
            card.project_selected.connect(self.on_project_selected)
            card.project_edit.connect(self.on_project_edit)
            card.project_delete.connect(self.on_project_delete)
            
            # Calcular posición en grid (3 columnas)
            row = i // 3
            col = i % 3
            
            self.grid_layout.addWidget(card, row, col)
        
        print(f"DEBUG: Grid actualizada con {self.grid_layout.count()} widgets")
    
    def filtrar_proyectos(self, texto):
        """Filtra proyectos por texto de búsqueda"""
        texto = texto.lower().strip()
        
        if not texto:
            # Si no hay texto, mostrar todos los proyectos
            self.proyectos_filtrados = self.proyectos.copy()
        else:
            # Filtrar por nombre, descripción o padrón
            self.proyectos_filtrados = []
            for proyecto in self.proyectos:
                # Buscar en nombre
                if texto in proyecto.nombre.lower():
                    self.proyectos_filtrados.append(proyecto)
                    continue
                
                # Buscar en descripción
                if proyecto.descripcion and texto in proyecto.descripcion.lower():
                    self.proyectos_filtrados.append(proyecto)
                    continue
                
                # Buscar en nombre del padrón (desde cache)
                padron_nombre = self.padrones_cache.get(proyecto.tabla_padron, "").lower()
                if texto in padron_nombre:
                    self.proyectos_filtrados.append(proyecto)
                    continue
        
        # Aplicar ordenamiento actual
        self.ordenar_proyectos()
        self.actualizar_contador()
    
    def ordenar_proyectos(self, criterio=None):
        """Ordena proyectos según criterio seleccionado"""
        if not criterio:
            criterio = self.combo_orden.currentText()
        
        if not self.proyectos_filtrados:
            return
        
        print(f"DEBUG: Ordenando por {criterio}")
        
        if criterio == "Nombre A-Z":
            self.proyectos_filtrados.sort(key=lambda x: x.nombre.lower())
        
        elif criterio == "Nombre Z-A":
            self.proyectos_filtrados.sort(key=lambda x: x.nombre.lower(), reverse=True)
        
        elif criterio == "Más recientes":
            self.proyectos_filtrados.sort(key=lambda x: x.fecha_creacion, reverse=True)
        
        elif criterio == "Más antiguos":
            self.proyectos_filtrados.sort(key=lambda x: x.fecha_creacion)
        
        elif criterio == "Por padrón A-Z":
            self.proyectos_filtrados.sort(
                key=lambda x: self.padrones_cache.get(x.tabla_padron, "").lower()
            )
        
        elif criterio == "Por padrón Z-A":
            self.proyectos_filtrados.sort(
                key=lambda x: self.padrones_cache.get(x.tabla_padron, "").lower(),
                reverse=True
            )
        
        # Actualizar la vista
        self.mostrar_proyectos()
    
    def actualizar_contador(self):
        """Actualiza el contador de resultados"""
        total = len(self.proyectos)
        filtrados = len(self.proyectos_filtrados)
        
        if total == 0:
            self.lbl_contador.setText("No hay proyectos disponibles")
        
        elif total == filtrados:
            self.lbl_contador.setText(f"📋 Mostrando todos los proyectos ({total})")
        
        else:
            self.lbl_contador.setText(f"🔍 {filtrados} de {total} proyectos encontrados")
    
    def on_project_selected(self, proyecto_id):
        """Cuando se selecciona un proyecto"""
        print(f"DEBUG: Proyecto seleccionado ID: {proyecto_id}")
        self.project_selected.emit(proyecto_id)
    
    def on_project_edit(self, proyecto_id):
        """Cuando se solicita editar un proyecto"""
        print(f"DEBUG: Editando proyecto ID: {proyecto_id}")
        
        if self.stacked_widget:
            try:
                formulario = FormularioProyecto(self.usuario, proyecto_id, self.stacked_widget)
                formulario.proyecto_guardado.connect(self.on_proyecto_guardado)
                
                self.stacked_widget.addWidget(formulario)
                self.stacked_widget.setCurrentWidget(formulario)
                print("DEBUG: Formulario de edición mostrado")
            except Exception as e:
                print(f"ERROR abriendo editor: {e}")
                QMessageBox.critical(self, "Error", f"No se pudo abrir el editor: {str(e)}")
        else:
            QMessageBox.information(self, "Editar Proyecto", 
                                  f"Editando proyecto {proyecto_id}")
    
    def on_project_delete(self, proyecto_id):
        """Cuando se solicita eliminar un proyecto (soft delete)"""
        print(f"DEBUG: Eliminando proyecto ID: {proyecto_id}")
        
        # Obtener nombre del proyecto para el mensaje
        proyecto_nombre = ""
        for proyecto in self.proyectos:
            if proyecto.id == proyecto_id:
                proyecto_nombre = proyecto.nombre
                break
        
        reply = QMessageBox.question(
            self, "Confirmar Eliminación",
            f"¿Está seguro que desea eliminar el proyecto?\n\n"
            f"📁 {proyecto_nombre}\n\n"
            f"Esta acción marcará el proyecto como eliminado (soft delete).",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.eliminar_proyecto(proyecto_id)
    
    def eliminar_proyecto(self, proyecto_id):
        """Elimina un proyecto (soft delete)"""
        db = SessionLocal()
        try:
            project_service = ProjectService(db)
            project_service.eliminar_proyecto(proyecto_id, self.usuario)
            
            # Recargar proyectos
            self.cargar_proyectos()
            
            QMessageBox.information(self, "Éxito", "✅ Proyecto marcado como eliminado")
            
        except PermissionError as e:
            QMessageBox.warning(self, "Permisos Insuficientes", str(e))
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error eliminando proyecto: {str(e)}")
            print(f"ERROR eliminando proyecto: {e}")
        finally:
            db.close()
    
    def crear_nuevo_proyecto(self):
        """Abre formulario para nuevo proyecto"""
        print("DEBUG: Creando nuevo proyecto")
        
        if self.stacked_widget:
            try:
                formulario = FormularioProyecto(self.usuario, None, self.stacked_widget)
                formulario.proyecto_guardado.connect(self.on_proyecto_guardado)
                
                self.stacked_widget.addWidget(formulario)
                self.stacked_widget.setCurrentWidget(formulario)
                print("DEBUG: Formulario de nuevo proyecto mostrado")
            except Exception as e:
                print(f"ERROR abriendo formulario: {e}")
                QMessageBox.critical(self, "Error", f"No se pudo abrir el formulario: {str(e)}")
        else:
            QMessageBox.information(self, "Nuevo Proyecto", 
                                  "Formulario de nuevo proyecto disponible")
    
    def on_proyecto_guardado(self):
        """Cuando se guarda un proyecto (creación o edición)"""
        print("DEBUG: Proyecto guardado, recargando lista...")
        
        # Recargar proyectos
        self.cargar_proyectos()
        
        # Si estamos en un stacked_widget, volver a este dashboard
        if self.stacked_widget:
            self.stacked_widget.setCurrentWidget(self)
            
        QMessageBox.information(self, "Éxito", "✅ Proyecto guardado correctamente")