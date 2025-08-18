# @author: MembaCo.

from flask import Flask, render_template, request, redirect, url_for, flash, session
import sqlite3
import os
import signal
import re
import requests
from bs4 import BeautifulSoup
from multiprocessing import Process
from worker import process_video

# --- AYARLAR ---
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "password"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36"
# -----------------

app = Flask(__name__)
app.secret_key = "cok_gizli_bir_anahtar_kodu"

DATABASE = "database.db"


def get_db():
    """Veritabanı bağlantısını açar."""
    db = sqlite3.connect(DATABASE, timeout=10)
    db.row_factory = sqlite3.Row
    return db


def scrape_metadata(url):
    """Requests ve BeautifulSoup ile bir URL'den film bilgilerini çeker. (Daha Güvenli)"""
    try:
        headers = {"User-Agent": USER_AGENT}
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

        # --- Hata Kontrollü Veri Çekme ---
        title_tag = soup.find("h1", class_="title")
        title = title_tag.text.strip() if title_tag else "Başlık Bulunamadı"

        extra_div = soup.find("div", class_="extra")
        if extra_div:
            genres = [a.text.strip() for a in extra_div.find_all("a")]
            year_text = extra_div.find(string=True, recursive=False)
            year = year_text.strip() if year_text else ""
            genre = genres[0] if genres else "Bilinmiyor"
        else:
            genres, year, genre = [], "", "Bilinmiyor"
        # ------------------------------------

        return {"title": title, "year": year, "genre": genre}
    except Exception as e:
        print(f"Meta veri çekilirken hata oluştu: {e}")
        return None


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        if (
            request.form["username"] == ADMIN_USERNAME
            and request.form["password"] == ADMIN_PASSWORD
        ):
            session["logged_in"] = True
            return redirect(url_for("index"))
        else:
            flash("Hatalı kullanıcı adı veya şifre.", "danger")
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.pop("logged_in", None)
    return redirect(url_for("login"))


@app.route("/")
def index():
    if not session.get("logged_in"):
        return redirect(url_for("login"))

    db = get_db()
    videos = db.execute("SELECT * FROM videos ORDER BY created_at DESC").fetchall()
    db.close()
    return render_template("index.html", videos=videos)


@app.route("/add", methods=["POST"])
def add_video():
    """Kuyruğa yeni video eklerken meta verilerini de çeker."""
    if not session.get("logged_in"):
        return redirect(url_for("login"))

    url = request.form["url"]
    if "hdfilmcehennemi.ltd" not in url:
        flash("Lütfen geçerli bir hdfilmcehennemi.ltd linki girin.", "warning")
        return redirect(url_for("index"))

    print(f"Meta veriler çekiliyor: {url}")
    metadata = scrape_metadata(url)

    if metadata:
        db = get_db()
        db.execute(
            "INSERT INTO videos (url, status, title, year, genre) VALUES (?, ?, ?, ?, ?)",
            (url, "Sırada", metadata["title"], metadata["year"], metadata["genre"]),
        )
        db.commit()
        db.close()
        flash(f'"{metadata["title"]}" başarıyla sıraya eklendi.', "success")
    else:
        flash("Film bilgileri çekilemedi. Lütfen linki kontrol edin.", "danger")

    return redirect(url_for("index"))


@app.route("/start/<int:video_id>")
def start_download(video_id):
    if not session.get("logged_in"):
        return redirect(url_for("login"))

    db = get_db()
    video = db.execute("SELECT * FROM videos WHERE id = ?", (video_id,)).fetchone()

    if video and video["status"] in [
        "Sırada",
        "Duraklatıldı",
        "Hata: Kaynak bulunamadı",
        "Hata: İndirilemedi",
        "Hata: Genel",
    ]:
        p = Process(target=process_video, args=(video_id,))
        p.start()
        db.execute(
            "UPDATE videos SET status = ?, pid = ?, progress = 0 WHERE id = ?",
            ("Kaynak aranıyor...", p.pid, video_id),
        )
        db.commit()
        flash(f'"{video["title"]}" için indirme başlatıldı.', "info")
    else:
        flash("Bu indirme şu anda başlatılamaz.", "warning")

    db.close()
    return redirect(url_for("index"))


@app.route("/stop/<int:video_id>")
def stop_download(video_id):
    if not session.get("logged_in"):
        return redirect(url_for("login"))

    db = get_db()
    video = db.execute("SELECT * FROM videos WHERE id = ?", (video_id,)).fetchone()

    # --- Hata Kontrollü Durdurma ---
    if (
        video and video["pid"] is not None
    ):  # Sadece geçerli bir PID varsa durdurmayı dene
        try:
            os.kill(video["pid"], signal.SIGTERM)
            flash("İndirme durduruldu.", "info")
        except ProcessLookupError:
            flash("İşlem zaten sonlanmış olabilir.", "warning")
        except OSError as e:
            flash(
                f"İşlem durdurulurken bir işletim sistemi hatası oluştu: {e}", "danger"
            )

        db.execute(
            "UPDATE videos SET status = 'Duraklatıldı', pid = NULL, progress = 0 WHERE id = ?",
            (video_id,),
        )
        db.commit()
    # ---------------------------------

    db.close()
    return redirect(url_for("index"))


@app.route("/delete/<int:video_id>", methods=["POST"])
def delete_video(video_id):
    if not session.get("logged_in"):
        return redirect(url_for("login"))

    # Silmeden önce çalışan bir işlem varsa durdur
    db = get_db()
    video = db.execute("SELECT * FROM videos WHERE id = ?", (video_id,)).fetchone()
    if video and video["pid"] is not None:
        stop_download(video_id)

    # Şimdi veritabanından sil
    db.execute("DELETE FROM videos WHERE id = ?", (video_id,))
    db.commit()
    db.close()

    flash("Video başarıyla silindi.", "success")
    return redirect(url_for("index"))


@app.route("/status")
def status_api():
    if not session.get("logged_in"):
        return {}, 401

    db = get_db()
    videos = db.execute("SELECT id, status, progress FROM videos").fetchall()
    db.close()

    return {v["id"]: {"status": v["status"], "progress": v["progress"]} for v in videos}


def setup_database():
    """Veritabanı tablosunu yeni meta veri sütunlarıyla günceller veya oluşturur."""
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    try:
        cursor.execute("PRAGMA table_info(videos);")
        columns = [col[1] for col in cursor.fetchall()]
        if "pid" not in columns:
            cursor.execute("ALTER TABLE videos ADD COLUMN pid INTEGER;")
        if "progress" not in columns:
            cursor.execute("ALTER TABLE videos ADD COLUMN progress INTEGER DEFAULT 0;")
        if "title" not in columns:
            cursor.execute("ALTER TABLE videos ADD COLUMN title TEXT;")
        if "year" not in columns:
            cursor.execute("ALTER TABLE videos ADD COLUMN year TEXT;")
        if "genre" not in columns:
            cursor.execute("ALTER TABLE videos ADD COLUMN genre TEXT;")
    except sqlite3.OperationalError:
        cursor.execute("""
        CREATE TABLE videos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url TEXT NOT NULL,
            status TEXT NOT NULL,
            title TEXT,
            year TEXT,
            genre TEXT,
            source_url TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            pid INTEGER,
            progress INTEGER DEFAULT 0
        );
        """)
    conn.commit()
    conn.close()


if __name__ == "__main__":
    setup_database()
    app.run(debug=True, host="0.0.0.0", port=5000)
