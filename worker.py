# @author: MembaCo.

import sqlite3
import time
import subprocess
import re
import os
import sys
from seleniumwire import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

DATABASE = "database.db"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36"
VIDEO_KEYWORDS = [".m3u8", "manifest", ".txt"]


def get_db():
    """Veritabanı bağlantısını açar ve satır formatını ayarlar."""
    db = sqlite3.connect(DATABASE, timeout=10)
    db.row_factory = sqlite3.Row
    return db


def update_status(video_id, status, source_url=None, progress=None):
    """Veritabanındaki bir videonun durumunu günceller."""
    db = get_db()
    cursor = db.cursor()
    if source_url:
        cursor.execute(
            "UPDATE videos SET status = ?, source_url = ? WHERE id = ?",
            (status, source_url, video_id),
        )
    elif progress is not None:
        cursor.execute(
            "UPDATE videos SET progress = ? WHERE id = ?", (progress, video_id)
        )
    else:
        cursor.execute("UPDATE videos SET status = ? WHERE id = ?", (status, video_id))
    db.commit()
    db.close()


def find_manifest_url(target_url):
    """Selenium ile SADECE manifest URL'sini bulur."""
    options = webdriver.ChromeOptions()
    options.add_argument("--headless=new")
    options.add_argument("--log-level=3")
    options.add_argument("--mute-audio")
    options.add_argument(f"user-agent={USER_AGENT}")

    driver = None
    try:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        wait = WebDriverWait(driver, 25)

        driver.get(target_url)

        play_button_main = wait.until(EC.element_to_be_clickable((By.ID, "fimcnt")))
        driver.execute_script("arguments[0].click();", play_button_main)

        iframe_locator = (By.CSS_SELECTOR, ".play-box-iframe iframe")
        driver.switch_to.default_content()
        iframe_element = wait.until(EC.presence_of_element_located(iframe_locator))
        iframe_src = iframe_element.get_attribute("src")
        driver.switch_to.frame(iframe_element)

        play_button_iframe = wait.until(EC.element_to_be_clickable((By.ID, "player")))

        del driver.requests
        play_button_iframe.click()

        time.sleep(15)

        for request in reversed(driver.requests):
            if any(key in request.url for key in VIDEO_KEYWORDS):
                return request.url, iframe_src
        return None, None

    finally:
        if driver:
            driver.quit()


def download_with_yt_dlp(video_id, manifest_url, referer_url, filename_template):
    """yt-dlp ile videoyu indirir ve ilerlemeyi veritabanına yazar."""
    if not os.path.exists("downloads"):
        os.makedirs("downloads")

    output_template = os.path.join(
        "downloads", f"{filename_template} [%(height)sp].%(ext)s"
    )

    command = [
        "yt-dlp",
        "--user-agent",
        USER_AGENT,
        "--referer",
        referer_url,
        "--newline",
        "--no-color",
        "--progress",
        "-o",
        output_template,
        manifest_url,
    ]

    process = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        bufsize=1,
    )

    for line in iter(process.stdout.readline, ""):
        progress_match = re.search(r"\[download\]\s+([0-9\.]+)%", line)
        if progress_match:
            progress = float(progress_match.group(1))
            update_status(video_id, status=None, progress=int(progress))

    process.wait()
    if process.returncode == 0:
        return True, "İndirme tamamlandı."
    else:
        return False, process.stderr.read()


def process_video(video_id):
    """Tek bir video için tüm bulma ve indirme sürecini yönetir."""
    db = get_db()
    video = db.execute("SELECT * FROM videos WHERE id = ?", (video_id,)).fetchone()
    db.close()

    if not video:
        print(f"Hata: ID {video_id} bulunamadı.")
        return

    try:
        print(f"ID {video_id}: Kaynak adresi aranıyor...")
        manifest_url, iframe_src = find_manifest_url(video["url"])

        if manifest_url:
            update_status(video_id, "İndiriliyor", source_url=manifest_url)

            # --- YENİ: Dosya adını veritabanından oluştur ---
            title = video["title"] or "Bilinmeyen Film"
            year = video["year"] or ""
            genre = video["genre"] or ""

            clean_title = re.sub(r'[<>:"/\\|?*]', "", title)
            clean_genre = re.sub(r'[<>:"/\\|?*]', "", genre)

            filename = f"{clean_title} - {year} - {clean_genre}".strip(" -")
            print(f"ID {video_id}: Dosya adı oluşturuldu: {filename}")
            # ----------------------------------------------

            success, message = download_with_yt_dlp(
                video_id, manifest_url, iframe_src, filename
            )

            if success:
                update_status(video_id, "Tamamlandı", progress=100)
                print(f"ID {video_id}: İndirme tamamlandı.")
            else:
                print(f"ID {video_id}: İndirme hatası - {message}")
                update_status(video_id, "Hata: İndirilemedi")
        else:
            print(f"ID {video_id}: Manifest URL bulunamadı.")
            update_status(video_id, "Hata: Kaynak bulunamadı")
    except Exception as e:
        print(f"ID {video_id}: Beklenmedik bir hata oluştu: {e}")
        update_status(video_id, "Hata: Genel")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        video_id_arg = int(sys.argv[1])
        process_video(video_id_arg)
    else:
        print("Bu script, app.py tarafından bir video ID'si ile çağrılmalıdır.")
