import xml.etree.ElementTree as ET
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from io import BytesIO

def generar_pdf(xml_file, pdf_file=None):
    tree = ET.parse(xml_file)
    root = tree.getroot()

    # estilos
    styles = getSampleStyleSheet()
    elementos = []

    # ejemplo: obtener RUC y datos principales
    ruc_emisor = root.findtext(".//RucEmisor")  # ajustar según estructura real
    razon_social = root.findtext(".//RazonSocial")
    cliente = root.findtext(".//RazonSocialComprador")

    elementos.append(Paragraph(f"<b>RUC:</b> {ruc_emisor}", styles['Normal']))
    elementos.append(Paragraph(f"<b>FACTURA:</b> {razon_social}", styles['Normal']))
    elementos.append(Paragraph(f"<b>CLIENTE:</b> {cliente}", styles['Normal']))
    elementos.append(Spacer(1, 12))

    # ejemplo tabla productos
    data = [["Código", "Descripción", "Cant.", "P.Unit", "Desc.", "Total"]]
    for det in root.findall(".//detalle"):
        codigo = det.findtext("codigoPrincipal")
        desc = det.findtext("descripcion")
        cant = det.findtext("cantidad")
        precio = det.findtext("precioUnitario")
        descu = det.findtext("descuento")
        total = det.findtext("precioTotalSinImpuesto")
        data.append([codigo, desc, cant, precio, descu, total])

    tabla = Table(data, repeatRows=1)
    tabla.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), colors.grey),
        ("TEXTCOLOR", (0,0), (-1,0), colors.whitesmoke),
        ("ALIGN", (0,0), (-1,-1), "CENTER"),
        ("GRID", (0,0), (-1,-1), 0.5, colors.black)
    ]))
    elementos.append(tabla)

    # ejemplo totales
    total_con_impuestos = root.findtext(".//importeTotal")
    elementos.append(Spacer(1, 12))
    elementos.append(Paragraph(f"<b>Total:</b> {total_con_impuestos}", styles['Normal']))

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    doc.build(elementos)
    pdf_bytes = buffer.getvalue()
    buffer.close()

    if pdf_file:
        with open(pdf_file, 'wb') as f:
            f.write(pdf_bytes)

    return pdf_bytes

# ejecutar
generar_pdf(
    "FACTURA_0708202501099284045500120010010000062191234567816_AUTORIZADO_1.xml",
    "factura_generada.pdf"
)

# Ejemplo de uso para adjuntar en correo:
# pdf_bytes = generar_pdf("factura.xml")
# send_email(..., attachments=[("factura.pdf", pdf_bytes)])
