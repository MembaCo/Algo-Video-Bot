# @author: MembaCo.

import logging
import time
import re
from seleniumwire import webdriver as sw_webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import undetected_chromedriver as uc
from selenium.common.exceptions import TimeoutException, WebDriverException
from .base_worker import BaseWorker
import config

logger = logging.getLogger(__name__)


class IzleInWorker(BaseWorker):
    """izle.in için video kaynağını bulan gelişmiş worker."""

    def find_manifest_url(self, target_url):
        options = uc.ChromeOptions()
        options.page_load_strategy = "eager"
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument(f"--user-agent={config.USER_AGENT}")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--start-maximized")
        options.add_argument("--log-level=3")
        options.add_argument("--mute-audio")

        driver = None
        try:
            logger.info(
                "izle.in için hibrit (uc+selenium-wire) tarayıcı yapılandırılıyor..."
            )
            patcher = uc.Patcher()
            executable_path = patcher.executable_path
            service = Service(executable_path=executable_path)
            driver = sw_webdriver.Chrome(service=service, options=options)

            driver.execute_cdp_cmd(
                "Page.addScriptToEvaluateOnNewDocument",
                {
                    "source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined});"
                },
            )

            wait = WebDriverWait(driver, 30)
            logger.info(f"Sayfa yükleniyor: {target_url}")
            driver.get(target_url)
            time.sleep(3)  # Sayfanın kendine gelmesi için kısa bir bekleme

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

            logger.info("Manifest URL'si ağ istekleri arasında aranıyor...")
            end_time = time.time() + 45
            manifest_url = None
            manifest_request = None
            while time.time() < end_time:
                for req in driver.requests:
                    for keyword in config.VIDEO_KEYWORDS:
                        if keyword in req.url:
                            manifest_url = req.url
                            manifest_request = req
                            break
                    if manifest_url:
                        break
                if manifest_url:
                    break
                time.sleep(0.5)

            if not manifest_url or not manifest_request:
                raise TimeoutException(
                    "Manifest URL'si veya isteği belirtilen sürede yakalanamadı."
                )

            logger.info(f"✅ BAŞARILI: Manifest URL'si bulundu: {manifest_url}")

            headers_to_pass = {
                key: value for key, value in manifest_request.headers.items()
            }
            headers_to_pass["Referer"] = target_url

            return manifest_url, headers_to_pass, driver.get_cookies()

        except WebDriverException as e:
            logger.error(f"Tarayıcı hatası oluştu: {e.msg}", exc_info=True)
            return None, None, None
        except TimeoutException as e:
            logger.error(
                f"Bir element beklenirken zaman aşımına uğradı: {e}", exc_info=True
            )
            return None, None, None
        except Exception as e:
            logger.error(
                f"izle.in worker'ında beklenmedik bir hata oluştu: {e}", exc_info=True
            )
            return None, None, None
        finally:
            if driver:
                driver.quit()
