# @author: MembaCo.

import logging
import time
import requests
import os
import uuid
from pathlib import Path

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
    hdfilmcehennemi için video kaynağını bulan, manifesti düzelten ve
    gelişmiş bot korumalarını aşan en kararlı worker.
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
            # undetected_chromedriver'ı selenium-wire ile birleştiren hibrit yapı
            patcher = uc.Patcher()
            executable_path = patcher.executable_path
            service = Service(executable_path=executable_path)
            driver = sw_webdriver.Chrome(service=service, options=options)

            # Bot algılamayı önlemek için en etkili script
            driver.execute_cdp_cmd(
                "Page.addScriptToEvaluateOnNewDocument",
                {
                    "source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined});"
                },
            )

            wait = WebDriverWait(driver, 45)
            logger.info(f"Sayfa yükleniyor: {target_url}")
            driver.get(target_url)
            time.sleep(5)  # Sayfanın kendine gelmesi için bekle

            # Ana oynatıcı konteynerine tıkla
            play_button_main = wait.until(
                EC.presence_of_element_located((By.ID, "fimcnt"))
            )
            driver.execute_script("arguments[0].click();", play_button_main)

            # Video iframe'ine geçiş yap
            iframe_locator = (By.CSS_SELECTOR, ".play-box-iframe iframe")
            wait.until(EC.frame_to_be_available_and_switch_to_it(iframe_locator))

            # Ağ isteklerini temizle, böylece sadece video isteğini yakalarız
            del driver.requests

            # Iframe içindeki oynatıcıya tıkla
            play_button_iframe = wait.until(
                EC.element_to_be_clickable((By.ID, "player"))
            )
            driver.execute_script("arguments[0].click();", play_button_iframe)
            logger.info("Manifest URL'si için ağ istekleri dinleniyor...")

            manifest_url, manifest_request = None, None
            end_time = time.time() + 45  # 45 saniye boyunca manifest ara
            while time.time() < end_time and not manifest_url:
                for req in driver.requests:
                    if any(kw in req.url for kw in config.VIDEO_KEYWORDS):
                        manifest_url, manifest_request = req.url, req
                        break
                time.sleep(0.5)

            if not manifest_url:
                raise TimeoutException(
                    "Manifest URL'si belirtilen sürede yakalanamadı."
                )
            logger.info(f"✅ BAŞARILI: Manifest URL'si bulundu: {manifest_url}")

            # Manifesti indir ve içeriğini düzelt (.png -> .ts)
            manifest_content = requests.get(
                manifest_url, headers=manifest_request.headers
            ).text
            corrected_content = manifest_content.replace(".png", ".ts")
            logger.info("Manifest içeriğindeki .png uzantıları .ts olarak düzeltildi.")

            # Geçici manifest dosyasını oluştur
            temp_manifest_dir = Path(config.DATA_DIR) / "temp_manifests"
            temp_manifest_dir.mkdir(parents=True, exist_ok=True)
            temp_manifest_filename = f"{uuid.uuid4()}.m3u8"
            temp_manifest_path = temp_manifest_dir / temp_manifest_filename

            with open(temp_manifest_path, "w", encoding="utf-8") as f:
                f.write(corrected_content)
            logger.info(
                f"Düzeltilmiş manifest uygulama dizinine kaydedildi: {temp_manifest_path}"
            )

            # yt-dlp'ye gönderilecek başlıkları hazırla
            headers_to_pass = {k: v for k, v in manifest_request.headers.items()}
            headers_to_pass["Referer"] = target_url  # Ana sayfanın referer'ı önemli

            return str(temp_manifest_path), headers_to_pass, driver.get_cookies()

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
                f"hdfilmcehennemi worker'ında beklenmedik bir hata: {e}", exc_info=True
            )
            return None, None, None
        finally:
            if driver:
                driver.quit()
