from jinja2 import Template
from datetime import datetime
from core.xml_data import XMLData
from jinja2 import Environment, FileSystemLoader
from config import settings

env = Environment(loader=FileSystemLoader(settings.TEMPLATES_DIR))

import os
TEMPLATES_DIR = os.path.join(os.path.dirname(__file__), '../templates')

processing_template_str = """<html><body><h1>Procesamiento XML</h1>
<p>Email destino: {{ email_extraido }}</p></body></html>"""

client_template_str = """<html><body><h1>Documento Electrónico</h1>
<p>Cliente: {{ razon_social }}</p></body></html>"""

def render_processing_template(xml_data: XMLData, email_origen: str, xml_filename: str, adjuntos: list) -> str:
    template = Template(processing_template_str)
    return template.render(
        fecha_procesamiento=datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
        entorno="TEST",
        email_origen=email_origen,
        xml_filename=xml_filename,
        email_extraido=xml_data.email_destinatario,
        clave_acceso=xml_data.clave_acceso,
        total=xml_data.total_con_impuestos,
        razon_social=xml_data.razon_social,
        fecha_emision=xml_data.fecha_emision,
        numero_factura=xml_data.numero_factura,
        adjuntos_procesados=adjuntos
    )

def render_client_template(xml_data: XMLData) -> str:
    template = Template(client_template_str)
    return template.render(
        razon_social=xml_data.razon_social or "Cliente",
        clave_acceso=xml_data.clave_acceso,
        total=xml_data.total_con_impuestos
    )

def test_processing_template():
    xml_data = XMLData(email_destinatario="test@example.com", clave_acceso="123", total_con_impuestos="10.00", razon_social="Empresa Test")
    return render_processing_template(xml_data, "origen@test.com", "archivo.xml", ["archivo.xml"])

def test_client_template():
    xml_data = XMLData(email_destinatario="cliente@example.com", clave_acceso="123", total_con_impuestos="50.00", razon_social="Cliente Test")
    return render_client_template(xml_data)

# --- Clase TemplatesService ---
class TemplatesService:
    @staticmethod
    def render_processing_template(xml_data: XMLData, email_origen: str, xml_filename: str, adjuntos: list) -> str:
        return render_processing_template(xml_data, email_origen, xml_filename, adjuntos)

    @staticmethod
    def render_client_template(xml_data: XMLData) -> str:
        return render_client_template(xml_data)

    @staticmethod
    def test_processing_template():
        return test_processing_template()

    @staticmethod
    def test_client_template():
        return test_client_template()

    @staticmethod
    def render(template_name: str, context: dict) -> str:
        # Usa la instancia global 'env' definida arriba
        global env
        template = env.get_template(template_name)
        return template.render(**context)