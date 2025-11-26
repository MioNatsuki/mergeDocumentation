from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QFrame, QFormLayout, QLineEdit,
                             QSpinBox, QComboBox, QCheckBox, QGroupBox,
                             QTabWidget, QTextEdit, QFileDialog, QMessageBox)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
from config.database import SessionLocal
from core.models import ConfiguracionSistema, Usuario, Proyecto
import json
import os

class PanelConfiguracion(QWidget):
    """Panel de configuración global del sistema"""
    configuracion_guardada = pyqtSignal()
    
    def __init__(self, usuario):
        super().__init__()
        self.usuario = usuario
        self.configuraciones = {}
        self.setup_ui()
        self.cargar_configuraciones()
    
    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(20)
        
        # Header
        header = QLabel("Configuración del Sistema")
        header.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(header)
        
        # Tabs
        self.tabs = QTabWidget()
        
        # Tab: Base de Datos
        tab_db = self.crear_tab_base_datos()
        self.tabs.addTab(tab_db, "🗃️ Base de Datos")
        
        # Tab: Rutas y Archivos
        tab_rutas = self.crear_tab_rutas()
        self.tabs.addTab(tab_rutas, "📁 Rutas y Archivos")
        
        # Tab: Seguridad
        tab_seguridad = self.crear_tab_seguridad()
        self.tabs.addTab(tab_seguridad, "🔐 Seguridad")
        
        # Tab: Backup
        tab_backup = self.crear_tab_backup()
        self.tabs.addTab(tab_backup, "💾 Backup")
        
        layout.addWidget(self.tabs)
        
        # Botones de acción
        button_layout = QHBoxLayout()
        
        btn_guardar = QPushButton("💾 Guardar Configuración")
        btn_guardar.clicked.connect(self.guardar_configuracion)
        btn_guardar.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                border: none;
                padding: 12px 24px;
                border-radius: 6px;
                font-weight: bold;
            }
        """)
        
        btn_restaurar = QPushButton("🔄 Restaurar Valores por Defecto")
        btn_restaurar.clicked.connect(self.restaurar_valores_defecto)
        btn_restaurar.setStyleSheet("""
            QPushButton {
                background-color: #ffc107;
                color: black;
                border: none;
                padding: 12px 24px;
                border-radius: 6px;
            }
        """)
        
        btn_test = QPushButton("🧪 Probar Configuración")
        btn_test.clicked.connect(self.probar_configuracion)
        btn_test.setStyleSheet("""
            QPushButton {
                background-color: #17a2b8;
                color: white;
                border: none;
                padding: 12px 24px;
                border-radius: 6px;
            }
        """)
        
        button_layout.addWidget(btn_guardar)
        button_layout.addWidget(btn_restaurar)
        button_layout.addWidget(btn_test)
        button_layout.addStretch()
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def crear_tab_base_datos(self) -> QWidget:
        """Crea la tab de configuración de base de datos"""
        tab = QWidget()
        layout = QFormLayout()
        
        # Configuraciones de BD
        self.txt_db_host = QLineEdit()
        self.txt_db_host.setPlaceholderText("localhost")
        layout.addRow("Servidor BD:", self.txt_db_host)
        
        self.txt_db_puerto = QLineEdit()
        self.txt_db_puerto.setPlaceholderText("5432")
        layout.addRow("Puerto BD:", self.txt_db_puerto)
        
        self.txt_db_nombre = QLineEdit()
        self.txt_db_nombre.setPlaceholderText("correspondencia_db")
        layout.addRow("Nombre BD:", self.txt_db_nombre)
        
        self.txt_db_usuario = QLineEdit()
        self.txt_db_usuario.setPlaceholderText("postgres")
        layout.addRow("Usuario BD:", self.txt_db_usuario)
        
        self.txt_db_password = QLineEdit()
        self.txt_db_password.setEchoMode(QLineEdit.EchoMode.Password)
        self.txt_db_password.setPlaceholderText("********")
        layout.addRow("Contraseña BD:", self.txt_db_password)
        
        # Opciones avanzadas
        advanced_group = QGroupBox("Opciones Avanzadas")
        advanced_layout = QFormLayout()
        
        self.spin_max_connections = QSpinBox()
        self.spin_max_connections.setRange(5, 100)
        self.spin_max_connections.setValue(20)
        advanced_layout.addRow("Máx. conexiones:", self.spin_max_connections)
        
        self.spin_timeout = QSpinBox()
        self.spin_timeout.setRange(10, 300)
        self.spin_timeout.setValue(30)
        self.spin_timeout.setSuffix(" segundos")
        advanced_layout.addRow("Timeout:", self.spin_timeout)
        
        self.check_pooling = QCheckBox("Usar pool de conexiones")
        self.check_pooling.setChecked(True)
        advanced_layout.addRow("", self.check_pooling)
        
        advanced_group.setLayout(advanced_layout)
        layout.addRow(advanced_group)
        
        tab.setLayout(layout)
        return tab
    
    def crear_tab_rutas(self) -> QWidget:
        """Crea la tab de configuración de rutas"""
        tab = QWidget()
        layout = QFormLayout()
        
        # Rutas del sistema
        self.txt_ruta_pdfs = QLineEdit()
        self.txt_ruta_pdfs.setPlaceholderText("C:/temp/documentos/")
        btn_buscar_pdfs = QPushButton("Examinar...")
        btn_buscar_pdfs.clicked.connect(lambda: self.seleccionar_directorio(self.txt_ruta_pdfs))
        
        ruta_layout = QHBoxLayout()
        ruta_layout.addWidget(self.txt_ruta_pdfs)
        ruta_layout.addWidget(btn_buscar_pdfs)
        layout.addRow("Ruta PDFs:", ruta_layout)
        
        self.txt_ruta_logs = QLineEdit()
        self.txt_ruta_logs.setPlaceholderText("C:/temp/logs/")
        btn_buscar_logs = QPushButton("Examinar...")
        btn_buscar_logs.clicked.connect(lambda: self.seleccionar_directorio(self.txt_ruta_logs))
        
        logs_layout = QHBoxLayout()
        logs_layout.addWidget(self.txt_ruta_logs)
        logs_layout.addWidget(btn_buscar_logs)
        layout.addRow("Ruta Logs:", logs_layout)
        
        self.txt_ruta_backup = QLineEdit()
        self.txt_ruta_backup.setPlaceholderText("C:/temp/backup/")
        btn_buscar_backup = QPushButton("Examinar...")
        btn_buscar_backup.clicked.connect(lambda: self.seleccionar_directorio(self.txt_ruta_backup))
        
        backup_layout = QHBoxLayout()
        backup_layout.addWidget(self.txt_ruta_backup)
        backup_layout.addWidget(btn_buscar_backup)
        layout.addRow("Ruta Backup:", backup_layout)
        
        # Opciones de archivos
        file_group = QGroupBox("Opciones de Archivos")
        file_layout = QFormLayout()
        
        self.spin_max_file_size = QSpinBox()
        self.spin_max_file_size.setRange(1, 100)
        self.spin_max_file_size.setValue(10)
        self.spin_max_file_size.setSuffix(" MB")
        file_layout.addRow("Tamaño máximo archivo:", self.spin_max_file_size)
        
        self.spin_keep_logs = QSpinBox()
        self.spin_keep_logs.setRange(1, 365)
        self.spin_keep_logs.setValue(30)
        self.spin_keep_logs.setSuffix(" días")
        file_layout.addRow("Conservar logs:", self.spin_keep_logs)
        
        file_group.setLayout(file_layout)
        layout.addRow(file_group)
        
        tab.setLayout(layout)
        return tab
    
    def crear_tab_seguridad(self) -> QWidget:
        """Crea la tab de configuración de seguridad"""
        tab = QWidget()
        layout = QFormLayout()
        
        # Configuración de seguridad
        security_group = QGroupBox("Configuración de Seguridad")
        security_layout = QFormLayout()
        
        self.spin_session_timeout = QSpinBox()
        self.spin_session_timeout.setRange(5, 480)
        self.spin_session_timeout.setValue(30)
        self.spin_session_timeout.setSuffix(" minutos")
        security_layout.addRow("Timeout sesión:", self.spin_session_timeout)
        
        self.spin_max_login_attempts = QSpinBox()
        self.spin_max_login_attempts.setRange(1, 10)
        self.spin_max_login_attempts.setValue(3)
        security_layout.addRow("Máx. intentos login:", self.spin_max_login_attempts)
        
        self.check_audit_all = QCheckBox("Auditar todas las acciones")
        security_layout.addRow("", self.check_audit_all)
        
        self.check_strong_passwords = QCheckBox("Requerir contraseñas fuertes")
        security_layout.addRow("", self.check_strong_passwords)
        
        security_group.setLayout(security_layout)
        layout.addRow(security_group)
        
        # Configuración de contraseñas
        password_group = QGroupBox("Política de Contraseñas")
        password_layout = QFormLayout()
        
        self.spin_min_password_length = QSpinBox()
        self.spin_min_password_length.setRange(6, 20)
        self.spin_min_password_length.setValue(8)
        self.spin_min_password_length.setSuffix(" caracteres")
        password_layout.addRow("Longitud mínima:", self.spin_min_password_length)
        
        self.spin_password_expiry = QSpinBox()
        self.spin_password_expiry.setRange(0, 365)
        self.spin_password_expiry.setValue(90)
        self.spin_password_expiry.setSuffix(" días (0=sin expiración)")
        password_layout.addRow("Expiración:", self.spin_password_expiry)
        
        self.check_require_special = QCheckBox("Requerir caracteres especiales")
        password_layout.addRow("", self.check_require_special)
        
        password_group.setLayout(password_layout)
        layout.addRow(password_group)
        
        tab.setLayout(layout)
        return tab
    
    def crear_tab_backup(self) -> QWidget:
        """Crea la tab de configuración de backup"""
        tab = QWidget()
        layout = QFormLayout()
        
        # Configuración de backup automático
        backup_group = QGroupBox("Backup Automático")
        backup_layout = QFormLayout()
        
        self.check_auto_backup = QCheckBox("Hacer backup automático")
        backup_layout.addRow("", self.check_auto_backup)
        
        self.combo_backup_frequency = QComboBox()
        self.combo_backup_frequency.addItems(["Diario", "Semanal", "Mensual"])
        backup_layout.addRow("Frecuencia:", self.combo_backup_frequency)
        
        self.spin_keep_backups = QSpinBox()
        self.spin_keep_backups.setRange(1, 100)
        self.spin_keep_backups.setValue(30)
        self.spin_keep_backups.setSuffix(" backups")
        backup_layout.addRow("Conservar:", self.spin_keep_backups)
        
        backup_group.setLayout(backup_layout)
        layout.addRow(backup_group)
        
        # Acciones manuales
        action_group = QGroupBox("Acciones Manuales")
        action_layout = QVBoxLayout()
        
        btn_backup_now = QPushButton("🔄 Hacer Backup Ahora")
        btn_backup_now.clicked.connect(self.hacer_backup_manual)
        btn_backup_now.setStyleSheet("background-color: #28a745; color: white; padding: 8px;")
        
        btn_restore = QPushButton("📥 Restaurar Backup")
        btn_restore.clicked.connect(self.restaurar_backup)
        btn_restore.setStyleSheet("background-color: #17a2b8; color: white; padding: 8px;")
        
        btn_clean_old = QPushButton("🧹 Limpiar Backups Antiguos")
        btn_clean_old.clicked.connect(self.limpiar_backups_antiguos)
        btn_clean_old.setStyleSheet("background-color: #ffc107; color: black; padding: 8px;")
        
        action_layout.addWidget(btn_backup_now)
        action_layout.addWidget(btn_restore)
        action_layout.addWidget(btn_clean_old)
        
        action_group.setLayout(action_layout)
        layout.addRow(action_group)
        
        tab.setLayout(layout)
        return tab
    
    def seleccionar_directorio(self, line_edit: QLineEdit):
        """Abre diálogo para seleccionar directorio"""
        directorio = QFileDialog.getExistingDirectory(self, "Seleccionar Directorio")
        if directorio:
            line_edit.setText(directorio)
    
    def cargar_configuraciones(self):
        """Carga las configuraciones desde la base de datos"""
        db = SessionLocal()
        try:
            configs = db.query(ConfiguracionSistema).all()
            for config in configs:
                self.configuraciones[config.clave] = config.valor
            
            # Aplicar configuraciones a los campos
            self.aplicar_configuraciones()
            
        finally:
            db.close()
    
    def aplicar_configuraciones(self):
        """Aplica las configuraciones cargadas a los campos"""
        # Base de datos
        self.txt_db_host.setText(self.configuraciones.get('db_host', 'localhost'))
        self.txt_db_puerto.setText(self.configuraciones.get('db_port', '5432'))
        self.txt_db_nombre.setText(self.configuraciones.get('db_name', 'correspondencia_db'))
        self.txt_db_usuario.setText(self.configuraciones.get('db_user', 'postgres'))
        
        # Rutas
        self.txt_ruta_pdfs.setText(self.configuraciones.get('ruta_pdfs', 'C:/temp/documentos/'))
        self.txt_ruta_logs.setText(self.configuraciones.get('ruta_logs', 'C:/temp/logs/'))
        self.txt_ruta_backup.setText(self.configuraciones.get('ruta_backup', 'C:/temp/backup/'))
    
    def guardar_configuracion(self):
        """Guarda la configuración en la base de datos"""
        db = SessionLocal()
        try:
            # Recopilar configuraciones de los campos
            nuevas_configs = {
                'db_host': self.txt_db_host.text(),
                'db_port': self.txt_db_puerto.text(),
                'db_name': self.txt_db_nombre.text(),
                'db_user': self.txt_db_usuario.text(),
                'ruta_pdfs': self.txt_ruta_pdfs.text(),
                'ruta_logs': self.txt_ruta_logs.text(),
                'ruta_backup': self.txt_ruta_backup.text(),
            }
            
            # Guardar en base de datos
            for clave, valor in nuevas_configs.items():
                config = db.query(ConfiguracionSistema).filter(ConfiguracionSistema.clave == clave).first()
                if config:
                    config.valor = valor
                else:
                    config = ConfiguracionSistema(
                        clave=clave,
                        valor=valor,
                        tipo='string',
                        descripcion=f'Configuración de {clave}',
                        editable=True
                    )
                    db.add(config)
            
            db.commit()
            QMessageBox.information(self, "Éxito", "Configuración guardada correctamente")
            self.configuracion_guardada.emit()
            
        except Exception as e:
            db.rollback()
            QMessageBox.critical(self, "Error", f"Error guardando configuración: {str(e)}")
        finally:
            db.close()
    
    def restaurar_valores_defecto(self):
        """Restaura los valores por defecto"""
        reply = QMessageBox.question(
            self, "Confirmar",
            "¿Está seguro de restaurar los valores por defecto?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # Restaurar valores por defecto en la UI
            self.txt_db_host.setText("localhost")
            self.txt_db_puerto.setText("5432")
            self.txt_db_nombre.setText("correspondencia_db")
            self.txt_db_usuario.setText("postgres")
            self.txt_db_password.setText("")
            
            QMessageBox.information(self, "Éxito", "Valores por defecto restaurados")
    
    def probar_configuracion(self):
        """Prueba la configuración actual"""
        QMessageBox.information(self, "Prueba", "Probando configuración...")
        # Aquí irían pruebas reales de conexión a BD, rutas, etc.
    
    def hacer_backup_manual(self):
        """Realiza backup manual"""
        QMessageBox.information(self, "Backup", "Iniciando backup manual...")
        # Aquí iría la implementación real de backup
    
    def restaurar_backup(self):
        """Restaura desde backup"""
        QMessageBox.information(self, "Restaurar", "Iniciando restauración...")
        # Aquí iría la implementación real de restauración
    
    def limpiar_backups_antiguos(self):
        """Limpia backups antiguos"""
        QMessageBox.information(self, "Limpieza", "Limpiando backups antiguos...")
        # Aquí iría la implementación real de limpieza