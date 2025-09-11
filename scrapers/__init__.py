# scrapers/__init__.py
import logging
from urllib.parse import urlparse
from .hdfilmcehennemi_scraper import HdfilmcehennemiScraper
import config

logger = logging.getLogger(__name__)

# Mevcut kazıyıcıları burada tanımlıyoruz
AVAILABLE_SCRAPERS = {
    "hdfilmcehennemi": HdfilmcehennemiScraper,
    # Gelecekte yeni bir site eklenirse -> "siteadi": SiteAdiScraper
}


def get_scraper_for_url(url):
    """Verilen URL'nin domain'ine göre uygun kazıyıcıyı döndürür."""
    try:
        domain = urlparse(url).netloc.replace("www.", "")
        scraper_key = config.SUPPORTED_DOMAINS.get(domain)
        if scraper_key and scraper_key in AVAILABLE_SCRAPERS:
            logger.info(f"{domain} için '{scraper_key}' kazıyıcısı seçildi.")
            return AVAILABLE_SCRAPERS[scraper_key]()
        logger.error(f"Desteklenmeyen domain: {domain}")
        return None
    except Exception as e:
        logger.error(f"Kazıyıcı seçilirken hata oluştu: {e}", exc_info=True)
        return None
