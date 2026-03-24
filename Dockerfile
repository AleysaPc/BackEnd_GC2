# Dockerfile - Solo backend sin Celery
FROM python:3.13-slim

RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-spa \
    poppler-utils \
    && apt-get clean

WORKDIR /app

COPY . .

RUN pip install -r requirements.txt
RUN python manage.py collectstatic --noinput

# SOLO GUNICORN - SIN CELERY WORKER
CMD gunicorn gestion_documental.wsgi:application --bind 0.0.0.0:$PORT