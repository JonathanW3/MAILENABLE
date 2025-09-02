import argparse
from services.email_service import EmailXMLProcessor
from services.templates_service import TemplatesService
from core.logger import logger
from config import settings
from datetime import datetime


def main():
    parser = argparse.ArgumentParser(description='Servicio de procesamiento de correos XML')
    parser.add_argument('--mode', choices=['service', 'test', 'monitor'], default='service')
    parser.add_argument('--test-type', choices=['processing', 'client', 'both'], default='both')
    parser.add_argument('--interval', type=int, default=30)
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
        logger.info("Ejecutando en modo MONITOR - Enviando email_template con datos extraídos")
        ts = TemplatesService()
        
        to_email = settings.TEST_EMAIL  # O puedes usar otro email de configuración
        
        # Usar los datos reales extraídos (esto debería venir de tu sistema de procesamiento)
        # Por ahora uso datos de ejemplo, pero deberías reemplazar esto con la lógica
        # que extrae los datos reales del XML procesado
        xml_data = {
            "email_destinatario": to_email,
            "clave_acceso": "1234567890",
            "total_con_impuestos": "100.00",
            "razon_social": "Empresa Test",
            "fecha_emision": datetime.now().strftime("%d/%m/%Y"),
            "numero_factura": "000001",
            "subtotal": "80.00",
            "iva": "20.00",
            "datos_adicionales": {"nota": "Monitoreo de datos", "vendedor": "Sistema"}
        }
        
        context = {
            "fecha_procesamiento": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
            "entorno": settings.ENVIRONMENT,
            "email_origen": "monitor@webpos.com",
            "asunto_original": "Monitoreo de datos extraídos",
            "xml_filename": "archivo_monitor.xml",
            "email_extraido": xml_data["email_destinatario"],
            "clave_acceso": xml_data["clave_acceso"],
            "total_con_impuestos": xml_data["total_con_impuestos"],
            "razon_social": xml_data["razon_social"],
            "fecha_emision": xml_data["fecha_emision"],
            "numero_factura": xml_data["numero_factura"],
            "adjuntos_procesados": ["archivo_monitor.xml"],
            "xml_data": xml_data
        }
        
        # Enviar usando email_template.html para monitoreo
        html = ts.render("email_template.html", context)
        processor.email_service.send_email(to_email, "Monitoreo - Datos Extraídos", html)
        logger.info(f"Email de monitoreo enviado exitosamente a {to_email} usando email_template.html")
    
    else:
        logger.info("Ejecutando servicio de monitoreo")
        processor.run_service(args.interval)


if __name__ == "__main__":
    main()