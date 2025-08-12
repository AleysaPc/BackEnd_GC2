import re

def limpiar_texto_ocr(texto):
    texto = re.sub(r'--- página \d+ ---', '', texto, flags=re.IGNORECASE)
    texto = re.sub(r'\s+', ' ', texto)
    texto = re.sub(r'[^a-zA-Z0-9áéíóúñÁÉÍÓÚÑ.,;:¡!¿?()\- ]+', '', texto)
    texto = re.sub(r'\s+([.,;:!?])', r'\1', texto)
    texto = texto.lower().strip()
    return texto
