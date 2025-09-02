# Dockerfile para servicio de procesamiento de correos XML
FROM python:3.12-slim

# Crear directorio de trabajo
WORKDIR /app

# Copiar archivos del proyecto
COPY . /app

# Instalar dependencias
RUN pip install --upgrade pip \
    && pip install -r requiements.txt

# Crear carpeta de logs y temp
RUN mkdir -p /app/log /app/temp /app/attachments

# Variables de entorno recomendadas
ENV PYTHONUNBUFFERED=1
ENV ENVIRONMENT=prod
ENV RETENTION_LOG=7

# Puerto (si aplica para API, opcional)
EXPOSE 8080

# Comando de inicio
CMD ["python", "main.py", "--mode", "service", "--interval", "30"]
