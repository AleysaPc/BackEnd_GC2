FROM python:3.13-slim

# Instalar Tesseract + idioma español + poppler
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-spa \
    poppler-utils \
    && apt-get clean

WORKDIR /app

COPY . .

RUN pip install -r requirements.txt

CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000"]