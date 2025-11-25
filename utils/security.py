import bcrypt
import re

def validar_fortaleza_password(password):
    """
    Valida que la contraseña cumpla con requisitos mínimos de seguridad
    """
    if len(password) < 8:
        return False, "La contraseña debe tener al menos 8 caracteres"
    
    if not re.search(r"[A-Z]", password):
        return False, "La contraseña debe tener al menos una mayúscula"
    
    if not re.search(r"[a-z]", password):
        return False, "La contraseña debe tener al menos una minúscula"
    
    if not re.search(r"\d", password):
        return False, "La contraseña debe tener al menos un número"
    
    return True, "Contraseña válida"

def generar_hash_password(password):
    """Genera hash seguro de contraseña"""
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def verificar_password(password, password_hash):
    """Verifica si la contraseña coincide con el hash"""
    return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))