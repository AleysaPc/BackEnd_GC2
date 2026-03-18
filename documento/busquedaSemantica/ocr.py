import os

import pytesseract
from pdf2image import convert_from_path
from pdf2image.exceptions import PDFInfoNotInstalledError
import pytesseract

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"


def extraer_texto_de_imagen(imagen, idioma="spa"):
    """
    Extrae texto de una imagen usando Tesseract OCR.
    """
    return pytesseract.image_to_string(imagen, lang=idioma)


def extraer_texto_de_pdf(ruta_pdf, idioma="spa"):
    """
    Convierte un PDF en imagenes y extrae el texto de cada pagina.
    """
    poppler_path = os.getenv("POPPLER_PATH")
    try:
        paginas = convert_from_path(ruta_pdf, poppler_path=poppler_path)
    except PDFInfoNotInstalledError:
        # Fallback para entornos donde pdfinfo/poppler no esta instalado.
        import pypdfium2 as pdfium

        pdf = pdfium.PdfDocument(ruta_pdf)
        scale = 300 / 72
        paginas = [pdf[i].render(scale=scale).to_pil() for i in range(len(pdf))]

    texto_completo = ""

    for i, pagina in enumerate(paginas, start=1):
        texto_pagina = extraer_texto_de_imagen(pagina, idioma)
        texto_completo += f"\n--- Pagina {i} ---\n{texto_pagina}"

    return texto_completo
