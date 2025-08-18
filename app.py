# @author: MembaCo.

import logging
import json
from flask import Flask, render_template, request, redirect, url_for, flash, session
import os
import signal
import requests
from bs4 import BeautifulSoup
from multiprocessing import Process
import sys
import subprocess
import glob
import re

# Yerel modüllerden importlar
import config
from database import get_db, setup_database
from worker import process_video
from logging_config import setup_logging

# Loglamayı başlat
logger = setup_logging()

app = Flask(__name__)
app.secret_key = config.SECRET_KEY

# Flask'in kendi logger'ını bizim yapılandırmamızla entegre et
if app.logger.handlers:
    app.logger.removeHandler(app.logger.handlers[0])
app.logger = logger


def _scrape_from_html(soup):
    """
    JSON-LD başarısız olduğunda doğrudan HTML'den veri kazımak için yedek fonksiyon.
    """
    logger.info("Yedek HTML kazıma yöntemi kullanılıyor.")
    try:
        metadata = {
            "title": "Başlık Bulunamadı",
            "description": "Özet bulunamadı.",
            "year": "Bilinmiyor",
            "genre": "Bilinmiyor",
            "imdb_score": "Bilinmiyor",
            "director": "Bilinmiyor",
            "cast": "Bilinmiyor",
        }

        header = soup.find("div", class_="sheader")
        if header:
            title_tag = header.find("h1")
            if title_tag:
                metadata["title"] = title_tag.text.strip()

        content_div = soup.find("div", class_="wp-content")
        if content_div and content_div.find("p"):
            metadata["description"] = content_div.find("p").text.strip()

        custom_fields = soup.find_all("div", class_="custom_fields")
        for field in custom_fields:
            label_tag = field.find("b", class_="variante")
            value_tag = field.find("span", class_="valor")
            if label_tag and value_tag:
                label = label_tag.text.strip().lower()
                value = value_tag.text.strip()

                if "imdb puanı" in label:
                    imdb_strong_tag = value_tag.find("strong")
                    metadata["imdb_score"] = (
                        imdb_strong_tag.text.strip() if imdb_strong_tag else value
                    )
                elif "yönetmen" in label:
                    metadata["director"] = value
                elif "oyuncular" in label:
                    metadata["cast"] = value

        if header:
            year_tag = header.find("span", class_="C")
            if year_tag and year_tag.find("a"):
                metadata["year"] = year_tag.find("a").text.strip()

            genre_div = header.find("div", class_="sgeneros")
            if genre_div:
                genres = [a.text.strip() for a in genre_div.find_all("a")]
                metadata["genre"] = ", ".join(genres)

        if "HDFilmcehennemi" in metadata["title"]:
            logger.warning("HTML kazıma jenerik bir başlık buldu, veri geçersiz.")
            return None

        return metadata

    except Exception:
        logger.error("Yedek HTML kazıma yöntemi sırasında hata oluştu.", exc_info=True)
        return None


def scrape_metadata(url):
    """
    BeautifulSoup ile bir URL'den detaylı film bilgilerini çeker.
    Önce JSON-LD dener, başarısız olursa HTML kazımayı dener.
    """
    try:
        headers = {"User-Agent": config.USER_AGENT}
        response = requests.get(url, headers=headers, timeout=20)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        json_ld_script = soup.find("script", type="application/ld+json")
        if json_ld_script:
            logger.info(f"JSON-LD verisi bulundu. URL: {url}")
            data = json.loads(json_ld_script.string)

            movie_data = None

            def find_movie_in_json(item):
                if not isinstance(item, dict):
                    return None
                item_type = item.get("@type")
                if (isinstance(item_type, str) and item_type == "Movie") or (
                    isinstance(item_type, list) and "Movie" in item_type
                ):
                    return item
                return None

            if isinstance(data, list):
                for item in data:
                    movie_data = find_movie_in_json(item)
                    if movie_data:
                        break
            else:
                movie_data = find_movie_in_json(data)

            if not movie_data:
                logger.warning(
                    f"'Movie' tipi bulunamadı. Yedek mekanizma devreye giriyor. URL: {url}"
                )
                if isinstance(data, list):
                    for item in data:
                        if isinstance(item, dict) and all(
                            k in item for k in ["director", "actor", "aggregateRating"]
                        ):
                            movie_data = item
                            logger.info("Yedek mekanizma ile film verisi bulundu.")
                            break
                elif isinstance(data, dict) and all(
                    k in data for k in ["director", "actor", "aggregateRating"]
                ):
                    movie_data = data
                    logger.info("Yedek mekanizma ile film verisi bulundu.")

            if movie_data:
                title = movie_data.get("name", "Başlık Bulunamadı")
                if "HDFilmcehennemi" in title and len(title) < 20:
                    logger.warning(
                        f"JSON-LD jenerik bir başlık içeriyor ('{title}'), yoksayılıyor."
                    )
                else:
                    rating = movie_data.get("aggregateRating", {})
                    actors = ", ".join(
                        [
                            actor["name"]
                            for actor in movie_data.get("actor", [])
                            if "name" in actor
                        ]
                    )
                    director_data = movie_data.get("director")
                    director = "Bilinmiyor"
                    if isinstance(director_data, list):
                        director = ", ".join(
                            [d["name"] for d in director_data if "name" in d]
                        )
                    elif isinstance(director_data, dict):
                        director = director_data.get("name", "Bilinmiyor")

                    metadata = {
                        "title": title,
                        "description": movie_data.get(
                            "description", "Özet bulunamadı."
                        ),
                        "year": movie_data.get("datePublished", "Bilinmiyor")[:4],
                        "genre": ", ".join(movie_data.get("genre", []))
                        if isinstance(movie_data.get("genre"), list)
                        else movie_data.get("genre", "Bilinmiyor"),
                        "imdb_score": rating.get("ratingValue", "Bilinmiyor"),
                        "director": director,
                        "cast": actors,
                    }
                    logger.info("JSON-LD ile film verisi başarıyla çekildi.")
                    return metadata

        logger.warning(
            f"JSON-LD ile geçerli veri bulunamadı, HTML kazıma yöntemine geçiliyor. URL: {url}"
        )
        return _scrape_from_html(soup)

    except requests.exceptions.RequestException:
        logger.error(f"Meta veri çekilirken ağ hatası oluştu: {url}", exc_info=True)
        return None
    except Exception:
        logger.error(
            f"Meta veri ayrıştırılırken genel bir hata oluştu: {url}", exc_info=True
        )
        return None


@app.before_request
def require_login():
    if not session.get("logged_in") and request.endpoint not in ["login", "static"]:
        return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if session.get("logged_in"):
        return redirect(url_for("index"))
    if request.method == "POST":
        if (
            request.form["username"] == config.ADMIN_USERNAME
            and request.form["password"] == config.ADMIN_PASSWORD
        ):
            session["logged_in"] = True
            logger.info(f"Kullanıcı '{config.ADMIN_USERNAME}' başarıyla giriş yaptı.")
            return redirect(url_for("index"))
        else:
            flash("Hatalı kullanıcı adı veya şifre.", "danger")
            logger.warning(
                f"Başarısız giriş denemesi. Kullanıcı adı: {request.form.get('username')}"
            )
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
    db.close()
    return render_template("index.html", videos=videos)


@app.route("/add", methods=["POST"])
def add_video():
    url = request.form["url"]
    if config.ALLOWED_DOMAIN not in url:
        flash(f"Lütfen geçerli bir {config.ALLOWED_DOMAIN} linki girin.", "warning")
        return redirect(url_for("index"))

    logger.info(f"Yeni video ekleme isteği alındı: {url}")
    metadata = scrape_metadata(url)
    if not metadata:
        flash(
            "Film bilgileri çekilemedi. Lütfen linki kontrol edin veya site yapısı değişmiş olabilir.",
            "danger",
        )
        return redirect(url_for("index"))

    db = get_db()
    db.execute(
        """
        INSERT INTO videos (url, status, title, year, genre, description, imdb_score, director, cast) 
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            url,
            "Sırada",
            metadata["title"],
            metadata["year"],
            metadata["genre"],
            metadata["description"],
            metadata["imdb_score"],
            metadata["director"],
            metadata["cast"],
        ),
    )
    db.commit()
    db.close()
    flash(f'"{metadata["title"]}" başarıyla sıraya eklendi.', "success")
    logger.info(f"'{metadata['title']}' adlı film sıraya eklendi.")
    return redirect(url_for("index"))


def start_worker_process(video_id):
    p = Process(target=process_video, args=(video_id,))
    p.start()
    return p.pid


@app.route("/start/<int:video_id>")
def start_download(video_id):
    db = get_db()
    video = db.execute("SELECT * FROM videos WHERE id = ?", (video_id,)).fetchone()
    if not video:
        flash("Video bulunamadı.", "danger")
        db.close()
        return redirect(url_for("index"))

    if video["status"] in ["Kaynak aranıyor...", "İndiriliyor"]:
        flash("Bu indirme zaten devam ediyor.", "warning")
    else:
        pid = start_worker_process(video_id)
        db.execute(
            "UPDATE videos SET status = ?, pid = ?, progress = 0, filepath = NULL WHERE id = ?",
            ("Kaynak aranıyor...", pid, video_id),
        )
        db.commit()
        flash(f'"{video["title"]}" için indirme başlatıldı.', "info")
        logger.info(
            f"ID {video_id} ('{video['title']}') için indirme işlemi başlatıldı. PID: {pid}"
        )
    db.close()
    return redirect(url_for("index"))


@app.route("/stop/<int:video_id>")
def stop_download(video_id):
    db = get_db()
    video = db.execute("SELECT * FROM videos WHERE id = ?", (video_id,)).fetchone()
    if video and video["pid"]:
        pid = video["pid"]
        logger.info(
            f"ID {video_id} ('{video['title']}') için durdurma isteği. PID: {pid}"
        )
        try:
            if sys.platform != "win32":
                os.killpg(os.getpgid(pid), signal.SIGTERM)
            else:
                subprocess.run(
                    ["taskkill", "/F", "/T", "/PID", str(pid)],
                    check=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                )
            flash("İndirme durdurma isteği gönderildi.", "info")
        except (ProcessLookupError, subprocess.CalledProcessError):
            flash("İşlem zaten sonlanmış.", "warning")
            logger.warning(
                f"Durdurulmaya çalışılan işlem (PID: {pid}) bulunamadı veya zaten sonlanmış."
            )
        except OSError as e:
            if "No such process" in str(e):
                flash("İşlem zaten sonlanmış.", "warning")
                logger.warning(
                    f"Durdurulmaya çalışılan işlem (PID: {pid}) bulunamadı (getpgid hatası)."
                )
            else:
                flash(f"İşlem durdurulurken bir hata oluştu: {e}", "danger")
                logger.error(
                    f"İşlem durdurulurken hata oluştu (PID: {pid})", exc_info=True
                )

        db.execute(
            "UPDATE videos SET status = 'Duraklatıldı', pid = NULL WHERE id = ?",
            (video_id,),
        )
        db.commit()
    db.close()
    return redirect(url_for("index"))


@app.route("/delete/<int:video_id>", methods=["POST"])
def delete_video(video_id):
    db = get_db()
    video = db.execute("SELECT * FROM videos WHERE id = ?", (video_id,)).fetchone()
    if video and video["pid"]:
        stop_download(video_id)

    title_to_log = "Bilinmeyen"
    if video:
        title_to_log = video["title"] or "Bilinmeyen"

    db.execute("DELETE FROM videos WHERE id = ?", (video_id,))
    db.commit()
    db.close()
    flash("Video kaydı başarıyla silindi.", "success")
    logger.info(f"ID {video_id} ('{title_to_log}') veritabanından silindi.")
    return redirect(url_for("index"))


@app.route("/delete_file/<int:video_id>", methods=["POST"])
def delete_file(video_id):
    db = get_db()
    video = db.execute("SELECT * FROM videos WHERE id = ?", (video_id,)).fetchone()
    if not video:
        flash("Video kaydı bulunamadı.", "danger")
        db.close()
        return redirect(url_for("index"))

    filepath = video["filepath"]
    if filepath and os.path.exists(filepath):
        try:
            os.remove(filepath)
            db.execute("UPDATE videos SET filepath = NULL WHERE id = ?", (video_id,))
            db.commit()
            flash(
                f'"{os.path.basename(filepath)}" diskten başarıyla silindi.', "success"
            )
            logger.info(f"Dosya diskten silindi: {filepath}")
        except OSError as e:
            flash("Dosya silinirken bir hata oluştu.", "danger")
            logger.error(f"Dosya silinemedi: {filepath}", exc_info=True)
    else:
        flash("Silinecek dosya bulunamadı veya zaten silinmiş.", "warning")
        # Dosya yoksa bile veritabanındaki yolu temizle
        db.execute("UPDATE videos SET filepath = NULL WHERE id = ?", (video_id,))
        db.commit()

    db.close()
    return redirect(url_for("index"))


@app.route("/status")
def status_api():
    if not session.get("logged_in"):
        return {}, 401
    db = get_db()
    videos = db.execute("SELECT id, status, progress, filepath FROM videos").fetchall()
    db.close()
    return {
        v["id"]: {
            "status": v["status"],
            "progress": v["progress"],
            "filepath": v["filepath"],
        }
        for v in videos
    }


if __name__ == "__main__":
    setup_database()
    if not os.path.exists(config.DOWNLOADS_FOLDER):
        os.makedirs(config.DOWNLOADS_FOLDER)
    logger.info("Uygulama başlatılıyor...")
    app.run(debug=True, host="0.0.0.0", port=5000)
