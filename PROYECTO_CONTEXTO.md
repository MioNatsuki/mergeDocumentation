# SISTEMA DE CORRESPONDENCIA - CONTEXTO

## 📌 ESTADO ACTUAL (Semana 3-4)
- ✅ **Semana 1-2 COMPLETADA**: Core, Auth, Base de datos, Login
- ✅ **Semana 3-4 PARCIAL**: Dashboards proyectos, Navegación básica
- 🚧 **PENDIENTE**: Formularios completos, Gestión plantillas, Generación PDF

## 🏗️ ARQUITECTURA TÉCNICA
Tipo: Standalone Desktop App
Lenguaje: Python
Interfaz: PyQt6
Base de datos: PostgreSQL
ORM: SQLAlchemy
Motor PDF: ReportLab + pdfrw

## 📁 ESTRUCTURA ACTUAL
correspondencia_app/
├── main.py
├── config/ (database.py, settings.py)
├── core/ (models.py, auth.py, project_service.py)
├── ui/
│ ├── login_window.py
│ ├── main_window.py
│ ├── modules/
│ │ ├── proyectos/ (dashboard_proyectos.py, formulario_proyecto.py)
│ │ └── plantillas/ (dashboard_plantillas.py)
│ └── components/ (project_card.py)
├── utils/ (logger.py, security.py)
└── database/ (init_db.py, reset_database.py)

## 👥 ROLES Y MÓDULOS IMPLEMENTADOS

### SuperAdmin
- Login ✓
- Dashboard proyectos (todos) ✓
- CRUD proyectos ✓
- Navegación a plantillas ✓

### Admin  
- Login ✓
- Dashboard proyectos (solo sus proyectos) ✓
- CRUD proyectos ✓
- Navegación a plantillas ✓

### Lector
- Login ✓
- Dashboard proyectos (solo sus proyectos) ✓
- Navegación a plantillas ✓

## 🗃️ BASE DE DATOS
```sql
-- Tablas principales implementadas:
usuarios, proyectos, plantillas, bitacora
-- Tablas pendientes: 
emisiones_temp, emisiones_final, configuracion_sistema

# .env
DB_HOST=localhost
DB_PORT=5432
DB_NAME=mergeDocumentation
DB_USER=postgres
DB_PASSWORD=root

# Credenciales por defecto
Usuario: superadmin
Contraseña: admin123


### **2. SCRIPT DE "CONTINUACIÓN"**

Crea **`continuar_proyecto.py`**:

```python
"""
SCRIPT DE INICIO PARA CONTINUAR EL PROYECTO
Ejecutar y pegar el output en la nueva conversación
"""

import os
import sys

def mostrar_estado():
    print("🚀 SISTEMA DE CORRESPONDENCIA - ESTADO ACTUAL")
    print("=" * 60)
    
    # Verificar estructura
    estructura = {
        "main.py": os.path.exists("main.py"),
        "config/": os.path.exists("config"),
        "core/": os.path.exists("core"), 
        "ui/modules/": os.path.exists("ui/modules"),
        "database/": os.path.exists("database")
    }
    
    print("📁 ESTRUCTURA DEL PROYECTO:")
    for archivo, existe in estructura.items():
        status = "✅" if existe else "❌"
        print(f"   {status} {archivo}")
    
    print("\n🎯 MÓDULOS IMPLEMENTADOS:")
    modulos = [
        "✅ Autenticación y roles",
        "✅ Gestión de proyectos", 
        "✅ Dashboard proyectos",
        "✅ Navegación proyectos → plantillas",
        "🚧 Editor de plantillas",
        "🚧 Procesamiento CSV",
        "🚧 Generación PDF"
    ]
    
    for modulo in modulos:
        print(f"   {modulo}")
    
    print("\n📋 PARA CONTINUAR, COPIAR ESTE MENSAJE EN NUEVA CONVERSACIÓN:")
    print("=" * 60)

if __name__ == "__main__":
    mostrar_estado()


## 🔄 CONTINUACIÓN PROYECTO SISTEMA DE CORRESPONDENCIA

**Contexto del proyecto anterior:**
- Aplicación desktop Python/PyQt6 para generación masiva de documentos
- Sistema de correspondencia con roles (superadmin, admin, lector)
- Base: PostgreSQL + SQLAlchemy + Autenticación bcrypt
- Estado: Semana 3-4 completada (Core, Auth, Dashboards proyectos)

**Lo que funciona:**
✅ Login con roles y auditoría
✅ Dashboard de proyectos con tarjetas interactivas  
✅ CRUD proyectos (crear, editar, eliminar)
✅ Navegación proyectos → plantillas
✅ Base de datos con modelos esenciales

**Próximos pasos pendientes:**
1. Completar gestión de plantillas (editor visual con coordenadas)
2. Implementar carga y validación de CSV
3. Sistema de generación de PDFs
4. Módulo de emisiones y acumulados

**Stack técnico:**
Python 3.11+, PyQt6, PostgreSQL, SQLAlchemy, ReportLab, bcrypt

**Estructura actual del proyecto:**
(mencionar la estructura de carpetas clave)

¿Podemos continuar desde aquí con el módulo de gestión de plantillas?