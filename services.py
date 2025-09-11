# @author: MembaCo.

import logging
import os
import signal
import subprocess
import sys
from multiprocessing import Process
import math
from urllib.parse import urlparse
import glob

from database import get_db, get_setting, get_all_settings
from worker import process_video, to_ascii_safe
from scrapers import get_scraper_for_url

logger = logging.getLogger(__name__)


def check_existing_file(base_filepath):
    """
    Verilen dosya yolunu (uzantısız) alarak, yaygın video uzantılarıyla eşleşen
    bir dosyanın olup olmadığını kontrol eder. Varsa, dosyanın tam yolunu döndürür.
    """
    # Yaygın video formatlarını arayacak glob deseni
    search_pattern = f"{base_filepath}.*"
    files_found = glob.glob(search_pattern)

    for filepath in files_found:
        # Dosya uzantısını al ve küçük harfe çevir
        extension = os.path.splitext(filepath)[1].lower()
        # Yaygın video uzantılarından biriyle eşleşiyorsa
        if extension in [".mkv", ".mp4", ".avi", ".mov", ".webm", ".flv"]:
            logger.info(f"Mevcut indirilmiş dosya bulundu: {filepath}")
            return filepath  # Eşleşen ilk dosyanın tam yolunu döndür

    return None


# --- FİLM İŞLEMLERİ ---
def add_movie_to_queue(url, scraper):
    db = get_db()
    if db.execute("SELECT id FROM movies WHERE url = ?", (url,)).fetchone():
        return False, "Bu film zaten kuyrukta mevcut."

    metadata = scraper.scrape_movie_metadata(url)
    if not metadata:
        return False, "Film bilgileri çekilemedi."

    settings = get_all_settings(db)
    movies_folder = settings.get("MOVIES_DOWNLOADS_FOLDER", "downloads/Movies")
    filename_template = settings.get("FILENAME_TEMPLATE", "{title} - {year}")

    # Potansiyel dosya adını oluştur
    filename_base = filename_template.format(
        title=metadata["title"] or "Bilinmeyen", year=metadata["year"] or "YYYY"
    )
    safe_filename_base = to_ascii_safe(filename_base)
    full_path_base = os.path.join(movies_folder, safe_filename_base)

    # Diskte dosyayı kontrol et
    existing_filepath = check_existing_file(full_path_base)

    status = "Tamamlandı" if existing_filepath else "Sırada"
    progress = 100.0 if existing_filepath else 0.0

    db.execute(
        "INSERT INTO movies (url, status, title, year, genre, description, imdb_score, director, cast, poster_url, source_site, filepath, progress) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            url,
            status,
            metadata["title"],
            metadata["year"],
            metadata["genre"],
            metadata["description"],
            metadata["imdb_score"],
            metadata["director"],
            metadata["cast"],
            metadata["poster_url"],
            urlparse(url).netloc.replace("www.", ""),
            existing_filepath,
            progress,
        ),
    )
    db.commit()

    if existing_filepath:
        return (
            True,
            f'"{metadata["title"]}" zaten indirilmiş olarak bulundu ve listeye eklendi.',
        )
    else:
        return True, f'"{metadata["title"]}" başarıyla sıraya eklendi.'


def add_movies_from_list_page_async(app, list_url):
    with app.app_context():
        scraper = get_scraper_for_url(list_url)
        if not scraper:
            logger.error(f"Toplu ekleme için uygun kazıyıcı bulunamadı: {list_url}")
            return

        movie_links, error = scraper.scrape_movie_links_from_list_page(list_url)
        if error:
            logger.error(f"Toplu ekleme işlemi başarısız: {error}")
            return
        added, skipped, failed = 0, 0, 0
        for link in movie_links:
            try:
                success, message = add_movie_to_queue(link, scraper)
                if success:
                    added += 1
                elif "zaten kuyrukta mevcut" in message.lower():
                    skipped += 1
                else:
                    failed += 1
            except Exception:
                failed += 1
                logger.error(
                    f"Toplu ekleme sırasında bir video ({link}) işlenirken hata oluştu.",
                    exc_info=True,
                )
        logger.info(
            f"Toplu ekleme tamamlandı. Eklenen: {added}, Atlanan: {skipped}, Başarısız: {failed}"
        )


# --- DİZİ İŞLEMLERİ ---
def add_series_to_queue(series_url, scraper):
    db = get_db()
    series_data = scraper.scrape_series_data(series_url)
    if not series_data:
        return (
            False,
            "Dizi bilgileri çekilemedi. Linki kontrol edin veya site yapısı değişmiş olabilir.",
        )

    settings = get_all_settings(db)
    series_folder = settings.get("SERIES_DOWNLOADS_FOLDER", "downloads/Series")
    template = settings.get(
        "SERIES_FILENAME_TEMPLATE",
        "{series_title}/S{season_number:02d}E{episode_number:02d} - {episode_title}",
    )

    cursor = db.cursor()
    cursor.execute(
        "SELECT id FROM series WHERE source_url = ?", (series_data["source_url"],)
    )
    series_row = cursor.fetchone()

    if not series_row:
        cursor.execute(
            "INSERT INTO series (title, poster_url, description, source_url) VALUES (?, ?, ?, ?)",
            (
                series_data["title"],
                series_data["poster_url"],
                series_data["description"],
                series_data["source_url"],
            ),
        )
        series_id = cursor.lastrowid
    else:
        series_id = series_row["id"]

    added_count = 0
    skipped_count = 0
    for season in series_data["seasons"]:
        cursor.execute(
            "SELECT id FROM seasons WHERE series_id = ? AND season_number = ?",
            (series_id, season["season_number"]),
        )
        season_row = cursor.fetchone()
        if not season_row:
            cursor.execute(
                "INSERT INTO seasons (series_id, season_number) VALUES (?, ?)",
                (series_id, season["season_number"]),
            )
            season_id = cursor.lastrowid
        else:
            season_id = season_row["id"]

        for episode in season["episodes"]:
            # Potansiyel dosya yolunu oluştur
            relative_path_str = template.format(
                series_title=series_data["title"],
                season_number=season["season_number"],
                episode_number=episode["episode_number"],
                episode_title=episode["title"] or "",
            )
            safe_relative_path = os.path.join(
                *[to_ascii_safe(p) for p in relative_path_str.split("/")]
            )
            full_path_base = os.path.join(series_folder, safe_relative_path)

            # Diskte dosyayı kontrol et
            existing_filepath = check_existing_file(full_path_base)

            status = "Tamamlandı" if existing_filepath else "Sırada"
            progress = 100.0 if existing_filepath else 0.0

            res = cursor.execute(
                "INSERT OR IGNORE INTO episodes (season_id, episode_number, title, url, status, filepath, progress) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (
                    season_id,
                    episode["episode_number"],
                    episode["title"],
                    episode["url"],
                    status,
                    existing_filepath,
                    progress,
                ),
            )
            if res.rowcount > 0:
                if existing_filepath:
                    skipped_count += 1
                else:
                    added_count += 1
    db.commit()

    message = f'"{series_data["title"]}" dizisi için işlem tamamlandı. Yeni eklenen: {added_count}, zaten mevcut olan: {skipped_count}.'
    return True, message


def add_series_to_queue_async(app, series_url):
    with app.app_context():
        scraper = get_scraper_for_url(series_url)
        if not scraper:
            logger.error(f"Dizi ekleme için uygun kazıyıcı bulunamadı: {series_url}")
            return
        success, message = add_series_to_queue(series_url, scraper)
        if not success:
            logger.error(f"Dizi ekleme hatası ({series_url}): {message}")
        else:
            logger.info(message)


# --- ORTAK İŞLEMLER ---
def start_download(item_id, item_type, active_processes):
    db = get_db()
    table = "movies" if item_type == "movie" else "episodes"
    item = db.execute(f"SELECT * FROM {table} WHERE id = ?", (item_id,)).fetchone()
    if not item:
        return False, "Kayıt bulunamadı."
    if item["status"] in ["Kaynak aranıyor...", "İndiriliyor"]:
        return False, "Bu indirme zaten devam ediyor."

    p = Process(target=process_video, args=(item_id, item_type))
    p.start()
    pid = p.pid
    active_processes[pid] = p

    db.execute(
        f"UPDATE {table} SET status = ?, pid = ?, progress = 0, filepath = NULL WHERE id = ?",
        ("Kaynak aranıyor...", pid, item_id),
    )
    db.commit()
    title = item["title"] if item_type == "movie" else f"Bölüm {item['episode_number']}"
    logger.info(f"ID {item_id} ('{title}') için indirme başlatıldı. PID: {pid}")
    return True, f'"{title}" için indirme başlatıldı.'


def stop_download(item_id, item_type):
    db = get_db()
    table = "movies" if item_type == "movie" else "episodes"
    item = db.execute(f"SELECT * FROM {table} WHERE id = ?", (item_id,)).fetchone()
    if not (item and item["pid"]):
        return False, "Durdurulacak bir işlem bulunamadı."
    pid = item["pid"]

    try:
        if sys.platform != "win32":
            os.killpg(os.getpgid(pid), signal.SIGTERM)
        else:
            subprocess.run(
                ["taskkill", "/F", "/T", "/PID", str(pid)],
                check=True,
                capture_output=True,
            )
        message = "İndirme durdurma isteği gönderildi."
    except (ProcessLookupError, subprocess.CalledProcessError):
        message = "İşlem zaten sonlanmış."
    except OSError as e:
        message = f"İşlem durdurulurken bir hata oluştu: {e}"

    db.execute(
        f"UPDATE {table} SET status = 'Duraklatıldı', pid = NULL WHERE id = ?",
        (item_id,),
    )
    db.commit()
    return True, message


def delete_record(item_id, item_type, active_processes):
    db = get_db()
    table = "movies" if item_type == "movie" else "episodes"
    item = db.execute(f"SELECT * FROM {table} WHERE id = ?", (item_id,)).fetchone()

    if item and item["pid"]:
        pid = item["pid"]
        stop_download(item_id, item_type)
        if pid in active_processes:
            del active_processes[pid]

    db.execute(f"DELETE FROM {table} WHERE id = ?", (item_id,))
    db.commit()
    return True, "Kayıt başarıyla silindi."


def delete_series_record(series_id, active_processes):
    db = get_db()
    episodes_to_delete = db.execute(
        """
        SELECT e.id, e.pid FROM episodes e
        JOIN seasons s ON e.season_id = s.id
        WHERE s.series_id = ?
    """,
        (series_id,),
    ).fetchall()
    for episode in episodes_to_delete:
        if episode["pid"]:
            pid = episode["pid"]
            stop_download(episode["id"], "episode")
            if pid in active_processes:
                del active_processes[pid]
    series = db.execute(
        "SELECT title FROM series WHERE id = ?", (series_id,)
    ).fetchone()
    if series:
        cursor = db.cursor()
        cursor.execute("DELETE FROM series WHERE id = ?", (series_id,))
        db.commit()
        logger.info(f"'{series['title']}' dizisi ve tüm bölümleri başarıyla silindi.")
        return True, f"'{series['title']}' dizisi başarıyla silindi."
    else:
        return False, "Silinecek dizi bulunamadı."


def start_all_episodes_for_series(series_id):
    db = get_db()
    episodes_to_queue = db.execute(
        """
        SELECT e.id FROM episodes e
        JOIN seasons s ON e.season_id = s.id
        WHERE s.series_id = ? AND e.status NOT IN ('Tamamlandı', 'İndiriliyor', 'Kaynak aranıyor...')
    """,
        (series_id,),
    ).fetchall()
    if not episodes_to_queue:
        return False, "Sıraya eklenecek yeni bölüm bulunamadı."
    count = 0
    for episode in episodes_to_queue:
        db.execute(
            "UPDATE episodes SET status = 'Sırada' WHERE id = ?", (episode["id"],)
        )
        count += 1
    db.commit()
    series_title = db.execute(
        "SELECT title FROM series WHERE id = ?", (series_id,)
    ).fetchone()["title"]
    logger.info(f"'{series_title}' dizisi için {count} bölüm indirme sırasına alındı.")
    return True, f"'{series_title}' dizisi için {count} bölüm indirme sırasına alındı."


def delete_item_file(item_id, item_type):
    db = get_db()
    table = "movies" if item_type == "movie" else "episodes"
    item = db.execute(f"SELECT * FROM {table} WHERE id = ?", (item_id,)).fetchone()
    if not item:
        return False, "Kayıt bulunamadı."
    filepath = item["filepath"]
    if filepath and os.path.exists(filepath):
        try:
            os.remove(filepath)
            db.execute(f"UPDATE {table} SET filepath = NULL WHERE id = ?", (item_id,))
            db.commit()
            logger.info(f"Dosya diskten silindi: {filepath}")
            return True, f'"{os.path.basename(filepath)}" diskten başarıyla silindi.'
        except OSError:
            logger.error(f"Dosya silinemedi: {filepath}", exc_info=True)
            return False, "Dosya silinirken bir hata oluştu."
    else:
        db.execute(f"UPDATE {table} SET filepath = NULL WHERE id = ?", (item_id,))
        db.commit()
        return False, "Silinecek dosya bulunamadı veya zaten silinmiş."


def retry_all_failed():
    db = get_db()
    cursor = db.cursor()
    cursor.execute(
        "UPDATE movies SET status = 'Sırada', pid = NULL WHERE status LIKE 'Hata:%' OR status = 'Duraklatıldı'"
    )
    movies_updated = cursor.rowcount
    cursor.execute(
        "UPDATE episodes SET status = 'Sırada', pid = NULL WHERE status LIKE 'Hata:%' OR status = 'Duraklatıldı'"
    )
    episodes_updated = cursor.rowcount
    db.commit()
    total_updated = movies_updated + episodes_updated
    if total_updated > 0:
        logger.info(f"{total_updated} adet sorunlu indirme tekrar sıraya alındı.")
        return True, f"{total_updated} adet sorunlu indirme tekrar sıraya alındı."
    else:
        return False, "Tekrar denenecek sorunlu bir indirme bulunamadı."


# --- OTOMATİK İNDİRME YÖNETİCİSİ ---
def run_auto_download_cycle(active_processes):
    db = get_db()
    try:
        concurrent_limit = int(get_setting("CONCURRENT_DOWNLOADS", db))
    except (ValueError, TypeError):
        concurrent_limit = 1
    for pid, process in list(active_processes.items()):
        if not process.is_alive():
            del active_processes[pid]
            logger.info(
                f"Otomatik yönetici: Tamamlanmış proses (PID: {pid}) temizlendi."
            )
    while len(active_processes) < concurrent_limit:
        next_item = db.execute(
            """
            SELECT id, 'movie' as type, created_at FROM movies WHERE status = 'Sırada'
            UNION ALL
            SELECT id, 'episode' as type, created_at FROM episodes WHERE status = 'Sırada'
            ORDER BY created_at ASC
            LIMIT 1
        """
        ).fetchone()
        if not next_item:
            break
        item_id = next_item["id"]
        item_type = next_item["type"]
        logger.info(
            f"[Auto-Download] Sırada bekleyen bulundu ({item_type} ID: {item_id}). İndirme başlatılıyor."
        )
        start_download(item_id, item_type, active_processes)


# --- API İÇİN VERİ ÇEKME FONKSİYONLARI ---
def get_all_movies_status(hide_completed=False, page=1, per_page=10):
    db = get_db()
    base_query = "FROM movies "
    count_query = "SELECT COUNT(id) "
    data_query = "SELECT * "
    params = {}
    where_clauses = []
    if hide_completed:
        where_clauses.append("status != :status")
        params["status"] = "Tamamlandı"
    if where_clauses:
        base_query += "WHERE " + " AND ".join(where_clauses)
    total_items = db.execute(count_query + base_query, params).fetchone()[0]
    total_pages = math.ceil(total_items / per_page)
    offset = (page - 1) * per_page
    final_query = (
        data_query
        + base_query
        + """
        ORDER BY CASE
            WHEN status = 'İndiriliyor' THEN 1 WHEN status = 'Kaynak aranıyor...' THEN 2
            WHEN status = 'Sırada' THEN 3 WHEN status LIKE 'Hata:%' THEN 4
            WHEN status = 'Duraklatıldı' THEN 5 WHEN status = 'Tamamlandı' THEN 6
            ELSE 7
        END, created_at DESC
        LIMIT :limit OFFSET :offset
    """
    )
    params["limit"] = per_page
    params["offset"] = offset
    movies = db.execute(final_query, params).fetchall()
    pagination_data = {
        "page": page,
        "per_page": per_page,
        "total_items": total_items,
        "total_pages": total_pages,
    }
    return {m["id"]: dict(m) for m in movies}, pagination_data


def get_all_series_status():
    db = get_db()
    series_list = db.execute("SELECT * FROM series ORDER BY title ASC").fetchall()
    series_data = []
    for s in series_list:
        series_dict = dict(s)
        seasons = db.execute(
            "SELECT * FROM seasons WHERE series_id = ? ORDER BY season_number ASC",
            (s["id"],),
        ).fetchall()
        series_dict["seasons"] = []
        for season in seasons:
            season_dict = dict(season)
            episodes = db.execute(
                "SELECT * FROM episodes WHERE season_id = ? ORDER BY episode_number ASC",
                (season["id"],),
            ).fetchall()
            season_dict["episodes"] = [dict(ep) for ep in episodes]
            series_dict["seasons"].append(season_dict)
        series_data.append(series_dict)
    return series_data


def get_active_downloads_status():
    db = get_db()
    query = """
        SELECT id, title, progress, 'Film' as type FROM movies WHERE status IN ('İndiriliyor', 'Kaynak aranıyor...')
        UNION ALL
        SELECT e.id, s.title || ' - S' || sea.season_number || 'E' || e.episode_number || ' - ' || e.title as title, e.progress, 'Dizi' as type
        FROM episodes e
        JOIN seasons sea ON e.season_id = sea.id
        JOIN series s ON sea.series_id = s.id
        WHERE e.status IN ('İndiriliyor', 'Kaynak aranıyor...')
    """
    active_items = db.execute(query).fetchall()
    return [dict(item) for item in active_items]
