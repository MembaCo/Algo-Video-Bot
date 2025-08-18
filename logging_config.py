# @author: MembaCo.

import logging
from logging.handlers import RotatingFileHandler
import sys
import os

LOG_FILE = "app.log"


def setup_logging():
    """Uygulama genelinde kullanılacak merkezi loglama yapılandırmasını kurar."""

    # Kök logger'ı al ve seviyesini ayarla. INFO ve üzeri seviyedeki tüm logları yakalar.
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    # Zaten bir handler eklenmişse (örn. web sunucusu tarafından), tekrar ekleme.
    if logger.hasHandlers():
        logger.handlers.clear()

    # Log mesajlarının formatını belirle
    # Zaman - Logger Adı - Seviye - Süreç ID - Mesaj
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(process)d - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Konsola log basacak handler
    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setFormatter(formatter)

    # Dosyaya log yazacak handler (5 MB'de bir dosya değiştirir, 5 eski dosya saklar)
    if not os.path.exists(os.path.dirname(LOG_FILE)) and os.path.dirname(LOG_FILE):
        os.makedirs(os.path.dirname(LOG_FILE))

    file_handler = RotatingFileHandler(
        LOG_FILE, maxBytes=1024 * 1024 * 5, backupCount=5, encoding="utf-8"
    )
    file_handler.setFormatter(formatter)

    # Handler'ları logger'a ekle
    logger.addHandler(stdout_handler)
    logger.addHandler(file_handler)

    # logger.info("Loglama sistemi başarıyla başlatıldı.")
    return logger
