from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QFrame, QGridLayout, QGroupBox,
                             QTableWidget, QTableWidgetItem, QHeaderView,
                             QDateEdit, QComboBox, QProgressBar)
from PyQt6.QtCore import Qt, QDate, pyqtSignal
from PyQt6.QtGui import QFont, QColor
from config.database import SessionLocal
from core.emission_service import EmissionService
from core.models import Proyecto
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import matplotlib
matplotlib.use('Qt5Agg')

class EstadisticasCanvas(FigureCanvas):
    """Canvas para gráficos de matplotlib"""
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        self.fig, self.ax = plt.subplots(figsize=(width, height), dpi=dpi)
        super().__init__(self.fig)
        self.setParent(parent)
    
    def actualizar_grafico(self, datos: dict, tipo: str = 'bar'):
        """Actualiza el gráfico con nuevos datos"""
        self.ax.clear()
        
        if tipo == 'bar' and datos:
            labels = list(datos.keys())
            values = list(datos.values())
            
            bars = self.ax.bar(labels, values, color=['#4CAF50', '#2196F3', '#FF9800', '#F44336'])
            self.ax.set_ylabel('Cantidad')
            self.ax.set_title('Estadísticas de Emisiones')
            
            # Agregar valores en las barras
            for bar, value in zip(bars, values):
                self.ax.text(bar.get_x() + bar.get_width()/2, bar.get_height(),
                           f'{value}', ha='center', va='bottom')
        
        self.fig.tight_layout()
        self.draw()

class DashboardEstadisticas(QWidget):
    """Dashboard de estadísticas y reportes"""
    def __init__(self, usuario, proyecto_id=None):
        super().__init__()
        self.usuario = usuario
        self.proyecto_id = proyecto_id
        self.setup_ui()
        self.cargar_estadisticas()
    
    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(20)
        
        # Header
        header = QLabel("Dashboard de Estadísticas")
        header.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(header)
        
        # Filtros
        filtros_group = QGroupBox("Filtros")
        filtros_layout = QHBoxLayout()
        
        # Selección de proyecto (solo para superadmin)
        if self.usuario.rol == 'superadmin':
            filtros_layout.addWidget(QLabel("Proyecto:"))
            self.combo_proyecto = QComboBox()
            self.combo_proyecto.currentTextChanged.connect(self.on_proyecto_cambiado)
            filtros_layout.addWidget(self.combo_proyecto)
        
        filtros_layout.addWidget(QLabel("Fecha desde:"))
        self.date_desde = QDateEdit()
        self.date_desde.setDate(QDate.currentDate().addDays(-30))
        self.date_desde.dateChanged.connect(self.cargar_estadisticas)
        filtros_layout.addWidget(self.date_desde)
        
        filtros_layout.addWidget(QLabel("Fecha hasta:"))
        self.date_hasta = QDateEdit()
        self.date_hasta.setDate(QDate.currentDate())
        self.date_hasta.dateChanged.connect(self.cargar_estadisticas)
        filtros_layout.addWidget(self.date_hasta)
        
        btn_actualizar = QPushButton("🔄 Actualizar")
        btn_actualizar.clicked.connect(self.cargar_estadisticas)
        btn_actualizar.setStyleSheet("background-color: #17a2b8; color: white;")
        filtros_layout.addWidget(btn_actualizar)
        
        filtros_group.setLayout(filtros_layout)
        layout.addWidget(filtros_group)
        
        # Tarjetas de estadísticas
        stats_layout = QGridLayout()
        stats_layout.setSpacing(15)
        
        # Tarjeta 1: Total Emisiones
        self.card_total = self.crear_tarjeta_estadistica("📊 Total Emisiones", "0", "#4CAF50")
        stats_layout.addWidget(self.card_total, 0, 0)
        
        # Tarjeta 2: Emisiones Hoy
        self.card_hoy = self.crear_tarjeta_estadistica("📅 Emisiones Hoy", "0", "#2196F3")
        stats_layout.addWidget(self.card_hoy, 0, 1)
        
        # Tarjeta 3: Emisiones Semana
        self.card_semana = self.crear_tarjeta_estadistica("📈 Esta Semana", "0", "#FF9800")
        stats_layout.addWidget(self.card_semana, 0, 2)
        
        # Tarjeta 4: Emisiones Mes
        self.card_mes = self.crear_tarjeta_estadistica("📋 Este Mes", "0", "#F44336")
        stats_layout.addWidget(self.card_mes, 0, 3)
        
        layout.addLayout(stats_layout)
        
        # Gráfico y tabla
        content_layout = QHBoxLayout()
        
        # Gráfico
        graph_group = QGroupBox("Gráfico de Emisiones")
        graph_layout = QVBoxLayout()
        
        self.canvas = EstadisticasCanvas(self, width=6, height=4, dpi=100)
        graph_layout.addWidget(self.canvas)
        
        graph_group.setLayout(graph_layout)
        content_layout.addWidget(graph_group, 2)  # 2/3 del espacio
        
        # Tabla de últimas emisiones
        table_group = QGroupBox("Últimas Emisiones")
        table_layout = QVBoxLayout()
        
        self.tabla_emisiones = QTableWidget()
        self.tabla_emisiones.setColumnCount(4)
        self.tabla_emisiones.setHorizontalHeaderLabels(["Fecha", "Cuenta", "Plantilla", "Estado"])
        self.tabla_emisiones.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        table_layout.addWidget(self.tabla_emisiones)
        
        table_group.setLayout(table_layout)
        content_layout.addWidget(table_group, 1)  # 1/3 del espacio
        
        layout.addLayout(content_layout)
        
        # Botones de acción
        action_layout = QHBoxLayout()
        
        btn_reporte = QPushButton("📄 Generar Reporte PDF")
        btn_reporte.clicked.connect(self.generar_reporte_pdf)
        btn_reporte.setStyleSheet("background-color: #28a745; color: white; padding: 10px;")
        
        btn_limpiar = QPushButton("🧹 Limpieza Automática")
        btn_limpiar.clicked.connect(self.ejecutar_limpieza)
        btn_limpiar.setStyleSheet("background-color: #ffc107; color: black; padding: 10px;")
        
        btn_exportar = QPushButton("📤 Exportar Datos")
        btn_exportar.clicked.connect(self.exportar_datos)
        btn_exportar.setStyleSheet("background-color: #17a2b8; color: white; padding: 10px;")
        
        action_layout.addWidget(btn_reporte)
        action_layout.addWidget(btn_limpiar)
        action_layout.addWidget(btn_exportar)
        action_layout.addStretch()
        
        layout.addLayout(action_layout)
        
        self.setLayout(layout)
        
        # Cargar proyectos si es superadmin
        if self.usuario.rol == 'superadmin':
            self.cargar_proyectos()
    
    def crear_tarjeta_estadistica(self, titulo: str, valor: str, color: str) -> QFrame:
        """Crea una tarjeta de estadística"""
        card = QFrame()
        card.setFrameStyle(QFrame.Shape.StyledPanel)
        card.setStyleSheet(f"""
            QFrame {{
                background-color: {color};
                color: white;
                border-radius: 8px;
                padding: 15px;
            }}
        """)
        
        layout = QVBoxLayout()
        
        lbl_titulo = QLabel(titulo)
        lbl_titulo.setStyleSheet("font-size: 14px; font-weight: bold;")
        
        lbl_valor = QLabel(valor)
        lbl_valor.setStyleSheet("font-size: 24px; font-weight: bold;")
        
        layout.addWidget(lbl_titulo)
        layout.addWidget(lbl_valor)
        
        card.setLayout(layout)
        return card
    
    def cargar_proyectos(self):
        """Carga la lista de proyectos para superadmin"""
        db = SessionLocal()
        try:
            proyectos = db.query(Proyecto).filter(Proyecto.activo == True).all()
            self.combo_proyecto.clear()
            for proyecto in proyectos:
                self.combo_proyecto.addItem(proyecto.nombre, proyecto.id)
        finally:
            db.close()
    
    def on_proyecto_cambiado(self):
        """Cuando cambia la selección de proyecto"""
        if self.usuario.rol == 'superadmin':
            self.proyecto_id = self.combo_proyecto.currentData()
            self.cargar_estadisticas()
    
    def cargar_estadisticas(self):
        """Carga las estadísticas actualizadas"""
        if not self.proyecto_id:
            return
        
        db = SessionLocal()
        try:
            emission_service = EmissionService(db)
            stats = emission_service.obtener_estadisticas_proyecto(self.proyecto_id)
            
            # Actualizar tarjetas
            self.actualizar_tarjeta(self.card_total, str(stats['total_emisiones']))
            self.actualizar_tarjeta(self.card_hoy, str(stats['emisiones_hoy']))
            self.actualizar_tarjeta(self.card_semana, str(stats['emisiones_semana']))
            self.actualizar_tarjeta(self.card_mes, str(stats['emisiones_mes']))
            
            # Actualizar gráfico
            datos_grafico = {
                'Hoy': stats['emisiones_hoy'],
                'Semana': stats['emisiones_semana'],
                'Mes': stats['emisiones_mes'],
                'Total': stats['total_emisiones']
            }
            self.canvas.actualizar_grafico(datos_grafico)
            
            # Actualizar tabla (simulada por ahora)
            self.actualizar_tabla_emisiones()
            
        except Exception as e:
            print(f"Error cargando estadísticas: {e}")
        finally:
            db.close()
    
    def actualizar_tarjeta(self, card: QFrame, valor: str):
        """Actualiza el valor de una tarjeta de estadística"""
        layout = card.layout()
        if layout and layout.itemAt(1):
            lbl_valor = layout.itemAt(1).widget()
            if lbl_valor:
                lbl_valor.setText(valor)
    
    def actualizar_tabla_emisiones(self):
        """Actualiza la tabla de últimas emisiones (simulada)"""
        self.tabla_emisiones.setRowCount(5)  # Simular 5 filas
        
        datos_ejemplo = [
            [datetime.now().strftime('%d/%m/%Y %H:%M'), '123456', 'Carta Standard', '✅ Completado'],
            [datetime.now().strftime('%d/%m/%Y %H:%M'), '123457', 'Notificación', '✅ Completado'],
            [datetime.now().strftime('%d/%m/%Y %H:%M'), '123458', 'Comunicado', '⏳ Procesando'],
            [datetime.now().strftime('%d/%m/%Y %H:%M'), '123459', 'Carta Standard', '✅ Completado'],
            [datetime.now().strftime('%d/%m/%Y %H:%M'), '123460', 'Oficio', '✅ Completado']
        ]
        
        for i, fila in enumerate(datos_ejemplo):
            for j, valor in enumerate(fila):
                item = QTableWidgetItem(str(valor))
                self.tabla_emisiones.setItem(i, j, item)
    
    def generar_reporte_pdf(self):
        """Genera reporte en PDF"""
        from PyQt6.QtWidgets import QMessageBox
        QMessageBox.information(self, "Reporte PDF", "Generando reporte PDF...")
        # Aquí iría la implementación real con ReportLab
    
    def ejecutar_limpieza(self):
        """Ejecuta limpieza automática"""
        db = SessionLocal()
        try:
            emission_service = EmissionService(db)
            exito, eliminados, errores = emission_service.limpiar_temporales()
            
            if exito:
                from PyQt6.QtWidgets import QMessageBox
                QMessageBox.information(self, "Limpieza", f"Se limpiaron {eliminados} registros temporales")
            else:
                QMessageBox.warning(self, "Limpieza", f"Error en limpieza: {errores}")
                
        finally:
            db.close()
    
    def exportar_datos(self):
        """Exporta datos a CSV"""
        from PyQt6.QtWidgets import QMessageBox
        QMessageBox.information(self, "Exportar", "Exportando datos a CSV...")
        # Aquí iría la implementación real de exportación