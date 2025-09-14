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
from pathlib import Path

import config
from logging_config import setup_logging
from database import get_all_settings as get_all_settings_from_db
from workers import get_worker_for_url

logger = logging.getLogger(__name__)


def _update_status_worker(
    conn, item_id, item_type, status=None, progress=None, filepath=None
):
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
        logger.error(f"DB güncelleme hatası: {e}", exc_info=True)


def download_with_yt_dlp(
    conn,
    item_id,
    item_type,
    manifest_filepath,
    headers,
    cookie_filepath,
    output_template,
    speed_limit,
):
    command = [
        "yt-dlp",
        "--enable-file-urls",
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

    # --- NİHAİ ve KESİN ÇÖZÜM: Kritik başlıkları özel komutlarla gönder ---
    # Bu, bot tespitini aşmak için en önemli adımdır.
    if headers:
        # Referer ve User-Agent'ı kendi özel parametreleriyle gönder
        if headers.get("Referer"):
            command.extend(["--referer", headers.pop("Referer")])
        if headers.get("User-Agent"):
            command.extend(["--user-agent", headers.pop("User-Agent")])

        # Geriye kalan diğer tüm başlıkları standart olarak ekle
        for key, value in headers.items():
            command.extend(["--add-header", f"{key}: {value}"])
    # --- ÇÖZÜM SONU ---

    manifest_uri = Path(manifest_filepath).as_uri()
    command.append(manifest_uri)

    logger.info(f"yt-dlp komutu çalıştırılıyor: {' '.join(command)}")

    process = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        encoding="utf-8",
        errors="ignore",
    )

    full_output = ""
    for line in iter(process.stdout.readline, ""):
        full_output += line
        progress_match = re.search(r"\[download\]\s+([0-9\.]+)%", line)
        if progress_match:
            try:
                progress = float(progress_match.group(1))
                _update_status_worker(conn, item_id, item_type, progress=progress)
            except (ValueError, IndexError):
                continue

    process.wait()

    downloaded_files = glob.glob(f"{output_template}.*")

    if process.returncode == 0 and downloaded_files:
        return True, "İndirme tamamlandı.", downloaded_files[0]
    else:
        last_lines = "\n".join(full_output.strip().split("\n")[-10:])
        error_message = f"Hata: İndirme başarısız oldu. Detay: ...{last_lines}"

        for f in glob.glob(f"{output_template}.*"):
            try:
                os.remove(f)
                logger.warning(
                    f"Temizlik: Başarısız indirme sonrası '{os.path.basename(f)}' silindi."
                )
            except OSError:
                pass

        return False, error_message, None


def to_ascii_safe(text):
    turkish_map = str.maketrans("ıİğĞüÜşŞöÖçÇ", "iIgGuUsSoOcC")
    text = str(text).translate(turkish_map)
    text = re.sub(r'[<>:"/\\|?*]', "_", text).strip()
    return re.sub(r"[^\x00-\x7F]+", "", text)


def process_video(item_id, item_type):
    global logger
    logger = setup_logging()
    conn = None
    manifest_filepath = None

    cookie_filepath = config.DATA_DIR / f"cookies_{item_id}_{item_type}.txt"

    try:
        conn = sqlite3.connect(str(config.DATABASE), timeout=20.0)
        conn.row_factory = sqlite3.Row
        settings = get_all_settings_from_db(conn)

        movies_base_folder = config.BASE_DIR / settings.get(
            "MOVIES_DOWNLOADS_FOLDER", "downloads/Movies"
        )
        series_base_folder = config.BASE_DIR / settings.get(
            "SERIES_DOWNLOADS_FOLDER", "downloads/Series"
        )
        temp_folder = config.BASE_DIR / settings.get(
            "TEMP_DOWNLOADS_FOLDER", "downloads/Temp"
        )

        movies_base_folder.mkdir(parents=True, exist_ok=True)
        series_base_folder.mkdir(parents=True, exist_ok=True)
        temp_folder.mkdir(parents=True, exist_ok=True)

        url_to_fetch, temp_output_template, final_folder = None, None, None

        if item_type == "movie":
            item = conn.execute(
                "SELECT * FROM movies WHERE id = ?", (item_id,)
            ).fetchone()
            if not item:
                return
            url_to_fetch = item["url"]
            template = settings.get("FILENAME_TEMPLATE", "{title} - {year}")
            filename_base = template.format(
                title=item["title"] or "Bilinmeyen", year=item["year"] or "YYYY"
            )
            temp_output_template = temp_folder / to_ascii_safe(filename_base)
            final_folder = movies_base_folder

        elif item_type == "episode":
            item = conn.execute(
                """
                SELECT e.*, s.season_number, ser.title as series_title FROM episodes e 
                JOIN seasons s ON e.season_id = s.id JOIN series ser ON s.series_id = ser.id 
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
            safe_relative_path = Path(
                *[to_ascii_safe(p) for p in relative_path_str.split("/")]
            )
            temp_output_template = temp_folder / safe_relative_path.name
            final_folder = series_base_folder / safe_relative_path.parent

        _update_status_worker(conn, item_id, item_type, status="Kaynak aranıyor...")
        worker_instance = get_worker_for_url(url_to_fetch)
        if not worker_instance:
            raise Exception("Desteklenen worker bulunamadı.")

        manifest_filepath, headers, cookies = worker_instance.find_manifest_url(
            url_to_fetch
        )

        if manifest_filepath:
            with open(cookie_filepath, "w", encoding="utf-8") as f:
                f.write("# Netscape HTTP Cookie File\n")
                for c in cookies:
                    if "name" in c and "value" in c:
                        f.write(
                            f"{c.get('domain', '')}\t{'TRUE'}\t{c.get('path', '/')}\t{'FALSE'}\t{int(c.get('expiry', 0))}\t{c['name']}\t{c['value']}\n"
                        )

            _update_status_worker(conn, item_id, item_type, status="İndiriliyor")

            success, message, downloaded_filepath = download_with_yt_dlp(
                conn,
                item_id,
                item_type,
                manifest_filepath,
                headers,
                str(cookie_filepath),
                str(temp_output_template),
                settings.get("SPEED_LIMIT"),
            )

            if success and downloaded_filepath:
                temp_filepath = Path(downloaded_filepath)
                final_folder.mkdir(parents=True, exist_ok=True)
                final_filepath = final_folder / temp_filepath.name

                shutil.move(str(temp_filepath), str(final_filepath))
                _update_status_worker(
                    conn,
                    item_id,
                    item_type,
                    status="Tamamlandı",
                    progress=100,
                    filepath=str(final_filepath),
                )
                logger.info(f"İndirme tamamlandı ve dosya taşındı: {final_filepath}")
            else:
                _update_status_worker(conn, item_id, item_type, status=message)
                logger.error(f"İndirme hatası: {message}")
        else:
            raise Exception("Manifest dosyası oluşturulamadı.")

    except Exception as e:
        logger.exception(f"İşlem sırasında beklenmedik bir hata oluştu: {e}")
        status_msg = "Hata: Beklenmedik Sistem Hatası"
        if conn:
            _update_status_worker(conn, item_id, item_type, status=status_msg)
    finally:
        if conn:
            conn.close()
        if manifest_filepath:
            Path(manifest_filepath).unlink(missing_ok=True)
