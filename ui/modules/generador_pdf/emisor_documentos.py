from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QFrame, QMessageBox, QProgressBar,
                             QGroupBox, QTextEdit, QComboBox, QCheckBox,
                             QSpinBox, QFormLayout)
from PyQt6.QtCore import Qt, pyqtSignal, QThread
from PyQt6.QtGui import QFont
from config.database import SessionLocal
from core.models import Plantilla, EmisionTemp, Proyecto
from core.csv_service import CSVService
import os
from datetime import datetime
import json

from core.pdf_service import PDFService
from core.models import Plantilla

class GeneracionPDFThread(QThread):
    """Hilo para generación de PDFs en segundo plano"""
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
        try:
            db = SessionLocal()
            pdf_service = PDFService()
            
            # Obtener registros a procesar
            registros = db.query(EmisionTemp).filter(
                EmisionTemp.proyecto_id == self.proyecto_id,
                EmisionTemp.sesion_id == self.sesion_id,
                EmisionTemp.estado == 'match_ok'
            ).all()
            
            total_registros = len(registros)
            if total_registros == 0:
                self.terminado.emit(False, 0, 0, ["No hay registros válidos para procesar"])
                return
            
            # Obtener plantilla y configuración
            plantilla = db.query(Plantilla).filter(Plantilla.id == self.plantilla_id).first()
            if not plantilla or not plantilla.campos_json:
                self.terminado.emit(False, 0, 0, ["Plantilla no encontrada o sin campos configurados"])
                return
            
            plantilla_config = {
                'page_size': 'A4',
                'margin': 20,
                'campos': plantilla.campos_json,
                'mostrar_info_sistema': True
            }
            
            # Validar configuración
            es_valida, erroes_validacion = pdf_service.validar_configuracion_plantilla(plantilla_config)
            if not es_valida:
                self.terminado.emit(False, 0, 0, erroes_validacion)
                return
            
            exitosos = 0
            erroes = []
            
            # Preparar datos para procesamiento por lotes
            datos_registros = []
            for registro in registros:
                datos = {
                    'cuenta': registro.cuenta,
                    'codigo_afiliado': registro.codigo_afiliado,
                    'datos_json': registro.datos_json
                }
                # Agregar datos del JSON si existe
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
            
            # Procesar por lotes
            if self.previsualizar:
                # Solo previsualizar el primer registro
                primer_registro = datos_registros[0] if datos_registros else {}
                cuenta_actual = primer_registro.get('cuenta', 'preview')
                
                self.progreso.emit(50, "Generando previsualización...", cuenta_actual)
                
                nombre_archivo = f"preview_{cuenta_actual}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
                exito, resultado = pdf_service.generar_pdf(
                    primer_registro, plantilla_config, self.ruta_salida, nombre_archivo
                )
                
                if exito:
                    self.terminado.emit(True, 1, 1, [])
                else:
                    self.terminado.emit(False, 1, 0, [resultado])
                    
            else:
                # Generación masiva
                resultados = pdf_service.generar_lote_pdfs(
                    datos_registros, 
                    plantilla_config, 
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
            self.terminado.emit(False, 0, 0, [f"Error general: {str(e)}"])
        finally:
            db.close()
    
    def generar_pdf_simulado(self, registro, plantilla, indice):
        """Simula la generación de PDF (reemplazar con ReportLab)"""
        # En producción, aquí iría la generación real con ReportLab
        nombre_archivo = f"documento_{registro.cuenta or indice}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        ruta_completa = os.path.join(self.ruta_salida, nombre_archivo)
        
        # Simular tiempo de generación
        import time
        time.sleep(0.1)
        
        # Crear archivo vacío (simulación)
        with open(ruta_completa, 'w') as f:
            f.write(f"SIMULACIÓN PDF - {registro.cuenta}")
        
        return nombre_archivo

class EmisorDocumentos(QWidget):
    """Interfaz para generación masiva de documentos PDF"""
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
        header = QLabel("Generación de Documentos PDF")
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
        config_layout.addRow("Plantilla:", self.combo_plantillas)
        
        # Ruta de salida
        ruta_layout = QHBoxLayout()
        self.lbl_ruta_salida = QLabel("C:/temp/documentos/")
        self.lbl_ruta_salida.setStyleSheet("background-color: #f8f9fa; padding: 5px; border: 1px solid #ddd;")
        
        btn_cambiar_ruta = QPushButton("Cambiar")
        btn_cambiar_ruta.clicked.connect(self.cambiar_ruta_salida)
        btn_cambiar_ruta.setStyleSheet("padding: 5px 10px;")
        
        ruta_layout.addWidget(self.lbl_ruta_salida)
        ruta_layout.addWidget(btn_cambiar_ruta)
        config_layout.addRow("Ruta de salida:", ruta_layout)
        
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
        
        self.btn_generar = QPushButton("🔄 Generar Documentos")
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
            
            # Cargar plantillas
            plantillas = db.query(Plantilla).filter(
                Plantilla.proyecto_id == self.proyecto_id,
                Plantilla.activa == True
            ).all()
            
            self.combo_plantillas.clear()
            for plantilla in plantillas:
                self.combo_plantillas.addItem(plantilla.nombre, plantilla.id)
            
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
                
                # Actualizar plantilla si hay una sesión
                if stats['match_ok'] > 0 and self.combo_plantillas.count() > 0:
                    self.btn_generar.setEnabled(True)
                else:
                    self.btn_generar.setEnabled(False)
            else:
                self.lbl_registros.setText("No hay sesión activa")
                self.lbl_sesion.setText("N/A")
                self.btn_generar.setEnabled(False)
            
            # Cargar plantilla actual
            if self.combo_plantillas.count() > 0:
                plantilla_id = self.combo_plantillas.currentData()
                plantilla = db.query(Plantilla).filter(Plantilla.id == plantilla_id).first()
                if plantilla:
                    self.lbl_plantilla.setText(plantilla.nombre)
            
        except Exception as e:
            self.agregar_log(f"❌ Error cargando datos: {str(e)}")
        finally:
            db.close()
    
    def cambiar_ruta_salida(self):
        """Cambiar la ruta de salida de los PDFs"""
        from PyQt6.QtWidgets import QFileDialog
        nueva_ruta = QFileDialog.getExistingDirectory(
            self, 
            "Seleccionar carpeta de salida",
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
            QMessageBox.warning(self, "Error", "No hay plantillas disponibles")
            return
        
        plantilla_id = self.combo_plantillas.currentData()
        previsualizar = self.check_previsualizar.isChecked()
        
        # Mostrar área de progreso
        self.grupo_progreso.setVisible(True)
        self.btn_generar.setEnabled(False)
        self.btn_previsualizar.setEnabled(False)
        
        # Limpiar log anterior
        self.texto_log.clear()
        self.agregar_log("🚀 Iniciando generación de documentos...")
        
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
        self.lbl_cuenta_actual.setText(f"Cuenta actual: {cuenta_actual}")
        self.agregar_log(f"📊 {mensaje} - {cuenta_actual}")
    
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
            QMessageBox.critical(
                self,
                "Error en Generación",
                f"❌ Hubo errores en la generación:\n\n{errores_str}"
            )
        
        self.btn_generar.setEnabled(True)
        self.btn_previsualizar.setEnabled(True)
    
    def agregar_log(self, mensaje: str):
        """Agregar mensaje al log"""
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