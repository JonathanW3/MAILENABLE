# Guía de Variables de Entorno (.env)

Este archivo describe cada variable del archivo `.env`, su propósito y cuándo deberías modificarla.

---

## Variables principales

- **ENVIRONMENT**
  - **Descripción:** Define el entorno de ejecución (`test` o `prod`).
  - **Uso:**
    - `test`: Usa el correo de prueba (`TEST_EMAIL`) para todos los envíos.
    - `prod`: Usa el correo extraído del XML.
  - **Cuándo cambiar:** Cambia a `prod` solo cuando el sistema esté en producción.

- **TEST_EMAIL**
  - **Descripción:** Correo(s) de destino para pruebas (separados por coma).
  - **Uso:** Solo se usa si `ENVIRONMENT=test`.
  - **Cuándo cambiar:** Modifica para probar con diferentes destinatarios.

- **MONITOR_EMAIL**
  - **Descripción:** Correo(s) que reciben notificaciones de monitoreo.
  - **Uso:** Para alertas o reportes automáticos.
  - **Cuándo cambiar:** Si cambian los responsables de monitoreo.

- **CONFIRMATION_EMAIL**
  - **Descripción:** Correo que recibirá copia (CC) de todos los envíos.
  - **Uso:** Auditoría o confirmación de entregas.
  - **Cuándo cambiar:** Si cambia el responsable de auditoría.

---

## Configuración de buzón POP3
- **POP_SERVER, POP_PORT, POP_USER, POP_PASSWORD**
  - **Descripción:** Datos de conexión al servidor POP3 para leer correos.
  - **Cuándo cambiar:** Solo si cambian los datos del buzón de entrada.

## Configuración SMTP (envío)
- **SMTP_SERVER, SMTP_PORT, SMTP_USE_SSL, SMTP_USER, SMTP_PASSWORD**
  - **Descripción:** Datos de conexión al servidor SMTP para enviar correos.
  - **Cuándo cambiar:** Si cambian los datos del servidor de salida.

## Configuración IMAP (lectura)
- **IMAP_SERVER, IMAP_PORT, IMAP_USER, IMAP_PASSWORD, IMAP_USE_SSL**
  - **Descripción:** Datos de conexión al servidor IMAP para leer correos no leídos.
  - **Cuándo cambiar:** Si cambian los datos del buzón de entrada.

---

## Configuración adicional
- **CHECK_INTERVAL**
  - **Descripción:** Intervalo (en segundos) para revisar el buzón en modo servicio.
  - **Cuándo cambiar:** Ajusta según la frecuencia deseada de revisión.

- **LOG_LEVEL**
  - **Descripción:** Nivel de detalle del log (`DEBUG`, `INFO`, `WARNING`, `ERROR`).
  - **Cuándo cambiar:** Usa `DEBUG` para desarrollo, `INFO` o superior en producción.

- **TEMP_DIR**
  - **Descripción:** Carpeta para archivos temporales.
  - **Cuándo cambiar:** Solo si necesitas cambiar la ubicación de temporales.

- **TEMPLATES_DIR**
  - **Descripción:** Carpeta donde están los templates HTML.
  - **Cuándo cambiar:** Si cambias la estructura de carpetas del proyecto.

- **ATTACHMENTS_DIR**
  - **Descripción:** Carpeta donde se guardan los adjuntos extraídos.
  - **Cuándo cambiar:** Si necesitas otra ubicación para los adjuntos.

- **RETENTION_LOG**
  - **Descripción:** Días que se conservan los logs antes de ser eliminados automáticamente.
  - **Cuándo cambiar:** Ajusta según tus políticas de auditoría.

---

## Notas
- Si agregas nuevas variables, documenta aquí su propósito y uso.
- No compartas el archivo `.env` con datos sensibles fuera de tu equipo/confianza.
