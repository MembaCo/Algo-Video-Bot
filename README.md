<p align="center">
<img src="https://placehold.co/800x200/111827/7c3aed?text=Algo-Video-Bot" alt="Algo-Video-Bot Banner">
</p>

<h1 align="center">Algo-Video-Bot: Gelişmiş Video İndirme Yöneticisi</h1>

<p align="center">
Modern ve dinamik video sitelerinden içerik indirmeyi otomatikleştiren, web tabanlı bir yönetim paneli.
</p>

<p align="center">
<a href="https://github.com/MembaCo/Algo-Video-Bot/actions/workflows/docker-publish.yml">
<img src="https://github.com/MembaCo/Algo-Video-Bot/actions/workflows/docker-publish.yml/badge.svg" alt="Docker Image CI">
</a>
<a href="https://github.com/MembaCo/Algo-Video-Bot/blob/main/LICENSE">
<img src="https://img.shields.io/badge/license-MIT-blue.svg" alt="License">
</a>
</p>

Algo-Video-Bot, modern ve dinamik video sitelerinden içerik indirmeyi otomatikleştiren, web tabanlı bir yönetim paneline sahip gelişmiş bir Python uygulamasıdır. Kullanıcıların video linklerini (tek tek, toplu veya dizi olarak) ekleyip indirme işlemlerini modern bir arayüz üzerinden yönetmelerini sağlar.

Proje, Docker ile paketlenmiş olup, GitHub Actions aracılığıyla otomatik olarak derlenir ve herhangi bir sunucuda veya CasaOS gibi platformlarda kolayca dağıtılabilir.

## 🚀 Temel Özellikler

- **Modern Web Arayüzü**: Videoları eklemek, kuyruğu yönetmek ve indirme durumlarını canlı olarak izlemek için kullanıcı dostu bir panel.
- **Güvenli Yönetim Paneli**: Panele erişimi korumak için hash'lenmiş parola sistemi ve arayüzden parola değiştirme imkanı.
- **Akıllı Meta Veri Çekme**: Sıraya eklenen her içerik için başlık, yıl, özet, IMDb puanı ve poster gibi zengin meta verileri otomatik olarak siteden çeker.
- **Esnek Video Ekleme**:
  - **Tekli Film Ekleme**: Tek bir film URL'si ile video ekleme.
  - **Toplu Film Ekleme**: Bir kategori veya arşiv sayfasındaki tüm videoları tek seferde kuyruğa ekleme.
  - **Dizi Desteği**: Dizi ana sayfasından tüm sezon ve bölüm bilgilerini çekerek indirme listesine ekleme.
- **Gelişmiş Ayarlar**: İndirme klasörünü, dosya adı şablonunu, eşzamanlı indirme sayısını ve hız limitini arayüzden yönetme.
- **Otomatik İndirme Yöneticisi**: Kuyruğa eklenen videoları, belirlenen eşzamanlı indirme limitine göre otomatik olarak indirir.
- **Dayanıklı Web Kazıma (Scraping)**: Selenium-wire kullanarak JavaScript ile korunan ve dinamik olarak yüklenen video kaynaklarını bulur.
- **Güvenilir Video İndirme**: `yt-dlp` entegrasyonu ile en karmaşık video akışlarını (.m3u8 vb.) sorunsuzca indirir.
- **Kolay Dağıtım**: GitHub Actions ile otomatik derlenen Docker imajı sayesinde tek komutla kurulum ve çalıştırma.

## 💻 Kullanılan Teknolojiler

- **Backend**: Python, Flask
- **Web Scraping**: Selenium, Selenium-Wire, BeautifulSoup
- **Video İndirme**: yt-dlp
- **Frontend**: HTML, Tailwind CSS, JavaScript (Fetch API)
- **Veritabanı**: SQLite
- **Dağıtım**: Docker, GitHub Actions

## ⚙️ Kurulum ve Çalıştırma

### 🐳 Docker ile Dağıtım (Tavsiye Edilen)

Bu proje, GitHub Actions kullanılarak otomatik olarak bir Docker imajı olarak derlenir ve GitHub Container Registry (GHCR) üzerinde yayınlanır.

#### Standart Sunucu Kurulumu

1. **Gerekli Klasörleri ve Dosyaları Hazırlayın:**

    ```bash
    mkdir -p algo-video-bot/data downloads
    cd algo-video-bot
    touch data/database.db data/app.log
    touch .env
    ```

2. **Parola Hash'i Üretin:** Terminalde aşağıdaki komutu çalıştırarak güvenli bir parola hash'i oluşturun ve çıktıyı kopyalayın.

    ```bash
    python3 -c "from werkzeug.security import generate_password_hash; print(generate_password_hash('SENIN_GUVENLI_PAROLAN'))"
    ```

3. **.env Dosyasını Doldurun:** `touch` komutuyla oluşturduğunuz `.env` dosyasını açın ve içini aşağıdaki gibi doldurun:

    ```env
    # Rastgele ve güvenli bir anahtar için 'openssl rand -hex 32' komutunu kullanabilirsiniz.
    SECRET_KEY="COK_GIZLI_VE_GUCLU_BIR_ANAHTAR_BURAYA_YAZIN"
    ADMIN_USERNAME="admin"
    ADMIN_PASSWORD_HASH="<BURAYA_KOPYALADIGINIZ_HASH_GELECEK>"
    DATA_DIR="/app/data"
    ```

4. **Docker Konteynerini Çalıştırın:**

    ```bash
    docker run -d \
      -p 5000:5000 \
      --name algo-video-bot \
      --restart unless-stopped \
      -v ./downloads:/app/downloads \
      -v ./data:/app/data \
      --env-file ./.env \
      --shm-size=2g \
      ghcr.io/membaco/algo-video-bot:latest
    ```

5. **Erişim:** Artık uygulamaya `http://SUNUCU_IP_ADRESINIZ:5000` adresinden erişebilirsiniz.

#### CasaOS Kurulumu

1. CasaOS arayüzünde **App Store**'a gidin.
2. Sağ üst köşedeki **Custom Install** butonuna tıklayın.
3. Açılan pencerede **Import** seçeneğine tıklayın.
4. Aşağıdaki `docker-compose.yml` kodunun tamamını metin kutusuna yapıştırın ve **Submit** butonuna basın.

    ```yaml
    services:
      algo-video-bot:
        image: ghcr.io/membaco/algo-video-bot:latest
        container_name: algo-video-bot
        ports:
          - 5000:5000
        volumes:
          - type: bind
            source: /DATA/AppData/algo-video-bot/downloads
            target: /app/downloads
          - type: bind
            source: /DATA/AppData/algo-video-bot/data
            target: /app/data
        environment:
          - SECRET_KEY= # Buraya çok gizli ve rastgele bir anahtar yazın
          - ADMIN_USERNAME=admin
          - ADMIN_PASSWORD_HASH= # Buraya ürettiğiniz parola hash'ini yapıştırın
          - DATA_DIR=/app/data
        restart: unless-stopped
        shm_size: 2g
        x-casaos:
          architectures:
            - amd64
          main: algo-video-bot
          description:
            en_us: Web tabanlı video indirme yöneticisi.
          tagline:
            en_us: Kişisel Video İndirme Yöneticiniz
          developer: MembaCo
          author: MembaCo
          icon: [https://raw.githubusercontent.com/walkxcode/dashboard-icons/main/png/movie-clapper.png](https://raw.githubusercontent.com/walkxcode/dashboard-icons/main/png/movie-clapper.png)
          title:
            en_us: Algo Video Bot
          category: Utilities
          port_map: "5000"
    ```

5. CasaOS'un göstereceği `SECRET_KEY` ve `ADMIN_PASSWORD_HASH` alanlarını doldurduktan sonra **Install** butonuna basarak kurulumu tamamlayın.

## 🤝 Katkıda Bulunma

Katkılarınız projeyi daha iyi hale getirecektir! Lütfen bir "issue" açarak veya "pull request" göndererek katkıda bulunun.

1. Projeyi Fork'layın.
2. Kendi Feature Branch'inizi oluşturun (`git checkout -b feature/AmazingFeature`).
3. Değişikliklerinizi Commit'leyin (`git commit -m 'Add some AmazingFeature'`).
4. Branch'inizi Push'layın (`git push origin feature/AmazingFeature`).
5. Bir Pull Request açın.

## 📄 Lisans

Bu proje MIT Lisansı ile lisanslanmıştır. Daha fazla bilgi için `LICENSE` dosyasına bakın.

<p align="center">
Bu proje, <strong>MembaCo.</strong> tarafından geliştirilmiştir.
</p>
