# @author: MembaCo.

import logging
import threading
import time
import os

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    session,
    jsonify,
    g,
)
from werkzeug.security import check_password_hash

# Yerel modüllerden importlar
import config
from database import get_db, setup_database, close_db
from logging_config import setup_logging
import services

# Loglamayı başlat
logger = setup_logging()

app = Flask(__name__)
app.secret_key = config.SECRET_KEY
app.teardown_appcontext(close_db)  # Her istek sonunda veritabanı bağlantısını kapat

# Flask'in kendi logger'ını bizim yapılandırmamızla entegre et
if app.logger.handlers:
    app.logger.removeHandler(app.logger.handlers[0])
app.logger = logger

# --- Otomatik İndirme Durumu ---
auto_download_manager_state = {"enabled": False, "thread": None}


def auto_download_manager():
    """Arka planda çalışarak otomatik indirmeleri yöneten thread."""
    logger.info("Otomatik indirme yöneticisi thread'i başlatıldı.")
    while auto_download_manager_state.get("enabled", False):
        try:
            with app.app_context():
                services.run_auto_download_cycle()
        except Exception as e:
            logger.error(f"Otomatik indirme yöneticisinde hata: {e}", exc_info=True)
        time.sleep(config.AUTO_DOWNLOAD_POLL_INTERVAL)
    logger.info("Otomatik indirme yöneticisi thread'i durduruldu.")


@app.before_request
def require_login():
    if not session.get("logged_in") and request.endpoint not in ["login", "static"]:
        return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if session.get("logged_in"):
        return redirect(url_for("index"))
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        if username == config.ADMIN_USERNAME and check_password_hash(
            config.ADMIN_PASSWORD_HASH, password
        ):
            session["logged_in"] = True
            logger.info(f"Kullanıcı '{username}' başarıyla giriş yaptı.")
            return redirect(url_for("index"))
        else:
            flash("Hatalı kullanıcı adı veya şifre.", "danger")
            logger.warning(f"Başarısız giriş denemesi. Kullanıcı adı: {username}")
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.pop("logged_in", None)
    flash("Başarıyla çıkış yaptınız.", "success")
    return redirect(url_for("login"))


@app.route("/")
def index():
    db = get_db()
    videos = db.execute("SELECT * FROM videos ORDER BY created_at DESC").fetchall()
    return render_template("index.html", videos=videos, version=config.VERSION)


@app.route("/add", methods=["POST"])
def add_video():
    url = request.form["url"]
    if config.ALLOWED_DOMAIN not in url:
        flash(f"Lütfen geçerli bir {config.ALLOWED_DOMAIN} linki girin.", "warning")
        return redirect(url_for("index"))

    success, message = services.add_video_to_queue(url)
    flash(message, "success" if success else "danger")
    return redirect(url_for("index"))


@app.route("/add_list", methods=["POST"])
def add_list():
    list_url = request.form["list_url"]
    if config.ALLOWED_DOMAIN not in list_url:
        flash(f"Lütfen geçerli bir {config.ALLOWED_DOMAIN} linki girin.", "warning")
        return redirect(url_for("index"))

    # --- DEĞİŞİKLİK BURADA ---
    # Arka plan işlemine 'app' nesnesini parametre olarak veriyoruz.
    thread = threading.Thread(
        target=services.add_videos_from_list_page_async, args=(app, list_url)
    )
    thread.daemon = True
    thread.start()

    flash(
        "Toplu ekleme işlemi arka planda başlatıldı. Videolar kısa süre içinde kuyruğa eklenecektir.",
        "info",
    )
    return redirect(url_for("index"))


@app.route("/start/<int:video_id>", methods=["POST"])
def start_download(video_id):
    success, message = services.start_download_for_video(video_id)
    flash(message, "info" if success else "warning")
    return redirect(url_for("index"))


@app.route("/stop/<int:video_id>", methods=["POST"])
def stop_download(video_id):
    success, message = services.stop_download_for_video(video_id)
    flash(message, "info" if success else "danger")
    return redirect(url_for("index"))


@app.route("/delete/<int:video_id>", methods=["POST"])
def delete_video(video_id):
    services.delete_video_record(video_id)
    flash("Video kaydı başarıyla silindi.", "success")
    return redirect(url_for("index"))


@app.route("/delete_file/<int:video_id>", methods=["POST"])
def delete_file(video_id):
    success, message = services.delete_video_file(video_id)
    flash(message, "success" if success else "danger")
    return redirect(url_for("index"))


@app.route("/toggle_auto_download", methods=["POST"])
def toggle_auto_download():
    is_enabled = auto_download_manager_state["enabled"]
    if is_enabled:
        auto_download_manager_state["enabled"] = False
        flash("Otomatik indirme pasif hale getirildi.", "info")
        logger.info("Otomatik indirme durumu: PASİF")
    else:
        auto_download_manager_state["enabled"] = True
        thread = threading.Thread(target=auto_download_manager, daemon=True)
        auto_download_manager_state["thread"] = thread
        thread.start()
        flash("Otomatik indirme aktif hale getirildi.", "info")
        logger.info("Otomatik indirme durumu: AKTİF")
    return redirect(url_for("index"))


@app.route("/status")
def status_api():
    if not session.get("logged_in"):
        return jsonify({"error": "Unauthorized"}), 401

    videos_data = services.get_all_videos_status()
    return jsonify(
        {
            "videos": videos_data,
            "auto_download_enabled": auto_download_manager_state["enabled"],
        }
    )


if __name__ == "__main__":
    setup_database()
    if not os.path.exists(config.DOWNLOADS_FOLDER):
        os.makedirs(config.DOWNLOADS_FOLDER)

    logger.info("Uygulama başlatılıyor...")
    app.run(debug=True, host="0.0.0.0", port=5000, use_reloader=False)
