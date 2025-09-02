import logging
from logging.handlers import TimedRotatingFileHandler
import os
from config import settings
from datetime import datetime, timedelta

LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'log')
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, f"email_service.log")

handler = TimedRotatingFileHandler(LOG_FILE, when="midnight", interval=1, backupCount=0, encoding="utf-8")
handler.suffix = "%Y-%m-%d"
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)

logger = logging.getLogger("email_service")
logger.setLevel(getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO))
logger.addHandler(handler)
logger.addHandler(logging.StreamHandler())

# Eliminar logs antiguos según RETENTION_LOG
def cleanup_old_logs():
    retention_days = int(getattr(settings, 'RETENTION_LOG', 7))
    now = datetime.now()
    for fname in os.listdir(LOG_DIR):
        if fname.startswith("email_service.log."):
            try:
                date_str = fname.split(".")[-1]
                log_date = datetime.strptime(date_str, "%Y-%m-%d")
                if (now - log_date).days > retention_days:
                    os.remove(os.path.join(LOG_DIR, fname))
                    logger.info(f"Log antiguo eliminado: {fname}")
            except Exception:
                pass

cleanup_old_logs()