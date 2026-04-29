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

### 2. Kredi Sistemi (Tek Noktadan Maliyet Yönetimi)
Her işlemin bir kredi maliyeti var. AI maliyeti de kredi üzerinden hesaplanır:
```
┌─────────────────────────────────────────────────────────────┐
│                    KREDİ MERKEZİ                            │
│                                                             │
│ Veri kaynakları:                                            │
│  ├── AI token maliyeti (Gemini/GPT/Claude) → kredi          │
│  ├── CRUD işlemleri (müşteri ekle, mülk sil) → 1 kredi      │
│  ├── Belge üretimi (PDF, kontrat) → 2 kredi                │
│  ├── Toplu işlem (Excel import, OCR) → N kredi              │
│  ├── SMS/email gönderim → 1 kredi                           │
│  ├── Sesli arama (AI telefon) → 5 kredi/dk                  │
│  ├── Rapor üretimi → 2 kredi                                │
│  └── Web arama/tarama → 2 kredi                             │
│                                                             │
│ Her işlem log'lanır:                                        │
│  → işlem_tipi, maliyet_usd, kredi_tutarı, zaman            │
│                                                             │
│ Admin panel: tek noktadan tüm maliyet takibi                │
└─────────────────────────────────────────────────────────────┘
```
- Pattern matching ile tanınan CRUD işlemleri → 1 kredi (AI yok, $0 maliyet)
- AI sohbet → AI dolar maliyeti × kar marjı → kredi
- Kredi yetersizse uyarı, satın alma yönlendirmesi

### 3. Diyalog Eğitim Sistemi (Büyüyen Zeka)
Onbinlerce diyalog oluşturmak, bunları işleme dönüştürmek ve sistem büyüdükçe öğrenmesi:
```
Kullanıcı diyalog → Başarılı işlem → Pattern DB'ye eklenir
                  → Başarısız işlem → Manuel inceleme → Düzeltme → Pattern güncellenir
```
- Her başarılı diyalog-işlem çifti saklanır (eğitim verisi)
- Zaman içinde pattern matching havuzu genişler → AI'ya daha az ihtiyaç → maliyet düşer
- Model eğitimi gibi: eklenerek büyüyen sistem
- Yeni komut kalıpları otomatik öğrenilir
- Admin: "anlaşılamayan mesajlar" paneli → manuel pattern ekleme

### 4. Güvenlik & Yedekleme (Sorumluluk Paylaşımı)
**Prensip:** Biz mümkün olduğu kadar veri tutma sözü vermeyiz. Kullanıcı kendi verisinin yedeğinden sorumludur.
- Google Drive entegrasyonu: tek tıkla yedekleme
- Mail ile veri gönderme: Excel formatında tüm verileri mail'e gönder
- Haftalık otomatik yedekleme hatırlatması
- Kritik işlemlerde (silme, toplu değişiklik) onay isteme
- İşlem log'u tutma (kim, ne zaman, ne yaptı)
- Kullanım koşullarında: "3 ay inaktif hesaplarda veri silinebilir" uyarısı
- Kullanıcı istediği zaman tüm verisini export edebilir

### 5. Kuantum Hızlı Modüler Mimari
Parametreler birbirleriyle ilişkili, gerektiğinde bir araya gelebilmeli:
```
Müşteri ←→ Mülk ←→ Yer Gösterme ←→ Belge
   ↕           ↕           ↕            ↕
 Talep ←→ Eşleştirme ←→ Planlama ←→ Muhasebe
   ↕           ↕           ↕            ↕
  Not  ←→  Rapor   ←→ Hatırlatma ←→  Fatura
```
- Her modül bağımsız çalışır AMA birbirini besler
- "Müşteri ekle" → otomatik olarak talep analizi → eşleşen mülkler → öneri
- "Mülk ekle" → otomatik fiyat karşılaştırma → potansiyel müşteriler → bildirim
- Tek bir komut zincirleme işlem tetikleyebilir

### 6. Tam Asistan Yetenekleri (Dil Modeli Gibi)
Asistan her şeyi yapabilmeli — gerçek bir dijital çalışan gibi:

**Okuma & Anlama:**
- PDF okuma ve içerik çıkarma
- Excel'den veri import
- Fotoğraftan OCR (sahibinden ilanları, kartvizitler, belgeler)
- Metin analizi ve özetleme

**Üretme & Yazma:**
- PDF belge oluşturma (kontrat, yer gösterme, fatura)
- Excel/tablo üretme (raporlar, listeler)
- Metin üretme (ilan metni, SMS, email)
- Web'de arama yapma (piyasa araştırması, fiyat karşılaştırma)

**İletişim:**
- Email gönderme (müşteriye, alıcıya)
- SMS gönderme
- WhatsApp mesajı gönderme
- **Sesli arama: AI telefon açma** (emlakçının yardımcısı gibi müşteriye telefon açıp konuşma — ileri seviye)

**Hesaplama & Analiz:**
- Kira vergisi, değer artış kazancı hesaplama
- Kira getirisi (ROI) hesaplama
- Piyasa analizi ve fiyat tavsiyesi
- Müşteri-mülk eşleştirme puanlama

### 7. Toplu İşlem Yetenekleri
- Fotoğraftan OCR ile portföy ekleme (sahibinden.com ekran görüntüsü → ilan listesi)
- Excel'den toplu müşteri/portföy import
- Telefon rehberinden toplu müşteri ekleme
- Toplu SMS/email gönderim
- AI proaktif olarak "Excel'den toplu portföy ekleyebilirsiniz" gibi öneriler sunar

### 8. Akıllı Diyalog & Akış Sistemi
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

### Faz 1 — Temel Altyapı ✅
- [x] Backend, Frontend, WhatsApp webhook, Meta app, AI anahtarları, JWT 30 gün
- [ ] WhatsApp numara taşıma — Meta Policy 1.4 incelemesi bekleniyor (2026-04-29)

### Faz 2 — AI Sohbet Arayüzü & Akıllı Motor ✅
- [x] 3 panel layout, AI sohbet, pattern matching, function calling, Türkçe NLP

### Faz 3 — Kredi Sistemi ✅
- [x] IslemLog modeli, kredi düşme, AI maliyet hesaplama, yetersiz bakiye kontrolü
- [ ] Kredi satın alma sayfası (ödeme entegrasyonu)
- [ ] Admin panel: maliyet raporlama

### Faz 4 — Gelişmiş CRM ✅
- [x] Müşteri düzenleme, silme, arama, filtre, dinamik detay (JSON)
- [ ] Müşteri gruplama ve grup bazlı toplu işlemler
- [ ] Müşteri talep listesi frontend sayfası
- [ ] Müşteri kartı mail/WhatsApp ile gönderme

### Faz 5 — Gelişmiş Portföy ✅
- [x] Düzenleme, silme, arama, filtre, tip bazlı dinamik detay (JSON)
- [ ] Fotoğraf yükleme (Supabase/S3 storage gerek)
- [ ] Emlak gruplama ve alarm
- [ ] Portföy-talep eşleştirme frontend sayfası

### Faz 6 — Belgeler & PDF ✅
- [x] Yer gösterme tutanağı PDF, kira kontratı PDF
- [ ] Yönlendirme belgeleri (alıcı/satıcı) PDF şablonu
- [ ] PDF okuma ve içerik çıkarma
- [ ] Fatura PDF oluşturma

### Faz 7 — İletişim ✅
- [x] Email gönderme (SMTP), müşteri/portföy email şablonları
- [ ] SMS gönderme (Netgsm/Twilio entegrasyonu)
- [ ] Planlı SMS/email zamanlama (scheduler/cron gerek)
- [ ] Mesai dışı WhatsApp AI otomatik yanıt

### Faz 8 — Muhasebe ✅
- [x] Gelir/gider, cari hesap, OCR fiş okuma (Gemini+OpenAI)
- [ ] Bütçe hazırlama frontend
- [ ] Fatura oluşturma ve takibi (L modülü)
- [ ] Ofis yönetimi/personel (M modülü)
- [ ] Muhasebe raporları (aylık/yıllık)

### Faz 9 — Hesaplamalar ✅
- [x] Kira vergisi, değer artış, ROI, aidat analizi + frontend

### Faz 10 — Planlama ✅
- [x] Görev CRUD, 4 tip, 4 öncelik, bugün/yaklaşan özet
- [ ] Takvim görünümü (calendar component)
- [ ] Günlük/haftalık özet diyalog (scheduler gerek)
- [ ] Proaktif hatırlatmalar (cron job)

### Faz 11 — Diyalog Eğitim ✅
- [x] DiyalogKayit, OgrenilenPattern, cache, istatistik, admin API

### Faz 12 — Yedekleme ✅
- [x] Excel export, email ile gönderim, veri özeti
- [ ] Google Drive entegrasyonu (OAuth)
- [ ] Haftalık otomatik yedekleme hatırlatması (scheduler)

### Faz 13 — Toplu İşlemler ✅
- [x] Excel müşteri/portföy import, OCR portföy, rehber import
- [ ] Toplu SMS/email gönderim (SMS API gerek)

### Faz 14 — Tanıtım & Danışmanlık ✅
- [x] Public profil API, danışmanlık bilgi bankası (8 konu)
- [ ] Tanıtım frontend sayfası (public)
- [ ] Özelleştirilebilir tasarım (logo, renk)

### Faz 15 — Lead & Çağrı ✅
- [x] Lead CRUD + istatistik, çağrı kaydı API
- [ ] Lead frontend sayfası
- [ ] Çağrı frontend sayfası
- [ ] Otomatik hatırlatma (scheduler)

### Faz 16 — Alıcı/Satıcı Portalı ✅
- [x] Belge onay (TC kimlik), müşteri talep gönderme → Lead
- [ ] WhatsApp üzerinden hesap açma
- [ ] WhatsApp davet sistemi

### Faz 17 — İleri Seviye ✅
- [x] Web arama (Gemini), metin analiz, sosyal medya içerik üretme (AI)
- [ ] Sesli arama: AI telefon (Twilio)
- [ ] Sesli not → metin çevirisi
- [ ] FSBO otomatik tarama

---

## KALAN EKSİKLER

### Tamamlanan (bu turda)
- [x] Lead frontend sayfası
- [x] Eşleştirme frontend sayfası
- [x] Takvim görünümü
- [x] Tanıtım & sosyal medya sayfası
- [x] Müşteri gruplama (form + filtre)
- [x] Sohbet arama + silme (sol panel)
- [x] "Unutma" komutu + hatırlatma listele

### Yapılacak — Güvenlik Denetimi
- [ ] Tüm endpoint'lerde JWT auth kontrolü
- [ ] SQL injection koruması (SQLAlchemy parametrik sorgular)
- [ ] XSS koruması (React varsayılan escape)
- [ ] CORS ayarları kontrolü
- [ ] Rate limiting (brute force koruması)
- [ ] Hassas veri loglanmaması (TC, şifre)
- [ ] Input validasyonu (max uzunluk, tip kontrolü)

### Yapılacak — Sohbet Geliştirmeleri
- [ ] Dosya ekleme butonu (sohbet inputunda)
- [ ] Fotoğraf çekme butonu (kamera)
- [ ] Sesli mesaj / konuşarak yazma (Web Speech API)
- [ ] Sohbet input pozisyonu yukarı taşıma

### Yapılacak — Bildirim Modülü
- [ ] Uygulama içi bildirim sistemi (bell icon + badge)
- [ ] Bildirim listesi (okundu/okunmadı)
- [ ] Bildirim türleri: yeni lead, hatırlatma, yedek, görev, kredi düşük
- [ ] Push notification (Service Worker — ileri seviye)

### Yapılacak — Otomatik Yedekleme & Hatırlatma
- [ ] Otomatik yedek alma modülü (zamanlayıcı ile)
- [ ] Yedekleme takip sistemi (son yedek tarihi, durum)
- [ ] Hatırlatma modülü: yedek alma, görev, müşteri dönüş, ödeme

### Yapılacak — Emlak Asistanı Tam Yetkinlik Kontrolü
Gerçek emlak asistanının yaptığı her şeyi yapabilmeli:
- [x] İdari destek: e-posta yönetme, randevu/takvim, toplantı planlama
- [x] İlan yönetimi: portföy CRUD, detaylı bilgi, arama/filtre
- [x] Belge takibi: sözleşme hazırlama (PDF), evrak süreçleri
- [x] Müşteri iletişimi: CRM, lead yönetimi, sorgu yönetme
- [x] Pazarlama: sosyal medya içerik üretme (AI)
- [x] Veri girişi ve CRM: müşteri/portföy veri işleme, eşleştirme
- [ ] İlan fotoğraflarını düzenleme (fotoğraf storage gerek)
- [ ] Sanal tur yönetimi (ileri seviye)
- [ ] Basılı pazarlama materyali (broşür PDF — ileri seviye)

### Dış Servis Entegrasyonları (API key/hesap gerekli)
- [ ] SMS API (Netgsm veya Twilio)
- [ ] Fotoğraf storage (Supabase veya S3)
- [ ] Google Drive OAuth (yedekleme)
- [ ] Scheduler/Cron (hatırlatma, planlı gönderim)
- [ ] Twilio (sesli arama — ileri seviye)
- [ ] Kredi satın alma (ödeme entegrasyonu)

### WhatsApp (numara taşıma bekleniyor)
- [ ] Numara taşıma (Meta Policy 1.4 onayı bekleniyor)
- [ ] WhatsApp'tan kayıt akışı
- [ ] Mesai dışı otomatik yanıt
- [ ] WhatsApp davet sistemi

---

## MEVCUT DURUM (2026-04-30)

### Altyapı
- GitHub: alisamat/emlakisim
- Backend: backend-production-9ffc.up.railway.app (Online, 72 endpoint)
- Frontend: emlakisim.com (Aktif, GitHub auto-deploy)
- Meta: Emlakisim (Published, webhook subscribed)
- AI: Gemini Flash + GPT-4o mini + Claude Haiku
- 17 faz backend API tamamlandı
- Syntax hatası: 0
- Build hatası: 0

### Bekleyen
- WhatsApp numara taşıma: Meta Policy 1.4 (2026-04-29 gönderildi)

---

## REFERANS

- Tasarım: OnMuhasebeci Esnaf (`/Users/mmacac/pc/Github/onmuhasebeciesnaf`)
- Domain: emlakisim.com
- Backend: https://backend-production-9ffc.up.railway.app
- GitHub: https://github.com/alisamat/emlakisim
