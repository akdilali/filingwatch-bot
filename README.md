# 🔍 FilingWatch - USPTO Patent/Trademark Bot

USPTO'dan yeni patent ve trademark başvurularını takip edip, ilginç olanları X (Twitter) hesabında otomatik olarak paylaşan bot.

## 📋 Özellikler

- ✅ USPTO'dan günlük patent/trademark verilerini çeker
- ✅ Büyük şirketlerin (Apple, Tesla, Meta, vb.) başvurularını filtreler
- ✅ İlginç keyword'lere sahip başvuruları tespit eder (AI, metaverse, crypto, vb.)
- ✅ Tweet atmadan önce manuel onay sistemi
- ✅ Rate limit koruması
- ✅ Mock data ile test modu

## 🚀 Kurulum

1. **Depoyu klonlayın:**
```bash
git clone <repo-url>
cd x_patent_project
```

2. **Virtual environment oluşturun:**
```bash
python -m venv .venv
source .venv/bin/activate  # macOS/Linux
# .venv\Scripts\activate  # Windows
```

3. **Bağımlılıkları yükleyin:**
```bash
pip install -r requirements.txt
```

4. **X (Twitter) API bilgilerini ayarlayın:**
   - https://developer.twitter.com/en/portal/dashboard adresine gidin
   - Yeni bir proje ve uygulama oluşturun
   - API Key, API Secret, Access Token, ve Bearer Token'ı alın
   - `.env.example` dosyasını `.env` olarak kopyalayın:
   ```bash
   cp .env.example .env
   ```
   - `.env` dosyasını düzenleyip API bilgilerinizi ekleyin

## 🔑 X API Ayarları

X Developer Portal'da uygulamanızın şu izinlere sahip olduğundan emin olun:
- ✅ Read and Write (Tweet atabilmek için)
- ✅ OAuth 1.0a aktif

## 📦 Gereksinimler

```
tweepy>=4.14.0      # X (Twitter) API
requests>=2.31.0    # HTTP istekleri
python-dotenv>=1.0.0 # .env dosya yönetimi
lxml>=5.0.0         # XML parsing (USPTO verileri için)
```

## 🎯 Kullanım

```bash
python main.py
```

Program şu adımları takip eder:
1. USPTO'dan veri çeker
2. İlginç patent/trademark'ları filtreler
3. Her biri için tweet önizlemesi gösterir
4. Kullanıcıdan onay alır (y/n/q)
5. Onaylananları X hesabında paylaşır

## 📝 Filtreleme Kriterleri

**Büyük Şirketler:**
- Apple, Google, Microsoft, Amazon, Meta
- Tesla, Nvidia, Netflix, Spotify
- OpenAI, Anthropic, Adobe
- Samsung, Sony, Nintendo, Disney
- ve daha fazlası...

**İlginç Keyword'ler:**
- AI, GPT, LLM, Neural Networks
- Metaverse, VR, AR, Mixed Reality
- Crypto, Blockchain, NFT, Web3
- Quantum Computing, Robotics
- Space, Satellite, Rocket
- Biotech, Gene Therapy
- Gaming, eSports, Fintech

## 🗂️ Proje Yapısı

```
x_patent_project/
├── main.py              # Ana uygulama
├── requirements.txt     # Python bağımlılıkları
├── .env.example         # API key template
├── .env                 # API keys (git'e eklenmez)
└── README.md           # Bu dosya
```

## 🔄 Gelecek Özellikler

- [ ] USPTO API entegrasyonu (şu anda mock data kullanılıyor)
- [ ] XML veri parsing
- [ ] Veritabanı entegrasyonu (tweet geçmişi)
- [ ] Zamanlanmış otomatik çalışma (cron/scheduler)
- [ ] Web dashboard
- [ ] Çoklu hesap desteği
- [ ] Kategori bazlı filtreleme
- [ ] ML bazlı ilginçlik skorlaması

## ⚠️ Önemli Notlar

- **Rate Limiting:** X API'si rate limit'e sahiptir. Bot tweet'ler arası 30 saniye bekler.
- **Mock Data:** Şu anda gerçek USPTO API'si yerine test verileri kullanılıyor.
- **API Keys:** `.env` dosyasını asla git'e eklemeyin (`.gitignore` içinde).

## 🐛 Sorun Giderme

**"X API credentials eksik" hatası:**
- `.env` dosyasının mevcut olduğundan emin olun
- API key'lerin doğru kopyalandığını kontrol edin
- Tırnak işareti kullanmayın

**"lxml kurulum hatası" (Python 3.13):**
- `requirements.txt`'te `lxml>=5.0.0` kullanın (5.x Python 3.13 uyumlu)

**Tweet atılamıyor:**
- X Developer Portal'da "Read and Write" izninin olduğunu kontrol edin
- Access Token'ı Read/Write izniyle yeniden oluşturun

## 📄 Lisans

MIT

## 👨‍💻 Geliştirici

Ali Akdil
