from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QFrame, QFileDialog, QProgressBar,
                             QMessageBox)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QDragEnterEvent, QDropEvent
import os

class CSVUploader(QWidget):
    """Componente para carga de archivos CSV con drag & drop"""
    archivo_cargado = pyqtSignal(str)  # Emite la ruta del archivo
    
    def __init__(self):
        super().__init__()
        self.setAcceptDrops(True)
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(15)
        
        # Área de drag & drop
        self.drop_area = QFrame()
        self.drop_area.setFrameStyle(QFrame.Shape.StyledPanel)
        self.drop_area.setMinimumHeight(150)
        self.drop_area.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border: 2px dashed #dee2e6;
                border-radius: 10px;
            }
            QFrame:hover {
                background-color: #e9ecef;
                border-color: #6c757d;
            }
        """)
        
        drop_layout = QVBoxLayout()
        drop_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.lbl_icono = QLabel("📁")
        self.lbl_icono.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_icono.setFont(QFont("Arial", 32))
        
        self.lbl_titulo = QLabel("Arrastra tu archivo CSV aquí")
        self.lbl_titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_titulo.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        
        self.lbl_subtitulo = QLabel("o haz clic para seleccionar")
        self.lbl_subtitulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_subtitulo.setStyleSheet("color: #6c757d;")
        
        self.lbl_archivo = QLabel("")
        self.lbl_archivo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_archivo.setStyleSheet("color: #28a745; font-weight: bold;")
        self.lbl_archivo.hide()
        
        drop_layout.addWidget(self.lbl_icono)
        drop_layout.addWidget(self.lbl_titulo)
        drop_layout.addWidget(self.lbl_subtitulo)
        drop_layout.addWidget(self.lbl_archivo)
        
        self.drop_area.setLayout(drop_layout)
        self.drop_area.mousePressEvent = self.on_drop_area_clicked
        
        # Botón de selección manual
        btn_layout = QHBoxLayout()
        btn_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.btn_seleccionar = QPushButton("Seleccionar Archivo CSV")
        self.btn_seleccionar.clicked.connect(self.seleccionar_archivo)
        self.btn_seleccionar.setStyleSheet("""
            QPushButton {
                background-color: #007bff;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
        """)
        
        btn_layout.addWidget(self.btn_seleccionar)
        
        # Información de formato
        info_frame = QFrame()
        info_frame.setStyleSheet("background-color: #e7f3ff; padding: 10px; border-radius: 5px;")
        info_layout = QVBoxLayout()
        
        lbl_info = QLabel("📋 Formato CSV requerido:")
        lbl_info.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        info_layout.addWidget(lbl_info)
        
        lbl_campos = QLabel("Campos obligatorios: <b>cuenta, codigo_afiliado</b><br>"
                           "Codificación recomendada: <b>UTF-8</b>")
        lbl_campos.setStyleSheet("color: #495057; font-size: 11px;")
        info_layout.addWidget(lbl_campos)
        
        info_frame.setLayout(info_layout)
        
        layout.addWidget(self.drop_area)
        layout.addLayout(btn_layout)
        layout.addWidget(info_frame)
        
        self.setLayout(layout)
    
    def dragEnterEvent(self, event: QDragEnterEvent):
        """Aceptar arrastre de archivos"""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            self.drop_area.setStyleSheet("""
                QFrame {
                    background-color: #d1ecf1;
                    border: 2px dashed #17a2b8;
                    border-radius: 10px;
                }
            """)
    
    def dragLeaveEvent(self, event):
        """Restaurar estilo cuando el arrastre sale"""
        self.drop_area.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border: 2px dashed #dee2e6;
                border-radius: 10px;
            }
        """)
    
    def dropEvent(self, event: QDropEvent):
        """Manejar soltado de archivos"""
        self.drop_area.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border: 2px dashed #dee2e6;
                border-radius: 10px;
            }
        """)
        
        urls = event.mimeData().urls()
        if urls:
            file_path = urls[0].toLocalFile()
            self.validar_y_cargar_archivo(file_path)
    
    def on_drop_area_clicked(self, event):
        """Manejar clic en el área de drop"""
        self.seleccionar_archivo()
    
    def seleccionar_archivo(self):
        """Abrir diálogo para seleccionar archivo"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Seleccionar archivo CSV",
            "",
            "Archivos CSV (*.csv);;Todos los archivos (*)"
        )
        
        if file_path:
            self.validar_y_cargar_archivo(file_path)
    
    def validar_y_cargar_archivo(self, file_path: str):
        """Validar y cargar el archivo seleccionado"""
        if not file_path.lower().endswith('.csv'):
            QMessageBox.warning(self, "Formato incorrecto", "Por favor selecciona un archivo CSV")
            return
        
        if not os.path.exists(file_path):
            QMessageBox.warning(self, "Archivo no encontrado", "El archivo seleccionado no existe")
            return
        
        # Mostrar información del archivo
        nombre_archivo = os.path.basename(file_path)
        tamano = os.path.getsize(file_path) / 1024  # KB
        
        self.lbl_archivo.setText(f"📄 {nombre_archivo} ({tamano:.1f} KB)")
        self.lbl_archivo.show()
        
        self.lbl_icono.setText("✅")
        self.lbl_titulo.setText("Archivo listo para procesar")
        
        # Emitir señal con la ruta del archivo
        self.archivo_cargado.emit(file_path)
    
    def resetear(self):
        """Resetear el componente a estado inicial"""
        self.lbl_icono.setText("📁")
        self.lbl_titulo.setText("Arrastra tu archivo CSV aquí")
        self.lbl_archivo.hide()