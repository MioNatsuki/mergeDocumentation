from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QFrame, QMessageBox, QProgressBar,
                             QGroupBox, QTextEdit, QComboBox, QCheckBox,
                             QSpinBox, QFormLayout, QFileDialog)
from PyQt6.QtCore import Qt, pyqtSignal, QThread
from PyQt6.QtGui import QFont
from config.database import SessionLocal
from core.template_service import TemplateService
from core.models import Plantilla, EmisionTemp, Proyecto
from core.csv_service import CSVService
import os
from datetime import datetime
import json

class GeneracionPDFThread(QThread):
    """Hilo para generación de PDFs en segundo plano usando plantillas Word"""
    progreso = pyqtSignal(int, str, str)  # porcentaje, mensaje, cuenta_actual
    terminado = pyqtSignal(bool, int, int, list)  # éxito, total, exitosos, errores
    
    def __init__(self, proyecto_id: int, plantilla_id: int, sesion_id: str, 
                 usuario_id: int, ruta_salida: str, previsualizar: bool = False):
        super().__init__()
        self.proyecto_id = proyecto_id
        self.plantilla_id = plantilla_id
        self.sesion_id = sesion_id
        self.usuario_id = usuario_id
        self.ruta_salida = ruta_salida
        self.previsualizar = previsualizar
    
    def run(self):
        db = SessionLocal()
        try:
            # 1. Obtener plantilla con configuración Word
            plantilla = db.query(Plantilla).filter(Plantilla.id == self.plantilla_id).first()
            
            if not plantilla:
                self.terminado.emit(False, 0, 0, ["Plantilla no encontrada"])
                return
            
            if not plantilla.ruta_archivo_docx or not os.path.exists(plantilla.ruta_archivo_docx):
                self.terminado.emit(False, 0, 0, [
                    f"Archivo Word de plantilla no encontrado: {plantilla.ruta_archivo_docx}"
                ])
                return
            
            if not plantilla.campos_mapeo:
                self.terminado.emit(False, 0, 0, ["La plantilla no tiene campos mapeados"])
                return
            
            # 2. Obtener registros a procesar
            registros = db.query(EmisionTemp).filter(
                EmisionTemp.proyecto_id == self.proyecto_id,
                EmisionTemp.sesion_id == self.sesion_id,
                EmisionTemp.estado == 'match_ok'
            ).order_by(EmisionTemp.orden_impresion).all()
            
            total_registros = len(registros)
            if total_registros == 0:
                self.terminado.emit(False, 0, 0, ["No hay registros válidos para procesar"])
                return
            
            # 3. Preparar datos para procesamiento
            datos_registros = []
            for registro in registros:
                datos = {
                    'cuenta': registro.cuenta,
                    'codigo_afiliado': registro.codigo_afiliado
                }
                
                # Combinar datos JSON del registro
                if registro.datos_json:
                    if isinstance(registro.datos_json, str):
                        try:
                            datos_json = json.loads(registro.datos_json)
                            datos.update(datos_json)
                        except:
                            pass
                    else:
                        datos.update(registro.datos_json)
                
                datos_registros.append(datos)
            
            # 4. Procesar según modo
            if self.previsualizar:
                # Solo previsualizar el primer registro
                self.progreso.emit(50, "Generando previsualización...", datos_registros[0].get('cuenta', 'preview'))
                
                resultado = TemplateService.generar_lote_pdfs(
                    plantilla.ruta_archivo_docx,
                    plantilla.campos_mapeo,
                    [datos_registros[0]],  # Solo el primero
                    self.ruta_salida,
                    callback_progreso=self.actualizar_progreso_callback
                )
                
                if resultado['exitosos'] > 0:
                    self.terminado.emit(True, 1, 1, [])
                else:
                    self.terminado.emit(False, 1, 0, resultado['errores'])
                    
            else:
                # Generación masiva
                self.progreso.emit(10, f"Preparando {total_registros} documentos...", "")
                
                # Procesar por lotes para mejor manejo de memoria
                resultados = TemplateService.generar_lote_pdfs(
                    plantilla.ruta_archivo_docx,
                    plantilla.campos_mapeo,
                    datos_registros,
                    self.ruta_salida,
                    callback_progreso=self.actualizar_progreso_callback
                )
                
                self.terminado.emit(
                    resultados['exitosos'] > 0,
                    resultados['total'],
                    resultados['exitosos'],
                    resultados['errores']
                )
                
        except Exception as e:
            error_msg = f"Error general en generación: {str(e)}"
            print(f"❌ {error_msg}")
            import traceback
            traceback.print_exc()
            self.terminado.emit(False, 0, 0, [error_msg])
        finally:
            db.close()
    
    def actualizar_progreso_callback(self, actual: int, total: int, cuenta: str, exito: bool):
        """Callback para actualizar progreso durante generación por lotes"""
        porcentaje = int((actual / total) * 100) if total > 0 else 0
        mensaje = f"Procesando {actual}/{total}"
        self.progreso.emit(porcentaje, mensaje, cuenta)

class EmisorDocumentos(QWidget):
    """Interfaz para generación masiva de documentos PDF desde plantillas Word"""
    generacion_completada = pyqtSignal()
    
    def __init__(self, usuario, proyecto_id, plantilla_id=None, sesion_id=None):
        super().__init__()
        self.usuario = usuario
        self.proyecto_id = proyecto_id
        self.plantilla_id = plantilla_id
        self.sesion_id = sesion_id
        self.thread_generacion = None
        self.setup_ui()
        self.cargar_datos()
    
    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(20)
        
        # Header
        header = QLabel("Generación de Documentos PDF desde Word")
        header.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(header)
        
        # Información del proceso
        info_group = QGroupBox("Información del Proceso")
        info_layout = QFormLayout()
        
        self.lbl_proyecto = QLabel("Cargando...")
        self.lbl_plantilla = QLabel("Cargando...")
        self.lbl_registros = QLabel("Cargando...")
        self.lbl_sesion = QLabel("Cargando...")
        
        info_layout.addRow("Proyecto:", self.lbl_proyecto)
        info_layout.addRow("Plantilla:", self.lbl_plantilla)
        info_layout.addRow("Registros a procesar:", self.lbl_registros)
        info_layout.addRow("Sesión:", self.lbl_sesion)
        
        info_group.setLayout(info_layout)
        layout.addWidget(info_group)
        
        # Configuración de generación
        config_group = QGroupBox("Configuración de Generación")
        config_layout = QFormLayout()
        
        # Selección de plantilla
        self.combo_plantillas = QComboBox()
        self.combo_plantillas.currentIndexChanged.connect(self.on_plantilla_cambiada)
        config_layout.addRow("Plantilla Word:", self.combo_plantillas)
        
        # Información de la plantilla seleccionada
        self.lbl_info_plantilla = QLabel("")
        self.lbl_info_plantilla.setStyleSheet("color: #6c757d; font-size: 11px;")
        self.lbl_info_plantilla.setWordWrap(True)
        config_layout.addRow("", self.lbl_info_plantilla)
        
        # Ruta de salida
        ruta_layout = QHBoxLayout()
        self.lbl_ruta_salida = QLabel("C:/temp/documentos/")
        self.lbl_ruta_salida.setStyleSheet("""
            QLabel {
                background-color: #f8f9fa;
                padding: 8px;
                border: 1px solid #dee2e6;
                border-radius: 4px;
            }
        """)
        self.lbl_ruta_salida.setWordWrap(True)
        
        btn_cambiar_ruta = QPushButton("📁 Cambiar")
        btn_cambiar_ruta.clicked.connect(self.cambiar_ruta_salida)
        btn_cambiar_ruta.setStyleSheet("padding: 8px 12px;")
        
        ruta_layout.addWidget(self.lbl_ruta_salida, 3)
        ruta_layout.addWidget(btn_cambiar_ruta, 1)
        config_layout.addRow("Ruta de salida PDFs:", ruta_layout)
        
        # Opciones
        self.check_previsualizar = QCheckBox("Generar solo previsualización (primer registro)")
        self.check_previsualizar.setChecked(False)
        
        self.spin_lote = QSpinBox()
        self.spin_lote.setRange(1, 1000)
        self.spin_lote.setValue(100)
        self.spin_lote.setSuffix(" registros por lote")
        
        config_layout.addRow("", self.check_previsualizar)
        config_layout.addRow("Tamaño de lote:", self.spin_lote)
        
        config_group.setLayout(config_layout)
        layout.addWidget(config_group)
        
        # Área de progreso
        self.grupo_progreso = QGroupBox("Progreso de Generación")
        self.grupo_progreso.setVisible(False)
        progreso_layout = QVBoxLayout()
        
        self.lbl_estado = QLabel("Preparando generación...")
        self.lbl_cuenta_actual = QLabel("")
        self.lbl_cuenta_actual.setStyleSheet("color: #17a2b8; font-weight: bold;")
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        
        self.texto_log = QTextEdit()
        self.texto_log.setMaximumHeight(120)
        self.texto_log.setReadOnly(True)
        self.texto_log.setStyleSheet("font-family: monospace; font-size: 10px;")
        
        progreso_layout.addWidget(self.lbl_estado)
        progreso_layout.addWidget(self.lbl_cuenta_actual)
        progreso_layout.addWidget(self.progress_bar)
        progreso_layout.addWidget(QLabel("Log de generación:"))
        progreso_layout.addWidget(self.texto_log)
        
        self.grupo_progreso.setLayout(progreso_layout)
        layout.addWidget(self.grupo_progreso)
        
        # Botones de acción
        button_layout = QHBoxLayout()
        
        self.btn_generar = QPushButton("🔄 Generar Documentos PDF")
        self.btn_generar.clicked.connect(self.generar_documentos)
        self.btn_generar.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                border: none;
                padding: 12px 24px;
                border-radius: 6px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover:enabled {
                background-color: #218838;
            }
            QPushButton:disabled {
                background-color: #6c757d;
            }
        """)
        
        self.btn_previsualizar = QPushButton("👁️ Previsualizar")
        self.btn_previsualizar.clicked.connect(self.previsualizar_documento)
        self.btn_previsualizar.setStyleSheet("""
            QPushButton {
                background-color: #17a2b8;
                color: white;
                border: none;
                padding: 12px 24px;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #138496;
            }
        """)
        
        self.btn_limpiar = QPushButton("🗑️ Limpiar")
        self.btn_limpiar.clicked.connect(self.limpiar)
        self.btn_limpiar.setStyleSheet("""
            QPushButton {
                background-color: #6c757d;
                color: white;
                border: none;
                padding: 12px 24px;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #5a6268;
            }
        """)
        
        button_layout.addWidget(self.btn_generar)
        button_layout.addWidget(self.btn_previsualizar)
        button_layout.addStretch()
        button_layout.addWidget(self.btn_limpiar)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
        
        # Configurar ruta por defecto
        self.ruta_salida = os.path.expanduser("~/Documents/generados")
        os.makedirs(self.ruta_salida, exist_ok=True)
        self.lbl_ruta_salida.setText(self.ruta_salida)
    
    def cargar_datos(self):
        """Carga los datos necesarios para la generación"""
        db = SessionLocal()
        try:
            # Cargar proyecto
            proyecto = db.query(Proyecto).filter(Proyecto.id == self.proyecto_id).first()
            if proyecto:
                self.lbl_proyecto.setText(proyecto.nombre)
            
            # Cargar plantillas Word activas
            plantillas = db.query(Plantilla).filter(
                Plantilla.proyecto_id == self.proyecto_id,
                Plantilla.activa == True,
                Plantilla.ruta_archivo_docx.isnot(None)  # Solo plantillas con Word
            ).all()
            
            self.combo_plantillas.clear()
            for plantilla in plantillas:
                self.combo_plantillas.addItem(f"📄 {plantilla.nombre}", plantilla.id)
            
            # Seleccionar plantilla por defecto si se proporcionó
            if self.plantilla_id:
                index = self.combo_plantillas.findData(self.plantilla_id)
                if index >= 0:
                    self.combo_plantillas.setCurrentIndex(index)
            
            # Cargar estadísticas de sesión
            if self.sesion_id:
                csv_service = CSVService(db)
                stats = csv_service.obtener_estadisticas_sesion(self.sesion_id)
                self.lbl_registros.setText(f"{stats['match_ok']} registros válidos")
                self.lbl_sesion.setText(self.sesion_id[:8] + "...")
                
                # Habilitar botones si hay registros y plantillas
                if stats['match_ok'] > 0 and self.combo_plantillas.count() > 0:
                    self.btn_generar.setEnabled(True)
                    self.btn_previsualizar.setEnabled(True)
                else:
                    self.btn_generar.setEnabled(False)
                    self.btn_previsualizar.setEnabled(False)
            else:
                self.lbl_registros.setText("No hay sesión activa")
                self.lbl_sesion.setText("N/A")
                self.btn_generar.setEnabled(False)
                self.btn_previsualizar.setEnabled(False)
            
            # Cargar información de plantilla actual
            self.actualizar_info_plantilla()
            
        except Exception as e:
            self.agregar_log(f"❌ Error cargando datos: {str(e)}")
        finally:
            db.close()
    
    def on_plantilla_cambiada(self):
        """Cuando cambia la selección de plantilla"""
        self.actualizar_info_plantilla()
    
    def actualizar_info_plantilla(self):
        """Actualiza la información de la plantilla seleccionada"""
        db = SessionLocal()
        try:
            if self.combo_plantillas.count() > 0:
                plantilla_id = self.combo_plantillas.currentData()
                if plantilla_id:
                    plantilla = db.query(Plantilla).filter(Plantilla.id == plantilla_id).first()
                    if plantilla:
                        self.lbl_plantilla.setText(plantilla.nombre)
                        
                        # Mostrar información detallada
                        campos = plantilla.campos_mapeo or {}
                        info_text = f"📝 {len(campos)} campos mapeados"
                        if plantilla.ruta_archivo_docx:
                            archivo = os.path.basename(plantilla.ruta_archivo_docx)
                            info_text += f" | Archivo: {archivo}"
                        
                        self.lbl_info_plantilla.setText(info_text)
                else:
                    self.lbl_plantilla.setText("Seleccione una plantilla")
                    self.lbl_info_plantilla.setText("")
            else:
                self.lbl_plantilla.setText("No hay plantillas disponibles")
                self.lbl_info_plantilla.setText("Cree una plantilla Word primero")
                
        finally:
            db.close()
    
    def cambiar_ruta_salida(self):
        """Cambiar la ruta de salida de los PDFs"""
        nueva_ruta = QFileDialog.getExistingDirectory(
            self, 
            "Seleccionar carpeta de salida para PDFs",
            self.ruta_salida
        )
        
        if nueva_ruta:
            self.ruta_salida = nueva_ruta
            self.lbl_ruta_salida.setText(self.ruta_salida)
            self.agregar_log(f"📁 Ruta de salida cambiada a: {nueva_ruta}")
    
    def generar_documentos(self):
        """Iniciar generación masiva de documentos"""
        if not self.sesion_id:
            QMessageBox.warning(self, "Error", "No hay sesión de CSV activa")
            return
        
        if self.combo_plantillas.count() == 0:
            QMessageBox.warning(self, "Error", "No hay plantillas Word disponibles")
            return
        
        plantilla_id = self.combo_plantillas.currentData()
        previsualizar = self.check_previsualizar.isChecked()
        
        # Confirmar si es generación masiva
        if not previsualizar:
            db = SessionLocal()
            try:
                csv_service = CSVService(db)
                stats = csv_service.obtener_estadisticas_sesion(self.sesion_id)
                total = stats['match_ok']
                
                if total > 50:
                    reply = QMessageBox.question(
                        self, "Confirmar Generación Masiva",
                        f"⚠️ Va a generar {total} documentos PDF.\n\n"
                        f"Esta operación puede tomar varios minutos.\n"
                        f"¿Desea continuar?",
                        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                        QMessageBox.StandardButton.No
                    )
                    
                    if reply != QMessageBox.StandardButton.Yes:
                        return
            finally:
                db.close()
        
        # Mostrar área de progreso
        self.grupo_progreso.setVisible(True)
        self.btn_generar.setEnabled(False)
        self.btn_previsualizar.setEnabled(False)
        
        # Limpiar log anterior
        self.texto_log.clear()
        
        if previsualizar:
            self.agregar_log("👁️ Iniciando previsualización...")
        else:
            self.agregar_log("🚀 Iniciando generación masiva de documentos...")
        
        # Crear y ejecutar hilo de generación
        self.thread_generacion = GeneracionPDFThread(
            self.proyecto_id, plantilla_id, self.sesion_id, 
            self.usuario.id, self.ruta_salida, previsualizar
        )
        self.thread_generacion.progreso.connect(self.actualizar_progreso)
        self.thread_generacion.terminado.connect(self.generacion_terminada)
        self.thread_generacion.start()
    
    def previsualizar_documento(self):
        """Generar solo previsualización del primer documento"""
        self.check_previsualizar.setChecked(True)
        self.generar_documentos()
    
    def actualizar_progreso(self, porcentaje: int, mensaje: str, cuenta_actual: str):
        """Actualizar barra de progreso"""
        self.progress_bar.setValue(porcentaje)
        self.lbl_estado.setText(mensaje)
        self.lbl_cuenta_actual.setText(f"Cuenta actual: {cuenta_actual}" if cuenta_actual else "")
        self.agregar_log(f"📊 {mensaje} - {cuenta_actual}" if cuenta_actual else f"📊 {mensaje}")
    
    def generacion_terminada(self, exito: bool, total: int, exitosos: int, errores: list):
        """Cuando termina la generación"""
        if exito:
            if self.check_previsualizar.isChecked():
                self.agregar_log("✅ Previsualización generada exitosamente")
                QMessageBox.information(
                    self, 
                    "Previsualización Lista", 
                    "✅ Previsualización generada exitosamente.\n\n"
                    "Revise el archivo en la carpeta de salida."
                )
            else:
                self.agregar_log(f"✅ Generación completada: {exitosos}/{total} documentos")
                
                # Mover registros a emisiones_final y acumulados
                self.mover_a_final_y_acumulados()
                
                QMessageBox.information(
                    self, 
                    "Generación Completada", 
                    f"✅ Generación completada exitosamente.\n\n"
                    f"Documentos generados: {exitosos}/{total}\n"
                    f"Ruta: {self.ruta_salida}"
                )
                self.generacion_completada.emit()
        else:
            self.agregar_log("❌ Generación fallida")
            errores_str = "\n".join(errores[:5])  # Mostrar solo primeros 5 errores
            if len(errores) > 5:
                errores_str += f"\n... y {len(errores) - 5} errores más"
            
            QMessageBox.critical(
                self,
                "Error en Generación",
                f"❌ Hubo errores en la generación:\n\n{errores_str}"
            )
        
        self.btn_generar.setEnabled(True)
        self.btn_previsualizar.setEnabled(True)
    
    def mover_a_final_y_acumulados(self):
        """Mueve registros procesados a tablas finales y acumulados"""
        db = SessionLocal()
        try:
            from core.emission_service import EmissionService
            emission_service = EmissionService(db)
            
            # Mover a emisiones_final
            exito, movidos, errores = emission_service.mover_a_emisiones_final(
                self.sesion_id, self.usuario.id
            )
            
            if exito:
                self.agregar_log(f"📋 {movidos} registros movidos a emisiones_final")
                
                # Acumular emisiones antiguas
                exito_acum, acumulados, errores_acum = emission_service.acumular_emisiones(
                    self.proyecto_id, dias_retroceso=30
                )
                
                if exito_acum and acumulados > 0:
                    self.agregar_log(f"🗃️ {acumulados} registros antiguos acumulados")
            else:
                self.agregar_log(f"⚠️ Error moviendo a final: {errores}")
                
        except Exception as e:
            self.agregar_log(f"⚠️ Error en proceso post-generación: {str(e)}")
        finally:
            db.close()
    
    def agregar_log(self, mensaje: str):
        """Agregar mensaje al log"""
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.texto_log.append(f"[{timestamp}] {mensaje}")
        # Auto-scroll al final
        cursor = self.texto_log.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        self.texto_log.setTextCursor(cursor)
    
    def limpiar(self):
        """Limpiar la interfaz"""
        self.grupo_progreso.setVisible(False)
        self.progress_bar.setValue(0)
        self.texto_log.clear()
        self.lbl_cuenta_actual.setText("")
        self.lbl_estado.setText("Preparando generación...")