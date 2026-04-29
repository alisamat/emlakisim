# Emlakisim — Proje Master Planı

> Son güncelleme: 2026-04-29
> Durum: Planlama + Altyapı kurulumu aşaması

---

## VİZYON

Emlakisim, emlakçılar için yapay zeka destekli tam otomasyon asistanı.
- WhatsApp Business + Web uygulaması (tarayıcı tabanlı, mobil responsive/hibrit)
- İki taraflı: **Emlakçı** (ana kullanıcı) + **Alıcı/Satıcı** (müşteri portalı)
- Ana sayfa = AI sohbet ekranı (OnMuhasebeci tarzı layout)
- Her işlem hem WhatsApp'tan hem uygulama içi sohbetten yapılabilir
- Yeni nesil AI uygulaması — vizyon yüksek tutulacak

---

## MİMARİ

### Teknoloji Stack
- **Backend:** Flask + SQLAlchemy + PostgreSQL (Railway)
- **Frontend:** React (Vercel) — emlakisim.com
- **AI:** Gemini Flash (ucuz/basit), GPT-4o mini (doküman), Claude Haiku (analiz)
- **WhatsApp:** Meta Cloud API (Business numara: +90 533 046 92 31)
- **Bildirimler:** WhatsApp 24 saat kuralı dışında uygulama bildirimleri

### Kredi/Maliyet Sistemi
- Tüm AI işlemlerinde token sayısı ve dolar maliyeti hesaplanır
- Dolar maliyeti üzerine kar marjı eklenir → kredi birimine dönüştürülür
- Kullanıcının kredi hesabından düşülür
- Tek bir noktadan kontrol ve raporlama

---

## LAYOUT (OnMuhasebeci Referans)

```
┌─────────────────────────────────────────────────────────┐
│ [Logo] Emlakisim AI    [Kredi: 100]  [Profil]  [Çıkış] │
├──────────┬──────────────────────────────┬───────────────┤
│ SOL      │ ORTA                         │ SAĞ           │
│ MENÜ     │ AI SOHBET ALANI              │ İŞLEM MENÜSÜ  │
│          │                              │               │
│ Sohbet   │ [AI mesajları + kullanıcı    │ Hızlı         │
│  Yeni    │  mesajları WhatsApp tarzı]   │ En Çok        │
│  Geçmiş  │                              │ En Son        │
│          │                              │ Analiz        │
│ Müşteri  │                              │               │
│ Portföy  │                              │ Müşteriler    │
│ Muhasebe │                              │ Portföy       │
│ Belgeler │                              │ Muhasebe      │
│ Raporlar │                              │ Belgeler      │
│          │                              │ Raporlar      │
│          │ [Mesaj yaz...] [Gönder]      │ Hesaplamalar  │
└──────────┴──────────────────────────────┴───────────────┘
```

**Mobilde:** Sol menü hamburger, sağ menü alt sheet olarak açılır.

---

## TEMEL PRENSİPLER

### 1. Hız Öncelikli İşlem Mimarisi
```
Kullanıcı mesajı → Türkçe normalleştirme → Pattern/Intent matching → Direkt DB işlemi
                                                    ↓ (anlaşılamazsa)
                                               AI'ya yönlendir (Gemini Flash)
                                                    ↓ (karmaşıksa)
                                               Claude Haiku ile analiz
```
- Pattern matching ile tanınan komutlar AI'ya gitmez → sıfır maliyet, anlık sonuç
- AI sadece anlaşılamayan veya karmaşık işlemlerde devreye girer

### 2. Maliyet Minimizasyonu
- Basit CRUD: pattern matching, AI yok → $0
- Genel sohbet: Gemini Flash → ~$0.0001/mesaj
- Belge/rapor: GPT-4o mini → ~$0.0003/mesaj  
- Analiz/eşleştirme: Claude Haiku → ~$0.0005/mesaj
- Hedef: Ortalama mesaj maliyeti < $0.0002

### 3. Onbinlerce Komut Kombinasyonu
AI, function calling ile DB'ye doğrudan işlem yapar:
- "Ali Yılmaz müşterisini ekle telefonu 532..." → müşteri INSERT
- "Kadıköy portföyündeki kiralıkları listele" → müşteri SELECT + filtre
- "Ahmet bey ile yarın saat 3'te yer gösterme planla" → planlama INSERT + hatırlatma
- "Son 1 ayın kira gelir raporunu çıkar" → muhasebe SELECT + rapor
- Doğru ve güvenilir: her işlem onay mekanizması ile (kritik işlemlerde "emin misiniz?")

### 4. Güvenlik & Yedekleme
- Kullanıcı kendi Google Drive'ına otomatik yedekleme yapabilir
- Haftalık otomatik yedekleme (JSON/Excel export)
- Kritik işlemlerde (silme, toplu değişiklik) onay isteme
- İşlem log'u tutma (kim, ne zaman, ne yaptı)

### 5. Toplu İşlem Yetenekleri
- Fotoğraftan OCR ile portföy ekleme (sahibinden.com ekran görüntüsü → ilan listesi)
- Excel'den toplu müşteri/portföy import
- Telefon rehberinden toplu müşteri ekleme
- Toplu SMS/email gönderim
- AI proaktif olarak "Excel'den toplu portföy ekleyebilirsiniz" gibi öneriler sunar

### 6. Akıllı Diyalog & Akış Sistemi
- **Günlük:** "Günaydın! Bugün 3 yer göstermeniz var, 2 kaçırılan çağrı, 1 yeni lead"
- **Haftalık:** "Bu hafta 12 müşteri görüştünüz, 3 yer gösterme yaptınız, gelir: ₺15.000"
- **Aylık:** "Nisan özeti: 45 müşteri, 8 satış, 12 kiralama, toplam ₺2.1M"
- **Yıllık:** "2026 performans raporu: 540 müşteri, 96 satış..."
- Proaktif hatırlatmalar: "Ahmet bey'e 3 gündür dönüş yapılmadı"
- Akıllı öneriler: "Kadıköy'de kiralık arayan 5 müşteriniz var, 3 uygun portföyünüz var"

---

## TÜRKÇE DOĞAL DİL İŞLEME

- Eksik karakter pattern'ları: "emlakçı kayıt" → "emlakçı kaydı" olarak anlaşılır
- Türkçe karakter toleransı: "musteri" = "müşteri", "portfoy" = "portföy"
- AI devreye girmeden önce keyword/pattern matching denenir (maliyet tasarrufu)
- Anlaşılamazsa AI'ya yönlendirilir

---

## MODÜLLER VE ÖZELLİKLER

### A. Kayıt & Giriş
- [ ] WhatsApp'tan kayıt olabilme (sohbet üzerinden tüm süreç)
- [ ] Uygulama üzerinden kayıt
- [ ] Giriş (email + şifre)
- [ ] WhatsApp'tan ilk mesaj → kayıtsızsa kayıt akışı başlat

### B. Müşteri Yönetimi (CRM)
- [ ] Yeni müşteri oluştur (WhatsApp + uygulama)
- [ ] Müşteri listesi görüntüleme
- [ ] Müşteri bilgilerini düzenleme
- [ ] Müşteri silme / gizleme
- [ ] Müşteri arama (isim, telefon, talep)
- [ ] Müşteri talepleri listesi
- [ ] Taleplere not ekleme
- [ ] Hatırlatma ekleme (müşteri bazlı)
- [ ] Otomatik SMS gönderme
- [ ] Otomatik e-mail gönderme
- [ ] Planlı SMS/email zamanlama
- [ ] Kendine hatırlatma kurma
- [ ] Müşteri gruplama (gruplar oluştur, yönet)
- [ ] Grup bazlı toplu işlemler
- [ ] Müşteri kartı mail/WhatsApp ile gönderme
- [ ] Müşteri bazlı para hareketi kaydı
- [ ] Para hareketi sorgulama

### C. Portföy (Emlak) Yönetimi
- [ ] Yeni emlak girişi (kolay form + WhatsApp)
- [ ] Emlak düzenleme
- [ ] Emlak silme
- [ ] Emlak gruplama
- [ ] Alarm/bildirim kurma (portföy bazlı)
- [ ] Emlak bilgisi mail ile gönderme
- [ ] Emlak fotoğraf yönetimi
- [ ] Emlak detay sayfası

### D. Eşleştirme & Analiz
- [ ] Portföy-talep otomatik eşleştirme
- [ ] Puanlama sistemi (uygunluk skoru)
- [ ] Planlama yapabilme
- [ ] Rapor sunma (eşleşme raporu)
- [ ] AI destekli karşılaştırma

### E. Muhasebe
- [ ] Gelir/gider kaydı
- [ ] Bütçe hazırlama
- [ ] KDE (Kar-Değer-Etki) gelir hesapları
- [ ] Raporlar (aylık, yıllık, dönemsel)
- [ ] Cari hesap tutma
- [ ] Cari hesap ekstresi mail/WhatsApp gönderme

### F. Planlama
- [ ] Günlük/haftalık/aylık planlama
- [ ] Takvim görünümü
- [ ] Hatırlatıcılar
- [ ] Görev yönetimi

### G. Notlar
- [ ] Serbest not oluşturma
- [ ] Müşteri/emlak ile ilişkilendirme
- [ ] Not arama
- [ ] Sesli not → metin çevirisi (ileri aşama)

### H. Belgeler & Formlar
- [ ] Yer gösterme belgesi (PDF)
- [ ] Kira kontratı oluşturma
- [ ] Diğer evraklar (şablonlar)
- [ ] Alıcı onay linki + TC kimlik doğrulama

### I. Hesaplamalar & Raporlar
- [ ] Kira vergisi hesaplama
- [ ] Değer artış kazanç vergisi hesaplama
- [ ] Kira getirisi hesaplama (ROI)
- [ ] Emlak piyasa raporları
- [ ] Genel emlak sektörü analizleri

### J. Yönlendirme Belgeleri
- [ ] Alıcı yönlendirme belgesi
- [ ] Satıcı yönlendirme belgesi
- [ ] Dijital onay süreci

### K. Emlakçı Tanıtım Sayfası
- [ ] Her emlakçıya özel web tanıtım sayfası (emlakisim.com/emlakci/xxx)
- [ ] Alıcı/satıcıya gösterilecek profil, portföy, iletişim bilgileri
- [ ] Paylaşılabilir portföy linki (tek emlak veya liste)
- [ ] Özelleştirilebilir tasarım (logo, renk, açıklama)

### L. Fatura & Satın Alma
- [ ] Fatura oluşturma (satış, kiralama, hizmet)
- [ ] Fatura takibi (ödendi/bekliyor/gecikmiş)
- [ ] Satın alma kaydı
- [ ] Fatura PDF oluşturma ve gönderme (mail/WhatsApp)

### M. Ofis Yönetimi & Muhasebe
- [ ] Ofis gider takibi (kira, faturalar, personel)
- [ ] Personel yönetimi
- [ ] Ofis bütçesi ve raporları
- [ ] Genel muhasebe defteri
- [ ] Vergi raporları

### N. Sosyal Medya Paylaşım
- [ ] Facebook için portföy paylaşım mesajı hazırlama
- [ ] WhatsApp için portföy bildirim mesajı hazırlama
- [ ] Instagram için portföy paylaşım içeriği hazırlama
- [ ] Şablonlar ve otomatik metin oluşturma (AI destekli)
- [ ] Toplu paylaşım planlama

### O. Akıllı Çağrı Yönetimi
- [ ] Gelen çağrıları dijitalleştirme (müşteri görüşme kaydı)
- [ ] Meşgulken kaçırılan önemli çağrı bildirimi
- [ ] Çağrı sonrası otomatik not oluşturma (AI destekli)
- [ ] Müşteri arama geçmişi ve takibi

### P. Otomatik Lead Yönetimi
- [ ] Lead'lere anında otomatik yanıt (ilk saat kuralı)
- [ ] FSBO (satıcı tarafından satılık) listelerini otomatik tarama
- [ ] Mesai dışı WhatsApp sorularına AI otomatik yanıt
- [ ] Lead sıcaklık takibi ve otomatik hatırlatma
- [ ] Lead kaynağı analizi (WhatsApp, web, telefon)

### Q. Emlak Danışmanlığı Modülü
- [ ] Müşteri sorularına AI destekli emlak danışmanlığı cevapları
- [ ] Emlak mevzuatı bilgi bankası (kira hukuku, tapu işlemleri, vergi)
- [ ] Bölge bazlı piyasa analizi ve fiyat tavsiyesi
- [ ] Yatırım danışmanlığı (getiri hesaplama, karşılaştırma)
- [ ] Sık sorulan sorular ve hazır cevap şablonları

---

## ALICI / SATICI PORTALI

- WhatsApp üzerinden cep no ile hesap açılır
- Emlakçının paylaştığı belgeleri görüntüleme
- Emlakçının tanıtım sayfasını görüntüleme
- Paylaşılan portföy linklerini inceleme
- Yer gösterme onayı (TC kimlik ile)
- Kendi taleplerini iletebilme
- İleri aşama: WhatsApp davet ile kayıt

---

## WhatsApp vs UYGULAMA

| Özellik | WhatsApp | Uygulama |
|---------|----------|----------|
| Müşteri CRUD | ✅ | ✅ |
| Portföy CRUD | ✅ | ✅ |
| Belge oluşturma | ✅ | ✅ |
| Eşleştirme | ✅ | ✅ |
| Muhasebe | ✅ | ✅ |
| Hatırlatma alma | ❌ (24 saat kuralı) | ✅ |
| Push bildirim | ❌ | ✅ |
| Planlı gönderim | ❌ | ✅ |
| Takvim | ❌ | ✅ |

> WhatsApp 24 saat kuralı: müşteri son mesaj attıktan 24 saat sonra sadece template mesaj gönderilebilir. Bu sebeple hatırlatma/bildirimler uygulama tarafında olmalı.

---

## KREDİ SİSTEMİ

```
Kullanıcı mesaj gönderir
  → AI modeli seçilir (Gemini/GPT/Claude)
  → Token sayısı hesaplanır (input + output)
  → Dolar maliyeti hesaplanır (model fiyatlandırması)
  → Kar marjı eklenir (örn: %40)
  → Kredi birimine dönüştürülür
  → Kullanıcı kredi hesabından düşülür
  → Kredi yetersizse uyarı verilir
```

### Fiyat Tablosu (tahmini)
| Model | Input (1M token) | Output (1M token) |
|-------|-------------------|---------------------|
| Gemini 1.5 Flash | $0.075 | $0.30 |
| GPT-4o mini | $0.15 | $0.60 |
| Claude Haiku | $0.25 | $1.25 |

---

## AŞAMALAR

### Faz 1 — Temel Altyapı (MEVCUT)
- [x] Backend (Flask + PostgreSQL + Railway)
- [x] Frontend (React + Vercel + emlakisim.com)
- [x] WhatsApp webhook kurulumu
- [x] Meta uygulama yayınlama
- [x] Çok modelli AI desteği
- [x] Temel sayfalar (giriş, kayıt, panel, müşteriler, portföy, profil)
- [ ] WhatsApp numara taşıma — Meta Policy 1.4 ihlali çözülmeli (icon güncellendi, form gönderildi, Meta incelemesi bekleniyor 2026-04-29). Onay gelince: numara WAOtomasyon WABA → Emlakisim WABA taşınacak (2FA kapatıldı)
- [ ] AI API anahtarları eklenmesi (GEMINI, OPENAI, ANTHROPIC)

### Faz 2 — Ana Sayfa & AI Sohbet
- [ ] OnMuhasebeci tarzı layout (sol menü + orta sohbet + sağ işlem menüsü)
- [ ] Uygulama içi AI sohbet (WebSocket veya polling)
- [ ] Sohbet geçmişi kaydetme
- [ ] İşlem menüsü (hızlı erişim)
- [ ] Mobil responsive layout
- [ ] Türkçe NLP pattern matching

### Faz 3 — Müşteri CRM
- [ ] Gelişmiş müşteri yönetimi (gruplama, arama, filtreleme)
- [ ] Hatırlatma sistemi
- [ ] Otomatik SMS/email
- [ ] Planlı gönderimler
- [ ] Müşteri kartı paylaşım

### Faz 4 — Portföy Gelişmiş
- [ ] Fotoğraf yükleme
- [ ] Emlak gruplama & alarm
- [ ] Emlak detay sayfası
- [ ] Portföy-talep eşleştirme & puanlama

### Faz 5 — Muhasebe & Finans
- [ ] Gelir/gider takibi
- [ ] Cari hesaplar
- [ ] Bütçe & raporlar
- [ ] Kredi sistemi entegrasyonu

### Faz 6 — Belgeler & Formlar
- [ ] Yer gösterme belgesi PDF
- [ ] Kira kontratı
- [ ] Yönlendirme belgeleri
- [ ] Alıcı/satıcı dijital onay

### Faz 7 — Hesaplamalar
- [ ] Kira vergisi hesaplama
- [ ] Değer artış kazanç vergisi
- [ ] Kira getirisi (ROI)
- [ ] Piyasa raporları

### Faz 8 — Alıcı/Satıcı Portalı
- [ ] WhatsApp üzerinden hesap açma
- [ ] Belge görüntüleme
- [ ] Onay süreci
- [ ] WhatsApp davet sistemi

---

## MEVCUT DURUM

### Tamamlanan
- GitHub repo: alisamat/emlakisim
- Railway backend: backend-production-9ffc.up.railway.app (Online)
- Vercel frontend: emlakisim.com (Aktif)
- Meta uygulaması: Emlakisim (Published)
- Webhook: kuruldu + messages subscribed
- Çok modelli AI: Gemini Flash + GPT-4o mini + Claude Haiku
- Gizlilik politikası sayfası

### Bekleyen
- WhatsApp numara taşıma: SMS doğrulama (telefon yanına gelince)
- AI anahtarları: GEMINI_API_KEY, OPENAI_API_KEY, ANTHROPIC_API_KEY Railway'e eklenmeli
- worthy-tenderness Railway projesi: silinebilir (duplikat, crashed)

### Bilinen Sorunlar
- Numara hala WAOtomasyon WABA'sına bağlı → yeni WABA'ya taşınacak
- WhatsApp gerçek mesaj henüz test edilemedi (numara taşıma bekliyor)

---

## REFERANS

- Tasarım referansı: OnMuhasebeci AI (3 panelli layout)
- Dosya: `/Users/mmacac/pc/emlakisim için ötnek ana sayfa.png`
- Domain: emlakisim.com (aktif, Vercel'e yönlendirildi)
- Backend URL: https://backend-production-9ffc.up.railway.app
