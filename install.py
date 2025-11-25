import subprocess
import sys
import os

def install_requirements():
    """Instala los requirements del proyecto"""
    print("Instalando dependencias...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Dependencias instaladas correctamente")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error instalando dependencias: {e}")
        sys.exit(1)

def setup_database():
    """Configura la base de datos"""
    print("\nConfigurando base de datos...")
    try:
        from database.init_db import init_database
        init_database()
    except Exception as e:
        print(f"❌ Error configurando base de datos: {e}")
        print("   Asegúrate de que PostgreSQL esté ejecutándose")
        sys.exit(1)

if __name__ == "__main__":
    print("🚀 Instalador del Sistema de Correspondencia")
    print("=" * 50)
    
    install_requirements()
    setup_database()
    
    print("\n🎉 Instalación completada!")
    print("\n📝 Próximos pasos:")
    print("1. Verifica que el archivo .env tenga la configuración correcta de PostgreSQL")
    print("2. Ejecuta: python main.py")
    print("3. Usa usuario: 'superadmin' y contraseña: 'admin123'")