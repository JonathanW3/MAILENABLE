from email.header import decode_header
from typing import List, Tuple
import email
from core.logger import logger

def extract_attachments(email_msg: email.message.Message) -> List[Tuple[str, bytes]]:
    attachments = []
    for part in email_msg.walk():
        if part.get_content_disposition() == 'attachment':
            filename = part.get_filename()
            if filename:
                decoded_filename = decode_header(filename)[0]
                if isinstance(decoded_filename[0], bytes):
                    filename = decoded_filename[0].decode(decoded_filename[1] or 'utf-8')
                else:
                    filename = decoded_filename[0]
                content = part.get_payload(decode=True)
                if content:
                    attachments.append((filename, content))
    logger.info(f"Encontrados {len(attachments)} adjuntos")
    return attachments