# test_authentication_fixed.py
from databasemanager import DatabaseManager
from authentication import AuthenticationManager

class AuthenticationTesterFixed:
    """Probador del sistema de autenticación - VERSIÓN CORREGIDA"""
    
    def __init__(self):
        self.db = DatabaseManager()
        self.auth = AuthenticationManager(self.db)
    
    def run_complete_test(self):
        """Ejecutar suite completa de pruebas"""
        print("🧪 INICIANDO PRUEBAS DE AUTENTICACIÓN CORREGIDAS\n")
        
        # Conectar a BD
        if not self.db.connect():
            print("❌ No se pudo conectar a la base de datos")
            return
        
        # 1. Prueba de login exitoso
        print("1. Probando login exitoso...")
        success, user, message = self.auth.login("sistemas", "super123")
        print(f"   Resultado: {success} - {message}")
        if success:
            print(f"   Usuario: {user['nombre']} - Rol: {user['rol']}")
        
        # 2. Verificar autenticación
        print("\n2. Verificando autenticación...")
        print(f"   Autenticado: {self.auth.is_authenticated()}")
        if self.auth.current_user:
            print(f"   Info usuario: {self.auth.current_user['nombre']}")
        
        # 3. Prueba de login fallido (debería funcionar ahora)
        print("\n3. Probando login fallido...")
        success, user, message = self.auth.login("admin", "password_incorrecto")
        print(f"   Resultado: {success} - {message}")
        
        # 4. Prueba de logout
        print("\n4. Probando logout...")
        if self.auth.is_authenticated():
            logout_success = self.auth.logout()
            print(f"   Logout exitoso: {logout_success}")
        else:
            print("   No hay usuario autenticado para hacer logout")
        
        print(f"   Autenticado después de logout: {self.auth.is_authenticated()}")
        
        self.db.disconnect()
        print("\n🎉 PRUEBAS DE AUTENTICACIÓN COMPLETADAS")

if __name__ == "__main__":
    # Ejecutar en este orden:
    print("\n🔧 PASO 2: Ejecutar pruebas corregidas")
    tester = AuthenticationTesterFixed()
    tester.run_complete_test()