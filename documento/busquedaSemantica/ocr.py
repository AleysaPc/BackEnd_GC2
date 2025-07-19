from pdf2image import convert_from_path
from PIL import Image
import pytesseract

pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
POPPLER_PATH = r'C:\poppler-24.07.0\Library\bin'  # Ajusta esta ruta

def extraer_texto_de_imagen(imagen, idioma='spa'):
    texto = pytesseract.image_to_string(imagen, lang=idioma)
    return texto

def extraer_texto_de_pdf(ruta_pdf, idioma='spa'):
    texto_completo = ""

    paginas = convert_from_path(ruta_pdf, poppler_path=POPPLER_PATH)

    for i, pagina in enumerate(paginas):
        texto_pagina = extraer_texto_de_imagen(pagina, idioma)
        texto_completo += f"\n--- Página {i+1} ---\n{texto_pagina}"

    return texto_completo
