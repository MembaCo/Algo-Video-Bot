# @author: MembaCo.

import logging
from urllib.parse import urlparse
from .hdfilmcehennemi_worker import HdfilmcehennemiWorker
from .izle_in_worker import IzleInWorker
import config

logger = logging.getLogger(__name__)

# config.py'daki domain adını worker sınıfıyla eşleştiriyoruz
AVAILABLE_WORKERS = {
    "hdfilmcehennemi": HdfilmcehennemiWorker,
    "izlein": IzleInWorker,
}


def get_worker_for_url(url):
    """Verilen URL'nin domain'ine göre uygun worker'ı döndürür."""
    try:
        domain = urlparse(url).netloc.replace("www.", "")
        scraper_key = config.SUPPORTED_DOMAINS.get(domain)

        if scraper_key and scraper_key in AVAILABLE_WORKERS:
            worker_class = AVAILABLE_WORKERS[scraper_key]
            logger.info(f"{domain} için '{worker_class.__name__}' worker'ı seçildi.")
            return worker_class()

        logger.error(f"Desteklenmeyen domain: {domain}")
        return None
    except Exception as e:
        logger.error(f"Worker seçilirken hata oluştu: {e}", exc_info=True)
        return None
