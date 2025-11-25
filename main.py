import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer
from ui.login_window import LoginWindow
from ui.main_window import MainWindow
from config.database import engine, Base

def create_tables():
    """Crea las tablas en la base de datos"""
    Base.metadata.create_all(bind=engine)

class AppController:
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.login_window = LoginWindow()
        self.main_window = None
        
        # Conectar señales
        self.login_window.login_successful.connect(self.on_login_success)
    
    def on_login_success(self, usuario):
        self.login_window.hide()
        self.main_window = MainWindow(usuario)
        self.main_window.show()
        
        # Si se cierra la ventana principal, cerrar app
        self.main_window.destroyed.connect(self.app.quit)
    
    def run(self):
        self.login_window.show()
        return self.app.exec()

if __name__ == "__main__":
    # Crear tablas si no existen
    create_tables()
    
    # Iniciar aplicación
    controller = AppController()
    sys.exit(controller.run())