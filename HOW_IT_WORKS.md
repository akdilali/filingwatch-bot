# FilingWatch Bot - Çalışma Mantığı 🤖

Bu belge, **FilingWatch** botunun arka planda nasıl karar verdiğini ve çalıştığını adım adım açıklar.

## 1. Tetiklenme (Trigger) ⏰
Bot, sunucu üzerinde kurulu bir **Cron Job** (Zamanlayıcı) tarafından otomatik olarak çalıştırılır.
- **Sıklık:** Her 3 saatte bir.
- **Komut:** `run_bot.sh`

## 2. Tarama (Scraping) 🔍
`tsdr_scraper.py` modülü devreye girer.
1.  **Son Serial'i Bul:** USPTO sitesine gidip "Şu an en son hangi başvuru yapılmış?" diye sorar (Örn: 99912345).
2.  **Farkı Hesapla:** Botun hafızasındaki (`daily_cache.json`) son numara ile yeni numara arasındaki farka bakar.
3.  **Veriyi Çek:** Aradaki tüm yeni başvuruları (bazen 100, bazen 500 tane) tek tek indirir.
    *   *Güvenlik:* Eğer fark çok fazlaysa (bot uzun süre kapalı kaldıysa), sistemi yormamak için sadece son 2000 taneyi çeker.

## 3. Analiz ve Puanlama (Analyzer) 🧠
`main_v2.py` içindeki `calculate_importance_score` fonksiyonu her başvuruyu inceler.

### Puanlama Kriterleri:
*   **Büyük Şirketler:** Apple, Google, Tesla gibi şirketler ise **+100 Puan** (Direkt `must_post`).
*   **Teknoloji:** AI, GPT, Crypto, Quantum, Robot gibi kelimeler **+30 Puan**.
*   **Popüler Sektörler:** Otonom araçlar, İlaç, Silah sanayi **+20 Puan**.
*   **Gıda/İçecek:** Pizza, Burger, Beer **+10 Puan** (Halk ilgisi).

### Özel Filtre: "Weird Detector" 🤪
Eğer başvuru içinde "ZOMBIE", "ALIEN", "MEME" gibi tuhaf kelimeler varsa veya slogan çok uzun/saçma ise **Weird Adayı** olur.
*   *Kural:* Günde en fazla 1 tane Weird tweet atılır.
*   *Kullanıcı:* Son 24 saatte Weird tweet atıldıysa bu özellik devre dışı kalır.

## 4. Seçim (Selection) ⚖️
1.  Taranan 200 başvuru arasından en yüksek puanlı **2 tanesi** seçilir.
2.  Eğer "Weird" kontenjanı açıksa, bir tanesi Weird seçilebilir.
3.  Daha önce tweet atılmış olanlar (`posted_tweets.json`) elenir.

## 5. Görsel Hazırlığı (Visuals) 🎨
Seçilen her marka için:
1.  **Resmi Çizim:** USPTO'da markanın resmi logosu var mı? Varsa indirilir.
2.  **Kartvizit Modu:** Eğer logo yoksa (sadece metinse), `visuals.py` devreye girer.
    *   Siyah, premium bir arka plan üzerine marka ismi ve sahibi şık bir fontla yazılır.
    *   Sol köşeye "FilingWatch" imzası atılır.

## 6. Tweetleme (Posting) 🐦
Twitter API v2 kullanılarak tweet atılır.

**Tweet Yapısı:**
*   **Başlık:** 🤖 NEW TRADEMARK FILED (veya 🤪 WEIRD ALERT)
*   **Marka Adı:** BOLD olarak yazılır.
*   **Açıklama:** Ne işe yaradığı (max 110 karakter).
*   **Sahibi:** Şirket ismi (Eğer bilinen bir şirketse @Apple gibi etiketlenir).
*   **Link:** Resmi USPTO inceleme linki.
*   **Hashtagler:** #AI #Tech #USPTO (İçeriğe göre dinamik).

## 7. Hafıza ve Raporlama (History) 💾
1.  **Kaydetme:** Atılan tweet `posted_tweets.json` dosyasına işlenir (Tekrar atılmasın diye).
2.  **Arşiv:** Taranan *her şey* `history.json` veritabanına eklenir.
3.  **Haftalık Rapor:** Her Pazartesi sabahı, `history.json` analiz edilerek "Bu hafta en çok AI başvurusu yapıldı" gibi bir istatistik tweeti hazırlanır.

---
*FilingWatch v2.1*
