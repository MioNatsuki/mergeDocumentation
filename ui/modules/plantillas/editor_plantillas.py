# ui/modules/plantillas/editor_plantillas.py - VERSIÓN SIMPLIFICADA
from PyQt6.QtWidgets import (QWidget, QHBoxLayout, QVBoxLayout, QLabel,
                             QPushButton, QMessageBox, QSplitter, QFrame,
                             QInputDialog, QFileDialog, QStackedWidget,
                             QDialog, QDialogButtonBox, QTextEdit,
                             QComboBox, QLineEdit, QCheckBox, QGroupBox,
                             QFormLayout, QSpinBox, QScrollArea)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer, QSize
from PyQt6.QtGui import QFont, QColor, QAction
import json
import os
import traceback
from typing import List, Dict, Optional
from core.pdf_generator import PDFGenerator
import tempfile

# Importar componentes
from ui.modules.plantillas.editor_mejorado.campo_widget import CampoSimpleWidget
from ui.modules.plantillas.editor_mejorado.campo_compuesto import CampoCompuestoWidget
from ui.modules.plantillas.editor_mejorado.tabla_widget import TablaWidget
from ui.modules.plantillas.editor_mejorado.preview_pdf import PreviewPDF
from ui.modules.plantillas.editor_mejorado.panel_propiedades import PanelPropiedades

# Importar de base de datos
from config.database import SessionLocal
from core.models import Plantilla, CampoPlantilla, Proyecto
from core.padron_service import PadronService

class EditorPlantillas(QWidget):
    """Editor principal - VERSIÓN FINAL CORREGIDA"""
    
    plantilla_guardada = pyqtSignal(dict)
    
    def __init__(self, usuario, proyecto_id, pdf_path=None, stacked_widget=None, plantilla_id=None):
        super().__init__() 
        self.usuario = usuario
        self.proyecto_id = proyecto_id
        self.pdf_path = pdf_path
        self.stacked_widget = stacked_widget
        self.plantilla_id = plantilla_id
        
        # Datos
        self.campos = []
        self.campo_seleccionado = None
        self.registros_preview = []
        self.proyecto = None
        self.total_registros_padron = 0
        self.tipo_campo_a_agregar = None
        
        self.setup_ui()
        self.cargar_datos_iniciales()
        
        # Cargar PDF si existe
        if pdf_path and os.path.exists(pdf_path):
            QTimer.singleShot(100, lambda: self.cargar_pdf(pdf_path))
        
        # Cargar campos existentes
        if plantilla_id:
            QTimer.singleShot(500, self.cargar_campos_existentes)
    
    def setup_ui(self):
        """Configura UI simplificada - VERSIÓN COMPLETA CORREGIDA"""
        self.setWindowTitle("🎨 Editor de Plantillas")
        
        layout = QVBoxLayout()
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # ===== BARRA SUPERIOR =====
        toolbar = QFrame()
        toolbar.setFixedHeight(50)
        toolbar.setStyleSheet("""
            QFrame {
                background: #2c3e50;
                border-bottom: 2px solid #1a252f;
            }
            QLabel {
                color: white;
                font-size: 14px;
                font-weight: bold;
                padding: 0 10px;
            }
            QPushButton {
                background-color: rgba(255, 255, 255, 0.1);
                color: white;
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 4px;
                padding: 6px 12px;
                margin: 0 3px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.2);
                border-color: rgba(255, 255, 255, 0.3);
            }
            QPushButton:checked {
                background-color: #3498db;
                font-weight: bold;
            }
        """)
        
        toolbar_layout = QHBoxLayout()
        toolbar_layout.setContentsMargins(10, 0, 10, 0)
        
        # Info
        self.lbl_info = QLabel("Editor de Plantillas")
        
        # Botones de MODO - ¡IMPORTANTE! Conectar CORRECTAMENTE
        self.btn_seleccion = QPushButton("👆 Seleccionar")
        self.btn_seleccion.setCheckable(True)
        self.btn_seleccion.setChecked(True)
        self.btn_seleccion.clicked.connect(lambda: self.cambiar_modo('seleccion'))
        
        self.btn_texto = QPushButton("📝 Texto (clic + arrastrar)")
        self.btn_texto.setCheckable(True)
        self.btn_texto.clicked.connect(lambda: self.cambiar_modo('agregar_texto'))
        self.btn_texto.setToolTip("Clic y arrastra para crear un campo de texto")
        
        self.btn_compuesto = QPushButton("🧩 Texto compuesto (clic + arrastrar)")
        self.btn_compuesto.setCheckable(True)
        self.btn_compuesto.clicked.connect(lambda: self.cambiar_modo('agregar_compuesto'))
        self.btn_compuesto.setToolTip("Clic y arrastra para crear un campo compuesto")
        
        self.btn_tabla = QPushButton("📊 Tabla (clic + arrastrar)")
        self.btn_tabla.setCheckable(True)
        self.btn_tabla.clicked.connect(lambda: self.cambiar_modo('agregar_tabla'))
        self.btn_tabla.setToolTip("Clic y arrastra para crear una tabla")
        
        # Grupo de botones modo
        self.botones_modo = [self.btn_seleccion, self.btn_texto, self.btn_compuesto, self.btn_tabla]
        
        toolbar_layout.addWidget(self.lbl_info)
        toolbar_layout.addStretch()
        toolbar_layout.addWidget(self.btn_seleccion)
        toolbar_layout.addWidget(self.btn_texto)
        toolbar_layout.addWidget(self.btn_compuesto)
        toolbar_layout.addWidget(self.btn_tabla)
        toolbar_layout.addStretch()
        
        # Botones de acción
        self.btn_cargar_datos = QPushButton("📊 Cargar datos preview")
        self.btn_cargar_datos.clicked.connect(self.cargar_datos_preview)
        self.btn_cargar_datos.setToolTip("Cargar datos para vista previa\n(Ctrl+R para recargar)")
        
        self.btn_deseleccionar = QPushButton("❌ Deseleccionar")
        self.btn_deseleccionar.clicked.connect(self.deseleccionar_todo)
        self.btn_deseleccionar.setToolTip("Deseleccionar todos los campos")
        self.btn_deseleccionar.setStyleSheet("""
            QPushButton {
                background-color: #ff4444;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 5px 10px;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #cc0000;
            }
        """)
        
        self.btn_test_pdf = QPushButton("🔄 Probar PDF")
        self.btn_test_pdf.clicked.connect(self.probar_generacion_pdf)
        self.btn_test_pdf.setToolTip("Generar PDF de prueba con datos actuales")
        self.btn_test_pdf.setStyleSheet("""
            QPushButton {
                background-color: #9C27B0;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 5px 10px;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #7B1FA2;
            }
        """)
        
        self.btn_guardar = QPushButton("💾 Guardar")
        self.btn_guardar.clicked.connect(self.guardar_plantilla)
        self.btn_guardar.setStyleSheet("background-color: #27ae60;")
        
        self.btn_salir = QPushButton("🚪 Salir")
        self.btn_salir.clicked.connect(self.salir_editor)
        self.btn_salir.setStyleSheet("background-color: #e74c3c;")
        
        # Agregar botones en orden
        toolbar_layout.addWidget(self.btn_deseleccionar)
        toolbar_layout.addWidget(self.btn_cargar_datos)
        toolbar_layout.addWidget(self.btn_test_pdf)
        toolbar_layout.addWidget(self.btn_guardar)
        toolbar_layout.addWidget(self.btn_salir)
        
        toolbar.setLayout(toolbar_layout)
        layout.addWidget(toolbar)
        
        # ===== ÁREA PRINCIPAL =====
        splitter_principal = QSplitter(Qt.Orientation.Horizontal)
        
        # Panel central: Preview PDF (80%)
        self.preview_pdf = PreviewPDF()
        
        # ¡CRÍTICO! Conectar señales del preview
        self.preview_pdf.solicita_agregar_campo.connect(self.agregar_campo_nuevo)
        self.preview_pdf.campo_seleccionado.connect(self.on_campo_seleccionado)
        
        # ¡CRÍTICO! Pasar proyecto_id al preview
        self.preview_pdf.set_proyecto_id(self.proyecto_id)
        
        splitter_principal.addWidget(self.preview_pdf)
        
        # Panel derecho: Propiedades (20%)
        self.panel_propiedades = PanelPropiedades(self.proyecto_id)
        self.panel_propiedades.propiedades_cambiadas.connect(self.on_propiedades_cambiadas)
        splitter_principal.addWidget(self.panel_propiedades)
        
        splitter_principal.setSizes([800, 200])
        layout.addWidget(splitter_principal)
        
        self.setLayout(layout)
        self.resize(1400, 900)
        
        # DEBUG: Verificar conexiones
        print("✅ UI Configurada")
        print(f"   Preview conectado: {self.preview_pdf}")
        print(f"   Señal 'solicita_agregar_campo' conectada: {self.preview_pdf.receivers(self.preview_pdf.solicita_agregar_campo) > 0}")
        print(f"   Proyecto ID pasado: {self.proyecto_id}")
    
    def deseleccionar_todo(self):
        """Deselecciona todos los campos"""
        if hasattr(self.preview_pdf, 'deseleccionar_todos_los_campos'):
            self.preview_pdf.deseleccionar_todos_los_campos()
            self.panel_propiedades.mostrar_campo(None)  # Limpiar panel
            self.actualizar_barra_estado("🗹 Todos los campos deseleccionados")
    def setup_modo_word(self):
        """Configura modo 'como Word' para crear campos"""
        # Conectar señales del preview
        self.preview_pdf.solicita_crear_campo_por_arrastre.connect(self.crear_campo_por_arrastre)
        self.preview_pdf.solicita_terminar_arrastre.connect(self.terminar_arrastre_campo)
    
    def crear_campo_por_arrastre(self, tipo_campo: str, x1_mm: float, y1_mm: float, 
                                x2_mm: float, y2_mm: float):
        """Crea un campo a partir de un rectángulo arrastrado"""
        # Calcular posición y tamaño
        x_min = min(x1_mm, x2_mm)
        y_min = min(y1_mm, y2_mm)
        x_max = max(x1_mm, x2_mm)
        y_max = max(y1_mm, y2_mm)
        
        ancho = x_max - x_min
        alto = y_max - y_min
        
        # Crear configuración básica
        config = {
            'nombre': f'{tipo_campo.capitalize()} {len(self.campos) + 1}',
            'tipo': tipo_campo,
            'x': x_min,
            'y': y_min,
            'ancho': ancho,
            'alto': alto,
            'alineacion': 'left',
            'fuente': 'Arial',
            'tamano_fuente': 12,
            'color': '#000000',
            'negrita': False,
            'cursiva': False
        }
        
        # Crear el campo
        self.crear_y_agregar_campo(config)
    
    def crear_y_agregar_campo(self, config: dict):
        """Crea y agrega un campo según configuración"""
        try:
            if config['tipo'] in ['texto', 'campo']:
                from ui.modules.plantillas.editor_mejorado.campo_widget import CampoSimpleWidget
                if config['tipo'] == 'texto':
                    config['texto_fijo'] = 'Nuevo texto'
                else:
                    config['columna_padron'] = ''
                campo_widget = CampoSimpleWidget(config, self)
                
            elif config['tipo'] == 'compuesto':
                from ui.modules.plantillas.editor_mejorado.campo_compuesto import CampoCompuestoWidget
                campo_widget = CampoCompuestoWidget(config, self)
                
            elif config['tipo'] == 'tabla':
                from ui.modules.plantillas.editor_mejorado.tabla_widget import TablaWidget
                campo_widget = TablaWidget(config, self)
            
            else:
                return
            
            # Conectar señales
            campo_widget.campo_seleccionado.connect(self.on_campo_seleccionado)
            campo_widget.campo_modificado.connect(self.on_campo_modificado)
            campo_widget.solicita_eliminar.connect(self.eliminar_campo)
            
            # Agregar visualmente
            self.preview_pdf.agregar_campo_visual(
                campo_widget,
                config['x'],
                config['y']
            )
            self.campos.append(campo_widget)
            
            # Si es tabla o compuesto, abrir editor
            if config['tipo'] in ['compuesto', 'tabla']:
                QTimer.singleShot(100, campo_widget.configurar_tabla 
                                 if config['tipo'] == 'tabla' 
                                 else campo_widget.mostrar_editor_componentes)
            
            print(f"✅ Campo {config['tipo']} creado: {config['x']:.1f}mm, {config['y']:.1f}mm")
            
        except Exception as e:
            print(f"❌ Error creando campo: {e}")
            import traceback
            traceback.print_exc()

    def cambiar_modo(self, modo: str):
        """Cambia el modo actual y establece tipo de campo a agregar - VERSIÓN CORREGIDA"""
        print(f"\n🔄 CAMBIANDO MODO: {modo}")
        
        # Deseleccionar todos los botones primero
        for btn in self.botones_modo:
            btn.setChecked(False)
        
        # Mapear modo a tipo de campo
        modo_a_tipo = {
            'seleccion': None,
            'agregar_texto': 'texto',
            'agregar_compuesto': 'compuesto',
            'agregar_tabla': 'tabla'
        }
        
        tipo_campo = modo_a_tipo.get(modo)
        print(f"  Tipo de campo a agregar: {tipo_campo}")
        
        if modo == 'seleccion':
            self.btn_seleccion.setChecked(True)
            self.modo = 'seleccion'
            self.tipo_campo_a_agregar = None
            
            # Volver a modo selección en preview
            if hasattr(self.preview_pdf, 'cambiar_modo_agregar'):
                self.preview_pdf.cambiar_modo_agregar(None)
            self.actualizar_barra_estado("👆 Modo selección - Selecciona campos existentes")
            
        elif tipo_campo:  # agregar_texto, agregar_compuesto, agregar_tabla
            # Activar el botón correspondiente
            if modo == 'agregar_texto':
                self.btn_texto.setChecked(True)
                mensaje = "➕ Modo agregar TEXTO - Haz clic en el PDF"
            elif modo == 'agregar_compuesto':
                self.btn_compuesto.setChecked(True)
                mensaje = "🧩 Modo agregar TEXTO COMPUESTO - Haz clic en el PDF"
            elif modo == 'agregar_tabla':
                self.btn_tabla.setChecked(True)
                mensaje = "📊 Modo agregar TABLA - Haz clic en el PDF"
            
            # IMPORTANTE: Cambiar modo EN EL PREVIEW también
            self.modo = 'agregar_campo'
            self.tipo_campo_a_agregar = tipo_campo
            
            # Establecer modo agregar en preview
            if hasattr(self.preview_pdf, 'cambiar_modo_agregar'):
                self.preview_pdf.cambiar_modo_agregar(tipo_campo)
                self.preview_pdf.tipo_campo_a_agregar = tipo_campo  # ← ¡CRÍTICO!
            
            self.actualizar_barra_estado(mensaje)
    
    def actualizar_barra_estado(self, mensaje: str):
        """Actualiza la barra de estado del preview"""
        if hasattr(self.preview_pdf, 'actualizar_barra_estado'):
            self.preview_pdf.actualizar_barra_estado.setText(mensaje)

    def cargar_datos_iniciales(self):
        """Carga datos iniciales y configura preview"""
        db = SessionLocal()
        try:
            self.proyecto = db.query(Proyecto).filter(Proyecto.id == self.proyecto_id).first()
            if self.proyecto:
                self.lbl_info.setText(f"Editor - {self.proyecto.nombre}")
                
                # ¡IMPORTANTE! Pasar proyecto_id al preview
                self.preview_pdf.set_proyecto_id(self.proyecto_id)
                
                # Cargar columnas del padrón
                if hasattr(self.panel_propiedades, 'cargar_columnas_reales'):
                    self.panel_propiedades.cargar_columnas_reales()
                    
        except Exception as e:
            print(f"Error cargando datos iniciales: {e}")
            traceback.print_exc()
        finally:
            db.close()
    
    def cargar_pdf(self, pdf_path: str):
        """Carga un PDF en el preview"""
        try:
            self.pdf_path = pdf_path
            self.preview_pdf.cargar_pdf(pdf_path)
        except Exception as e:
            QMessageBox.critical(self, "Error cargando PDF", 
                               f"No se pudo cargar el PDF:\n\n{str(e)}")
            import traceback
            traceback.print_exc()
    
    def cargar_datos_preview(self):
        """Cambia a modo vista previa (carga datos automáticamente)"""
        try:
            # 1. Verificar que hay PDF cargado
            if not self.pdf_path or not os.path.exists(self.pdf_path):
                QMessageBox.warning(self, "Sin PDF", "Debes cargar un PDF primero")
                return
            
            # 2. Verificar que hay campos definidos
            if not self.campos:
                reply = QMessageBox.question(
                    self, "Sin campos",
                    "No has agregado ningún campo. ¿Ver vista previa de todos modos?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                if reply != QMessageBox.StandardButton.Yes:
                    return
            
            # 3. Cambiar a modo selección (para evitar clics accidentales)
            self.cambiar_modo('seleccion')
            
            # 4. Cambiar a modo vista previa (esto cargará datos automáticamente)
            self.preview_pdf.cambiar_modo_vista('preview')
            
            # 5. Actualizar barra de estado
            self.actualizar_barra_estado("👁️ Modo Vista Previa - Navega con los botones Anterior/Siguiente")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo cargar la vista previa: {str(e)}")
            import traceback
            traceback.print_exc()
    
    def keyPressEvent(self, event):
        """Atajos de teclado para navegación rápida"""
        if self.preview_pdf.modo_vista == 'preview':
            # Teclas para navegar en vista previa
            if event.key() == Qt.Key.Key_Left or event.key() == Qt.Key.Key_Up:
                self.preview_pdf.anterior_registro()
            elif event.key() == Qt.Key.Key_Right or event.key() == Qt.Key.Key_Down:
                self.preview_pdf.siguiente_registro()
            elif event.key() == Qt.Key.Key_Home:
                self.preview_pdf.ir_a_registro(1)
            elif event.key() == Qt.Key.Key_End:
                if hasattr(self.preview_pdf, 'registros_reales'):
                    self.preview_pdf.ir_a_registro(len(self.preview_pdf.registros_reales))
            elif event.key() == Qt.Key.Key_R and event.modifiers() == Qt.KeyboardModifier.ControlModifier:
                self.preview_pdf.recargar_datos()
        
        super().keyPressEvent(event)

    def cargar_campos_existentes(self):
        """Carga campos existentes de una plantilla"""
        if not self.plantilla_id:
            return
        
        db = SessionLocal()
        try:
            plantilla = db.query(Plantilla).filter(Plantilla.id == self.plantilla_id).first()
            if not plantilla:
                QMessageBox.warning(self, "Error", "Plantilla no encontrada")
                return
            
            campos_db = db.query(CampoPlantilla).filter(
                CampoPlantilla.plantilla_id == self.plantilla_id,
                CampoPlantilla.activo == True
            ).order_by(CampoPlantilla.orden).all()
            
            print(f"Cargando {len(campos_db)} campos existentes...")
            
            for campo_db in campos_db:
                self.crear_campo_desde_db(campo_db)
            
            print("✅ Campos cargados exitosamente")
            
        except Exception as e:
            print(f"Error cargando campos existentes: {str(e)}")
            import traceback
            traceback.print_exc()
        finally:
            db.close()
    
    def crear_campo_desde_db(self, campo_db):
        """Crea un widget de campo desde registro de BD - CON COMPUESTOS"""
        try:
            config = {
                'id': campo_db.id,
                'nombre': campo_db.nombre,
                'tipo': campo_db.tipo,
                'x': float(campo_db.x),
                'y': float(campo_db.y),
                'ancho': float(campo_db.ancho),
                'alto': float(campo_db.alto),
                'alineacion': campo_db.alineacion,
                'fuente': campo_db.fuente,
                'tamano_fuente': campo_db.tamano_fuente,
                'color': campo_db.color,
                'negrita': campo_db.negrita,
                'cursiva': campo_db.cursiva,
                'texto_fijo': campo_db.texto_fijo,
                'columna_padron': campo_db.columna_padron,
                'componentes': campo_db.componentes_json or [],
                'tabla_config': campo_db.tabla_config_json or {}
            }
            
            if campo_db.tipo == 'compuesto':
                from ui.modules.plantillas.editor_mejorado.campo_compuesto import CampoCompuestoWidget
                campo_widget = CampoCompuestoWidget(config, self)
            elif campo_db.tipo == 'tabla':
                from ui.modules.plantillas.editor_mejorado.tabla_widget import TablaWidget
                campo_widget = TablaWidget(config, self)
            else:
                from ui.modules.plantillas.editor_mejorado.campo_widget import CampoSimpleWidget
                campo_widget = CampoSimpleWidget(config, self)
            
            # Conectar señales
            campo_widget.campo_seleccionado.connect(self.on_campo_seleccionado)
            campo_widget.campo_modificado.connect(self.on_campo_modificado)
            campo_widget.solicita_eliminar.connect(self.eliminar_campo)
            
            # Agregar visualmente
            self.agregar_campo_visual(campo_widget)
            
        except Exception as e:
            print(f"Error creando campo desde DB: {str(e)}")
    
    def agregar_campo_nuevo(self, tipo_campo: str, x_mm: float, y_mm: float):
        """Agrega un nuevo campo - CON SOPORTE PARA COMPUESTOS"""
        try:
            config_base = {
                'nombre': f'Nuevo {tipo_campo}',
                'tipo': tipo_campo,
                'x': x_mm,
                'y': y_mm,
                'ancho': 150.0 if tipo_campo == 'compuesto' else 80.0,
                'alto': 20.0 if tipo_campo == 'compuesto' else 15.0,
                'alineacion': 'left',
                'fuente': 'Arial',
                'tamano_fuente': 12,
                'color': '#000000',
                'negrita': False,
                'cursiva': False
            }
            
            if tipo_campo in ['texto', 'campo']:
                from ui.modules.plantillas.editor_mejorado.campo_widget import CampoSimpleWidget
                if tipo_campo == 'texto':
                    config_base['texto_fijo'] = 'Texto de ejemplo'
                else:
                    config_base['columna_padron'] = ''
                campo_widget = CampoSimpleWidget(config_base, self)
                
            elif tipo_campo == 'compuesto':
                from ui.modules.plantillas.editor_mejorado.campo_compuesto import CampoCompuestoWidget
                campo_widget = CampoCompuestoWidget(config_base, self)
                
                # Mostrar editor de componentes INMEDIATAMENTE
                QTimer.singleShot(100, campo_widget.mostrar_editor_componentes)
                
            elif tipo_campo == 'tabla':
                from ui.modules.plantillas.editor_mejorado.tabla_widget import TablaWidget
                campo_widget = TablaWidget(config_base, self)
                QTimer.singleShot(100, campo_widget.configurar_tabla)
            
            else:
                return
            
            # Conectar señales
            campo_widget.campo_seleccionado.connect(self.on_campo_seleccionado)
            campo_widget.campo_modificado.connect(self.on_campo_modificado)
            campo_widget.solicita_eliminar.connect(self.eliminar_campo)
            
            # Agregar visualmente
            self.agregar_campo_visual(campo_widget)
            
            print(f"✅ Campo {tipo_campo} agregado en ({x_mm:.1f}, {y_mm:.1f})")
            
        except Exception as e:
            print(f"Error agregando campo: {str(e)}")
            traceback.print_exc()
    
    def agregar_campo_visual(self, campo_widget):
        """Agrega un campo visualmente al preview"""
        self.preview_pdf.agregar_campo_visual(
            campo_widget,
            campo_widget.config['x'],
            campo_widget.config['y']
        )
        self.campos.append(campo_widget)
        self.panel_propiedades.mostrar_campo(campo_widget)
    
    def on_campo_seleccionado(self, campo):
        """Cuando se selecciona un campo"""
        self.campo_seleccionado = campo
        self.panel_propiedades.mostrar_campo(campo)
    
    def on_campo_modificado(self, cambios):
        """Cuando se modifica un campo"""
        print(f"Campo modificado: {cambios}")
    
    def on_propiedades_cambiadas(self, propiedades):
        """Cuando cambian propiedades en el panel"""
        if self.campo_seleccionado:
            for key, value in propiedades.items():
                self.campo_seleccionado.config[key] = value
            
            if hasattr(self.campo_seleccionado, 'actualizar_estilo'):
                self.campo_seleccionado.actualizar_estilo()
            if hasattr(self.campo_seleccionado, 'actualizar_texto'):
                self.campo_seleccionado.actualizar_texto()
            if hasattr(self.campo_seleccionado, 'actualizar_vista'):
                self.campo_seleccionado.actualizar_vista()
    
    def eliminar_campo(self, campo):
        """Elimina un campo"""
        reply = QMessageBox.question(
            self, "Eliminar campo",
            f"¿Eliminar el campo '{campo.config.get('nombre', 'Sin nombre')}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.preview_pdf.eliminar_campo(campo)
            if campo in self.campos:
                self.campos.remove(campo)
            
            if self.campo_seleccionado == campo:
                self.campo_seleccionado = None
                self.panel_propiedades.mostrar_campo(None)
    
    def guardar_plantilla(self):
        """Guarda la plantilla - SIN pdf_paginas"""
        if not self.pdf_path:
            QMessageBox.warning(self, "Sin PDF", "Debes cargar un PDF primero")
            return
        
        if not self.campos:
            reply = QMessageBox.question(
                self, "Sin campos",
                "No has agregado ningún campo. ¿Guardar de todos modos?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply != QMessageBox.StandardButton.Yes:
                return
        
        nombre, ok = QInputDialog.getText(
            self, "Nombre de plantilla",
            "Ingresa un nombre para la plantilla:",
            text=f"Plantilla {len(self.campos)} campos"
        )
        
        if not ok or not nombre.strip():
            return
        
        db = SessionLocal()
        try:
            # Crear o actualizar plantilla - ¡SIN pdf_paginas!
            if self.plantilla_id:
                plantilla = db.query(Plantilla).filter(Plantilla.id == self.plantilla_id).first()
                if plantilla:
                    plantilla.nombre = nombre.strip()
                    plantilla.ruta_archivo = self.pdf_path
                else:
                    QMessageBox.critical(self, "Error", "Plantilla no encontrada")
                    return
            else:
                # ¡IMPORTANTE! Sin campo pdf_paginas
                plantilla = Plantilla(
                    proyecto_id=self.proyecto_id,
                    nombre=nombre.strip(),
                    descripcion=f"Creada con editor visual - {len(self.campos)} campos",
                    ruta_archivo=self.pdf_path,
                    tipo_plantilla='carta',
                    activa=True,
                    usuario_creador=self.usuario.id,
                    is_deleted=False
                )
                db.add(plantilla)
            
            db.flush()
            
            # Eliminar campos existentes si es actualización
            if self.plantilla_id:
                db.query(CampoPlantilla).filter(
                    CampoPlantilla.plantilla_id == plantilla.id
                ).delete()
            
            # Guardar cada campo
            for idx, campo_widget in enumerate(self.campos):
                campo_db = CampoPlantilla(
                    plantilla_id=plantilla.id,
                    nombre=campo_widget.config.get('nombre', f'Campo {idx+1}'),
                    tipo=campo_widget.config.get('tipo', 'texto'),
                    x=float(campo_widget.config.get('x', 50.0)),
                    y=float(campo_widget.config.get('y', 50.0)),
                    ancho=float(campo_widget.config.get('ancho', 80.0)),
                    alto=float(campo_widget.config.get('alto', 15.0)),
                    alineacion=campo_widget.config.get('alineacion', 'left'),
                    fuente=campo_widget.config.get('fuente', 'Arial'),
                    tamano_fuente=int(campo_widget.config.get('tamano_fuente', 12)),
                    color=campo_widget.config.get('color', '#000000'),
                    negrita=bool(campo_widget.config.get('negrita', False)),
                    cursiva=bool(campo_widget.config.get('cursiva', False)),
                    texto_fijo=campo_widget.config.get('texto_fijo'),
                    columna_padron=campo_widget.config.get('columna_padron'),
                    componentes_json=campo_widget.config.get('componentes', []),
                    tabla_config_json=campo_widget.config.get('tabla_config', {}),
                    orden=idx,
                    activo=True
                )
                db.add(campo_db)
            
            db.commit()
            
            if not self.plantilla_id:
                self.plantilla_id = plantilla.id
            
            configuracion = {
                'id': plantilla.id,
                'nombre': plantilla.nombre,
                'pdf_path': self.pdf_path,
                'campos_count': len(self.campos)
                # ¡NO INCLUIR pdf_paginas!
            }
            self.plantilla_guardada.emit(configuracion)
            
            QMessageBox.information(
                self, "✅ Éxito",
                f"Plantilla '{nombre}' guardada exitosamente\n\n"
                f"• ID: {plantilla.id}\n"
                f"• Campos: {len(self.campos)}\n"
                f"• Registros padrón: {self.total_registros_padron}"
            )

            reply = QMessageBox.question(
            self, "Probar alineación",
            "¿Deseas generar un PDF de prueba para verificar la alineación?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                self.probar_generacion_pdf()
            
        except Exception as e:
            db.rollback()
            QMessageBox.critical(self, "❌ Error", f"Error guardando plantilla: {str(e)}")
            import traceback
            traceback.print_exc()
        finally:
            db.close()
    
    def salir_editor(self):  # <-- ¡CORREGIDO! Se llamaba 'salir' antes
        """Sale del editor"""
        if self.campos:
            reply = QMessageBox.question(
                self, "Salir",
                "¿Salir del editor? Los cambios no guardados se perderán.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply != QMessageBox.StandardButton.Yes:
                return
        
        self.plantilla_guardada.emit({})
        if self.stacked_widget:
            self.stacked_widget.removeWidget(self)
    
    def probar_generacion_pdf(self):
        """Genera un PDF de prueba para verificar alineación"""
        if not self.campos:
            QMessageBox.warning(self, "Sin campos", "Agrega campos primero")
            return
        
        if not self.pdf_path:
            QMessageBox.warning(self, "Sin PDF", "Carga un PDF base primero")
            return
        
        # Obtener datos de prueba
        datos_prueba = self.obtener_datos_prueba_para_pdf()
        
        # Preparar configuración de campos
        config_campos = []
        for campo in self.campos:
            config_campos.append(campo.config.copy())
        
        # Generar PDF
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
            output_path = tmp.name
        
        generador = PDFGenerator(self.pdf_path)
        
        if generador.generar_pdf_con_datos(config_campos, datos_prueba, output_path):
            # Abrir el PDF generado
            self.abrir_pdf_generado(output_path)
            
            # Mostrar mensaje
            QMessageBox.information(
                self, "✅ PDF Generado",
                f"PDF de prueba generado exitosamente.\n\n"
                f"Verifica que la alineación es correcta.\n"
                f"Archivo: {os.path.basename(output_path)}"
            )
        else:
            QMessageBox.critical(self, "❌ Error", "No se pudo generar el PDF")
    
    def obtener_datos_prueba_para_pdf(self):
        """Obtiene datos de prueba para el PDF"""
        datos = {}
        
        # Si hay vista previa activa, usar esos datos
        if (hasattr(self.preview_pdf, 'registros_reales') and 
            self.preview_pdf.registros_reales):
            idx = self.preview_pdf.registro_actual_idx
            if idx < len(self.preview_pdf.registros_reales):
                datos = self.preview_pdf.registros_reales[idx].copy()
        
        # Si no hay datos, crear datos de prueba
        if not datos:
            for campo in self.campos:
                if campo.config['tipo'] == 'campo':
                    columna = campo.config.get('columna_padron', '')
                    if columna:
                        # Crear dato de prueba realista
                        if 'nombre' in columna.lower():
                            datos[columna] = "JUAN PÉREZ"
                        elif 'apellido' in columna.lower():
                            datos[columna] = "GONZÁLEZ"
                        elif 'direccion' in columna.lower():
                            datos[columna] = "AV. PRINCIPAL 123"
                        elif 'dni' in columna.lower() or 'cedula' in columna.lower():
                            datos[columna] = "12345678"
                        elif 'telefono' in columna.lower():
                            datos[columna] = "(555) 123-4567"
                        elif 'email' in columna.lower():
                            datos[columna] = "juan@ejemplo.com"
                        elif 'monto' in columna.lower():
                            datos[columna] = "$1,234.56"
                        elif 'fecha' in columna.lower():
                            datos[columna] = "15/03/2024"
                        else:
                            datos[columna] = f"Valor de prueba para {columna}"
        
        return datos
    
    def abrir_pdf_generado(self, pdf_path: str):
        """Abre el PDF generado con el visor por defecto"""
        try:
            import platform
            import subprocess
            
            if platform.system() == 'Windows':
                os.startfile(pdf_path)
            elif platform.system() == 'Darwin':  # macOS
                subprocess.run(['open', pdf_path])
            else:  # Linux
                subprocess.run(['xdg-open', pdf_path])
                
        except Exception as e:
            print(f"⚠️ No se pudo abrir el PDF: {e}")
            # Mostrar ubicación
            QMessageBox.information(
                self, "Ubicación del PDF",
                f"El PDF se guardó en:\n\n{pdf_path}"
            )