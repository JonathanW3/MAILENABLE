import zipfile, io
import xml.etree.ElementTree as ET
from typing import Optional
from core.logger import logger
from core.xml_data import XMLData

def process_xml_file(xml_content: bytes) -> Optional[XMLData]:
    try:
        if xml_content.startswith(b'PK'):
            return _process_zip_xml(xml_content)
        # Detectar si es un XML de autorizacion con CDATA
        try:
            text = xml_content.decode('utf-8')
        except Exception:
            text = xml_content.decode('latin1')
        if '<autorizacion>' in text and '<comprobante><![CDATA[' in text:
            import xml.etree.ElementTree as ET
            try:
                root = ET.fromstring(text)
                comprobante = root.find('comprobante')
                if comprobante is not None and comprobante.text:
                    inner_xml = comprobante.text.strip()
                    logger.info(f"Contenido extraído del CDATA:\n{inner_xml[:500]}")
                    # Elimina encabezado XML si existe
                    if inner_xml.startswith('<?xml'):
                        idx = inner_xml.find('?>')
                        if idx != -1:
                            inner_xml = inner_xml[idx+2:].lstrip('\r\n')
                    # Procesar el contenido del CDATA
                    xml_data = _parse_xml_content(inner_xml.encode('utf-8'))
                    if xml_data:
                        # EXTRAER DATOS DEL XML DE AUTORIZACIÓN (fuera del CDATA)
                        _extract_authorization_data(root, xml_data)
                    return xml_data
            except Exception as e:
                logger.error(f"Error extrayendo CDATA con ElementTree: {e}")
                return None
        return _parse_xml_content(xml_content)
    except Exception as e:
        logger.error(f"Error procesando XML: {e}")
        return None

def _process_zip_xml(zip_content: bytes) -> Optional[XMLData]:
    try:
        zip_file = zipfile.ZipFile(io.BytesIO(zip_content))
        for file_info in zip_file.filelist:
            if file_info.filename.lower().endswith('.xml'):
                return _parse_xml_content(zip_file.read(file_info.filename))
    except Exception as e:
        logger.error(f"Error procesando ZIP: {e}")
        return None

def _extract_authorization_data(auth_root: ET.Element, xml_data: XMLData) -> None:
    """
    Extrae datos del XML de autorización (fuera del CDATA)
    """
    try:
        # Extraer número de autorización
        numero_autorizacion = auth_root.find('.//numeroAutorizacion')
        if numero_autorizacion is not None:
            xml_data.numero_autorizacion = numero_autorizacion.text or ""
            logger.info(f"Número de autorización (desde XML autorización): {xml_data.numero_autorizacion}")
        
        # Extraer fecha de autorización si existe
        fecha_autorizacion = auth_root.find('.//fechaAutorizacion')
        if fecha_autorizacion is not None:
            xml_data.fecha_autorizacion = fecha_autorizacion.text or ""
            logger.info(f"Fecha de autorización: {xml_data.fecha_autorizacion}")
        
        # Extraer estado
        estado = auth_root.find('.//estado')
        if estado is not None:
            xml_data.estado_autorizacion = estado.text or ""
            logger.info(f"Estado autorización: {xml_data.estado_autorizacion}")
            
    except Exception as e:
        logger.error(f"Error extrayendo datos de autorización: {e}")

def _parse_xml_content(xml_content: bytes) -> Optional[XMLData]:
    try:
        root = ET.fromstring(xml_content)
        
        # Inicializar XMLData con valores por defecto
        xml_data = XMLData(email_destinatario="")
        
        # Inicializar todos los nuevos atributos con valores por defecto
        xml_data.estab = ""
        xml_data.pto_emi = ""
        xml_data.secuencial = ""
        xml_data.numero_autorizacion = ""
        xml_data.codigo_documento = ""
        xml_data.tipo_emision = ""
        xml_data.fecha_autorizacion = ""
        xml_data.estado_autorizacion = ""
        
        # Buscar email del destinatario
        email_destinatario = None
        for campo in root.iter('campoAdicional'):
            nombre_campo = campo.get('nombre', '').lower().strip()  # Añadir .strip() para quitar espacios
            logger.info(f"Campo encontrado: '{campo.get('nombre', '')}' -> '{nombre_campo}'")  # Debug
            if nombre_campo in ["correo", "email", "mail", "correo_electronico"]:
                email_destinatario = campo.text
                logger.info(f"Email encontrado: {email_destinatario}")  # Debug
                break
        
        # Si no se encuentra email, usar valores por defecto pero continuar procesando
        if not email_destinatario:
            logger.warning("No se encontró email del destinatario, usando valor por defecto")
            # Buscar en otros campos posibles
            razon_comprador = root.find('.//razonSocialComprador')
            if razon_comprador is not None:
                # Generar un email por defecto basado en la razón social
                email_destinatario = f"facturacion@{razon_comprador.text.lower().replace(' ', '').replace('.', '')}.com"
                logger.info(f"Email generado por defecto: {email_destinatario}")
            else:
                email_destinatario = "sin-email@factura.com"
                logger.info(f"Email por defecto asignado: {email_destinatario}")
        
        xml_data.email_destinatario = email_destinatario
        
        # Extraer clave de acceso
        clave = root.find('.//claveAcceso')
        if clave is not None:
            xml_data.clave_acceso = clave.text or ""
            logger.info(f"Clave de acceso: {xml_data.clave_acceso}")
        
        # Extraer total con impuestos
        total = root.find('.//importeTotal')
        if total is not None:
            xml_data.total_con_impuestos = total.text or "0.00"
            logger.info(f"Total con impuestos: {xml_data.total_con_impuestos}")
        
        # Buscar razonSocialComprador en todo el árbol
        razon_comprador = None
        for elem in root.iter('razonSocialComprador'):
            razon_comprador = elem
            break
        if razon_comprador is not None:
            xml_data.razon_social_comprador = razon_comprador.text or ""
            logger.info(f"Razón social comprador: {xml_data.razon_social_comprador}")
        else:
            logger.warning("No se encontró la etiqueta <razonSocialComprador> en el XML.")
        
        # Razón social del emisor
        razon = root.find('.//razonSocial')
        if razon is not None:
            xml_data.razon_social = razon.text or ""
            logger.info(f"Razón social: {xml_data.razon_social}")
        
        # Fecha de emisión
        fecha = root.find('.//fechaEmision')
        if fecha is not None:
            xml_data.fecha_emision = fecha.text or ""
            logger.info(f"Fecha emisión: {xml_data.fecha_emision}")
        
        # Número de factura (secuencial)
        secuencial = root.find('.//secuencial')
        if secuencial is not None:
            xml_data.numero_factura = secuencial.text or ""
            xml_data.secuencial = secuencial.text or ""
            logger.info(f"Número factura/secuencial: {xml_data.numero_factura}")
        
        # *** NUEVOS CAMPOS PARA EXTRAER ***
        
        # Establecimiento
        estab = root.find('.//estab')
        if estab is not None:
            xml_data.estab = estab.text or ""
            logger.info(f"Establecimiento: {xml_data.estab}")
        
        # Punto de emisión
        pto_emi = root.find('.//ptoEmi')
        if pto_emi is not None:
            xml_data.pto_emi = pto_emi.text or ""
            logger.info(f"Punto de emisión: {xml_data.pto_emi}")
        
        # Número de autorización
        numero_autorizacion = root.find('.//numeroAutorizacion')
        if numero_autorizacion is not None:
            xml_data.numero_autorizacion = numero_autorizacion.text or ""
            logger.info(f"Número de autorización: {xml_data.numero_autorizacion}")
        
        # Código de documento (tipo de documento)
        cod_doc = root.find('.//codDoc')
        if cod_doc is not None:
            xml_data.codigo_documento = cod_doc.text or ""
            logger.info(f"Código de documento: {xml_data.codigo_documento}")
        
        # Tipo de emisión
        tipo_emision = root.find('.//tipoEmision')
        if tipo_emision is not None:
            xml_data.tipo_emision = tipo_emision.text or ""
            logger.info(f"Tipo de emisión: {xml_data.tipo_emision}")
        
        # También buscar en infoTributaria si no se encontraron en otros lugares
        info_tributaria = root.find('.//infoTributaria')
        if info_tributaria is not None:
            if not xml_data.estab:
                estab_elem = info_tributaria.find('estab')
                if estab_elem is not None:
                    xml_data.estab = estab_elem.text or ""
                    logger.info(f"Establecimiento (infoTributaria): {xml_data.estab}")
            
            if not xml_data.pto_emi:
                pto_emi_elem = info_tributaria.find('ptoEmi')
                if pto_emi_elem is not None:
                    xml_data.pto_emi = pto_emi_elem.text or ""
                    logger.info(f"Punto de emisión (infoTributaria): {xml_data.pto_emi}")
            
            if not xml_data.secuencial:
                secuencial_elem = info_tributaria.find('secuencial')
                if secuencial_elem is not None:
                    xml_data.secuencial = secuencial_elem.text or ""
                    xml_data.numero_factura = xml_data.secuencial  # Mantener compatibilidad
                    logger.info(f"Secuencial (infoTributaria): {xml_data.secuencial}")
            
            if not xml_data.codigo_documento:
                cod_doc_elem = info_tributaria.find('codDoc')
                if cod_doc_elem is not None:
                    xml_data.codigo_documento = cod_doc_elem.text or ""
                    logger.info(f"Código de documento (infoTributaria): {xml_data.codigo_documento}")
            
            if not xml_data.tipo_emision:
                tipo_emision_elem = info_tributaria.find('tipoEmision')
                if tipo_emision_elem is not None:
                    xml_data.tipo_emision = tipo_emision_elem.text or ""
                    logger.info(f"Tipo de emisión (infoTributaria): {xml_data.tipo_emision}")
        
        logger.info(f"=== DATOS XML PROCESADOS EXITOSAMENTE ===")
        logger.info(f"Email destinatario: {xml_data.email_destinatario}")
        logger.info(f"Clave acceso: {xml_data.clave_acceso}")
        logger.info(f"Total: {xml_data.total_con_impuestos}")
        logger.info(f"Establecimiento: {xml_data.estab}")
        logger.info(f"Punto emisión: {xml_data.pto_emi}")
        logger.info(f"Secuencial: {xml_data.secuencial}")
        logger.info(f"Número autorización: {xml_data.numero_autorizacion}")
        logger.info(f"Código documento: {xml_data.codigo_documento}")
        logger.info(f"Tipo emisión: {xml_data.tipo_emision}")
        logger.info(f"Datos completos: {xml_data.__dict__}")
        
        return xml_data
        
    except Exception as e:
        logger.error(f"Error parseando XML: {e}")
        return None