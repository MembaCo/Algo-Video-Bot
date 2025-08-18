# @author: MembaCo.

import sqlite3
import time
import subprocess
import re
import os
import sys
import logging
import glob
from seleniumwire import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import TimeoutException

# Yerel modüllerden importlar
import config
from database import get_db
from logging_config import setup_logging

logger = logging.getLogger(__name__)


def update_status(video_id, status=None, source_url=None, progress=None, filepath=None):
    """Veritabanındaki bir videonun durumunu, ilerlemesini veya dosya yolunu günceller."""
    db = get_db()
    if status:
        db.execute("UPDATE videos SET status = ? WHERE id = ?", (status, video_id))
    if source_url:
        db.execute(
            "UPDATE videos SET source_url = ? WHERE id = ?", (source_url, video_id)
        )
    if progress is not None:
        db.execute("UPDATE videos SET progress = ? WHERE id = ?", (progress, video_id))
    if filepath is not None:
        db.execute("UPDATE videos SET filepath = ? WHERE id = ?", (filepath, video_id))
    db.commit()
    db.close()


def find_manifest_url(target_url):
    """Selenium ile manifest URL'sini, gerekli headerları ve çerezleri bulur."""
    options = webdriver.ChromeOptions()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--log-level=3")
    options.add_argument("--mute-audio")
    options.add_argument(f"user-agent={config.USER_AGENT}")

    driver = None
    try:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        wait = WebDriverWait(driver, 30)
        driver.get(target_url)
        play_button_main = wait.until(EC.element_to_be_clickable((By.ID, "fimcnt")))
        driver.execute_script("arguments[0].click();", play_button_main)
        iframe_locator = (By.CSS_SELECTOR, ".play-box-iframe iframe")
        wait.until(EC.frame_to_be_available_and_switch_to_it(iframe_locator))
        iframe_src = driver.current_url
        play_button_iframe = wait.until(EC.element_to_be_clickable((By.ID, "player")))
        del driver.requests
        play_button_iframe.click()
        request = driver.wait_for_request(
            r".*(" + "|".join(re.escape(k) for k in config.VIDEO_KEYWORDS) + r").*",
            timeout=20,
        )
        logger.info(f"Manifest URL'si bulundu: {request.url}")
        headers = dict(request.headers)
        cookies = driver.get_cookies()
        return request.url, iframe_src, headers, cookies
    except TimeoutException:
        logger.warning(
            f"Manifest URL'si beklenirken zaman aşımına uğradı. URL: {target_url}"
        )
        return None, None, None, None
    finally:
        if driver:
            driver.quit()


def download_with_yt_dlp(
    video_id, manifest_url, headers, cookie_filepath, filename_template
):
    """yt-dlp ile videoyu indirir ve ilerlemeyi veritabanına yazar."""
    output_template = os.path.join(
        config.DOWNLOADS_FOLDER, f"{filename_template}.%(ext)s"
    )
    command = [
        "yt-dlp",
        "--cookies",
        cookie_filepath,
        "--no-check-certificates",
        "--no-color",
        "--progress",
        "--verbose",
        "--hls-use-mpegts",
        "-o",
        output_template,
    ]
    for key, value in headers.items():
        command.extend(["--add-header", f"{key}: {value}"])
    command.append(manifest_url)

    process = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        preexec_fn=os.setsid if sys.platform != "win32" else None,
    )
    full_output = ""
    for line_bytes in iter(process.stdout.readline, b""):
        line = line_bytes.decode("utf-8", errors="ignore")
        full_output += line
        progress_match = re.search(r"\[download\]\s+([0-9\.]+)%", line)
        if progress_match:
            try:
                progress = float(progress_match.group(1))
                update_status(video_id, progress=int(progress))
            except (ValueError, IndexError):
                continue
    process.wait()
    if process.returncode == 0:
        return True, "İndirme tamamlandı."
    else:
        return False, full_output


def process_video(video_id):
    """Tek bir video için tüm bulma ve indirme sürecini yönetir."""
    global logger
    logger = setup_logging()
    db = get_db()
    video = db.execute("SELECT * FROM videos WHERE id = ?", (video_id,)).fetchone()
    db.close()
    if not video:
        logger.error(f"Veritabanında video ID {video_id} bulunamadı.")
        return

    cookie_filepath = f"cookies_{video_id}.txt"
    try:
        logger.info(f"ID {video_id}: Kaynak adresi aranıyor... URL: {video['url']}")
        manifest_url, iframe_src, headers, cookies = find_manifest_url(video["url"])
        if manifest_url:
            with open(cookie_filepath, "w", encoding="utf-8") as f:
                f.write("# Netscape HTTP Cookie File\n")
                for cookie in cookies:
                    if "name" not in cookie or "value" not in cookie:
                        continue
                    domain = cookie.get("domain", "")
                    include_subdomains = "TRUE" if domain.startswith(".") else "FALSE"
                    path = cookie.get("path", "/")
                    secure = "TRUE" if cookie.get("secure") else "FALSE"
                    expiry = cookie.get("expiry")
                    expiry = int(expiry) if expiry is not None else 0
                    name = cookie["name"]
                    value = cookie["value"]
                    f.write(
                        f"{domain}\t{include_subdomains}\t{path}\t{secure}\t{expiry}\t{name}\t{value}\n"
                    )

            update_status(video_id, status="İndiriliyor", source_url=manifest_url)
            title = video["title"] or "Bilinmeyen Film"
            year = video["year"] or ""
            genre = video["genre"] or ""

            def to_ascii_safe(text):
                text = (
                    text.replace("ı", "i")
                    .replace("İ", "I")
                    .replace("ğ", "g")
                    .replace("Ğ", "G")
                )
                text = (
                    text.replace("ü", "u")
                    .replace("Ü", "U")
                    .replace("ş", "s")
                    .replace("Ş", "S")
                )
                text = (
                    text.replace("ö", "o")
                    .replace("Ö", "O")
                    .replace("ç", "c")
                    .replace("Ç", "C")
                )
                text = re.sub(r"[^\x00-\x7F]+", "", text)
                text = re.sub(r'[<>:"/\\|?*]', "", text).strip()
                return text

            clean_title = to_ascii_safe(title)
            clean_genre = to_ascii_safe(genre)
            filename_base = f"{clean_title} - {year} - {clean_genre}".strip(" -")

            logger.info(
                f"ID {video_id}: İndirme başlıyor. Güvenli (ASCII) dosya adı: {filename_base}"
            )

            success, message = download_with_yt_dlp(
                video_id, manifest_url, headers, cookie_filepath, filename_base
            )
            if success:
                search_pattern = os.path.join(
                    config.DOWNLOADS_FOLDER, f"{filename_base}.*"
                )
                files = glob.glob(search_pattern)
                if files:
                    final_filepath = files[0]
                    update_status(
                        video_id,
                        status="Tamamlandı",
                        progress=100,
                        filepath=final_filepath,
                    )
                    logger.info(
                        f"ID {video_id}: İndirme başarıyla tamamlandı. Dosya: {final_filepath}"
                    )
                else:
                    update_status(
                        video_id, status="Hata: Dosya bulunamadı", progress=100
                    )
                    logger.error(
                        f"ID {video_id}: İndirme başarılı görünse de dosya bulunamadı. Aranan: {search_pattern}"
                    )
            else:
                update_status(video_id, status="Hata: İndirilemedi")
                logger.error(f"ID {video_id}: İndirme hatası - {message}")
        else:
            update_status(video_id, status="Hata: Kaynak bulunamadı")
            logger.warning(f"ID {video_id}: Manifest URL bulunamadı.")
    except Exception:
        logger.exception(
            f"ID {video_id}: process_video içinde beklenmedik bir genel hata oluştu."
        )
        update_status(video_id, status="Hata: Genel")
    finally:
        if os.path.exists(cookie_filepath):
            os.remove(cookie_filepath)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        video_id_arg = int(sys.argv[1])
        process_video(video_id_arg)
    else:
        setup_logging()
        logger.warning(
            "Bu script, app.py tarafından bir video ID'si ile çağrılmalıdır."
        )
