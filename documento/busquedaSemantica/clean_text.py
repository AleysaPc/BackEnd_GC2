import re
import unicodedata

def limpiar_texto_ocr(texto):
    texto = re.sub(r'--- página \d+ ---', '', texto, flags=re.IGNORECASE)
    texto = re.sub(r'\s+', ' ', texto)
    texto = re.sub(r'[^a-zA-Z0-9áéíóúñÁÉÍÓÚÑ.,;:¡!¿?()\- ]+', '', texto)
    texto = re.sub(r'\s+([.,;:!?])', r'\1', texto)
    texto = texto.lower().strip()
    return texto

def quitar_acentos(texto):
    return ''.join(
        c for c in unicodedata.normalize('NFD', texto)
        if unicodedata.category(c) != 'Mn'
    )

def limpiar_consulta(texto):
    texto = texto.lower()

    texto = quitar_acentos(texto)

    #Eliminar signos de puntuación 
    texto = re.sub(r'[^\w\sáéíóúñ]', ' ', texto)

    # Normalizar espacios
    texto = re.sub(r'\s+', ' ', texto)

    return texto.strip()