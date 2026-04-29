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
- [x] Backend (Flask + PostgreSQL + Railway)
- [x] Frontend (React + Vercel + emlakisim.com)
- [x] WhatsApp webhook kurulumu + Meta uygulama yayınlama
- [x] Çok modelli AI desteği (Gemini Flash + GPT-4o mini + Claude Haiku)
- [x] Temel sayfalar (giriş, kayıt, müşteriler, portföy, profil)
- [x] AI API anahtarları (GEMINI, OPENAI, ANTHROPIC) Railway'e eklendi
- [x] JWT token süresi 30 güne uzatıldı
- [x] Gizlilik politikası sayfası
- [ ] WhatsApp numara taşıma — Meta Policy 1.4 ihlali çözülmeli (icon güncellendi, form gönderildi, Meta incelemesi bekleniyor 2026-04-29). Onay gelince: numara WAOtomasyon WABA → Emlakisim WABA taşınacak (2FA kapatıldı)

### Faz 2 — AI Sohbet Arayüzü & Akıllı Motor ✅
- [x] 3 panelli layout (sol menü + orta sohbet + sağ işlem menüsü)
- [x] Uygulama içi AI sohbet (REST, sohbet geçmişi DB'de)
- [x] İşlem menüsü (kategorili, aranabilir)
- [x] Mobil responsive (hamburger + bottom sheet)
- [x] Pattern matching (sıfır maliyetli komut tanıma)
- [x] Türkçe normalleştirme (karakter toleransı)
- [x] Function calling (AI doğrudan DB işlemi)
- [x] Bekleyen işlem sistemi (adımlı komut tamamlama)
- [x] Proaktif öneriler ("Excel'den toplu portföy ekleyebilirsiniz")

### Faz 3 — Kredi Sistemi & İşlem Log
- [ ] Kredi merkezi: her işlem log'lanır (işlem_tipi, maliyet_usd, kredi_tutarı, zaman)
- [ ] AI token maliyet hesaplama → kredi dönüşümü (kar marjı ile)
- [ ] CRUD işlemleri → 1 kredi, belge → 2 kredi, toplu → N kredi
- [ ] Kredi yetersizse uyarı + satın alma yönlendirmesi
- [ ] Admin panel: tek noktadan maliyet takibi ve raporlama
- [ ] Kredi satın alma sayfası (ödeme entegrasyonu)

### Faz 4 — Gelişmiş Müşteri CRM
- [ ] Müşteri düzenleme, silme, gizleme
- [ ] Gelişmiş arama ve filtreleme (isim, telefon, talep, bütçe)
- [ ] Müşteri gruplama ve grup bazlı toplu işlemler
- [ ] Hatırlatma sistemi (müşteri bazlı)
- [ ] Müşteri bazlı para hareketi kaydı ve sorgulama
- [ ] Müşteri kartı mail/WhatsApp ile gönderme
- [ ] Telefon rehberinden toplu müşteri ekleme
- [ ] Excel'den toplu müşteri import

### Faz 5 — Gelişmiş Portföy
- [ ] Fotoğraf yükleme ve yönetimi
- [ ] Emlak gruplama ve alarm kurma
- [ ] Emlak detay sayfası (tam bilgi + fotoğraf galeri)
- [ ] Portföy-talep otomatik eşleştirme ve puanlama
- [ ] OCR ile portföy ekleme (sahibinden ekran görüntüsü → ilan çıkarma)
- [ ] Excel'den toplu portföy import
- [ ] Paylaşılabilir portföy linki (tek emlak veya liste)
- [ ] Sosyal medya paylaşım mesajı hazırlama (Facebook, Instagram, WhatsApp)

### Faz 6 — Belgeler & Formlar & PDF
- [ ] Yer gösterme belgesi PDF oluşturma
- [ ] Kira kontratı oluşturma (şablonlu)
- [ ] Yönlendirme belgeleri (alıcı/satıcı)
- [ ] Alıcı/satıcı dijital onay süreci (TC kimlik ile)
- [ ] PDF okuma ve içerik çıkarma
- [ ] Fatura PDF oluşturma ve gönderme

### Faz 7 — İletişim & Bildirimler
- [ ] Otomatik SMS gönderme
- [ ] Otomatik email gönderme
- [ ] Planlı SMS/email zamanlama
- [ ] Hatırlatıcılar (kendine, müşteriye)
- [ ] Mesai dışı WhatsApp AI otomatik yanıt
- [ ] Lead'lere anında otomatik yanıt (ilk saat kuralı)

### Faz 8 — Muhasebe & Finans
- [ ] Gelir/gider kaydı
- [ ] Cari hesap tutma ve ekstre gönderme
- [ ] Bütçe hazırlama
- [ ] Fatura oluşturma ve takibi (ödendi/bekliyor/gecikmiş)
- [ ] Ofis gider takibi (kira, faturalar, personel)
- [ ] Raporlar (aylık, yıllık, dönemsel)

### Faz 9 — Hesaplamalar & Raporlar
- [ ] Kira vergisi hesaplama
- [ ] Değer artış kazanç vergisi hesaplama
- [ ] Kira getirisi hesaplama (ROI)
- [ ] Piyasa analizi ve fiyat tavsiyesi
- [ ] Müşteri-mülk eşleştirme raporu
- [ ] Günlük/haftalık/aylık/yıllık performans özeti

### Faz 10 — Planlama & Takvim
- [ ] Günlük/haftalık/aylık planlama
- [ ] Takvim görünümü
- [ ] Görev yönetimi
- [ ] Akıllı diyalog akışı (günlük özet, haftalık rapor)
- [ ] Proaktif hatırlatmalar ("Ahmet bey'e 3 gündür dönüş yapılmadı")

### Faz 11 — Diyalog Eğitim Sistemi
- [ ] Başarılı diyalog-işlem çiftlerini saklama (eğitim verisi)
- [ ] Pattern havuzu otomatik genişletme
- [ ] Admin: "anlaşılamayan mesajlar" paneli → manuel pattern ekleme
- [ ] Zaman içinde AI'ya daha az ihtiyaç → maliyet düşer

### Faz 12 — Yedekleme & Güvenlik
- [ ] Google Drive entegrasyonu (tek tıkla yedekleme)
- [ ] Mail ile veri gönderme (Excel formatında)
- [ ] Haftalık otomatik yedekleme hatırlatması
- [ ] İşlem log'u (kim, ne zaman, ne yaptı)
- [ ] Tüm veriyi export etme (JSON/Excel)
- [ ] Kullanım koşulları ("3 ay inaktif → veri silinebilir" uyarısı)

### Faz 13 — Toplu İşlemler & OCR
- [ ] Fotoğraftan OCR (kartvizit, belge, ilan)
- [ ] Sahibinden.com ekran görüntüsünden ilan listesi çıkarma
- [ ] Excel'den toplu import (müşteri + portföy)
- [ ] Telefon rehberinden toplu müşteri ekleme
- [ ] Toplu SMS/email gönderim

### Faz 14 — Emlakçı Tanıtım & Danışmanlık
- [ ] Her emlakçıya özel web tanıtım sayfası (emlakisim.com/e/xxx)
- [ ] Özelleştirilebilir tasarım (logo, renk, açıklama)
- [ ] Emlak danışmanlığı modülü (AI destekli cevaplar)
- [ ] Emlak mevzuatı bilgi bankası
- [ ] Sık sorulan sorular ve hazır cevap şablonları

### Faz 15 — Lead & Çağrı Yönetimi
- [ ] Lead sıcaklık takibi ve otomatik hatırlatma
- [ ] Lead kaynağı analizi (WhatsApp, web, telefon)
- [ ] Gelen çağrıları dijitalleştirme (görüşme kaydı)
- [ ] Kaçırılan çağrı bildirimi
- [ ] Çağrı sonrası otomatik not oluşturma

### Faz 16 — Alıcı/Satıcı Portalı
- [ ] WhatsApp üzerinden hesap açma
- [ ] Belge görüntüleme ve onay süreci
- [ ] Emlakçının tanıtım sayfasını görüntüleme
- [ ] Paylaşılan portföy linklerini inceleme
- [ ] WhatsApp davet sistemi

### Faz 17 — İleri Seviye (Gelecek)
- [ ] Sesli arama: AI telefon açma (emlakçının yardımcısı gibi müşteriye konuşma)
- [ ] Sesli not → metin çevirisi
- [ ] Web'de arama yapma (piyasa araştırması, fiyat karşılaştırma)
- [ ] FSBO listelerini otomatik tarama
- [ ] Ofis yönetimi ve personel modülü

---

## MEVCUT DURUM (2026-04-29)

### Tamamlanan
- GitHub repo: alisamat/emlakisim
- Railway backend: backend-production-9ffc.up.railway.app (Online)
- Vercel frontend: emlakisim.com (Aktif, GitHub'a bağlandı)
- Meta uygulaması: Emlakisim (Published)
- Webhook: kuruldu + messages subscribed
- Çok modelli AI: Gemini Flash + GPT-4o mini + Claude Haiku
- AI API anahtarları: GEMINI_API_KEY, OPENAI_API_KEY, ANTHROPIC_API_KEY eklendi
- 3 panelli AI sohbet arayüzü (sol/orta/sağ)
- Pattern matching + function calling + bekleyen işlem motoru
- Türkçe normalleştirme
- JWT 30 gün
- Gizlilik politikası sayfası
- worthy-tenderness duplikat projesi silindi

### Bekleyen (Bizden Bağımsız)
- WhatsApp numara taşıma: Meta Policy 1.4 inceleme sonucu bekleniyor (2026-04-29 gönderildi)
  - Onay gelince: WAOtomasyon WABA → Emlakisim WABA (2FA kapatıldı, hazır)

### Sıradaki İş
- Faz 3: Kredi sistemi & işlem log implementasyonu

---

## REFERANS

- Tasarım referansı: OnMuhasebeci Esnaf (`/Users/mmacac/pc/Github/onmuhasebeciesnaf`)
- Örnek ana sayfa: `/Users/mmacac/pc/emlakisim için ötnek ana sayfa.png`
- Domain: emlakisim.com (aktif, Vercel'e bağlı)
- Backend URL: https://backend-production-9ffc.up.railway.app
- GitHub: https://github.com/alisamat/emlakisim
