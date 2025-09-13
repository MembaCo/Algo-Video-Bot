# @author: MembaCo.

import logging
import re
import time

# DEĞİŞİKLİK: İki kütüphaneyi birleştirmek için gerekli importlar
from seleniumwire import webdriver as sw_webdriver
from selenium.webdriver.chrome.service import Service
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
    undetected-chromedriver ve selenium-wire'ı birleştirerek en yüksek başarıyı hedefleyen worker.
    """

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
                "hdfilmcehennemi için hibrit (uc+selenium-wire) tarayıcı yapılandırılıyor..."
            )

            # DEĞİŞİKLİK: undetected-chromedriver ile sürücüyü yamala
            patcher = uc.Patcher()
            executable_path = patcher.executable_path
            service = Service(executable_path=executable_path)

            # DEĞİŞİKLİK: Yamalanmış sürücüyü selenium-wire ile başlat
            # Bu bize hem gizlilik hem de .requests özelliğini verir
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

            logger.info("Bot kontrollerinin geçmesi için bekleniyor...")
            time.sleep(5)

            play_button_main = wait.until(
                EC.presence_of_element_located((By.ID, "fimcnt"))
            )
            driver.execute_script("arguments[0].click();", play_button_main)

            iframe_locator = (By.CSS_SELECTOR, ".play-box-iframe iframe")
            wait.until(EC.frame_to_be_available_and_switch_to_it(iframe_locator))

            del driver.requests

            play_button_iframe = wait.until(
                EC.element_to_be_clickable((By.ID, "player"))
            )
            driver.execute_script("arguments[0].click();", play_button_iframe)

            logger.info("Manifest URL'si ağ istekleri arasında aranıyor...")

            end_time = time.time() + 45
            manifest_url = None
            while time.time() < end_time:
                # artık driver.requests hata vermeyecek
                for req in driver.requests:
                    for keyword in config.VIDEO_KEYWORDS:
                        if keyword in req.url:
                            manifest_url = req.url
                            break
                    if manifest_url:
                        break
                if manifest_url:
                    break
                time.sleep(0.5)

            if not manifest_url:
                raise TimeoutException(
                    "Manifest URL'si belirtilen sürede yakalanamadı."
                )

            logger.info(f"✅ BAŞARILI: Manifest URL'si bulundu: {manifest_url}")

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
                driver.quit()
