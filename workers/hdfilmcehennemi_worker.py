# @author: MembaCo.

import logging
import time
import re  # EKSİK OLAN IMPORT EKLENDİ
from seleniumwire import webdriver as sw_webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from .base_worker import BaseWorker
import config

logger = logging.getLogger(__name__)


class HdfilmcehennemiWorker(BaseWorker):
    """hdfilmcehennemi.ltd için video kaynağını bulan worker."""

    def find_manifest_url(self, target_url):
        options = sw_webdriver.ChromeOptions()
        options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--log-level=3")
        options.add_argument("--mute-audio")
        options.add_argument(f"user-agent={config.USER_AGENT}")

        driver = None
        try:
            logger.info("hdfilmcehennemi için standart tarayıcı yapılandırılıyor...")
            service = Service()
            driver = sw_webdriver.Chrome(service=service, options=options)
            wait = WebDriverWait(driver, 30)

            driver.get(target_url)
            logger.info("hdfilmcehennemi sitesi için mantık çalıştırılıyor.")

            play_button_main = wait.until(EC.element_to_be_clickable((By.ID, "fimcnt")))
            driver.execute_script("arguments[0].click();", play_button_main)

            iframe_locator = (By.CSS_SELECTOR, ".play-box-iframe iframe")
            wait.until(EC.frame_to_be_available_and_switch_to_it(iframe_locator))

            play_button_iframe = wait.until(
                EC.element_to_be_clickable((By.ID, "player"))
            )
            del driver.requests
            driver.execute_script("arguments[0].click();", play_button_iframe)

            request = driver.wait_for_request(
                r".*(" + "|".join(re.escape(k) for k in config.VIDEO_KEYWORDS) + r").*",
                timeout=45,
            )
            logger.info(f"✅ BAŞARILI: Manifest URL'si bulundu: {request.url}")
            return request.url, dict(request.headers), driver.get_cookies()

        finally:
            if driver:
                driver.quit()
