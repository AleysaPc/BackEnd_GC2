import os
import time
from celery import shared_task
from .busquedaSemantica.ocr import extraer_texto_de_pdf


@shared_task
def ocr_task(ruta_archivo):

    print(f"Ruta recibida: {ruta_archivo}")

    tiempo_espera = 0
    max_espera = 20  # segundos

    while not os.path.exists(ruta_archivo) and tiempo_espera < max_espera:
        print(f"Esperando archivo... ({tiempo_espera}s)")
        time.sleep(1)
        tiempo_espera += 1

    if not os.path.exists(ruta_archivo):
        raise FileNotFoundError(f"No se encontró el archivo: {ruta_archivo}")

    print("Archivo encontrado. Iniciando OCR...")

    texto = extraer_texto_de_pdf(ruta_archivo)

    return texto