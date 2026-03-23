import os
import pytesseract
from pdf2image import convert_from_path
from pdf2image.exceptions import PDFInfoNotInstalledError

# Configurar Tesseract según entorno
if os.name == "nt":  # Windows (local)
    pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
else:  # Linux (Railway)
    pytesseract.pytesseract.tesseract_cmd = "/usr/bin/tesseract"


def extraer_texto_de_imagen(imagen, idioma="spa"):
    return pytesseract.image_to_string(imagen, lang=idioma)


def extraer_texto_de_pdf(ruta_pdf, idioma="spa"):
    try:
        paginas = convert_from_path(ruta_pdf) 
    except PDFInfoNotInstalledError:
        import pypdfium2 as pdfium

        pdf = pdfium.PdfDocument(ruta_pdf)
        scale = 300 / 72
        paginas = [pdf[i].render(scale=scale).to_pil() for i in range(len(pdf))]

    texto_completo = ""

    for i, pagina in enumerate(paginas, start=1):
        texto_pagina = extraer_texto_de_imagen(pagina, idioma)
        texto_completo += f"\n--- Pagina {i} ---\n{texto_pagina}"

    return texto_completo