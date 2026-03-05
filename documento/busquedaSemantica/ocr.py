from pdf2image import convert_from_path  # Convierte PDF → imágenes
import pytesseract


def extraer_texto_de_imagen(imagen, idioma="spa"):
    """
    Extrae texto de una imagen usando Tesseract OCR.
    """
    return pytesseract.image_to_string(imagen, lang=idioma)


def extraer_texto_de_pdf(ruta_pdf, idioma="spa"):
    """
    Convierte un PDF en imágenes y extrae el texto de cada página.
    """
    paginas = convert_from_path(ruta_pdf)

    texto_completo = ""

    for i, pagina in enumerate(paginas, start=1):
        texto_pagina = extraer_texto_de_imagen(pagina, idioma)
        texto_completo += f"\n--- Página {i} ---\n{texto_pagina}"

    return texto_completo