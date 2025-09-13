# @author: MembaCo.

import logging
import re
import time
import requests
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

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
    hdfilmcehennemi için token-aware video kaynağını bulan,
    undetected-chromedriver ve selenium-wire'ı birleştirerek en yüksek başarıyı hedefleyen worker.
    """

    def _extract_tokens_from_requests(self, requests):
        """Tüm request'lerden token'ları ve önemli parametreleri çıkarır"""
        tokens = {}
        patterns = [
            r"token=([^&]+)",
            r"auth=([^&]+)",
            r"signature=([^&]+)",
            r"key=([^&]+)",
            r"session=([^&]+)",
            r"t=([^&]+)",
            r"hash=([^&]+)",
            r"verify=([^&]+)",
        ]

        for req in requests:
            url = req.url
            # URL'den parametreleri çıkar
            parsed_url = urlparse(url)
            params = parse_qs(parsed_url.query)

            for pattern in patterns:
                matches = re.findall(pattern, url)
                if matches:
                    param_name = (
                        pattern.split("=")[0].replace(r"\b", "").replace("(", "")
                    )
                    tokens[param_name] = matches[0]

        logger.info(f"Bulunan token'lar: {list(tokens.keys())}")
        return tokens

    def _get_manifest_with_tokens(self, manifest_url, tokens, headers):
        """Token'ları kullanarak manifest içeriğini alır ve segment URL'lerini günceller"""
        try:
            # Manifest'i indir
            response = requests.get(manifest_url, headers=headers, timeout=30)
            response.raise_for_status()
            manifest_content = response.text

            logger.info(f"Manifest içeriği alındı ({len(manifest_content)} karakter)")

            # Segment URL'lerini token'larla güncelle
            lines = manifest_content.split("\n")
            updated_lines = []

            for line in lines:
                if line.startswith("http"):
                    # Bu bir segment URL'si
                    parsed_url = urlparse(line)
                    existing_params = parse_qs(parsed_url.query)

                    # Token'ları ekle
                    for token_name, token_value in tokens.items():
                        existing_params[token_name] = [token_value]

                    # URL'yi yeniden oluştur
                    new_query = urlencode(existing_params, doseq=True)
                    updated_url = urlunparse(
                        (
                            parsed_url.scheme,
                            parsed_url.netloc,
                            parsed_url.path,
                            parsed_url.params,
                            new_query,
                            parsed_url.fragment,
                        )
                    )
                    updated_lines.append(updated_url)
                else:
                    updated_lines.append(line)

            updated_manifest = "\n".join(updated_lines)
            logger.info("Manifest token'larla güncellendi")
            return updated_manifest

        except Exception as e:
            logger.error(f"Manifest token güncellemesi başarısız: {e}")
            return None

    def find_manifest_url(self, target_url):
        # Anti-bot script'lerini engellemek için request blocking konfigürasyonu
        seleniumwire_options = {
            "block_requests": [
                # DevTools detector'ları ve diğer anti-bot script'lerini engelle
                ".*devtools.*",
                ".*detector.*",
                ".*antibot.*",
                ".*bot.*detect.*",
                # Bilinen anti-bot script dosyalarını engelle
                ".*devtools-detector.*",
                ".*console.*detect.*",
                ".*webdriver.*detect.*",
            ]
        }

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
        # Ek güvenlik parametreleri
        options.add_argument("--disable-web-security")
        options.add_argument("--allow-running-insecure-content")

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
            driver = sw_webdriver.Chrome(
                service=service,
                options=options,
                seleniumwire_options=seleniumwire_options,
            )

            driver.execute_cdp_cmd(
                "Page.addScriptToEvaluateOnNewDocument",
                {
                    "source": """
                        Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
                        Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
                        Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']});
                        window.chrome = {runtime: {}};
                        
                        // Video oynatımını simüle etmek için ek JavaScript
                        window.addEventListener('load', function() {
                            setTimeout(function() {
                                const videos = document.querySelectorAll('video');
                                videos.forEach(video => {
                                    try {
                                        video.muted = true;
                                        video.play().catch(e => {});
                                    } catch(e) {}
                                });
                            }, 2000);
                        });
                    """
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

            # Request'leri temizle
            del driver.requests

            play_button_iframe = wait.until(
                EC.element_to_be_clickable((By.ID, "player"))
            )
            driver.execute_script("arguments[0].click();", play_button_iframe)

            # Video oynatımının başlaması ve daha fazla request için bekle
            logger.info(
                "Video oynatımının başlaması ve token'ların yakalanması için bekleniyor..."
            )
            time.sleep(15)  # Daha uzun bekleme

            logger.info("Tüm video request'leri analiz ediliyor...")

            # Tüm video ile ilgili request'leri topla
            all_requests = list(driver.requests)
            video_requests = []
            manifest_url = None
            manifest_request = None

            for req in all_requests:
                # Video ile ilgili tüm request'leri topla
                if any(
                    keyword in req.url.lower()
                    for keyword in [".m3u8", ".ts", "manifest", "playlist", "segment"]
                ):
                    video_requests.append(req)
                    logger.info(f"Video request bulundu: {req.url[:100]}...")

                # Ana manifest'i bul
                for keyword in config.VIDEO_KEYWORDS:
                    if keyword in req.url:
                        manifest_url = req.url
                        manifest_request = req
                        break

            if not manifest_url:
                logger.warning(
                    "Ana manifest bulunamadı, alternatif yöntemler deneniyor..."
                )
                # m3u8 URL'leri arasından en uzun olanını seç
                m3u8_requests = [req for req in video_requests if ".m3u8" in req.url]
                if m3u8_requests:
                    manifest_request = max(m3u8_requests, key=lambda x: len(x.url))
                    manifest_url = manifest_request.url
                    logger.info(f"Alternatif manifest bulundu: {manifest_url}")

            if not manifest_url:
                raise TimeoutException("Manifest URL'si hiçbir yöntemle bulunamadı.")

            logger.info(f"✅ BAŞARILI: Manifest URL'si bulundu: {manifest_url}")

            # Token'ları çıkar
            tokens = self._extract_tokens_from_requests(video_requests)

            # Header'ları hazırla
            headers_to_pass = {}
            if manifest_request and manifest_request.headers:
                critical_headers = [
                    "User-Agent",
                    "Accept",
                    "Accept-Language",
                    "Accept-Encoding",
                ]
                for header_name in critical_headers:
                    if header_name in manifest_request.headers:
                        headers_to_pass[header_name] = manifest_request.headers[
                            header_name
                        ]

            # Referer header'ını ekle
            headers_to_pass["Referer"] = target_url

            logger.info(f"yt-dlp'ye gönderilecek header'lar: {headers_to_pass}")

            # Cookies'leri al
            cookies = driver.get_cookies()

            # Eğer token bulunduysa, manifest'i güncelle
            if tokens:
                logger.info("Token'larla güncellenmiş manifest oluşturuluyor...")
                updated_manifest = self._get_manifest_with_tokens(
                    manifest_url, tokens, headers_to_pass
                )
                if updated_manifest:
                    # Güncellenmiş manifest'i geçici dosyaya kaydet
                    import tempfile

                    with tempfile.NamedTemporaryFile(
                        mode="w", suffix=".m3u8", delete=False
                    ) as f:
                        f.write(updated_manifest)
                        temp_manifest_path = f.name

                    logger.info(f"Token'lı manifest kaydedildi: {temp_manifest_path}")

                    # Özel metadata ile dön - worker.py'da bu kontrol edilecek
                    return (
                        manifest_url,
                        {
                            **headers_to_pass,
                            "_token_manifest_path": temp_manifest_path,  # Özel anahtar
                            "_original_manifest_url": manifest_url,
                            "_tokens": tokens,
                        },
                        cookies,
                    )

            return manifest_url, headers_to_pass, cookies

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
