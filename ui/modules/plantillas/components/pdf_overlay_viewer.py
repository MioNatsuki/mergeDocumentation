class PDFOverlayViewer(QWidget):
    """
    Visor de PDF con overlay interactivo que muestra:
    - Campos detectados automáticamente
    - Rectángulos en las coordenadas encontradas
    - Permitir ajuste manual arrastrando
    """
    
    def __init__(self):
        super().__init__()
        self.pdf_pixmap = None
        self.campos = []
        self.campo_seleccionado = None
        self.escala = 1.0
        
    def cargar_pdf(self, pdf_path: str):
        """Cargar PDF y renderizar"""
        doc = fitz.open(pdf_path)
        page = doc[0]
        pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
        
        # Convertir a QPixmap
        img = QImage(pix.samples, pix.width, pix.height, 
                    pix.stride, QImage.Format.Format_RGB888)
        self.pdf_pixmap = QPixmap.fromImage(img)
        
        # Calcular escala (pixels a mm)
        self.escala = pix.width / 215.9  # Ancho OFICIO en mm
        
        self.update()
    
    def dibujar_campos(self, campos: List[Dict]):
        """Dibujar rectángulos sobre campos detectados"""
        self.campos = campos
        self.update()
    
    def paintEvent(self, event):
        """Dibujar PDF y overlay de campos"""
        painter = QPainter(self)
        
        # Dibujar PDF
        if self.pdf_pixmap:
            painter.drawPixmap(0, 0, self.pdf_pixmap)
        
        # Dibujar campos detectados
        for campo in self.campos:
            if campo.get('coordenadas_pdf'):
                coord = campo['coordenadas_pdf']
                
                # Convertir mm a pixels
                x = coord['x_mm'] * self.escala
                y = coord['y_mm'] * self.escala
                ancho = coord.get('ancho_mm', 50) * self.escala
                alto = coord.get('alto_mm', 10) * self.escala
                
                # Dibujar rectángulo
                painter.setPen(QPen(QColor(255, 0, 0), 2))
                painter.setBrush(QBrush(QColor(255, 0, 0, 30)))
                painter.drawRect(int(x), int(y), int(ancho), int(alto))
                
                # Etiqueta con nombre
                painter.setPen(QColor(0, 0, 0))
                painter.drawText(int(x), int(y) - 5, campo['placeholder'])