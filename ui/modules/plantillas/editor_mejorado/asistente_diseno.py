# ui/modules/plantillas/editor_mejorado/asistente_diseno.py
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QFrame, QMessageBox, QProgressBar,
                             QGroupBox, QListWidget, QListWidgetItem,
                             QCheckBox, QFileDialog, QWizard, QWizardPage,
                             QLineEdit, QComboBox)
from PyQt6.QtCore import Qt, pyqtSignal, QThread
from PyQt6.QtGui import QFont, QColor
import os
import PyPDF2
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
import tempfile

from ui.modules.plantillas.dashboard_mejorado import DashboardPlantillasMejorado

class AnalizadorPDFThread(QThread):
    """Hilo para análisis de PDF en segundo plano"""
    analisis_completado = pyqtSignal(list)  # Lista de campos detectados
    progreso = pyqtSignal(int, str)
    error = pyqtSignal(str)
    
    def __init__(self, pdf_path):
        super().__init__()
        self.pdf_path = pdf_path
    
    def run(self):
        try:
            self.progreso.emit(10, "Abriendo PDF...")
            
            campos_detectados = self.analizar_pdf(self.pdf_path)
            
            self.progreso.emit(100, "Análisis completado")
            self.analisis_completado.emit(campos_detectados)
            
        except Exception as e:
            self.error.emit(f"Error analizando PDF: {str(e)}")
    
    def analizar_pdf(self, pdf_path):
        """Analiza PDF para detectar campos vacíos/etiquetas"""
        campos = []
        
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            
            # Método 1: Buscar líneas con guiones o espacios (campos vacíos)
            for page_num in range(len(reader.pages)):
                page = reader.pages[page_num]
                texto = page.extract_text()
                
                if texto:
                    lineas = texto.split('\n')
                    
                    for i, linea in enumerate(lineas):
                        linea = linea.strip()
                        
                        # Detectar etiquetas comunes
                        if any(palabra in linea.lower() for palabra in [
                            'nombre', 'cuenta', 'fecha', 'monto', 'direccion',
                            'telefono', 'email', 'codigo', 'referencia'
                        ]):
                            # Buscar campo vacío en línea siguiente
                            if i + 1 < len(lineas):
                                siguiente = lineas[i + 1].strip()
                                if self.es_campo_vacio(siguiente):
                                    campos.append({
                                        'etiqueta': linea,
                                        'tipo': self.inferir_tipo(linea),
                                        'posicion': 'aproximada',  # Necesitaríamos coordenadas
                                        'sugerencia': self.generar_sugerencia(linea)
                                    })
        
        # Si no se detectaron campos, crear sugerencias genéricas
        if not campos:
            campos = self.sugerencias_genericas()
        
        return campos
    
    def es_campo_vacio(self, texto):
        """Determina si un texto parece un campo vacío"""
        vacios = ['______', '_________', '____________', 
                  '__________', '______________', 
                  '________________', '____________________']
        
        return (len(texto) > 5 and 
                all(c in '_.- ' for c in texto) or
                texto in vacios)
    
    def inferir_tipo(self, etiqueta):
        """Infiere tipo de campo basado en etiqueta"""
        etiqueta_lower = etiqueta.lower()
        
        if any(palabra in etiqueta_lower for palabra in ['nombre', 'apellido']):
            return 'texto'
        elif any(palabra in etiqueta_lower for palabra in ['cuenta', 'codigo', 'referencia', 'folio']):
            return 'codigo'
        elif any(palabra in etiqueta_lower for palabra in ['monto', 'total', 'saldo', 'importe', 'cantidad']):
            return 'moneda'
        elif any(palabra in etiqueta_lower for palabra in ['fecha']):
            return 'fecha'
        elif any(palabra in etiqueta_lower for palabra in ['direccion', 'domicilio', 'colonia', 'ciudad']):
            return 'direccion'
        elif any(palabra in etiqueta_lower for palabra in ['telefono', 'celular', 'contacto']):
            return 'telefono'
        elif any(palabra in etiqueta_lower for palabra in ['email', 'correo']):
            return 'email'
        else:
            return 'texto'
    
    def generar_sugerencia(self, etiqueta):
        """Genera sugerencia de mapeo a columna de padrón"""
        etiqueta_lower = etiqueta.lower().replace(':', '').replace('.', '')
        
        mapeos = {
            'nombre': 'nombre',
            'cuenta': 'cuenta',
            'codigo afiliado': 'codigo_afiliado',
            'codigo': 'codigo_afiliado',
            'folio': 'cuenta',
            'monto': 'adeudo',
            'total': 'adeudo',
            'saldo': 'adeudo',
            'importe': 'adeudo',
            'fecha': 'fecha_actual',  # Campo especial
            'direccion': 'afiliado_direccion',
            'domicilio': 'afiliado_direccion',
            'telefono': 'afiliado_telefono',
            'celular': 'afiliado_celular',
            'email': 'email',  # Podría no existir
            'rfc': 'rfc'
        }
        
        for key, value in mapeos.items():
            if key in etiqueta_lower:
                return value
        
        # Convertir a snake_case
        return etiqueta_lower.replace(' ', '_')
    
    def sugerencias_genericas(self):
        """Sugerencias cuando no se detectan campos automáticamente"""
        return [
            {
                'etiqueta': 'Nombre del Afiliado',
                'tipo': 'texto',
                'posicion': 'sugerida',
                'sugerencia': 'nombre'
            },
            {
                'etiqueta': 'Número de Cuenta',
                'tipo': 'codigo',
                'posicion': 'sugerida',
                'sugerencia': 'cuenta'
            },
            {
                'etiqueta': 'Monto Adeudado',
                'tipo': 'moneda',
                'posicion': 'sugerida',
                'sugerencia': 'adeudo'
            },
            {
                'etiqueta': 'Fecha Actual',
                'tipo': 'fecha',
                'posicion': 'sugerida',
                'sugerencia': 'fecha_actual'
            },
            {
                'etiqueta': 'Código de Barras',
                'tipo': 'codigo_barras',
                'posicion': 'sugerida',
                'sugerencia': 'codigo_barras'
            }
        ]

class AsistenteDiseno(QWidget):
    """Asistente paso a paso para crear plantillas"""
    
    plantilla_creada = pyqtSignal()
    
    def __init__(self, usuario, proyecto_id, stacked_widget):
        super().__init__()
        self.usuario = usuario
        self.proyecto_id = proyecto_id
        self.stacked_widget = stacked_widget
        self.pdf_path = None
        self.campos_detectados = []
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Wizard-like interface
        self.pagina_actual = 0
        self.paginas = []
        
        # Página 1: Subir PDF
        pagina1 = self.crear_pagina_subida()
        self.paginas.append(pagina1)
        
        # Página 2: Revisar campos detectados
        pagina2 = self.crear_pagina_revision()
        self.paginas.append(pagina2)
        
        # Página 3: Configuración básica
        pagina3 = self.crear_pagina_configuracion()
        self.paginas.append(pagina3)
        
        # Agregar primera página
        layout.addWidget(pagina1)
        
        # Navegación
        self.nav_frame = QFrame()
        self.nav_frame.setStyleSheet("""
            QFrame {
                background-color: #F5F5F5;
                border-top: 1px solid #E0E0E0;
                padding: 15px;
            }
        """)
        
        nav_layout = QHBoxLayout()
        
        self.btn_atras = QPushButton("← Atrás")
        self.btn_atras.clicked.connect(self.pagina_anterior)
        self.btn_atras.setEnabled(False)
        
        self.btn_siguiente = QPushButton("Siguiente →")
        self.btn_siguiente.clicked.connect(self.pagina_siguiente)
        
        self.btn_cancelar = QPushButton("Cancelar")
        self.btn_cancelar.clicked.connect(self.cancelar)
        
        nav_layout.addWidget(self.btn_atras)
        nav_layout.addStretch()
        nav_layout.addWidget(self.btn_cancelar)
        nav_layout.addWidget(self.btn_siguiente)
        
        self.nav_frame.setLayout(nav_layout)
        layout.addWidget(self.nav_frame)
        
        self.setLayout(layout)
    
    def crear_pagina_subida(self):
        """Página para subir PDF"""
        pagina = QFrame()
        pagina.setStyleSheet("""
            QFrame {
                background-color: white;
                padding: 40px;
            }
        """)
        
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(30)
        
        # Icono y título
        lbl_icono = QLabel("📄")
        lbl_icono.setFont(QFont("Arial", 48))
        lbl_icono.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        lbl_titulo = QLabel("Sube tu documento PDF")
        lbl_titulo.setFont(QFont("Arial", 20, QFont.Weight.Bold))
        lbl_titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        lbl_subtitulo = QLabel("El sistema analizará automáticamente campos para llenar")
        lbl_subtitulo.setStyleSheet("color: #666; font-size: 14px;")
        lbl_subtitulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Área de drop
        drop_frame = QFrame()
        drop_frame.setFixedSize(400, 250)
        drop_frame.setStyleSheet("""
            QFrame {
                background-color: #F8F9FA;
                border: 3px dashed #99b898;
                border-radius: 15px;
            }
            QFrame:hover {
                border-color: #2196F3;
                background-color: #F0F8FF;
            }
        """)
        
        drop_layout = QVBoxLayout()
        drop_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        lbl_drop_icon = QLabel("📁")
        lbl_drop_icon.setFont(QFont("Arial", 32))
        
        lbl_drop_text = QLabel("Arrastra tu PDF aquí")
        lbl_drop_text.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        
        lbl_drop_sub = QLabel("o haz clic para seleccionar")
        lbl_drop_sub.setStyleSheet("color: #666;")
        
        self.lbl_archivo = QLabel("")
        self.lbl_archivo.setStyleSheet("color: #4CAF50; font-weight: bold;")
        
        drop_layout.addWidget(lbl_drop_icon)
        drop_layout.addWidget(lbl_drop_text)
        drop_layout.addWidget(lbl_drop_sub)
        drop_layout.addWidget(self.lbl_archivo)
        drop_frame.setLayout(drop_layout)
        
        # Hacer clickeable
        drop_frame.mousePressEvent = self.seleccionar_pdf
        
        # Botón manual
        btn_seleccionar = QPushButton("Seleccionar archivo PDF")
        btn_seleccionar.clicked.connect(self.seleccionar_pdf)
        btn_seleccionar.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                padding: 12px 24px;
                border-radius: 8px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)
        
        layout.addWidget(lbl_icono)
        layout.addWidget(lbl_titulo)
        layout.addWidget(lbl_subtitulo)
        layout.addWidget(drop_frame)
        layout.addWidget(btn_seleccionar)
        
        pagina.setLayout(layout)
        return pagina
    
    def crear_pagina_revision(self):
        """Página para revisar campos detectados"""
        pagina = QFrame()
        pagina.setStyleSheet("""
            QFrame {
                background-color: white;
                padding: 30px;
            }
        """)
        
        layout = QVBoxLayout()
        layout.setSpacing(20)
        
        # Título
        lbl_titulo = QLabel("📋 Campos detectados en tu PDF")
        lbl_titulo.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        
        lbl_subtitulo = QLabel("Revisa y ajusta los campos que el sistema identificó")
        lbl_subtitulo.setStyleSheet("color: #666;")
        
        # Área de progreso (oculta inicialmente)
        self.progress_revision = QProgressBar()
        self.progress_revision.setVisible(False)
        
        # Lista de campos
        self.lista_campos = QListWidget()
        self.lista_campos.setStyleSheet("""
            QListWidget {
                border: 2px solid #E0E0E0;
                border-radius: 8px;
                padding: 10px;
                background-color: #FAFAFA;
            }
            QListWidget::item {
                padding: 15px;
                border-bottom: 1px solid #EEE;
            }
            QListWidget::item:selected {
                background-color: #E3F2FD;
                border-left: 4px solid #2196F3;
            }
        """)
        
        # Botones de acción
        btn_frame = QFrame()
        btn_layout = QHBoxLayout()
        
        self.btn_agregar_campo = QPushButton("➕ Agregar campo manual")
        self.btn_agregar_campo.clicked.connect(self.agregar_campo_manual)
        
        self.btn_eliminar_campo = QPushButton("🗑️ Eliminar seleccionado")
        self.btn_eliminar_campo.clicked.connect(self.eliminar_campo_seleccionado)
        
        btn_layout.addWidget(self.btn_agregar_campo)
        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_eliminar_campo)
        btn_frame.setLayout(btn_layout)
        
        layout.addWidget(lbl_titulo)
        layout.addWidget(lbl_subtitulo)
        layout.addWidget(self.progress_revision)
        layout.addWidget(self.lista_campos)
        layout.addWidget(btn_frame)
        
        pagina.setLayout(layout)
        return pagina
    
    def crear_pagina_configuracion(self):
        """Página para configurar nombre y tipo de plantilla"""
        pagina = QFrame()
        
        layout = QVBoxLayout()
        layout.setSpacing(25)
        layout.setContentsMargins(40, 40, 40, 40)
        
        # Título
        lbl_titulo = QLabel("⚙️ Configuración de la plantilla")
        lbl_titulo.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        
        # Formulario
        form_frame = QFrame()
        form_frame.setStyleSheet("""
            QFrame {
                background-color: #F8F9FA;
                border-radius: 10px;
                padding: 25px;
            }
        """)
        
        form_layout = QVBoxLayout()
        form_layout.setSpacing(20)
        
        # Nombre
        lbl_nombre = QLabel("Nombre de la plantilla *")
        lbl_nombre.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        
        self.txt_nombre = QLineEdit()
        self.txt_nombre.setPlaceholderText("Ej: Carta de Cobranza - Pensiones")
        self.txt_nombre.setStyleSheet("""
            QLineEdit {
                padding: 12px;
                border: 2px solid #E0E0E0;
                border-radius: 6px;
                font-size: 14px;
            }
            QLineEdit:focus {
                border-color: #2196F3;
            }
        """)
        
        # Descripción
        lbl_desc = QLabel("Descripción")
        lbl_desc.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        
        self.txt_desc = QLineEdit()
        self.txt_desc.setPlaceholderText("Breve descripción del propósito de esta plantilla")
        self.txt_desc.setStyleSheet(self.txt_nombre.styleSheet())
        
        # Tipo
        lbl_tipo = QLabel("Tipo de plantilla")
        lbl_tipo.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        
        self.combo_tipo = QComboBox()
        self.combo_tipo.addItems([
            "Carta",
            "Notificación", 
            "Oficio",
            "Comunicado",
            "Cobranza",
            "Otro"
        ])
        self.combo_tipo.setStyleSheet("""
            QComboBox {
                padding: 10px;
                border: 2px solid #E0E0E0;
                border-radius: 6px;
                font-size: 14px;
                background-color: white;
            }
        """)
        
        # Checkbox activa
        self.check_activa = QCheckBox("Activar plantilla inmediatamente")
        self.check_activa.setChecked(True)
        
        form_layout.addWidget(lbl_nombre)
        form_layout.addWidget(self.txt_nombre)
        form_layout.addWidget(lbl_desc)
        form_layout.addWidget(self.txt_desc)
        form_layout.addWidget(lbl_tipo)
        form_layout.addWidget(self.combo_tipo)
        form_layout.addWidget(self.check_activa)
        
        form_frame.setLayout(form_layout)
        
        layout.addWidget(lbl_titulo)
        layout.addWidget(form_frame)
        
        pagina.setLayout(layout)
        return pagina
    
    def seleccionar_pdf(self, event=None):
        """Abre diálogo para seleccionar PDF"""
        archivo, _ = QFileDialog.getOpenFileName(
            self,
            "Seleccionar archivo PDF",
            "",
            "Archivos PDF (*.pdf);;Todos los archivos (*)"
        )
        
        if archivo:
            self.pdf_path = archivo
            nombre = os.path.basename(archivo)
            self.lbl_archivo.setText(f"📄 {nombre}")
            
            # Analizar PDF en segundo plano
            self.analizar_pdf()
    
    def analizar_pdf(self):
        """Inicia análisis del PDF"""
        if not self.pdf_path:
            return
        
        # Mostrar progreso en página 2
        self.paginas[1].layout().itemAt(2).widget().setVisible(True)
        self.paginas[1].layout().itemAt(2).widget().setValue(0)
        
        # Ejecutar análisis en hilo
        self.thread_analisis = AnalizadorPDFThread(self.pdf_path)
        self.thread_analisis.analisis_completado.connect(self.on_analisis_completado)
        self.thread_analisis.progreso.connect(self.on_progreso_analisis)
        self.thread_analisis.error.connect(self.on_error_analisis)
        self.thread_analisis.start()
    
    def on_progreso_analisis(self, porcentaje, mensaje):
        """Actualiza barra de progreso"""
        self.progress_revision.setValue(porcentaje)
        self.progress_revision.setFormat(f"{mensaje}... %p%")
    
    def on_analisis_completado(self, campos):
        """Cuando se completa el análisis"""
        self.campos_detectados = campos
        self.progress_revision.setVisible(False)
        self.mostrar_campos_detectados()
    
    def on_error_analisis(self, error):
        """Maneja error en análisis"""
        self.progress_revision.setVisible(False)
        QMessageBox.warning(self, "Error en análisis", error)
        
        # Usar campos genéricos
        self.campos_detectados = AnalizadorPDFThread("").sugerencias_genericas()
        self.mostrar_campos_detectados()
    
    def mostrar_campos_detectados(self):
        """Muestra campos detectados en la lista"""
        self.lista_campos.clear()
        
        for campo in self.campos_detectados:
            item = QListWidgetItem()
            
            # Widget personalizado para cada campo
            widget = self.crear_widget_campo(campo)
            item.setSizeHint(widget.sizeHint())
            
            self.lista_campos.addItem(item)
            self.lista_campos.setItemWidget(item, widget)
    
    def crear_widget_campo(self, campo):
        """Crea widget personalizado para campo"""
        widget = QFrame()
        widget.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 6px;
                padding: 10px;
            }
            QFrame:hover {
                background-color: #F5F5F5;
            }
        """)
        
        layout = QHBoxLayout()
        
        # Icono según tipo
        iconos = {
            'texto': '📝',
            'codigo': '🔢',
            'moneda': '💰',
            'fecha': '📅',
            'direccion': '📍',
            'telefono': '📞',
            'email': '📧',
            'codigo_barras': '📊'
        }
        
        icono = iconos.get(campo['tipo'], '❓')
        lbl_icono = QLabel(icono)
        lbl_icono.setFont(QFont("Arial", 16))
        
        # Información del campo
        info_layout = QVBoxLayout()
        
        lbl_etiqueta = QLabel(campo['etiqueta'])
        lbl_etiqueta.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        
        lbl_detalles = QLabel(f"Tipo: {campo['tipo'].title()} | Sugerencia: {campo['sugerencia']}")
        lbl_detalles.setStyleSheet("color: #666; font-size: 10px;")
        
        info_layout.addWidget(lbl_etiqueta)
        info_layout.addWidget(lbl_detalles)
        
        # Checkbox para incluir
        self.check_incluir = QCheckBox("Incluir")
        self.check_incluir.setChecked(True)
        
        layout.addWidget(lbl_icono)
        layout.addLayout(info_layout)
        layout.addStretch()
        layout.addWidget(self.check_incluir)
        
        widget.setLayout(layout)
        return widget
    
    def agregar_campo_manual(self):
        """Agrega campo manualmente"""
        from PyQt6.QtWidgets import QInputDialog
        
        nombre, ok = QInputDialog.getText(
            self, 
            "Agregar campo manual",
            "Nombre del campo:"
        )
        
        if ok and nombre:
            tipo, ok2 = QInputDialog.getItem(
                self,
                "Tipo de campo",
                "Selecciona el tipo:",
                ["texto", "codigo", "moneda", "fecha", "direccion", "telefono", "email", "codigo_barras"],
                0, False
            )
            
            if ok2:
                nuevo_campo = {
                    'etiqueta': nombre,
                    'tipo': tipo,
                    'posicion': 'manual',
                    'sugerencia': nombre.lower().replace(' ', '_')
                }
                
                self.campos_detectados.append(nuevo_campo)
                self.mostrar_campos_detectados()
    
    def eliminar_campo_seleccionado(self):
        """Elimina campo seleccionado"""
        item = self.lista_campos.currentItem()
        if item:
            row = self.lista_campos.row(item)
            self.campos_detectados.pop(row)
            self.mostrar_campos_detectados()
    
    def pagina_siguiente(self):
        """Avanza a la siguiente página"""
        if self.pagina_actual == 0:
            # Validar que se subió PDF
            if not self.pdf_path:
                QMessageBox.warning(self, "PDF requerido", "Debes seleccionar un archivo PDF primero")
                return
        
        elif self.pagina_actual == 1:
            # Validar que hay campos
            if not self.campos_detectados:
                QMessageBox.warning(self, "Campos requeridos", "Debe haber al menos un campo en la plantilla")
                return
        
        elif self.pagina_actual == 2:
            # Validar y guardar plantilla
            if self.guardar_plantilla():
                self.plantilla_creada.emit()
            return
        
        # Ocultar página actual
        self.layout().itemAt(0).widget().hide()
        
        # Mostrar siguiente página
        self.pagina_actual += 1
        self.layout().insertWidget(0, self.paginas[self.pagina_actual])
        
        # Actualizar navegación
        self.btn_atras.setEnabled(self.pagina_actual > 0)
        
        if self.pagina_actual == len(self.paginas) - 1:
            self.btn_siguiente.setText("✨ Crear Plantilla")
        else:
            self.btn_siguiente.setText("Siguiente →")
    
    def pagina_anterior(self):
        """Retrocede a la página anterior"""
        if self.pagina_actual == 0:
            return
        
        # Ocultar página actual
        self.layout().itemAt(0).widget().hide()
        
        # Mostrar página anterior
        self.pagina_actual -= 1
        self.layout().insertWidget(0, self.paginas[self.pagina_actual])
        
        # Actualizar navegación
        self.btn_atras.setEnabled(self.pagina_actual > 0)
        self.btn_siguiente.setText("Siguiente →")
    
    def guardar_plantilla(self):
        """Guarda la plantilla en la base de datos"""
        # Validar nombre
        nombre = self.txt_nombre.text().strip()
        if not nombre:
            QMessageBox.warning(self, "Nombre requerido", "El nombre de la plantilla es obligatorio")
            return False
        
        # Preparar configuración JSON
        configuracion = {
            "version": "2.0",
            "pdf_base": self.pdf_path,
            "campos": {},
            "metadata": {
                "fecha_creacion": "auto",
                "usuario_creador": self.usuario.id
            }
        }
        
        # Convertir campos detectados a estructura
        for campo in self.campos_detectados:
            configuracion["campos"][campo['sugerencia']] = {
                "tipo": campo['tipo'],
                "etiqueta_original": campo['etiqueta'],
                "posicion": campo['posicion'],
                "config": {
                    "fuente": "Arial",
                    "tamano": 12,
                    "color": "#000000",
                    "alineacion": "left"
                }
            }
        
        from config.database import SessionLocal
        from core.models import Plantilla
        
        db = SessionLocal()
        try:
            plantilla = Plantilla(
                proyecto_id=self.proyecto_id,
                nombre=nombre,
                descripcion=self.txt_desc.text().strip(),
                ruta_archivo=self.pdf_path,
                tipo_plantilla=self.combo_tipo.currentText().lower(),
                campos_json=configuracion,
                activa=self.check_activa.isChecked(),
                usuario_creador=self.usuario.id,
                is_deleted=False
            )
            
            db.add(plantilla)
            db.commit()
            
            # Crear carpeta para plantilla si no existe
            plantilla_dir = f"plantillas/{plantilla.id}"
            os.makedirs(plantilla_dir, exist_ok=True)
            
            return True
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error guardando plantilla: {str(e)}")
            return False
        finally:
            db.close()
    
    def cancelar(self):
        """Cancela el asistente"""
        reply = QMessageBox.question(
            self, "Cancelar",
            "¿Está seguro de cancelar la creación de la plantilla?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            if self.stacked_widget:
                # Volver al dashboard
                for i in range(self.stacked_widget.count()):
                    widget = self.stacked_widget.widget(i)
                    if isinstance(widget, DashboardPlantillasMejorado):
                        self.stacked_widget.setCurrentWidget(widget)
                        break