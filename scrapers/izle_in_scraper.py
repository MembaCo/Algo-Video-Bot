# @author: MembaCo.

import logging
import requests
from bs4 import BeautifulSoup
from .base_scraper import BaseScraper
import config

logger = logging.getLogger(__name__)


class IzleInScraper(BaseScraper):
    """izle.in sitesi için kazıma işlemlerini yürüten sınıf."""

    def __init__(self):
        self.headers = {"User-Agent": config.USER_AGENT}

    def scrape_movie_metadata(self, url):
        try:
            response = requests.get(url, headers=self.headers, timeout=20)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")

            # Open Graph etiketlerinden daha kaliteli veri alıyoruz
            title = (
                soup.find("meta", property="og:title")["content"]
                if soup.find("meta", property="og:title")
                else "Başlık Bulunamadı"
            )
            description = (
                soup.find("meta", property="og:description")["content"]
                if soup.find("meta", property="og:description")
                else "Özet bulunamadı."
            )
            poster_url = (
                soup.find("meta", property="og:image")["content"]
                if soup.find("meta", property="og:image")
                else ""
            )

            # Diğer bilgileri sayfadan kazıyoruz
            year_tag = soup.select_one(".info-right .title .release a")
            year = year_tag.text.strip() if year_tag else "Bilinmiyor"

            imdb_tag = soup.select_one(".rating-bottom .imdb-rating")
            imdb_score = imdb_tag.text.split()[0].strip() if imdb_tag else "Bilinmiyor"

            director_tag = soup.select_one(".cast .director a")
            director = director_tag.text.strip() if director_tag else "Bilinmiyor"

            actor_tag = soup.select_one(".cast .actor")
            # "Oyuncular:" metnini kaldırıp temizliyoruz
            cast = (
                actor_tag.text.replace("Oyuncular:", "").strip()
                if actor_tag
                else "Bilinmiyor"
            )

            genres = [a.text for a in soup.select(".categories a")]

            metadata = {
                "title": title.replace(" izle", ""),  # " izle" ekini temizliyoruz
                "description": description,
                "year": year,
                "genre": ", ".join(genres),
                "imdb_score": imdb_score,
                "director": director,
                "cast": cast,
                "poster_url": poster_url,
            }
            logger.info(
                f"izle.in sitesinden '{metadata['title']}' için meta veri çekildi."
            )
            return metadata
        except requests.exceptions.RequestException as e:
            logger.error(f"Meta veri çekilirken ağ hatası oluştu: {url}", exc_info=True)
            return None
        except Exception as e:
            logger.error(
                f"Meta veri ayrıştırılırken genel bir hata oluştu: {url}", exc_info=True
            )
            return None

    def scrape_movie_links_from_list_page(self, list_url):
        logger.warning("izle.in için toplu film ekleme özelliği henüz kodlanmadı.")
        return [], "Bu özellik bu site için henüz mevcut değil."

    def scrape_series_data(self, series_url):
        logger.warning("izle.in için dizi ekleme özelliği henüz kodlanmadı.")
        return None
