import os
import smtplib
import poplib
import email
import imaplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from pathlib import Path
from typing import List, Tuple, Optional
from datetime import datetime
import json

from config import settings
from core.logger import logger
from core.email_config import EmailConfig
from core.xml_data import XMLData
from services.attachment_handler import extract_attachments
from services.xml_processor import process_xml_file
from services.templates_service import render_processing_template, render_client_template, TemplatesService
from core.perseo_remove import limpiar_perseo_pdf_bytes

class EmailXMLProcessor:
    def __init__(self):
        self.config = self._load_config()
        self.environment = settings.ENVIRONMENT
        self.test_email = settings.TEST_EMAIL
        self.attachments_dir = Path("attachments")
        self.attachments_dir.mkdir(exist_ok=True)
        logger.info(f"Servicio iniciado en modo: {self.environment}")
        self.email_service = self

    def _load_config(self) -> EmailConfig:
        return EmailConfig(
            pop_server=settings.POP_SERVER,
            pop_port=settings.POP_PORT,
            pop_user=settings.POP_USER,
            pop_password=settings.POP_PASSWORD,
            smtp_server=settings.SMTP_SERVER,
            smtp_port=settings.SMTP_PORT,
            smtp_user=settings.SMTP_USER,
            smtp_password=settings.SMTP_PASSWORD,
            smtp_use_ssl=settings.SMTP_USE_SSL
        )

    def connect_pop(self) -> poplib.POP3:
        try:
            pop_conn = poplib.POP3(self.config.pop_server, self.config.pop_port)
            pop_conn.user(self.config.pop_user)
            pop_conn.pass_(self.config.pop_password)
            return pop_conn
        except Exception as e:
            logger.error(f"Error conectando a POP3: {e}")
            raise

    def get_unread_emails(self) -> List[email.message.Message]:
        pop_conn = self.connect_pop()
        emails = []
        try:
            num_messages = len(pop_conn.list()[1])
            logger.info(f"Total de mensajes en el buzón: {num_messages}")
            for i in range(1, num_messages + 1):
                raw_email = b"\n".join(pop_conn.retr(i)[1])
                email_message = email.message_from_bytes(raw_email)
                emails.append(email_message)
        finally:
            pop_conn.quit()
        return emails

    def connect_imap(self) -> imaplib.IMAP4_SSL:
        try:
            if settings.IMAP_USE_SSL:
                imap_conn = imaplib.IMAP4_SSL(settings.IMAP_SERVER, settings.IMAP_PORT)
            else:
                imap_conn = imaplib.IMAP4(settings.IMAP_SERVER, settings.IMAP_PORT)
            imap_conn.login(settings.IMAP_USER, settings.IMAP_PASSWORD)
            return imap_conn
        except Exception as e:
            logger.error(f"Error conectando a IMAP: {e}")
            raise

    def get_unread_emails_imap(self) -> List[email.message.Message]:
        imap_conn = self.connect_imap()
        emails = []
        try:
            imap_conn.select('INBOX')
            typ, data = imap_conn.search(None, 'UNSEEN')
            for num in data[0].split():
                typ, msg_data = imap_conn.fetch(num, '(RFC822)')
                raw_email = msg_data[0][1]
                email_message = email.message_from_bytes(raw_email)
                emails.append(email_message)
                imap_conn.store(num, '+FLAGS', '\\Seen')
        finally:
            imap_conn.logout()
        return emails

    def send_email(self, to_email: str, subject: str, html_content: str,
                   attachments: List[Tuple[str, bytes]] = None, add_confirmation_cc: bool = True) -> bool:
        try:
            logger.info(f"Preparando email para enviar. Destino: {to_email}, Asunto: '{subject}'")
            confirmation_email = getattr(settings, 'CONFIRMATION_EMAIL', None)
            logger.info(f"Email recuperado del XML: {to_email}")
            logger.info(f"Email al que se envió: {to_email}")
            if confirmation_email and add_confirmation_cc:
                logger.info(f"Email confirmation (CC): {confirmation_email}")
            msg = MIMEMultipart('alternative')
            msg['From'] = self.config.smtp_user
            msg['To'] = to_email
            msg['Subject'] = subject
            if confirmation_email and add_confirmation_cc:
                msg['Cc'] = confirmation_email
            msg.attach(MIMEText(html_content, 'html', 'utf-8'))

            if attachments:
                for filename, content in attachments:
                    attachment = MIMEApplication(content)
                    attachment.add_header('Content-Disposition', 'attachment', filename=filename)
                    msg.attach(attachment)

            server = smtplib.SMTP(self.config.smtp_server, self.config.smtp_port)
            if self.config.smtp_use_ssl:
                server.starttls()
            server.login(self.config.smtp_user, self.config.smtp_password)
            server.send_message(msg)
            server.quit()
            logger.info(f"Email enviado exitosamente a: {to_email}")
            return True
        except Exception as e:
            logger.error(f"Error enviando email a {to_email}: {e}")
            return False

    def process_single_email(self, email_msg: email.message.Message) -> bool:
        sender = email_msg.get('From', 'Desconocido')
        subject = email_msg.get('Subject', 'Sin asunto')
        logger.info(f"Procesando email de: {sender}, Asunto: {subject}")

        attachments = extract_attachments(email_msg)
        logger.info(f"Adjuntos encontrados: {[att[0] for att in attachments]}")
        if not attachments:
            logger.warning("No se encontraron adjuntos en el email.")
            return False

        xml_data = None
        xml_filename = ""
        pdf_attachments = []

        for filename, content in attachments:
            logger.info(f"Procesando adjunto: {filename}")
            if filename.lower().endswith(('.xml', '.zip')):
                xml_data = process_xml_file(content)
                xml_filename = filename
                logger.info(f"Datos extraídos del XML: {xml_data}")
            elif filename.lower().endswith('.pdf'):
                pdf_attachments.append((filename, content))

        if not xml_data:
            logger.error(f"No se pudo extraer datos del XML en el adjunto: {xml_filename}")
            return False

        destination_email = self.test_email if self.environment == 'test' else xml_data.email_destinatario
        logger.info(f"Email destino para cliente: {destination_email}")

        # Construir número de comprobante: estab + ptoEmi + secuencial
        numero_comprobante = ""
        if xml_data.estab and xml_data.pto_emi and xml_data.secuencial:
            numero_comprobante = f"{xml_data.estab}-{xml_data.pto_emi}-{xml_data.secuencial}"
        
        # Obtener texto descriptivo usando los métodos de XMLData
        tipo_documento_texto = xml_data.get_tipo_documento_texto()
        tipo_emision_texto = xml_data.get_tipo_emision_texto()

        # *** CAMBIO PRINCIPAL: Usar el mismo contexto y plantillas que en main.py ***
        context = {
            "fecha_procesamiento": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
            "entorno": self.environment,
            "email_origen": sender,
            "asunto_original": subject,
            "xml_filename": xml_filename,
            "email_extraido": xml_data.email_destinatario,
            "clave_acceso": xml_data.clave_acceso,
            "total_con_impuestos": xml_data.total_con_impuestos,
            "razon_social": xml_data.razon_social_comprador or xml_data.razon_social,
            "fecha_emision": xml_data.fecha_emision,
            "numero_factura": xml_data.numero_factura,
            "adjuntos_procesados": [att[0] for att in attachments],
            "xml_data": xml_data.__dict__,
            
            # *** NUEVOS CAMPOS AGREGADOS ***
            "numero_comprobante": numero_comprobante,
            "numero_autorizacion": xml_data.numero_autorizacion,
            "estab": xml_data.estab,
            "pto_emi": xml_data.pto_emi,
            "secuencial": xml_data.secuencial,
            "codigo_documento": xml_data.codigo_documento,
            "tipo_documento_texto": tipo_documento_texto,
            "tipo_emision": xml_data.tipo_emision,
            "tipo_emision_texto": tipo_emision_texto
        }
        
        logger.info(f"=== SERVICIO - CONTEXTO PARA PLANTILLAS ===")
        logger.info(f"Número de comprobante generado: {numero_comprobante}")
        logger.info(f"Tipo de documento: {xml_data.codigo_documento} - {tipo_documento_texto}")
        logger.info(f"Tipo de emisión: {xml_data.tipo_emision} - {tipo_emision_texto}")
        #logger.info(f"Contexto completo: {json.dumps(context, indent=2, ensure_ascii=False)}")

        # Email de procesamiento - MISMO que en main.py
        logger.info("=== ENVIANDO EMAIL DE PROCESSING (email_template.html) ===")
        ts = TemplatesService()  # Usar instancia como en main.py
        processing_html = ts.render("email_template.html", context)
        #logger.info(f"HTML generado para email_template.html (primeros 200 chars): {processing_html[:200]}...")
        result_proc = self.send_email(
            self.config.smtp_user, 
            f"[{self.environment.upper()}] XML Procesado - {xml_filename}", 
            processing_html,
            add_confirmation_cc=False
        )
        if result_proc:
            logger.info(f"Email de procesamiento enviado correctamente a {self.config.smtp_user}")
        else:
            logger.error(f"Error al enviar email de procesamiento a {self.config.smtp_user}")

        # Email de cliente - MISMO que en main.py (usar webpos_template.html)
        logger.info("=== ENVIANDO EMAIL DE CLIENTE (webpos_template.html) ===")
        client_html = ts.render("webpos_template.html", context)  
        
        # Adjuntar solo el XML y los PDFs correctamente
        xml_attachment = None
        for filename, content in attachments:
            if filename.lower().endswith('.xml'):
                xml_attachment = (filename, content)
        client_attachments = []
        if xml_attachment:
            client_attachments.append(xml_attachment)
        # Limpiar PDFs antes de adjuntar usando perseo_remove
        
        for filename, content in pdf_attachments:
            pdf_limpio = limpiar_perseo_pdf_bytes(content)
            client_attachments.append((filename, pdf_limpio))

        confirmation_email = getattr(settings, 'CONFIRMATION_EMAIL', None)
        # Log de archivos adjuntos y hora de envío
        hora_envio = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        archivos = [fn for fn, _ in client_attachments]
        logger.info(f"Hora de envío: {hora_envio}")
        logger.info(f"Archivos enviados: {archivos}")
        logger.info(f"Email destino: {destination_email}")
        if confirmation_email:
            logger.info(f"Email CC: {confirmation_email}")

        result_client = self.send_email(
            destination_email, 
            "Su Documento Electrónico - WebPOS", 
            client_html, 
            client_attachments
        )
        if result_client:
            logger.info(f"Email de cliente enviado correctamente a {destination_email}")
        else:
            logger.error(f"Error al enviar email de cliente a {destination_email}")
            
        return result_proc and result_client

    def run_service(self, check_interval: int = settings.CHECK_INTERVAL):
        logger.info("=== INICIANDO SERVICIO - PROCESANDO EMAILS REALES ===")
        emails = self.get_unread_emails_imap()
        logger.info(f"Correos no leídos encontrados: {len(emails)}")
        if not emails:
            logger.info("No hay correos nuevos para procesar.")
        for idx, email_msg in enumerate(emails):
            logger.info(f"Procesando email #{idx+1} de {len(emails)}")
            self.process_single_email(email_msg)
        if check_interval > 0:
            import time
            while True:
                try:
                    emails = self.get_unread_emails_imap()
                    logger.info(f"Correos no leídos encontrados: {len(emails)}")
                    if not emails:
                        logger.info("No hay correos nuevos para procesar.")
                    for idx, email_msg in enumerate(emails):
                        logger.info(f"Procesando email #{idx+1} de {len(emails)}")
                        self.process_single_email(email_msg)
                except Exception as e:
                    logger.error(f"Error en servicio: {e}")
                time.sleep(check_interval)

    def test_send_email(self, test_type: str = "both"):
        from services.templates_service import test_processing_template, test_client_template
        if test_type in ["processing", "both"]:
            html = test_processing_template()
            self.send_email(self.test_email, "[TEST] Procesamiento", html)
        if test_type in ["client", "both"]:
            html = test_client_template()
            self.send_email(self.test_email, "[TEST] Documento Electrónico", html)