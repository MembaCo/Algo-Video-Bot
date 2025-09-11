# @author: MembaCo.

from abc import ABC, abstractmethod


class BaseScraper(ABC):
    """
    Tüm site kazıyıcıları (scrapers) için temel arayüz (interface) görevi görür.
    Yeni bir site desteği eklemek için bu sınıftan miras alınmalı ve
    aşağıdaki tüm abstract metodlar doldurulmalıdır.
    """

    @abstractmethod
    def scrape_movie_metadata(self, url):
        """
        Verilen URL'den tek bir filmin meta verilerini (başlık, yıl, poster vb.) çeker.

        Args:
            url (str): Filmin detay sayfasının URL'si.

        Returns:
            dict or None: Film bilgilerini içeren bir sözlük veya başarısız olursa None.
        """
        pass

    @abstractmethod
    def scrape_movie_links_from_list_page(self, list_url):
        """
        Bir liste (kategori, arşiv, arama sonucu vb.) sayfasındaki tüm film linklerini çeker.

        Args:
            list_url (str): Liste sayfasının URL'si.

        Returns:
            tuple: (list of urls, error_message or None) formatında bir tuple.
                   Başarılı olursa film linklerinin listesi ve None,
                   başarısız olursa boş liste ve hata mesajı döner.
        """
        pass

    @abstractmethod
    def scrape_series_data(self, series_url):
        """
        Bir dizinin ana sayfasından tüm sezon ve bölüm bilgilerini (URL'ler dahil) çeker.

        Args:
            series_url (str): Dizinin ana sayfasının URL'si.

        Returns:
            dict or None: Dizi, sezonlar ve bölümler hakkındaki tüm bilgileri içeren
                          iç içe bir sözlük veya başarısız olursa None.
        """
        pass
