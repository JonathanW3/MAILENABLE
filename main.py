import argparse
from services.email_service import EmailXMLProcessor
from services.templates_service import TemplatesService
from core.logger import logger
from config import settings
from datetime import datetime
import json


def main():
    parser = argparse.ArgumentParser(description='Servicio de procesamiento de correos XML')
    parser.add_argument('--mode', choices=['service', 'test', 'monitor'], default='service')
    parser.add_argument('--test-type', choices=['processing', 'client', 'both'], default='both')
    parser.add_argument('--interval', type=int, default=30)
    parser.add_argument('--email-sender', type=str, help='Email del remitente a buscar en modo monitor')
    parser.add_argument('--email-subject', type=str, help='Asunto del email a buscar en modo monitor')
    args = parser.parse_args()

    processor = EmailXMLProcessor()

    if args.mode == 'test':
        logger.info("Ejecutando en modo TEST")
        ts = TemplatesService()

        to_email = settings.TEST_EMAIL

        # Datos de ejemplo para test
        xml_data = {
            "email_destinatario": to_email,
            "clave_acceso": "1234567890",
            "total_con_impuestos": "100.00",
            "razon_social": "Empresa Test",
            "fecha_emision": "01/09/2025",
            "numero_factura": "000001",
            "subtotal": "80.00",
            "iva": "20.00",
            "datos_adicionales": {"nota": "Prueba", "vendedor": "Test"}
        }
        context = {
            "fecha_procesamiento": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
            "entorno": settings.ENVIRONMENT,
            "email_origen": "test@webpos.com",
            "asunto_original": "Prueba de procesamiento",
            "xml_filename": "archivo.xml",
            "email_extraido": xml_data["email_destinatario"],
            "clave_acceso": xml_data["clave_acceso"],
            "total_con_impuestos": xml_data["total_con_impuestos"],
            "razon_social": xml_data["razon_social"],
            "fecha_emision": xml_data["fecha_emision"],
            "numero_factura": xml_data["numero_factura"],
            "adjuntos_procesados": ["archivo.xml"],
            "xml_data": xml_data
        }
        if args.test_type in ["processing", "both"]:
            html = ts.render("email_template.html", context)
            processor.email_service.send_email(to_email, "Prueba Processing", html)

        if args.test_type in ["client", "both"]:
            html = ts.render("webpos_template.html", context)
            processor.email_service.send_email(to_email, "Prueba Cliente", html)
    
    elif args.mode == 'monitor':
        logger.info("=== INICIANDO MODO MONITOR - Buscando email específico ===")
        ts = TemplatesService()
        monitor_email = settings.MONITOR_EMAIL
        
        # Validar que se proporcionen criterios de búsqueda
        if not args.email_sender and not args.email_subject:
            logger.error("MODO MONITOR requiere --email-sender o --email-subject para buscar un email específico")
            print("Error: Modo monitor requiere criterios de búsqueda.")
            print("Uso: python main.py --mode monitor --email-sender remitente@ejemplo.com")
            print("  o: python main.py --mode monitor --email-subject 'Asunto del email'")
            print("  o: python main.py --mode monitor --email-sender remitente@ejemplo.com --email-subject 'Asunto'")
            return
        
        try:
            # Conectar al buzón y obtener todos los emails
            logger.info("Conectando al buzón para buscar email específico...")
            emails = processor.get_unread_emails_imap()
            logger.info(f"Total de emails en buzón: {len(emails)}")
            
            # Buscar el email que coincida con los criterios
            target_email = None
            for email_msg in emails:
                sender = email_msg.get('From', '').lower()
                subject = email_msg.get('Subject', '').lower()
                
                # Verificar criterios de búsqueda
                sender_match = True
                subject_match = True
                
                if args.email_sender:
                    sender_match = args.email_sender.lower() in sender
                    
                if args.email_subject:
                    subject_match = args.email_subject.lower() in subject
                
                if sender_match and subject_match:
                    target_email = email_msg
                    logger.info(f"✅ Email encontrado - Remitente: {email_msg.get('From')}, Asunto: {email_msg.get('Subject')}")
                    break
            
            if not target_email:
                logger.warning("❌ No se encontró ningún email que coincida con los criterios")
                criteria = []
                if args.email_sender:
                    criteria.append(f"remitente: '{args.email_sender}'")
                if args.email_subject:
                    criteria.append(f"asunto: '{args.email_subject}'")
                
                # Crear contexto para notificar email no encontrado
                context = {
                    "fecha_procesamiento": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
                    "entorno": settings.ENVIRONMENT,
                    "email_origen": "monitor@webpos.com",
                    "asunto_original": f"Email no encontrado - Criterios: {', '.join(criteria)}",
                    "xml_filename": "email_no_encontrado.xml",
                    "email_extraido": "N/A",
                    "clave_acceso": "N/A",
                    "total_con_impuestos": "0.00",
                    "razon_social": f"Email no encontrado con criterios: {', '.join(criteria)}",
                    "fecha_emision": datetime.now().strftime("%d/%m/%Y"),
                    "numero_factura": "N/A",
                    "adjuntos_procesados": [],
                    "xml_data": {
                        "mensaje": f"No se encontró email con criterios: {', '.join(criteria)}",
                        "total_emails_revisados": len(emails)
                    }
                }
            else:
                # Procesar el email encontrado y extraer datos reales
                sender = target_email.get('From', 'Desconocido')
                subject = target_email.get('Subject', 'Sin asunto')
                logger.info(f"🔍 Procesando email específico - De: {sender}, Asunto: {subject}")
                
                # Extraer adjuntos usando el sistema existente
                from services.attachment_handler import extract_attachments
                from services.xml_processor import process_xml_file
                
                attachments = extract_attachments(target_email)
                logger.info(f"📎 Adjuntos encontrados: {[att[0] for att in attachments]}")
                
                xml_data = None
                xml_filename = ""
                
                # Procesar XML usando el sistema existente
                for filename, content in attachments:
                    logger.info(f"🔄 Procesando adjunto: {filename}")
                    if filename.lower().endswith(('.xml', '.zip')):
                        xml_data = process_xml_file(content)
                        xml_filename = filename
                        logger.info(f"✅ Datos extraídos del XML: {xml_data}")
                        break
                
                if xml_data:
                    # Crear contexto con datos reales extraídos del email específico
                    context = {
                        "fecha_procesamiento": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
                        "entorno": settings.ENVIRONMENT,
                        "email_origen": sender,
                        "asunto_original": subject,
                        "xml_filename": xml_filename,
                        "email_extraido": xml_data.email_destinatario,
                        "clave_acceso": xml_data.clave_acceso,
                        "total_con_impuestos": xml_data.total_con_impuestos,
                        "razon_social": xml_data.razon_social,
                        "fecha_emision": xml_data.fecha_emision,
                        "numero_factura": xml_data.numero_factura,
                        "adjuntos_procesados": [att[0] for att in attachments],
                        "xml_data": xml_data.__dict__ if hasattr(xml_data, '__dict__') else xml_data
                    }
                    logger.info(f"📊 DATOS EXTRAÍDOS PARA MONITOR:")
                    logger.info(f"   👤 Cliente: {xml_data.razon_social}")
                    logger.info(f"   📧 Email destino: {xml_data.email_destinatario}")
                    logger.info(f"   🧾 Factura: {xml_data.numero_factura}")
                    logger.info(f"   💰 Total: {xml_data.total_con_impuestos}")
                    logger.info(f"   🔑 Clave: {xml_data.clave_acceso}")
                else:
                    logger.error("❌ No se pudo extraer datos del XML en el email encontrado")
                    context = {
                        "fecha_procesamiento": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
                        "entorno": settings.ENVIRONMENT,
                        "email_origen": sender,
                        "asunto_original": subject,
                        "xml_filename": "error_xml.xml",
                        "email_extraido": "Error",
                        "clave_acceso": "Error",
                        "total_con_impuestos": "0.00",
                        "razon_social": "Error al procesar XML del email encontrado",
                        "fecha_emision": datetime.now().strftime("%d/%m/%Y"),
                        "numero_factura": "Error",
                        "adjuntos_procesados": [att[0] for att in attachments] if attachments else [],
                        "xml_data": {"error": f"No se pudo procesar XML del email: {subject}"}
                    }
            
            # Enviar email de monitoreo a MONITOR_EMAIL
            logger.info(f"📤 ENVIANDO REPORTE DE MONITOR")
            logger.info(f"📧 Destino: {monitor_email}")
            
            html = ts.render("email_template.html", context)
            result = processor.email_service.send_email(
                monitor_email, 
                f"[{settings.ENVIRONMENT.upper()}] MONITOR - Email Específico Procesado", 
                html
            )
            
            if result:
                logger.info(f"✅ Reporte de monitor enviado exitosamente a {monitor_email}")
                if context['clave_acceso'] != 'N/A' and context['clave_acceso'] != 'Error':
                    logger.info(f"📋 RESUMEN: Factura #{context['numero_factura']} | Total: {context['total_con_impuestos']} | Cliente: {context['razon_social']}")
                else:
                    logger.info(f"📋 RESUMEN: {context['razon_social']}")
            else:
                logger.error(f"❌ Error al enviar reporte de monitor a {monitor_email}")
                
        except Exception as e:
            logger.error(f"💥 Error crítico en modo monitor: {e}")
            import traceback
            logger.error(f"Traceback completo: {traceback.format_exc()}")
            
            # Enviar email de error crítico
            error_context = {
                "fecha_procesamiento": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
                "entorno": settings.ENVIRONMENT,
                "email_origen": "sistema@webpos.com",
                "asunto_original": "Error crítico en modo monitor",
                "xml_filename": "error_critico.xml",
                "email_extraido": "Error",
                "clave_acceso": "Error",
                "total_con_impuestos": "0.00",
                "razon_social": "Error crítico en sistema de monitoreo",
                "fecha_emision": datetime.now().strftime("%d/%m/%Y"),
                "numero_factura": "Error",
                "adjuntos_procesados": [],
                "xml_data": {"error_critico": str(e), "traceback": traceback.format_exc()}
            }
            
            html = ts.render("email_template.html", error_context)
            processor.email_service.send_email(
                monitor_email, 
                f"[{settings.ENVIRONMENT.upper()}] MONITOR - ERROR CRÍTICO", 
                html
            )
            logger.error(f"🚨 Notificación de error crítico enviada a {monitor_email}")
    
    else:
        logger.info("Ejecutando servicio de monitoreo")
        processor.run_service(args.interval)


if __name__ == "__main__":
    main()