from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLabel, QLineEdit, QPushButton, QFrame)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QPixmap, QPainter, QColor

class LoginWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Emisor de Documentos")
        self.setFixedSize(1280, 720)

        # Widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Layout principal horizontal
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Panel izquierdo con ilustración
        left_panel = self.create_left_panel()
        
        # Panel derecho con formulario
        right_panel = self.create_right_panel()
        
        main_layout.addWidget(left_panel, stretch=1)
        main_layout.addWidget(right_panel, stretch=1)
        
        # Estilos
        self.setStyleSheet("""
            QMainWindow {
                background-color: #F3E8E8;
            }
        """)

        pixmap = QPixmap("./monstrito.png")
        self.illustration_label.setPixmap(pixmap.scaled(400, 400, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        self.illustration_label.setStyleSheet("")
    
    def create_left_panel(self):
        """Crea el panel izquierdo con el header y la ilustración"""
        panel = QWidget()
        panel.setStyleSheet("background-color: #F3E8E8;")
        
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Header con título
        header = QWidget()
        header.setFixedHeight(80)
        header.setStyleSheet("background-color: #7D5F5F;")
        
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(40, 0, 0, 0)
        
        title = QLabel("Emisor de Documentos")
        title.setStyleSheet("color: white; font-size: 36px; font-weight: 300;")
        header_layout.addWidget(title, alignment=Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        
        layout.addWidget(header)
        
        # Área de ilustración (placeholder)
        illustration_container = QWidget()
        illustration_layout = QVBoxLayout(illustration_container)
        illustration_layout.setContentsMargins(80, 100, 80, 100)
        
        # Aquí iría tu ilustración del monstruito
        # Por ahora un placeholder
        self.illustration_label = QLabel("🖥️")
        self.illustration_label.setStyleSheet("font-size: 200px;")
        self.illustration_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        illustration_layout.addWidget(self.illustration_label)
        
        layout.addWidget(illustration_container)
        
        return panel
    
    def create_right_panel(self):
        """Crea el panel derecho con el formulario de login"""
        panel = QWidget()
        panel.setStyleSheet("background-color: #F3E8E8;")
        
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(100, 0, 100, 0)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Contenedor del formulario
        form_container = QWidget()
        form_container.setMaximumWidth(500)
        form_layout = QVBoxLayout(form_container)
        form_layout.setSpacing(20)
        
        # Título "Ingresa a tu cuenta"
        title = QLabel("Ingresa a tu cuenta")
        title.setStyleSheet("font-size: 28px; font-weight: bold; color: #000000; margin-bottom: 20px;")
        title.setAlignment(Qt.AlignmentFlag.AlignLeft)
        form_layout.addWidget(title)
        
        # Campo Usuario
        self.username_input = self.create_input_field("👤 Usuario")
        form_layout.addWidget(self.username_input)
        
        # Campo Contraseña
        self.password_input = self.create_input_field("🔒 Contraseña", is_password=True)
        form_layout.addWidget(self.password_input)
        
        # Botón Entrar
        login_button = QPushButton("Entrar")
        login_button.setFixedHeight(55)
        login_button.setCursor(Qt.CursorShape.PointingHandCursor)
        login_button.setStyleSheet("""
            QPushButton {
                background-color: #7D5F5F;
                color: white;
                font-size: 18px;
                font-weight: bold;
                border: none;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #6B4F4F;
            }
            QPushButton:pressed {
                background-color: #5A4040;
            }
        """)
        login_button.clicked.connect(self.handle_login)
        form_layout.addWidget(login_button)
        
        layout.addWidget(form_container)
        
        return panel
    
    def create_input_field(self, placeholder, is_password=False):
        """Crea un campo de entrada estilizado"""
        input_field = QLineEdit()
        input_field.setPlaceholderText(placeholder)
        input_field.setFixedHeight(55)
        
        if is_password:
            input_field.setEchoMode(QLineEdit.EchoMode.Password)
        
        input_field.setStyleSheet("""
            QLineEdit {
                background-color: white;
                border: 2px solid #D0C5C0;
                border-radius: 8px;
                padding-left: 15px;
                font-size: 16px;
                color: #666666;
            }
            QLineEdit:focus {
                border: 2px solid #7D5F5F;
                outline: none;
            }
        """)
        
        return input_field
    
    def handle_login(self):
        """Maneja el evento de login"""
        username = self.username_input.text()
        password = self.password_input.text()
        
        # Aquí irá la lógica de autenticación
        print(f"Login attempt - Usuario: {username}")
        
        # TODO: Validar credenciales contra la base de datos
        # TODO: Abrir ventana principal si credenciales correctas


# Para probar la ventana
if __name__ == "__main__":
    from PyQt6.QtWidgets import QApplication
    import sys
    
    app = QApplication(sys.argv)
    window = LoginWindow()
    window.show()
    sys.exit(app.exec())