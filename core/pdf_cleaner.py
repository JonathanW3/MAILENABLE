import fitz  # PyMuPDF
import io

def limpiar_logo_pdf(pdf_bytes: bytes) -> bytes:
    """
    Recibe un PDF en bytes, elimina el área del logo en cada página y retorna el PDF limpio en bytes.
    """
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    for page in doc:
        rect = fitz.Rect(0, page.rect.height - 100, page.rect.width, page.rect.height)
        page.add_redact_annot(rect, fill=(1, 1, 1))
        page.apply_redactions()
    output = io.BytesIO()
    doc.save(output)
    doc.close()
    return output.getvalue()
