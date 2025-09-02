import os
from dotenv import load_dotenv

load_dotenv()

ENVIRONMENT = os.getenv("ENVIRONMENT", "test").lower()
TEST_EMAIL = os.getenv("TEST_EMAIL")
MONITOR_EMAIL = os.getenv("MONITOR_EMAIL", "jalcoser@webpospanama.com")

POP_SERVER = os.getenv('POP_SERVER', 'mail.webpossa.com')
POP_PORT = int(os.getenv('POP_PORT', '110'))
POP_USER = os.getenv('POP_USER', 'webpos_inbox@webpossa.com')
POP_PASSWORD = os.getenv('POP_PASSWORD', 'password')

SMTP_SERVER = os.getenv('SMTP_SERVER', 'mail.webpossa.com')
SMTP_PORT = int(os.getenv('SMTP_PORT', '587'))
SMTP_USER = os.getenv('SMTP_USER', 'edelivery@webpossa.com')
SMTP_PASSWORD = os.getenv('SMTP_PASSWORD', 'password')
SMTP_USE_SSL = os.getenv('SMTP_USE_SSL', 'true').lower() == 'true'

IMAP_SERVER = os.getenv('IMAP_SERVER', 'mail.webpossa.com')
IMAP_PORT = int(os.getenv('IMAP_PORT', '993'))
IMAP_USER = os.getenv('IMAP_USER', 'webpos_inbox@webpossa.com')
IMAP_PASSWORD = os.getenv('IMAP_PASSWORD', 'QD4$xG')
IMAP_USE_SSL = os.getenv('IMAP_USE_SSL', 'true').lower() == 'true'

CHECK_INTERVAL = int(os.getenv('CHECK_INTERVAL', '30'))

TEMPLATES_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'templates')
RETENTION_LOG = int(os.getenv('RETENTION_LOG', '7'))
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')