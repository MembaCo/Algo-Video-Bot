# @author: MembaCo.

import sqlite3
import time
import subprocess
import re
import os
import sys
import logging
import glob
import shutil

import config
from logging_config import setup_logging
from database import get_all_settings as get_all_settings_from_db
from workers import get_worker_for_url  # YENİ FABRİKA IMPORTU

logger = logging.getLogger(__name__)


def _update_status_worker(
    conn, item_id, item_type, status=None, progress=None, filepath=None
):
    """Mevcut bir veritabanı bağlantısını kullanarak durumu günceller."""
    table = "movies" if item_type == "movie" else "episodes"
    try:
        cursor = conn.cursor()
        if status:
            cursor.execute(
                f"UPDATE {table} SET status = ? WHERE id = ?", (status, item_id)
            )
        if progress is not None:
            cursor.execute(
                f"UPDATE {table} SET progress = ? WHERE id = ?", (progress, item_id)
            )
        if filepath is not None:
            cursor.execute(
                f"UPDATE {table} SET filepath = ? WHERE id = ?", (filepath, item_id)
            )
        conn.commit()
    except sqlite3.Error as e:
        logger.error(
            f"ID {item_id} ({item_type}) için worker DB güncellemesinde hata: {e}",
            exc_info=True,
        )


def download_with_yt_dlp(
    conn,
    item_id,
    item_type,
    manifest_url,
    headers,
    cookie_filepath,
    output_template,
    speed_limit,
):
    """yt-dlp ile videoyu indirir ve ilerlemeyi veritabanına yazar."""
    command = [
        "yt-dlp",
        "--cookies",
        cookie_filepath,
        "--newline",
        "--no-check-certificates",
        "--no-color",
        "--progress",
        "--verbose",
        "--hls-use-mpegts",
        "-o",
        f"{output_template}.%(ext)s",
    ]
    if speed_limit:
        command.extend(["--limit-rate", speed_limit])
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
                _update_status_worker(conn, item_id, item_type, progress=progress)
            except (ValueError, IndexError):
                continue
    process.wait()

    if process.returncode == 0:
        return True, "İndirme tamamlandı."
    else:
        if "403 Forbidden" in full_output:
            error_message = "Hata: Sunucu erişimi reddetti (403)."
        elif "No space left on device" in full_output:
            error_message = "Hata: Diskte yeterli alan yok."
        elif "HTTP Error 404" in full_output:
            error_message = "Hata: Video kaynağı bulunamadı (404)."
        else:
            last_lines = "\n".join(full_output.strip().split("\n")[-5:])
            error_message = f"Hata: İndirme başarısız oldu. Detay: ...{last_lines}"
        return False, error_message


def to_ascii_safe(text):
    text = (
        str(text)
        .replace("ı", "i")
        .replace("İ", "I")
        .replace("ğ", "g")
        .replace("Ğ", "G")
        .replace("ü", "u")
        .replace("Ü", "U")
        .replace("ş", "s")
        .replace("Ş", "S")
        .replace("ö", "o")
        .replace("Ö", "O")
        .replace("ç", "c")
        .replace("Ç", "C")
    )
    text = re.sub(r'[<>:"/\\|?*]', "_", text).strip()
    text = re.sub(r"[^\x00-\x7F]+", "", text)
    return text


def process_video(item_id, item_type):
    global logger
    logger = setup_logging()
    conn = None
    cookie_filepath = f"cookies_{item_id}_{item_type}.txt"
    manifest_url, headers, cookies = None, None, None

    try:
        conn = sqlite3.connect(config.DATABASE, timeout=20.0)
        conn.row_factory = sqlite3.Row
        settings = get_all_settings_from_db(conn)

        movies_base_folder = settings.get("MOVIES_DOWNLOADS_FOLDER", "downloads/Movies")
        series_base_folder = settings.get("SERIES_DOWNLOADS_FOLDER", "downloads/Series")
        temp_folder = settings.get("TEMP_DOWNLOADS_FOLDER", "downloads/Temp")

        os.makedirs(movies_base_folder, exist_ok=True)
        os.makedirs(series_base_folder, exist_ok=True)
        os.makedirs(temp_folder, exist_ok=True)

        url_to_fetch = None
        temp_output_template = None
        final_folder = None

        # Dosya yolu oluşturma mantığı...
        if item_type == "movie":
            item = conn.execute(
                "SELECT * FROM movies WHERE id = ?", (item_id,)
            ).fetchone()
            if not item:
                return
            url_to_fetch = item["url"]
            filename_template = settings.get("FILENAME_TEMPLATE", "{title} - {year}")
            filename_base = filename_template.format(
                title=item["title"] or "Bilinmeyen", year=item["year"] or "YYYY"
            )
            safe_filename = to_ascii_safe(filename_base)
            temp_output_template = os.path.join(temp_folder, safe_filename)
            final_folder = movies_base_folder
        elif item_type == "episode":
            item = conn.execute(
                """
                SELECT e.*, s.season_number, ser.title as series_title
                FROM episodes e JOIN seasons s ON e.season_id = s.id JOIN series ser ON s.series_id = ser.id
                WHERE e.id = ?
            """,
                (item_id,),
            ).fetchone()
            if not item:
                return
            url_to_fetch = item["url"]
            template = settings.get(
                "SERIES_FILENAME_TEMPLATE",
                "{series_title}/S{season_number:02d}E{episode_number:02d} - {episode_title}",
            )
            relative_path_str = template.format(
                series_title=item["series_title"],
                season_number=item["season_number"],
                episode_number=item["episode_number"],
                episode_title=item["title"] or "",
            )
            safe_relative_path = os.path.join(
                *[to_ascii_safe(p) for p in relative_path_str.split("/")]
            )
            filename_base = os.path.basename(safe_relative_path)
            temp_output_template = os.path.join(temp_folder, filename_base)
            final_folder = os.path.join(
                series_base_folder, os.path.dirname(safe_relative_path)
            )

        if not url_to_fetch or not temp_output_template or not final_folder:
            raise ValueError("URL veya çıktı şablonu oluşturulamadı.")

        _update_status_worker(conn, item_id, item_type, status="Kaynak aranıyor...")

        worker_instance = get_worker_for_url(url_to_fetch)
        if not worker_instance:
            raise Exception(f"Desteklenen bir worker bulunamadı: {url_to_fetch}")

        # Hata ayıklama artık her worker'ın kendi içinde yönetiliyor
        manifest_url, headers, cookies = worker_instance.find_manifest_url(url_to_fetch)

        if manifest_url:
            with open(cookie_filepath, "w", encoding="utf-8") as f:
                f.write("# Netscape HTTP Cookie File\n")
                for cookie in cookies:
                    if "name" not in cookie or "value" not in cookie:
                        continue
                    f.write(
                        f"{cookie.get('domain', '')}\t{'TRUE'}\t{cookie.get('path', '/')}\t{'FALSE'}\t{int(cookie.get('expiry', 0))}\t{cookie['name']}\t{cookie['value']}\n"
                    )

            _update_status_worker(conn, item_id, item_type, status="İndiriliyor")
            success, message = download_with_yt_dlp(
                conn,
                item_id,
                item_type,
                manifest_url,
                headers,
                cookie_filepath,
                temp_output_template,
                settings.get("SPEED_LIMIT"),
            )

            if success:
                files = glob.glob(f"{temp_output_template}.*")
                if files:
                    temp_filepath = files[0]
                    downloaded_filename = os.path.basename(temp_filepath)
                    os.makedirs(final_folder, exist_ok=True)
                    final_filepath = os.path.join(final_folder, downloaded_filename)
                    shutil.move(temp_filepath, final_filepath)
                    logger.info(f"Dosya şuraya taşındı: {final_filepath}")
                    _update_status_worker(
                        conn,
                        item_id,
                        item_type,
                        status="Tamamlandı",
                        progress=100,
                        filepath=final_filepath,
                    )
                    logger.info(
                        f"ID {item_id} ({item_type}): İndirme tamamlandı. Dosya: {final_filepath}"
                    )
                else:
                    _update_status_worker(
                        conn,
                        item_id,
                        item_type,
                        status="Hata: Taşınacak dosya bulunamadı",
                    )
            else:
                _update_status_worker(conn, item_id, item_type, status=message)
                logger.error(f"ID {item_id} ({item_type}): İndirme hatası - {message}")
        else:
            raise Exception("Manifest URL'si bulunamadı.")

    except Exception as e:
        logger.exception(
            f"ID {item_id} ({item_type}): process_video içinde beklenmedik hata: {e}"
        )
        status_msg = (
            "Hata: Video kaynağı bulunamadı"
            if not manifest_url
            else "Hata: Beklenmedik Sistem Hatası"
        )
        if conn:
            _update_status_worker(conn, item_id, item_type, status=status_msg)
    finally:
        if conn:
            conn.close()
        if os.path.exists(cookie_filepath):
            os.remove(cookie_filepath)
