from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QPushButton, QMessageBox, QFrame)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QPixmap
from config.database import SessionLocal
from core.auth import AuthService

class LoginWindow(QWidget):
    login_successful = pyqtSignal(object)  # Emite el usuario autenticado
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Sistema de Correspondencia - Login")
        self.setFixedSize(400, 500)
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(20)
        
        # Logo/Header
        header = QLabel("Sistema de Correspondencia")
        header.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Form frame
        form_frame = QFrame()
        form_frame.setFrameStyle(QFrame.Shape.StyledPanel)
        form_layout = QVBoxLayout()
        form_layout.setSpacing(15)
        
        # Usuario
        lbl_usuario = QLabel("Usuario:")
        self.txt_usuario = QLineEdit()
        self.txt_usuario.setPlaceholderText("Ingrese su usuario")
        
        # Contraseña
        lbl_password = QLabel("Contraseña:")
        self.txt_password = QLineEdit()
        self.txt_password.setPlaceholderText("Ingrese su contraseña")
        self.txt_password.setEchoMode(QLineEdit.EchoMode.Password)
        
        # Botón
        self.btn_login = QPushButton("Iniciar Sesión")
        self.btn_login.clicked.connect(self.attempt_login)
        
        # Agregar al form
        form_layout.addWidget(lbl_usuario)
        form_layout.addWidget(self.txt_usuario)
        form_layout.addWidget(lbl_password)
        form_layout.addWidget(self.txt_password)
        form_layout.addWidget(self.btn_login)
        
        form_frame.setLayout(form_layout)
        
        # Agregar al layout principal
        layout.addWidget(header)
        layout.addWidget(form_frame)
        
        self.setLayout(layout)
        
        # Enter para login
        self.txt_password.returnPressed.connect(self.attempt_login)
    
    def attempt_login(self):
        usuario = self.txt_usuario.text().strip()
        password = self.txt_password.text()
        
        if not usuario or not password:
            QMessageBox.warning(self, "Error", "Por favor complete todos los campos")
            return
        
        self.btn_login.setEnabled(False)
        self.btn_login.setText("Verificando...")
        
        try:
            db = SessionLocal()
            auth_service = AuthService(db)
            
            user, mensaje = auth_service.autenticar_usuario(
                usuario, password,
                ip_address="localhost",  # En producción obtener IP real
                user_agent="PyQt App"
            )
            
            if user:
                self.login_successful.emit(user)
            else:
                QMessageBox.critical(self, "Error de autenticación", mensaje)
                self.txt_password.clear()
                self.txt_password.setFocus()
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error de conexión: {str(e)}")
        finally:
            db.close()
            self.btn_login.setEnabled(True)
            self.btn_login.setText("Iniciar Sesión")