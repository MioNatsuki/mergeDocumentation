from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QFrame, QMessageBox, QTextEdit,
                             QProgressBar, QGroupBox)
from PyQt6.QtCore import Qt, pyqtSignal, QThread
from PyQt6.QtGui import QFont
from config.database import SessionLocal
from core.csv_service import CSVService
from ui.components.csv_uploader import CSVUploader
import uuid

class ProcesamientoCSVThread(QThread):
    """Hilo para procesamiento de CSV en segundo plano"""
    progreso = pyqtSignal(int, str)
    terminado = pyqtSignal(bool, int, list)
    
    def __init__(self, file_path: str, proyecto_id: int, usuario_id: int, sesion_id: str):
        super().__init__()
        self.file_path = file_path
        self.proyecto_id = proyecto_id
        self.usuario_id = usuario_id
        self.sesion_id = sesion_id
        self.csv_service = None
    
    def run(self):
        try:
            db = SessionLocal()
            self.csv_service = CSVService(db)
            
            self.progreso.emit(10, "Validando estructura del CSV...")
            es_valido, campos, erroes = self.csv_service.validar_estructura_csv(self.file_path)
            
            if not es_valido:
                self.terminado.emit(False, 0, erroes)
                return
            
            self.progreso.emit(30, "Procesando registros...")
            exito, registros, erroes = self.csv_service.procesar_csv(
                self.file_path, self.proyecto_id, self.usuario_id, self.sesion_id
            )
            
            if not exito:
                self.terminado.emit(False, registros, erroes)
                return
            
            self.progreso.emit(70, "Realizando match con padrón...")
            exito_match, registros_match, erroes_match = self.csv_service.hacer_match_padron(
                self.proyecto_id, self.sesion_id
            )
            
            self.progreso.emit(100, "Procesamiento completado")
            self.terminado.emit(True, registros, erroes + erroes_match)
            
        except Exception as e:
            self.terminado.emit(False, 0, [f"Error en procesamiento: {str(e)}"])
        finally:
            db.close()

class CargadorCSV(QWidget):
    """Interfaz para carga y procesamiento de archivos CSV"""
    procesamiento_completado = pyqtSignal(str)  # sesion_id
    
    def __init__(self, usuario, proyecto_id, plantilla_id=None):
        super().__init__()
        self.usuario = usuario
        self.proyecto_id = proyecto_id
        self.plantilla_id = plantilla_id
        self.sesion_id = str(uuid.uuid4())
        self.thread_procesamiento = None
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(20)
        
        # Header
        header = QLabel("Carga y Procesamiento de CSV")
        header.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(header)
        
        # Cargador de CSV
        self.csv_uploader = CSVUploader()
        self.csv_uploader.archivo_cargado.connect(self.on_archivo_cargado)
        layout.addWidget(self.csv_uploader)
        
        # Área de progreso (oculta inicialmente)
        self.grupo_progreso = QGroupBox("Progreso de Procesamiento")
        self.grupo_progreso.setVisible(False)
        progreso_layout = QVBoxLayout()
        
        self.lbl_estado = QLabel("Preparando...")
        self.lbl_estado.setStyleSheet("color: #6c757d;")
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        
        self.texto_log = QTextEdit()
        self.texto_log.setMaximumHeight(150)
        self.texto_log.setReadOnly(True)
        self.texto_log.setStyleSheet("font-family: monospace; font-size: 10px;")
        
        progreso_layout.addWidget(self.lbl_estado)
        progreso_layout.addWidget(self.progress_bar)
        progreso_layout.addWidget(QLabel("Log de ejecución:"))
        progreso_layout.addWidget(self.texto_log)
        
        self.grupo_progreso.setLayout(progreso_layout)
        layout.addWidget(self.grupo_progreso)
        
        # Botones de acción
        button_layout = QHBoxLayout()
        
        self.btn_procesar = QPushButton("🚀 Iniciar Procesamiento")
        self.btn_procesar.clicked.connect(self.iniciar_procesamiento)
        self.btn_procesar.setEnabled(False)
        self.btn_procesar.setStyleSheet("""
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
        
        self.btn_limpiar = QPushButton("🔄 Limpiar")
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
        
        button_layout.addWidget(self.btn_procesar)
        button_layout.addStretch()
        button_layout.addWidget(self.btn_limpiar)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def on_archivo_cargado(self, file_path: str):
        """Cuando se carga un archivo CSV"""
        self.file_path = file_path
        self.btn_procesar.setEnabled(True)
        self.agregar_log(f"📄 Archivo cargado: {file_path}")
    
    def iniciar_procesamiento(self):
        """Iniciar el procesamiento del CSV"""
        if not hasattr(self, 'file_path'):
            QMessageBox.warning(self, "Error", "Primero debe cargar un archivo CSV")
            return
        
        # Mostrar área de progreso
        self.grupo_progreso.setVisible(True)
        self.btn_procesar.setEnabled(False)
        self.csv_uploader.setEnabled(False)
        
        # Limpiar log anterior
        self.texto_log.clear()
        self.agregar_log("🚀 Iniciando procesamiento...")
        
        # Crear y ejecutar hilo de procesamiento
        self.thread_procesamiento = ProcesamientoCSVThread(
            self.file_path, self.proyecto_id, self.usuario.id, self.sesion_id
        )
        self.thread_procesamiento.progreso.connect(self.actualizar_progreso)
        self.thread_procesamiento.terminado.connect(self.procesamiento_terminado)
        self.thread_procesamiento.start()
    
    def actualizar_progreso(self, porcentaje: int, mensaje: str):
        """Actualizar barra de progreso"""
        self.progress_bar.setValue(porcentaje)
        self.lbl_estado.setText(mensaje)
        self.agregar_log(f"📊 {mensaje}")
    
    def procesamiento_terminado(self, exito: bool, registros: int, erroes: list):
        """Cuando termina el procesamiento"""
        if exito:
            self.agregar_log(f"✅ Procesamiento completado: {registros} registros")
            QMessageBox.information(
                self, 
                "Procesamiento Exitoso", 
                f"✅ Se procesaron {registros} registros correctamente.\n\n"
                f"Session ID: {self.sesion_id}"
            )
            self.procesamiento_completado.emit(self.sesion_id)
        else:
            self.agregar_log("❌ Procesamiento fallido")
            erroes_str = "\n".join(erroes[:10])  # Mostrar solo primeros 10 errores
            if len(erroes) > 10:
                erroes_str += f"\n... y {len(erroes) - 10} errores más"
            
            QMessageBox.critical(
                self,
                "Error en Procesamiento",
                f"❌ Hubo errores en el procesamiento:\n\n{erroes_str}"
            )
        
        self.btn_procesar.setEnabled(True)
        self.csv_uploader.setEnabled(True)
    
    def agregar_log(self, mensaje: str):
        """Agregar mensaje al log"""
        self.texto_log.append(f"{mensaje}")
        # Auto-scroll al final
        cursor = self.texto_log.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        self.texto_log.setTextCursor(cursor)
    
    def limpiar(self):
        """Limpiar todo el formulario"""
        self.csv_uploader.resetear()
        self.grupo_progreso.setVisible(False)
        self.btn_procesar.setEnabled(False)
        self.progress_bar.setValue(0)
        self.texto_log.clear()
        
        if hasattr(self, 'file_path'):
            del self.file_path
        
        if self.thread_procesamiento and self.thread_procesamiento.isRunning():
            self.thread_procesamiento.terminate()