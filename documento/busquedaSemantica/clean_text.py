import re

def limpiar_texto_ocr(texto):
    # 1. Eliminar marcas de página y encabezados comunes
    texto = re.sub(r'--- página \d+ ---', '', texto, flags=re.IGNORECASE)

    # 2. Eliminar saltos de línea y múltiples espacios
    texto = re.sub(r'\s+', ' ', texto)

    # 3. Eliminar caracteres no deseados, más amplios
    texto = re.sub(r'[^a-zA-Z0-9áéíóúñÁÉÍÓÚÑ.,;:¡!¿?()\- ]+', '', texto)

    # 4. Eliminar espacios antes de signos de puntuación
    texto = re.sub(r'\s+([.,;:!?])', r'\1', texto)

    # 5. Pasar a minúsculas
    texto = texto.lower()

    # 6. Eliminar espacios iniciales y finales
    texto = texto.strip()

    return texto
