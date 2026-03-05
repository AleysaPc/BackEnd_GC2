from pdf2image import convert_from_path
from PIL import Image
import pytesseract

def extraer_texto_de_pdf(ruta_pdf):
    paginas = convert_from_path(ruta_pdf)

    texto_total = ""

    for pagina in paginas:
        texto = pytesseract.image_to_string(pagina, lang="spa")
        texto_total += texto + "\n"

    return texto_total

def extraer_texto_de_imagen(imagen, idioma='spa'):
    return pytesseract.image_to_string(imagen, lang=idioma)

def extraer_texto_de_pdf(ruta_pdf, idioma='spa'):
    texto_completo = ""
    # Convertir PDF a imágenes para trabaar con tesseract
    paginas = convert_from_path(ruta_pdf, poppler_path=POPPLER_PATH)
    for i, pagina in enumerate(paginas):
        texto_pagina = extraer_texto_de_imagen(pagina, idioma)
        texto_completo += f"\n--- Página {i+1} ---\n{texto_pagina}"
    return texto_completo
