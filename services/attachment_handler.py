import email
from typing import List, Tuple
from core.logger import logger

def extract_attachments(email_msg: email.message.Message) -> List[Tuple[str, bytes]]:
    """
    Extrae todos los adjuntos de un mensaje de email.
    
    Args:
        email_msg: Mensaje de email del cual extraer adjuntos
        
    Returns:
        Lista de tuplas (filename, content) con los adjuntos encontrados
    """
    attachments = []
    
    try:
        # Procesar todas las partes del email
        for part in email_msg.walk():
            # Obtener el content-disposition
            content_disposition = part.get("Content-Disposition", "")
            content_type = part.get_content_type()
            
            logger.info(f"Procesando parte del email:")
            logger.info(f"  Content-Type: {content_type}")
            logger.info(f"  Content-Disposition: {content_disposition}")
            
            # Verificar si es un adjunto
            if "attachment" in content_disposition or _is_attachment_by_type(content_type):
                filename = part.get_filename()
                
                # Si no hay filename en Content-Disposition, intentar obtenerlo de otro lado
                if not filename:
                    filename = _extract_filename_from_content_type(part)
                
                # Si aún no hay filename, generar uno basado en el content-type
                if not filename:
                    filename = _generate_filename_from_content_type(content_type)
                
                logger.info(f"  Filename detectado: {filename}")
                
                # Obtener el contenido del adjunto
                try:
                    payload = part.get_payload(decode=True)
                    if payload:
                        # Validar que el contenido coincida con la extensión
                        if _validate_content_type(filename, payload):
                            attachments.append((filename, payload))
                            logger.info(f"✅ Adjunto extraído: {filename} ({len(payload)} bytes)")
                        else:
                            logger.warning(f"⚠️  Contenido no coincide con la extensión: {filename}")
                    else:
                        logger.warning(f"⚠️  No se pudo obtener contenido del adjunto: {filename}")
                        
                except Exception as e:
                    logger.error(f"❌ Error extrayendo contenido del adjunto {filename}: {e}")
                    
    except Exception as e:
        logger.error(f"❌ Error general extrayendo adjuntos: {e}")
    
    logger.info(f"📎 Total de adjuntos extraídos: {len(attachments)}")
    for filename, content in attachments:
        logger.info(f"   - {filename}: {len(content)} bytes, tipo detectado: {_detect_file_type(content)}")
    
    return attachments

def _is_attachment_by_type(content_type: str) -> bool:
    """
    Determina si un content-type corresponde a un tipo de adjunto esperado.
    """
    attachment_types = [
        'application/xml',
        'text/xml',
        'application/zip',
        'application/pdf',
        'application/octet-stream'
    ]
    return content_type in attachment_types

def _extract_filename_from_content_type(part: email.message.Message) -> str:
    """
    Intenta extraer el filename del Content-Type si no está en Content-Disposition.
    """
    content_type = part.get_content_type()
    params = part.get_params()
    
    if params:
        for param in params:
            if len(param) == 2 and param[0].lower() in ['name', 'filename']:
                return param[1]
    
    return ""

def _generate_filename_from_content_type(content_type: str) -> str:
    """
    Genera un filename basado en el content-type.
    """
    import uuid
    unique_id = str(uuid.uuid4())[:8]
    
    type_extensions = {
        'application/xml': f'documento_{unique_id}.xml',
        'text/xml': f'documento_{unique_id}.xml',
        'application/zip': f'archivo_{unique_id}.zip',
        'application/pdf': f'documento_{unique_id}.pdf',
        'application/octet-stream': f'archivo_{unique_id}.dat'
    }
    
    return type_extensions.get(content_type, f'archivo_{unique_id}.dat')

def _validate_content_type(filename: str, content: bytes) -> bool:
    """
    Valida que el contenido del archivo coincida con su extensión.
    """
    if not filename or not content:
        return False
    
    # Obtener extensión del archivo
    extension = filename.lower().split('.')[-1] if '.' in filename else ''
    
    # Detectar tipo de archivo por contenido
    detected_type = _detect_file_type(content)
    
    # Validaciones específicas
    if extension == 'xml':
        # XML debe comenzar con declaración XML o <
        is_xml = (
            content.startswith(b'<?xml') or 
            content.startswith(b'<') or
            b'<autorizacion>' in content[:1000] or
            b'<factura' in content[:1000]
        )
        if not is_xml:
            logger.error(f"❌ Archivo {filename} tiene extensión .xml pero el contenido no es XML:")
            logger.error(f"   Primeros 100 caracteres: {content[:100]}")
            return False
    
    elif extension == 'pdf':
        # PDF debe comenzar con %PDF
        if not content.startswith(b'%PDF'):
            logger.error(f"❌ Archivo {filename} tiene extensión .pdf pero el contenido no es PDF")
            return False
    
    elif extension == 'zip':
        # ZIP debe comenzar con PK
        if not content.startswith(b'PK'):
            logger.error(f"❌ Archivo {filename} tiene extensión .zip pero el contenido no es ZIP")
            return False
    
    logger.info(f"✅ Validación exitosa: {filename} - Tipo detectado: {detected_type}")
    return True

def _detect_file_type(content: bytes) -> str:
    """
    Detecta el tipo de archivo basado en su contenido (magic numbers).
    """
    if not content:
        return "vacío"
    
    # Primeros bytes para detectar tipo
    header = content[:20]
    
    if content.startswith(b'%PDF'):
        return "PDF"
    elif content.startswith(b'PK'):
        return "ZIP"
    elif content.startswith(b'<?xml') or content.startswith(b'<'):
        return "XML"
    elif b'<autorizacion>' in content[:1000]:
        return "XML de Autorización"
    elif b'<factura' in content[:1000] or b'<notaCredito' in content[:1000]:
        return "XML de Comprobante"
    else:
        return f"Desconocido (primeros bytes: {header.hex()[:20]}...)"

def debug_email_structure(email_msg: email.message.Message) -> None:
    """
    Función de debug para analizar la estructura completa de un email.
    """
    logger.info("=== ESTRUCTURA COMPLETA DEL EMAIL ===")
    logger.info(f"From: {email_msg.get('From', 'N/A')}")
    logger.info(f"Subject: {email_msg.get('Subject', 'N/A')}")
    logger.info(f"Content-Type: {email_msg.get_content_type()}")
    logger.info(f"Is multipart: {email_msg.is_multipart()}")
    
    part_count = 0
    for part in email_msg.walk():
        part_count += 1
        logger.info(f"--- PARTE {part_count} ---")
        logger.info(f"Content-Type: {part.get_content_type()}")
        logger.info(f"Content-Disposition: {part.get('Content-Disposition', 'N/A')}")
        logger.info(f"Filename: {part.get_filename() or 'N/A'}")
        logger.info(f"Content-Transfer-Encoding: {part.get('Content-Transfer-Encoding', 'N/A')}")
        
        # Mostrar una muestra del contenido
        try:
            payload = part.get_payload(decode=True)
            if payload:
                content_preview = payload[:100]
                if isinstance(content_preview, bytes):
                    try:
                        content_preview = content_preview.decode('utf-8', errors='replace')
                    except:
                        content_preview = content_preview.hex()[:100]
                logger.info(f"Contenido (muestra): {content_preview}")
                logger.info(f"Tamaño: {len(payload)} bytes")
                logger.info(f"Tipo detectado: {_detect_file_type(payload)}")
        except Exception as e:
            logger.info(f"Error obteniendo payload: {e}")
    
    logger.info("=== FIN ESTRUCTURA EMAIL ===")