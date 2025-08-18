# @author: MembaCo.

import os

# --- Güvenlik Ayarları ---
# Flask uygulamasının session'larını güvende tutmak için kullanılır.
# Gerçek bir projede, 'os.urandom(24)' gibi bir komutla üretilmiş rastgele bir değer kullanın.
SECRET_KEY = os.environ.get('SECRET_KEY', 'cok_gizli_bir_anahtar_kodu_bunu_mutlaka_degistir')

# --- Yönetici Giriş Bilgileri ---
# Bu bilgileri doğrudan kod içine yazmak yerine ortam değişkenlerinden (environment variables) almak daha güvenlidir.
ADMIN_USERNAME = os.environ.get('ADMIN_USERNAME', 'admin')
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'password')

# --- Veritabanı Ayarları ---
DATABASE = os.environ.get('DATABASE_FILE', 'database.db')

# --- Web Scraping Ayarları ---
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36"
VIDEO_KEYWORDS = [".m3u8", "manifest", ".txt"]
DOWNLOADS_FOLDER = "downloads"

# --- Hedef Site Ayarları ---
ALLOWED_DOMAIN = "hdfilmcehennemi.ltd"