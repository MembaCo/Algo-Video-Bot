# @author: MembaCo.

import logging
import re
import threading
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
from .base_worker import BaseWorker
import config

logger = logging.getLogger(__name__)


class HdfilmcehennemiWorker(BaseWorker):
    """
    hdfilmcehennemi için video kaynağını bulan,
    CDP Fetch domain'ini kullanarak ağ isteklerini yöneten en gelişmiş worker.
    """

    def find_manifest_url(self, target_url):
        options = uc.ChromeOptions()
        # options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument(f"user-agent={config.USER_AGENT}")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--log-level=3")
        options.add_argument("--mute-audio")

        driver = None
        # Thread'ler arası veri aktarımı için event ve değişkenler
        manifest_url_found = threading.Event()
        manifest_url_holder = {"url": None}
        block_patterns = ["devtools-detector.js", "debugger"]

        def request_paused_handler(params):
            """Her duraklatılan ağ isteğinde çalışacak olan fonksiyon."""
            request_id = params["requestId"]
            url = params["request"]["url"]

            # İsteğin engellenip engellenmeyeceğini kontrol et
            should_block = any(pattern in url for pattern in block_patterns)

            if should_block:
                try:
                    driver.execute_cdp_cmd(
                        "Fetch.failRequest",
                        {"requestId": request_id, "errorReason": "BlockedByClient"},
                    )
                except WebDriverException:
                    # Tarayıcı kapanmışsa hata almamak için
                    pass
                return

            # Manifest URL'sini yakala
            if not manifest_url_holder["url"]:
                for keyword in config.VIDEO_KEYWORDS:
                    if keyword in url:
                        manifest_url_holder["url"] = url
                        manifest_url_found.set()  # Ana thread'e sinyal gönder
                        break

            # Geri kalan tüm isteklere devam etmelerini söyle
            try:
                driver.execute_cdp_cmd(
                    "Fetch.continueRequest", {"requestId": request_id}
                )
            except WebDriverException:
                pass

        try:
            logger.info(
                "hdfilmcehennemi için CDP Fetch tabanlı 'undetected' tarayıcı yapılandırılıyor..."
            )
            driver = uc.Chrome(options=options, use_subprocess=True)

            # --- KORUMA KALKANI ---
            driver.execute_cdp_cmd(
                "Page.addScriptToEvaluateOnNewDocument",
                {
                    "source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined});"
                },
            )
            # --- KORUMA KALKANI SONU ---

            # Önerdiğiniz gibi Fetch domain'ini etkinleştir ve dinleyiciyi ekle
            driver.execute_cdp_cmd("Fetch.enable", {"patterns": [{"urlPattern": "*"}]})
            driver.add_cdp_listener("Fetch.requestPaused", request_paused_handler)
            logger.info("CDP Fetch.requestPaused dinleyicisi aktif edildi.")

            wait = WebDriverWait(driver, 45)
            driver.get(target_url)

            play_button_main = wait.until(EC.element_to_be_clickable((By.ID, "fimcnt")))
            driver.execute_script("arguments[0].click();", play_button_main)

            iframe_locator = (By.CSS_SELECTOR, ".play-box-iframe iframe")
            wait.until(EC.frame_to_be_available_and_switch_to_it(iframe_locator))

            play_button_iframe = wait.until(
                EC.element_to_be_clickable((By.ID, "player"))
            )
            driver.execute_script("arguments[0].click();", play_button_iframe)

            # Manifest URL'sinin bulunması için sinyali bekle (maksimum 45 saniye)
            found = manifest_url_found.wait(timeout=45)
            if not found or not manifest_url_holder["url"]:
                raise TimeoutException(
                    "Manifest URL'si belirtilen sürede yakalanamadı."
                )

            manifest_url = manifest_url_holder["url"]
            logger.info(
                f"✅ BAŞARILI: Manifest URL'si CDP Fetch ile bulundu: {manifest_url}"
            )

            return manifest_url, {}, driver.get_cookies()

        except WebDriverException as e:
            logger.error(f"Tarayıcı hatası oluştu: {e.msg}", exc_info=True)
            return None, None, None
        except TimeoutException as e:
            logger.error(
                f"Bir element beklenirken veya manifest yakalanamazken zaman aşımına uğradı: {e}",
                exc_info=True,
            )
            return None, None, None
        except Exception as e:
            logger.error(
                f"hdfilmcehennemi worker'ında beklenmedik bir hata oluştu: {e}",
                exc_info=True,
            )
            return None, None, None
        finally:
            if driver:
                # Dinleyiciyi ve Fetch domain'ini temizle
                driver.clear_cdp_listeners()
                try:
                    driver.execute_cdp_cmd("Fetch.disable", {})
                except WebDriverException:
                    pass  # Tarayıcı zaten kapandıysa hata vermesini engelle
                driver.quit()
