from dataclasses import dataclass
from typing import Optional

@dataclass
class XMLData:
    """
    Clase para almacenar los datos extraídos de un XML de documento electrónico del SRI
    """
    email_destinatario: str
    clave_acceso: str = ""
    total_con_impuestos: str = "0.00"
    razon_social: str = ""
    razon_social_comprador: str = ""
    fecha_emision: str = ""
    numero_factura: str = ""  # Mantener por compatibilidad
    
    # Nuevos campos agregados
    estab: str = ""                    # Establecimiento
    pto_emi: str = ""                  # Punto de emisión
    secuencial: str = ""               # Número secuencial
    numero_autorizacion: str = ""      # Número de autorización del SRI
    codigo_documento: str = ""         # Código del tipo de documento (01, 04, 05, etc.)
    tipo_emision: str = ""             # Tipo de emisión (1, 2)
    fecha_autorizacion: str = ""       # Fecha de autorización
    estado_autorizacion: str = ""      # Estado de la autorización
    
    def __post_init__(self):
        """
        Validaciones y ajustes post-inicialización
        """
        # Si secuencial está definido pero numero_factura no, sincronizar
        if self.secuencial and not self.numero_factura:
            self.numero_factura = self.secuencial
        elif self.numero_factura and not self.secuencial:
            self.secuencial = self.numero_factura
    
    def get_numero_comprobante(self) -> str:
        """
        Genera el número de comprobante en formato: estab-ptoEmi-secuencial
        """
        if self.estab and self.pto_emi and self.secuencial:
            return f"{self.estab}-{self.pto_emi}-{self.secuencial}"
        return ""
    
    def get_tipo_documento_texto(self) -> str:
        """
        Convierte el código de tipo de documento a texto descriptivo
        """
        tipos_documento = {
            "01": "Factura",
            "03": "Liquidación de Compra de Bienes y Prestación de Servicios",
            "04": "Nota de Crédito",
            "05": "Nota de Débito", 
            "06": "Guía de Remisión",
            "07": "Comprobante de Retención"
        }
        return tipos_documento.get(self.codigo_documento, f"Documento tipo {self.codigo_documento}")
    
    def get_tipo_emision_texto(self) -> str:
        """
        Convierte el código de tipo de emisión a texto descriptivo
        """
        tipos_emision = {
            "1": "Emisión Normal",
            "2": "Emisión por Indisponibilidad del Sistema"
        }
        return tipos_emision.get(self.tipo_emision, f"Emisión tipo {self.tipo_emision}")
    
    def is_authorized(self) -> bool:
        """
        Verifica si el documento está autorizado
        """
        return self.estado_autorizacion.upper() == "AUTORIZADO"
    
    def to_dict(self) -> dict:
        """
        Convierte la instancia a diccionario para fácil serialización
        """
        return {
            "email_destinatario": self.email_destinatario,
            "clave_acceso": self.clave_acceso,
            "total_con_impuestos": self.total_con_impuestos,
            "razon_social": self.razon_social,
            "razon_social_comprador": self.razon_social_comprador,
            "fecha_emision": self.fecha_emision,
            "numero_factura": self.numero_factura,
            "estab": self.estab,
            "pto_emi": self.pto_emi,
            "secuencial": self.secuencial,
            "numero_autorizacion": self.numero_autorizacion,
            "codigo_documento": self.codigo_documento,
            "tipo_emision": self.tipo_emision,
            "fecha_autorizacion": self.fecha_autorizacion,
            "estado_autorizacion": self.estado_autorizacion,
            "numero_comprobante": self.get_numero_comprobante(),
            "tipo_documento_texto": self.get_tipo_documento_texto(),
            "tipo_emision_texto": self.get_tipo_emision_texto(),
            "is_authorized": self.is_authorized()
        }