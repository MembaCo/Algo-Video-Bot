# @author: MembaCo.

from abc import ABC, abstractmethod


class BaseWorker(ABC):
    """
    Tüm site worker'ları için temel arayüz (interface) görevi görür.
    Her worker, bu sınıftan miras almalı ve `find_manifest_url` metodunu doldurmalıdır.
    """

    @abstractmethod
    def find_manifest_url(self, target_url):
        """
        Verilen URL için video kaynağını (manifest), header'ları ve cookie'leri bulur.

        Args:
            target_url (str): Filmin izleme sayfasının URL'si.

        Returns:
            tuple: (manifest_url, headers, cookies) içeren bir tuple
                   veya başarısız olursa (None, None, None).
        """
        pass
