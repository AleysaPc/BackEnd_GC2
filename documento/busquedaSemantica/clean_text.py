import re
#Contendrá las funciones relacionadas con la extracción de texto usando OCR.

def limpiar_texto_ocr(texto):
    # 1. Eliminar saltos de línea y múltiples espacios
    texto = re.sub(r'\s+', ' ', texto)

    # 2. Eliminar caracteres no deseados (como caracteres especiales mal reconocidos)
    texto = re.sub(r'[^\w\sáéíóúñÁÉÍÓÚÑ.,;:¡!¿?()\-]', '', texto)

    # 3. Eliminar espacios antes de signos de puntuación
    texto = re.sub(r'\s+([.,;:!?])', r'\1', texto)

    # 4. Normalizar texto: todo en minúsculas
    texto = texto.lower()

    # 5. Eliminar espacios iniciales y finales
    texto = texto.strip()

    return texto
