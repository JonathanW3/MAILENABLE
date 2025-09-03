# Dockerfile para servicio de procesamiento de correos XML
FROM python:3.12-slim

# Crear directorio de trabajo
WORKDIR /app


# Copiar archivos del proyecto y .env
COPY . /app
COPY .env /app/.env

# Instalar dependencias
RUN pip install --upgrade pip \
    && pip install -r requiements.txt

# Crear carpeta de logs y temp
RUN mkdir -p /app/log /app/temp /app/attachments

# Variables de entorno recomendadas
ENV PYTHONUNBUFFERED=1

# Comando de inicio
ENV ENV_FILE=/app/.env
CMD ["python", "main.py", "--mode", "service", "--interval", "30"]
