# ui/modules/plantillas/dashboard_mejorado.py - VERSIÓN CORREGIDA
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QScrollArea, QGridLayout, 
                             QMessageBox, QFrame, QComboBox, QLineEdit,
                             QToolButton, QMenu, QInputDialog)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QAction, QColor
from config.database import SessionLocal
from core.models import Proyecto, Plantilla
import os

class DashboardPlantillasMejorado(QWidget):
    """Dashboard moderno de plantillas con filtros y vista mejorada"""
    
    plantilla_seleccionada = pyqtSignal(int, str)  # id, accion (editar|usar|ver)
    volver_a_proyectos = pyqtSignal()  # ← ¡SEÑAL AÑADIDA!
    
    def __init__(self, usuario, proyecto_id, stacked_widget=None):
        super().__init__()
        self.usuario = usuario
        self.proyecto_id = proyecto_id
        self.proyecto = None
        self.plantillas = []
        self.plantillas_filtradas = []
        self.stacked_widget = stacked_widget
        self.setup_ui()
        self.cargar_datos()
    
    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # HEADER CON ACCIONES
        header = QFrame()
        header.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #4CAF50, stop:1 #2196F3);
                border-radius: 10px;
                padding: 15px;
            }
        """)
        
        header_layout = QVBoxLayout()
        
        # Título y acciones rápidas
        top_bar = QHBoxLayout()
        
        # Botón volver
        btn_volver = QPushButton("← Volver a Proyectos")
        btn_volver.clicked.connect(self.volver_proyectos)  # ← CONECTAR AL MÉTODO
        btn_volver.setStyleSheet("""
            QPushButton {
                background-color: rgba(255,255,255,0.2);
                color: white;
                border: none;
                padding: 8px 15px;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: rgba(255,255,255,0.3);
            }
        """)
        
        # Título del proyecto
        self.lbl_titulo = QLabel("Cargando proyecto...")
        self.lbl_titulo.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        self.lbl_titulo.setStyleSheet("color: white;")
        
        top_bar.addWidget(btn_volver)
        top_bar.addStretch()
        top_bar.addWidget(self.lbl_titulo)
        top_bar.addStretch()
        
        # Botón nueva plantilla (destacado)
        self.btn_nueva = QPushButton("✨ Nueva Plantilla")
        self.btn_nueva.clicked.connect(self.crear_nueva_plantilla)
        self.btn_nueva.setStyleSheet("""
            QPushButton {
                background-color: #FF9800;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 8px;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #F57C00;
            }
        """)
        top_bar.addWidget(self.btn_nueva)
        
        header_layout.addLayout(top_bar)
        
        # Descripción
        self.lbl_descripcion = QLabel()
        self.lbl_descripcion.setStyleSheet("color: rgba(255,255,255,0.9); font-size: 12px;")
        self.lbl_descripcion.setWordWrap(True)
        header_layout.addWidget(self.lbl_descripcion)
        
        header.setLayout(header_layout)
        layout.addWidget(header)
        
        # BARRA DE HERRAMIENTAS
        toolbar = QFrame()
        toolbar_layout = QHBoxLayout()
        
        # Búsqueda
        self.txt_buscar = QLineEdit()
        self.txt_buscar.setPlaceholderText("🔍 Buscar plantillas...")
        self.txt_buscar.textChanged.connect(self.filtrar_plantillas)
        self.txt_buscar.setStyleSheet("""
            QLineEdit {
                padding: 8px 12px;
                border: 2px solid #E0E0E0;
                border-radius: 6px;
                font-size: 13px;
            }
            QLineEdit:focus {
                border-color: #2196F3;
            }
        """)
        toolbar_layout.addWidget(self.txt_buscar)
        
        toolbar_layout.addStretch()
        
        # Filtros
        self.combo_filtro = QComboBox()
        self.combo_filtro.addItems(["Todas", "Activas", "Inactivas", "Cartas", "Notificaciones", "Oficios"])
        self.combo_filtro.currentTextChanged.connect(self.filtrar_plantillas)
        toolbar_layout.addWidget(QLabel("Filtrar:"))
        toolbar_layout.addWidget(self.combo_filtro)
        
        # Orden
        self.combo_orden = QComboBox()
        self.combo_orden.addItems(["Más recientes", "A-Z", "Z-A", "Más usadas"])
        self.combo_orden.currentTextChanged.connect(self.ordenar_plantillas)
        toolbar_layout.addWidget(QLabel("Orden:"))
        toolbar_layout.addWidget(self.combo_orden)
        
        toolbar.setLayout(toolbar_layout)
        layout.addWidget(toolbar)
        
        # CONTADOR
        self.lbl_contador = QLabel()
        self.lbl_contador.setStyleSheet("""
            QLabel {
                color: #666;
                font-size: 12px;
                padding: 5px 10px;
                background-color: #F5F5F5;
                border-radius: 4px;
                border-left: 3px solid #4CAF50;
            }
        """)
        layout.addWidget(self.lbl_contador)
        
        # ÁREA DE PLANTILLAS
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        
        self.plantillas_container = QWidget()
        self.grid_layout = QGridLayout()
        self.grid_layout.setSpacing(20)
        self.grid_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.grid_layout.setContentsMargins(10, 10, 10, 10)
        
        self.plantillas_container.setLayout(self.grid_layout)
        scroll_area.setWidget(self.plantillas_container)
        layout.addWidget(scroll_area)
        
        # MENSAJES DE ESTADO
        self.lbl_sin_plantillas = self.crear_mensaje_estado(
            "📭 No hay plantillas",
            "Crea tu primera plantilla para este proyecto",
            "#FF9800"
        )
        layout.addWidget(self.lbl_sin_plantillas)
        self.lbl_sin_plantillas.hide()
        
        self.lbl_sin_resultados = self.crear_mensaje_estado(
            "🔍 No se encontraron resultados",
            "Intenta con otros términos de búsqueda",
            "#2196F3"
        )
        layout.addWidget(self.lbl_sin_resultados)
        self.lbl_sin_resultados.hide()
        
        self.setLayout(layout)
    
    def crear_mensaje_estado(self, titulo, subtitulo, color):
        """Crea widget de mensaje de estado"""
        frame = QFrame()
        frame.setStyleSheet(f"""
            QFrame {{
                background-color: {color}10;
                border: 2px dashed {color};
                border-radius: 10px;
                padding: 40px;
            }}
        """)
        
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        lbl_titulo = QLabel(titulo)
        lbl_titulo.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        lbl_titulo.setStyleSheet(f"color: {color};")
        
        lbl_subtitulo = QLabel(subtitulo)
        lbl_subtitulo.setFont(QFont("Arial", 11))
        lbl_subtitulo.setStyleSheet("color: #666;")
        
        layout.addWidget(lbl_titulo)
        layout.addWidget(lbl_subtitulo)
        frame.setLayout(layout)
        
        return frame
    
    def cargar_datos(self):
        """Carga proyecto y plantillas"""
        db = SessionLocal()
        try:
            # Cargar proyecto
            self.proyecto = db.query(Proyecto).filter(Proyecto.id == self.proyecto_id).first()
            if self.proyecto:
                self.lbl_titulo.setText(f"Plantillas - {self.proyecto.nombre}")
                self.lbl_descripcion.setText(self.proyecto.descripcion or "Sin descripción")
            
            # Cargar plantillas
            self.plantillas = db.query(Plantilla).filter(
                Plantilla.proyecto_id == self.proyecto_id,
                Plantilla.is_deleted == False
            ).all()
            
            self.plantillas_filtradas = self.plantillas.copy()
            self.mostrar_plantillas()
            self.actualizar_contador()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error cargando datos: {str(e)}")
        finally:
            db.close()
    
    def mostrar_plantillas(self):
        """Muestra plantillas en grid"""
        # Limpiar grid
        for i in reversed(range(self.grid_layout.count())): 
            widget = self.grid_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)
        
        if not self.plantillas:
            self.lbl_sin_plantillas.show()
            self.lbl_sin_resultados.hide()
            return
        
        if not self.plantillas_filtradas:
            self.lbl_sin_plantillas.hide()
            self.lbl_sin_resultados.show()
            return
        
        # Ocultar mensajes
        self.lbl_sin_plantillas.hide()
        self.lbl_sin_resultados.hide()
        
        # Mostrar plantillas (3 columnas responsive)
        for i, plantilla in enumerate(self.plantillas_filtradas):
            card = self.crear_card_plantilla(plantilla)
            row = i // 3
            col = i % 3
            self.grid_layout.addWidget(card, row, col)
    
    def crear_card_plantilla(self, plantilla):
        """Crea tarjeta moderna para plantilla"""
        card = QFrame()
        card.setFixedSize(280, 220)
        card.setCursor(Qt.CursorShape.PointingHandCursor)
        
        # Estilos según estado
        if plantilla.activa:
            border_color = "#4CAF50"
            bg_color = "#FFFFFF"
        else:
            border_color = "#9E9E9E"
            bg_color = "#FAFAFA"
        
        card.setStyleSheet(f"""
            QFrame {{
                background-color: {bg_color};
                border: 2px solid {border_color};
                border-radius: 10px;
                padding: 15px;
            }}
            QFrame:hover {{
                border-color: #2196F3;
                background-color: #F8FDFF;
            }}
        """)
        
        layout = QVBoxLayout()
        layout.setSpacing(10)
        
        # Icono según tipo
        icono = self.obtener_icono_tipo(plantilla.tipo_plantilla)
        lbl_icono = QLabel(icono)
        lbl_icono.setFont(QFont("Arial", 24))
        lbl_icono.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(lbl_icono)
        
        # Nombre
        lbl_nombre = QLabel(plantilla.nombre)
        lbl_nombre.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        lbl_nombre.setWordWrap(True)
        lbl_nombre.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(lbl_nombre)
        
        # Descripción (truncada)
        desc = plantilla.descripcion or "Sin descripción"
        if len(desc) > 60:
            desc = desc[:57] + "..."
        
        lbl_desc = QLabel(desc)
        lbl_desc.setStyleSheet("color: #666; font-size: 11px;")
        lbl_desc.setWordWrap(True)
        lbl_desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(lbl_desc)
        
        # Estado y fecha
        info_layout = QHBoxLayout()
        
        estado = QLabel("✅ Activa" if plantilla.activa else "⏸️ Inactiva")
        estado.setStyleSheet(f"""
            color: {'#4CAF50' if plantilla.activa else '#9E9E9E'};
            font-size: 10px;
            font-weight: bold;
        """)
        
        fecha = QLabel(plantilla.fecha_creacion.strftime("%d/%m/%Y"))
        fecha.setStyleSheet("color: #999; font-size: 10px;")
        
        info_layout.addWidget(estado)
        info_layout.addStretch()
        info_layout.addWidget(fecha)
        layout.addLayout(info_layout)
        
        layout.addStretch()
        
        # Botones de acción
        btn_layout = QHBoxLayout()
        
        # Botón principal (Usar/Ver)
        if plantilla.activa:
            btn_accion = QPushButton("📄 Usar Plantilla")
            btn_accion.clicked.connect(lambda: self.plantilla_seleccionada.emit(plantilla.id, "usar"))
            btn_accion.setStyleSheet("""
                QPushButton {
                    background-color: #4CAF50;
                    color: white;
                    border: none;
                    padding: 6px 12px;
                    border-radius: 4px;
                    font-size: 11px;
                }
                QPushButton:hover {
                    background-color: #45a049;
                }
            """)
        else:
            btn_accion = QPushButton("👁️ Ver")
            btn_accion.clicked.connect(lambda: self.plantilla_seleccionada.emit(plantilla.id, "ver"))
            btn_accion.setStyleSheet("""
                QPushButton {
                    background-color: #9E9E9E;
                    color: white;
                    border: none;
                    padding: 6px 12px;
                    border-radius: 4px;
                    font-size: 11px;
                }
            """)
        
        btn_layout.addWidget(btn_accion)
        
        # Menú de opciones (solo admin/superadmin)
        if self.usuario.rol in ["superadmin", "admin"]:
            btn_menu = QToolButton()
            btn_menu.setText("⋮")
            btn_menu.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
            
            menu = QMenu()
            
            action_editar = QAction("✏️ Editar", self)
            action_editar.triggered.connect(lambda: self.plantilla_seleccionada.emit(plantilla.id, "editar"))
            
            action_duplicar = QAction("📋 Duplicar", self)
            action_duplicar.triggered.connect(lambda: self.duplicar_plantilla(plantilla.id))
            
            if plantilla.activa:
                action_desactivar = QAction("⏸️ Desactivar", self)
                action_desactivar.triggered.connect(lambda: self.cambiar_estado_plantilla(plantilla.id, False))
            else:
                action_activar = QAction("▶️ Activar", self)
                action_activar.triggered.connect(lambda: self.cambiar_estado_plantilla(plantilla.id, True))
            
            action_eliminar = QAction("🗑️ Eliminar", self)
            action_eliminar.triggered.connect(lambda: self.eliminar_plantilla(plantilla.id))
            
            menu.addAction(action_editar)
            menu.addAction(action_duplicar)
            menu.addSeparator()
            menu.addAction(action_desactivar if plantilla.activa else action_activar)
            menu.addAction(action_eliminar)
            
            btn_menu.setMenu(menu)
            btn_layout.addWidget(btn_menu)
        
        layout.addLayout(btn_layout)
        card.setLayout(layout)
        
        return card
    
    def obtener_icono_tipo(self, tipo):
        """Devuelve icono según tipo de plantilla"""
        iconos = {
            "carta": "📝",
            "notificacion": "📢", 
            "oficio": "📄",
            "comunicado": "🗞️",
            "cobranza": "💸",
            "pensiones": "👵",
            None: "📁"
        }
        return iconos.get(tipo, "📁")
    
    def filtrar_plantillas(self):
        """Filtra plantillas por texto y filtros"""
        texto = self.txt_buscar.text().lower().strip()
        filtro = self.combo_filtro.currentText()
        
        self.plantillas_filtradas = []
        
        for plantilla in self.plantillas:
            # Filtro por texto
            if texto and texto not in plantilla.nombre.lower():
                if not plantilla.descripcion or texto not in plantilla.descripcion.lower():
                    continue
            
            # Filtro por estado/tipo
            if filtro == "Activas" and not plantilla.activa:
                continue
            elif filtro == "Inactivas" and plantilla.activa:
                continue
            elif filtro not in ["Todas", "Activas", "Inactivas"]:
                if plantilla.tipo_plantilla != filtro.lower():
                    continue
            
            self.plantillas_filtradas.append(plantilla)
        
        self.ordenar_plantillas()
        self.actualizar_contador()
    
    def ordenar_plantillas(self):
        """Ordena plantillas según criterio"""
        criterio = self.combo_orden.currentText()
        
        if criterio == "Más recientes":
            self.plantillas_filtradas.sort(key=lambda x: x.fecha_creacion, reverse=True)
        elif criterio == "A-Z":
            self.plantillas_filtradas.sort(key=lambda x: x.nombre.lower())
        elif criterio == "Z-A":
            self.plantillas_filtradas.sort(key=lambda x: x.nombre.lower(), reverse=True)
        # "Más usadas" requeriría tracking de uso
        
        self.mostrar_plantillas()
    
    def actualizar_contador(self):
        """Actualiza contador de resultados"""
        total = len(self.plantillas)
        filtradas = len(self.plantillas_filtradas)
        
        if total == 0:
            self.lbl_contador.setText("No hay plantillas en este proyecto")
        elif total == filtradas:
            self.lbl_contador.setText(f"📋 Mostrando {total} plantillas")
        else:
            self.lbl_contador.setText(f"🔍 {filtradas} de {total} plantillas")
    
    def crear_nueva_plantilla(self):
        """Abre editor para nueva plantilla"""
        from PyQt6.QtWidgets import QFileDialog
        
        pdf_path, _ = QFileDialog.getOpenFileName(
            self, 
            "Seleccionar PDF Base", 
            "", 
            "Archivos PDF (*.pdf)"
        )
        
        if not pdf_path:
            return
        
        # IMPORTANTE: Resetear plantilla_a_editar
        if hasattr(self, 'plantilla_a_editar'):
            delattr(self, 'plantilla_a_editar')
        
        self.abrir_editor_con_pdf(pdf_path)
    
    def editar_plantilla(self, plantilla_id):
        """Abre editor para editar plantilla existente"""
        from config.database import SessionLocal
        from core.models import Plantilla
        
        db = SessionLocal()
        try:
            plantilla = db.query(Plantilla).filter(Plantilla.id == plantilla_id).first()
            if plantilla and plantilla.campos_json:
                # Guardar datos de la plantilla para editar
                self.plantilla_a_editar = plantilla.campos_json
                self.plantilla_a_editar["nombre"] = plantilla.nombre
                self.plantilla_a_editar["id"] = plantilla.id
                
                # Abrir editor con el PDF de la plantilla
                if plantilla.ruta_archivo and os.path.exists(plantilla.ruta_archivo):
                    self.abrir_editor_con_pdf(plantilla.ruta_archivo, self.plantilla_a_editar)
                else:
                    QMessageBox.warning(self, "Error", 
                                    f"El archivo PDF no existe: {plantilla.ruta_archivo}")
            else:
                QMessageBox.warning(self, "Error", "Plantilla no encontrada o sin campos")
        finally:
            db.close()

    def abrir_editor_con_pdf(self, pdf_path, plantilla_existente=None):
        """Abre el editor con un PDF específico"""
        try:
            from ui.modules.plantillas.editor_mejorado.editor_visual import EditorVisual
            
            editor = EditorVisual(
                self.usuario, 
                self.proyecto_id, 
                pdf_path,
                self.stacked_widget
            )
            
            # Si hay plantilla existente, cargarla
            if plantilla_existente:
                editor.plantilla_existente = plantilla_existente
                QTimer.singleShot(500, editor.cargar_plantilla_existente)
            
            editor.plantilla_guardada.connect(self.on_plantilla_guardada)
            
            self.stacked_widget.addWidget(editor)
            self.stacked_widget.setCurrentWidget(editor)
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo abrir el editor: {str(e)}")

    def on_plantilla_guardada(self, configuracion):
        """Cuando se guarda una plantilla desde el editor"""
        if not configuracion:
            # Cancelado
            if self.stacked_widget:
                self.stacked_widget.setCurrentWidget(self)
            return
        
        # Guardar en base de datos
        from config.database import SessionLocal
        from core.models import Plantilla
        from PyQt6.QtWidgets import QInputDialog
        
        db = SessionLocal()
        try:
            # Pedir nombre de la plantilla
            nombre, ok = QInputDialog.getText(
                self, "Nombre de la plantilla",
                "Ingresa un nombre para la plantilla:",
                text=f"Plantilla {len(self.plantillas) + 1}"
            )
            
            if not ok or not nombre.strip():
                return
            
            # Crear plantilla
            plantilla = Plantilla(
                proyecto_id=self.proyecto_id,
                nombre=nombre.strip(),
                descripcion="Creada con el editor visual",
                ruta_archivo=configuracion.get("pdf_base", ""),
                tipo_plantilla="carta",
                campos_json=configuracion,
                activa=True,
                usuario_creador=self.usuario.id,
                is_deleted=False
            )
            
            db.add(plantilla)
            db.commit()
            
            # Actualizar lista
            self.cargar_datos()
            
            # Volver al dashboard
            if self.stacked_widget:
                self.stacked_widget.setCurrentWidget(self)
            
            QMessageBox.information(self, "Éxito", "✅ Plantilla guardada correctamente")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error guardando plantilla: {str(e)}")
            db.rollback()
        finally:
            db.close()

    def on_plantilla_creada(self):
        """Cuando se crea una nueva plantilla"""
        self.cargar_datos()
        if self.stacked_widget:
            self.stacked_widget.setCurrentWidget(self)
        
        QMessageBox.information(self, "Éxito", "✅ Plantilla creada correctamente")
    
    def volver_proyectos(self):
        """Regresa al dashboard de proyectos"""
        self.volver_a_proyectos.emit()  # ← ¡EMITIR LA SEÑAL!
    
    def duplicar_plantilla(self, plantilla_id):
        """Duplica una plantilla existente"""
        db = SessionLocal()
        try:
            plantilla = db.query(Plantilla).filter(Plantilla.id == plantilla_id).first()
            if plantilla:
                nueva = Plantilla(
                    proyecto_id=plantilla.proyecto_id,
                    nombre=f"{plantilla.nombre} (Copia)",
                    descripcion=plantilla.descripcion,
                    ruta_archivo=plantilla.ruta_archivo,
                    tipo_plantilla=plantilla.tipo_plantilla,
                    campos_json=plantilla.campos_json,
                    activa=False,
                    usuario_creador=self.usuario.id
                )
                db.add(nueva)
                db.commit()
                
                self.cargar_datos()
                QMessageBox.information(self, "Éxito", "✅ Plantilla duplicada")
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error duplicando plantilla: {str(e)}")
        finally:
            db.close()
    
    def cambiar_estado_plantilla(self, plantilla_id, activar):
        """Activa/desactiva una plantilla"""
        db = SessionLocal()
        try:
            plantilla = db.query(Plantilla).filter(Plantilla.id == plantilla_id).first()
            if plantilla:
                plantilla.activa = activar
                db.commit()
                
                self.cargar_datos()
                estado = "activada" if activar else "desactivada"
                QMessageBox.information(self, "Éxito", f"✅ Plantilla {estado}")
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error cambiando estado: {str(e)}")
        finally:
            db.close()
    
    def eliminar_plantilla(self, plantilla_id):
        """Elimina (soft delete) una plantilla"""
        reply = QMessageBox.question(
            self, "Confirmar eliminación",
            "¿Está seguro de eliminar esta plantilla?\n\n"
            "Esta acción marcará la plantilla como eliminada.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            db = SessionLocal()
            try:
                plantilla = db.query(Plantilla).filter(Plantilla.id == plantilla_id).first()
                if plantilla:
                    plantilla.is_deleted = True  # Soft delete
                    db.commit()
                    
                    self.cargar_datos()
                    QMessageBox.information(self, "Éxito", "✅ Plantilla eliminada")
                    
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error eliminando plantilla: {str(e)}")
            finally:
                db.close()