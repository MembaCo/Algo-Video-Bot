# @author: MembaCo.

import os

VERSION = "1.2.0"

# --- Güvenlik Ayarları ---
SECRET_KEY = os.environ.get(
    "SECRET_KEY", "cok_gizli_bir_anahtar_kodu_bunu_mutlaka_degistir"
)

# --- Yönetici Giriş Bilgileri ---
ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "password")

# --- Veritabanı Ayarları ---
DATABASE = os.environ.get("DATABASE_FILE", "database.db")

# --- Web Scraping Ayarları ---
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36"
VIDEO_KEYWORDS = [".m3u8", "manifest", ".txt"]
DOWNLOADS_FOLDER = "downloads"

# --- Hedef Site Ayarları ---
ALLOWED_DOMAIN = "hdfilmcehennemi.ltd"

# --- Otomatik İndirme Ayarları ---
AUTO_DOWNLOAD_POLL_INTERVAL = (
    10  # Yöneticinin yeni video kontrolü yapma sıklığı (saniye)
)
