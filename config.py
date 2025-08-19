# @author: MembaCo.

import os
from dotenv import load_dotenv

# .env dosyasındaki değişkenleri yükle
load_dotenv()

VERSION = "1.3.0 - Beta"

# --- Güvenlik Ayarları ---
# .env dosyasından oku, yoksa varsayılanı kullan
SECRET_KEY = os.getenv("SECRET_KEY", "cok_gizli_bir_anahtar_kodu_bunu_mutlaka_degistir")

# --- Yönetici Giriş Bilgileri ---
# Kullanıcı adını .env'den oku
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
# Parolayı hash'lemek için:
# from werkzeug.security import generate_password_hash
# print(generate_password_hash('senin_guvenli_parolan'))
# Çıktıyı aşağıdaki değişkene yapıştır.
ADMIN_PASSWORD_HASH = os.getenv(
    "ADMIN_PASSWORD_HASH", "scrypt:32768:8:1$..."
)  # Örnek hash

# --- Veritabanı Ayarları ---
DATABASE = os.getenv("DATABASE_FILE", "database.db")

# --- Web Scraping Ayarları ---
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36"
VIDEO_KEYWORDS = [".m3u8", "manifest", ".txt"]
DOWNLOADS_FOLDER = "downloads"

# --- Hedef Site Ayarları ---
ALLOWED_DOMAIN = "hdfilmcehennemi.ltd"

# --- Otomatik İndirme Ayarları ---
AUTO_DOWNLOAD_POLL_INTERVAL = 10
