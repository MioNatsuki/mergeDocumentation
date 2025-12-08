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
        """Configura UI simplificada"""
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
        
        # Botones de MODO
        self.btn_seleccion = QPushButton("👆 Seleccionar")
        self.btn_seleccion.setCheckable(True)
        self.btn_seleccion.setChecked(True)
        self.btn_seleccion.clicked.connect(lambda: self.cambiar_modo('seleccion'))
        
        self.btn_texto = QPushButton("📝 Texto simple")
        self.btn_texto.setCheckable(True)
        self.btn_texto.clicked.connect(lambda: self.cambiar_modo('agregar_texto'))
        
        self.btn_compuesto = QPushButton("🧩 Texto compuesto")
        self.btn_compuesto.setCheckable(True)
        self.btn_compuesto.clicked.connect(lambda: self.cambiar_modo('agregar_compuesto'))
        
        self.btn_tabla = QPushButton("📊 Tabla")
        self.btn_tabla.setCheckable(True)
        self.btn_tabla.clicked.connect(lambda: self.cambiar_modo('agregar_tabla'))
        
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
        
        self.btn_guardar = QPushButton("💾 Guardar")
        self.btn_guardar.clicked.connect(self.guardar_plantilla)
        self.btn_guardar.setStyleSheet("background-color: #27ae60;")
        
        self.btn_salir = QPushButton("🚪 Salir")
        self.btn_salir.clicked.connect(self.salir_editor)  # <-- ¡CORREGIDO! salir -> salir_editor
        self.btn_salir.setStyleSheet("background-color: #e74c3c;")
        
        toolbar_layout.addWidget(self.btn_cargar_datos)
        toolbar_layout.addWidget(self.btn_guardar)
        toolbar_layout.addWidget(self.btn_salir)
        
        toolbar.setLayout(toolbar_layout)
        layout.addWidget(toolbar)
        
        # ===== ÁREA PRINCIPAL =====
        splitter_principal = QSplitter(Qt.Orientation.Horizontal)
        
        # Panel central: Preview PDF (80%)
        self.preview_pdf = PreviewPDF()
        self.preview_pdf.solicita_agregar_campo.connect(self.agregar_campo_nuevo)
        self.preview_pdf.campo_seleccionado.connect(self.on_campo_seleccionado)
        splitter_principal.addWidget(self.preview_pdf)
        
        # Panel derecho: Propiedades (20%)
        self.panel_propiedades = PanelPropiedades(self.proyecto_id)
        self.panel_propiedades.propiedades_cambiadas.connect(self.on_propiedades_cambiadas)
        splitter_principal.addWidget(self.panel_propiedades)
        
        splitter_principal.setSizes([800, 200])
        layout.addWidget(splitter_principal)
        
        self.setLayout(layout)
        self.resize(1400, 900)
    
    def cambiar_modo(self, modo: str):
        """Cambia el modo actual y establece tipo de campo a agregar"""
        for btn in self.botones_modo:
            btn.setChecked(False)
        
        # Mapear modo a tipo de campo
        modo_a_tipo = {
            'seleccion': None,
            'agregar_texto': 'texto',
            'agregar_compuesto': 'compuesto',
            'agregar_tabla': 'tabla'
        }
        
        self.tipo_campo_a_agregar = modo_a_tipo.get(modo)
        
        if modo == 'seleccion':
            self.btn_seleccion.setChecked(True)
            self.preview_pdf.cambiar_modo('seleccion')
            self.barra_estado("👆 Modo selección - Selecciona campos")
        elif modo == 'agregar_texto':
            self.btn_texto.setChecked(True)
            self.preview_pdf.cambiar_modo('agregar_campo')
            self.barra_estado("➕ Modo agregar texto - Haz clic en el PDF")
        elif modo == 'agregar_compuesto':
            self.btn_compuesto.setChecked(True)
            self.preview_pdf.cambiar_modo('agregar_campo')
            self.barra_estado("🧩 Modo agregar compuesto - Haz clic en el PDF")
        elif modo == 'agregar_tabla':
            self.btn_tabla.setChecked(True)
            self.preview_pdf.cambiar_modo('agregar_campo')
            self.barra_estado("📊 Modo agregar tabla - Haz clic en el PDF")
    
    def actualizar_barra_estado(self, mensaje: str):
        """Actualiza la barra de estado del preview"""
        if hasattr(self.preview_pdf, 'barra_estado'):
            self.preview_pdf.barra_estado.setText(mensaje)

    def cargar_datos_iniciales(self):
        """Carga datos iniciales y total de registros del padrón"""
        db = SessionLocal()
        try:
            self.proyecto = db.query(Proyecto).filter(Proyecto.id == self.proyecto_id).first()
            if self.proyecto:
                self.lbl_info.setText(f"Editor - {self.proyecto.nombre}")
                
                # Cargar columnas del padrón
                if hasattr(self.panel_propiedades, 'cargar_columnas_reales'):
                    self.panel_propiedades.cargar_columnas_reales()
                
                # OBTENER TOTAL DE REGISTROS DEL PADRÓN
                if self.proyecto.tabla_padron:
                    padron_service = PadronService(db)
                    
                    # Obtener el nombre real de la tabla
                    identificador = padron_service.obtener_padron_por_uuid(self.proyecto.tabla_padron)
                    if identificador and identificador.nombre_tabla:
                        from sqlalchemy import text
                        query = text(f"SELECT COUNT(*) as total FROM {identificador.nombre_tabla}")
                        result = db.execute(query).fetchone()
                        self.total_registros_padron = result[0] if result else 0
                        print(f"📊 Total registros en padrón: {self.total_registros_padron}")
                
        except Exception as e:
            print(f"Error cargando datos iniciales: {e}")
            import traceback
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
        """Carga datos REALES del padrón para vista previa"""
        db = SessionLocal()
        try:
            if not self.proyecto or not self.proyecto.tabla_padron:
                QMessageBox.warning(self, "Sin padrón", 
                                  "Este proyecto no tiene una tabla de padrón configurada")
                return
            
            # Obtener datos del padrón
            padron_service = PadronService(db)
            registros = padron_service.obtener_todos_registros(
                self.proyecto.tabla_padron, 
                limit=min(100, self.total_registros_padron)
            )
            
            if not registros:
                QMessageBox.information(self, "Sin datos", 
                                      "No hay datos en el padrón. Usando datos de prueba...")
                columnas = padron_service.obtener_columnas_padron(self.proyecto.tabla_padron)
                registros = []
                for i in range(min(10, self.total_registros_padron)):
                    registro = {}
                    for col in columnas[:8]:
                        nombre = col['nombre']
                        
                        if 'nombre' in nombre.lower():
                            valor = f"Nombre {i+1}"
                        elif 'apellido' in nombre.lower():
                            valor = f"Apellido {i+1}"
                        elif 'direccion' in nombre.lower():
                            valor = f"Calle {i+1} #123"
                        elif 'telefono' in nombre.lower():
                            valor = f"555-{1000+i}"
                        elif 'email' in nombre.lower():
                            valor = f"test{i+1}@ejemplo.com"
                        elif 'fecha' in nombre.lower():
                            valor = f"2024-01-{i+1:02d}"
                        elif 'monto' in nombre.lower() or 'saldo' in nombre.lower():
                            valor = f"${(i+1)*1000}"
                        else:
                            valor = f"Valor {i+1} - {nombre}"
                        
                        registro[nombre] = valor
                    registros.append(registro)
            
            # Establecer datos en preview
            self.preview_pdf.set_registros_preview(registros)
            self.registros_preview = registros
            
            QMessageBox.information(self, "Datos cargados", 
                                  f"Se cargaron {len(registros)} registros para vista previa\n"
                                  f"Total en padrón: {self.total_registros_padron}")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error cargando datos: {str(e)}")
            import traceback
            traceback.print_exc()
        finally:
            db.close()
    
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
        """Crea un widget de campo desde registro de BD"""
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
            
            if campo_db.tipo == 'texto' or campo_db.tipo == 'campo':
                from ui.modules.plantillas.editor_mejorado.campo_widget import CampoSimpleWidget
                campo_widget = CampoSimpleWidget(config, self)
                
            elif campo_db.tipo == 'compuesto':
                from ui.modules.plantillas.editor_mejorado.campo_compuesto import CampoCompuestoWidget
                campo_widget = CampoCompuestoWidget(config, self)
                
            elif campo_db.tipo == 'tabla':
                from ui.modules.plantillas.editor_mejorado.tabla_widget import TablaWidget
                campo_widget = TablaWidget(config, self)
                
            else:
                print(f"Tipo de campo desconocido: {campo_db.tipo}")
                return
            
            # Conectar señales
            campo_widget.campo_seleccionado.connect(self.on_campo_seleccionado)
            campo_widget.campo_modificado.connect(self.on_campo_modificado)
            campo_widget.solicita_eliminar.connect(self.eliminar_campo)
            
            # Agregar visualmente
            self.agregar_campo_visual(campo_widget)
            
        except Exception as e:
            print(f"Error creando campo desde DB: {str(e)}")
            import traceback
            traceback.print_exc()
    
    def agregar_campo_nuevo(self, tipo_campo: str, x_mm: float, y_mm: float):
        """Agrega un nuevo campo al hacer clic en el PDF"""
        try:
            config_base = {
                'nombre': f'Nuevo {tipo_campo}',
                'tipo': tipo_campo,
                'x': x_mm,
                'y': y_mm,
                'ancho': 80.0 if tipo_campo != 'tabla' else 200.0,
                'alto': 15.0 if tipo_campo != 'tabla' else 100.0,
                'alineacion': 'left',
                'fuente': 'Arial',
                'tamano_fuente': 12,
                'color': '#000000',
                'negrita': False,
                'cursiva': False
            }
            
            if tipo_campo == 'texto':
                from ui.modules.plantillas.editor_mejorado.campo_widget import CampoSimpleWidget
                config_base['texto_fijo'] = 'Texto de ejemplo'
                campo_widget = CampoSimpleWidget(config_base, self)
                campo_widget.cambiar_tipo('texto')
                
            elif tipo_campo == 'campo':
                from ui.modules.plantillas.editor_mejorado.campo_widget import CampoSimpleWidget
                config_base['columna_padron'] = ''
                campo_widget = CampoSimpleWidget(config_base, self)
                campo_widget.cambiar_tipo('campo')
                
            elif tipo_campo == 'compuesto':
                from ui.modules.plantillas.editor_mejorado.campo_compuesto import CampoCompuestoWidget
                campo_widget = CampoCompuestoWidget(config_base, self)
                QTimer.singleShot(100, campo_widget.mostrar_dialogo_agregar)
                
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
            
        except Exception as e:
            print(f"Error agregando campo: {str(e)}")
            import traceback
            traceback.print_exc()
            QMessageBox.critical(self, "Error", f"Error creando campo: {str(e)}")
    
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