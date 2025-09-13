# @author: MembaCo.

import logging
import time
import re
import os
from seleniumwire import webdriver as sw_webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import undetected_chromedriver as uc
from .base_worker import BaseWorker
import config

logger = logging.getLogger(__name__)


class IzleInWorker(BaseWorker):
    """izle.in için video kaynağını bulan gelişmiş worker."""

    def find_manifest_url(self, target_url):
        options = sw_webdriver.ChromeOptions()
        options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument(f"user-agent={config.USER_AGENT}")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option("useAutomationExtension", False)
        options.add_argument("--log-level=3")
        options.add_argument("--mute-audio")

        driver = None
        try:
            logger.info("izle.in için gelişmiş tarayıcı yapılandırılıyor...")
            patcher = uc.Patcher()
            executable_path = patcher.executable_path
            service = Service(executable_path=executable_path)
            driver = sw_webdriver.Chrome(service=service, options=options)

            driver.block_requests(urls=["*devtools-console-detect*"])
            logger.info("Anti-debug script'i için URL blokajı aktif edildi.")

            driver.execute_cdp_cmd(
                "Page.addScriptToEvaluateOnNewDocument",
                {
                    "source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
                },
            )

            wait = WebDriverWait(driver, 45)
            driver.get(target_url)
            time.sleep(2)

            iframe_locator = (By.CSS_SELECTOR, ".video-content iframe")
            wait.until(EC.frame_to_be_available_and_switch_to_it(iframe_locator))
            logger.info("Video iframe'ine başarıyla geçiş yapıldı.")
            time.sleep(2)

            play_button_selector = (
                By.CSS_SELECTOR,
                "[class*='vjs-big-play-button'], [aria-label*='Play'], [class*='play_button']",
            )
            play_button = wait.until(EC.element_to_be_clickable(play_button_selector))
            del driver.requests
            logger.info("Oynat butonu bulundu, tıklama yapılıyor...")
            driver.execute_script("arguments[0].click();", play_button)

            request = driver.wait_for_request(
                r".*(" + "|".join(re.escape(k) for k in config.VIDEO_KEYWORDS) + r").*",
                timeout=45,
            )
            logger.info(f"✅ BAŞARILI: Manifest URL'si bulundu: {request.url}")
            return request.url, dict(request.headers), driver.get_cookies()

        finally:
            if driver:
                driver.quit()
