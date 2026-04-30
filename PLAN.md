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
- [x] Uygulama üzerinden kayıt + giriş (email + şifre)
- [x] Şifre değiştirme
- [ ] WhatsApp'tan kayıt akışı (numara taşıma bekleniyor)

### B. Müşteri Yönetimi (CRM)
- [x] CRUD (ekle, düzenle, sil, listele)
- [x] Arama (isim, telefon, tercih) + sıcaklık filtresi
- [x] Müşteri gruplama + grup filtresi
- [x] Dinamik detay alanları (JSON, işlem türüne göre)
- [x] Müşteri kartı email ile gönderme
- [x] Müşteri'ye WhatsApp mesaj gönderme
- [x] Talepler & geri bildirim sayfası
- [x] İletişim geçmişi (telefon/whatsapp/email/yüz yüze)
- [x] Hatırlatma ekleme ("unutma" komutu)
- [x] Email gönderme (SMTP)
- [ ] SMS gönderme (Netgsm/Twilio API gerek)
- [x] Para hareketi: cari hesap takibi

### C. Portföy (Emlak) Yönetimi
- [x] CRUD (ekle, düzenle, sil, listele)
- [x] Arama + tip filtresi + işlem filtresi + grup filtresi
- [x] Dinamik detay (tip bazlı JSON — 22+ alan)
- [x] Emlak gruplama
- [x] Broşür PDF
- [x] İlan metni oluşturma (AI)
- [x] Link kopyalama (paylaşım)
- [x] Portföy email gönderme
- [x] Zincirleme: mülk ekle → uygun müşteri bildirimi
- [ ] Fotoğraf yükleme (storage gerek)

### D. Eşleştirme & Analiz
- [x] Portföy-talep otomatik eşleştirme + puanlama
- [x] Eşleştirme frontend sayfası
- [x] Zincirleme: müşteri ekle → uygun mülk bildirimi

### E. Muhasebe
- [x] Gelir/gider kaydı + kategori + silme
- [x] Kâr/Zarar sayfası (dönemsel, kategori dağılımı)
- [x] Cari hesap (borç/alacak takibi + hareket)
- [x] Bütçe planlama (kategori bazlı, gerçekleşen karşılaştırma)
- [x] Fatura CRUD + durum takibi + PDF
- [x] OCR fiş okuma (Gemini + OpenAI)
- [x] Banka Excel import (otomatik kategori tahmin)
- [x] Muhasebe raporu (aylık tablo + AI özet)

### F. Planlama
- [x] Görev CRUD (4 tip, 4 öncelik, checkbox)
- [x] Takvim görünümü (aylık grid)
- [x] Bugün/yaklaşan özet
- [x] Otomatik hatırlatma (APScheduler)

### G. Notlar & Hatırlatma
- [x] Not CRUD
- [x] "Unutma" komutu (sohbetten hatırlatma kaydet)
- [x] Hatırlatma listele

### H. Belgeler & Formlar
- [x] Yer gösterme belgesi PDF
- [x] Kira kontratı PDF
- [x] Yönlendirme belgeleri (alıcı + satıcı) PDF
- [x] Broşür PDF
- [x] Fatura PDF
- [x] PDF okuma ve analiz (pypdf + Gemini OCR)
- [x] Alıcı onay linki + TC kimlik doğrulama

### I. Hesaplamalar
- [x] Kira vergisi (dilimli)
- [x] Değer artış kazancı
- [x] Kira getirisi (ROI)
- [x] Aidat analizi
- [x] Hesaplamalar frontend sayfası

### J-K. Tanıtım & Paylaşım
- [x] Public emlakçı profil API
- [x] Tanıtım sayfası (link + profil + sosyal medya)
- [x] Paylaşılabilir portföy linki
- [x] Logo yükleme (Ayarlar)
- [x] Sosyal medya içerik üretme (Instagram/Facebook/WhatsApp — AI)
- [x] İlan metni oluşturma (AI)

### L. Lead & Çağrı
- [x] Lead CRUD + istatistik + durum değiştirme
- [x] Çağrı kayıtları (gelen/giden/kaçırılmış)
- [x] Lead soğuma uyarısı (3+ gün → bildirim, APScheduler)
- [x] Mesai dışı WhatsApp otomatik yanıt

### M. Ofis & Ekip
- [x] Envanter takibi (ofis malzeme, min miktar uyarı)
- [x] Danışman yönetimi (ekip)
- [x] Müşteri → danışman atama
- [x] Geri bildirim (yer gösterme sonrası)

### N. Danışmanlık
- [x] 14 konu bilgi bankası (tapu, kira, vergi, kredi, ekspertiz...)
- [x] Sektörel haber takibi (AI)
- [x] Piyasa analizi (şehir bazlı)

### O. Sistem
- [x] Kredi sistemi + işlem log
- [x] Diyalog eğitim (pattern öğrenme)
- [x] Hafıza motoru (bağlam, güncel durum, müşteri tanıma)
- [x] Bildirim sistemi (bell + badge + panel)
- [x] Yedekleme (Excel export + email + takip)
- [x] Toplu işlem (Excel/OCR/rehber import)
- [x] Dark mode
- [x] Ayarlar (profil + logo + tema + şifre)
- [x] Performans dashboard
- [x] Süreç takip (tapu/kredi adımları)
- [x] Evrak arşivi
- [x] Zamanlayıcı (5 otomatik görev)
- [x] İşlem zincirleme (proaktif bildirim)
- [x] Rate limiting (güvenlik)
- [x] 30+ asistan pattern komutu

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
- [x] Admin panel: maliyet raporlama (API + frontend)

### Faz 4 — Gelişmiş CRM ✅
- [x] Müşteri CRUD + gruplama + arama + filtre + dinamik detay
- [x] Talepler & geri bildirim sayfası + iletişim geçmişi
- [x] Müşteri kartı email + WhatsApp gönderme

### Faz 5 — Gelişmiş Portföy ✅
- [x] CRUD + gruplama + arama + filtre + dinamik detay (tip bazlı 22+ alan)
- [x] Broşür PDF + ilan metni (AI) + link paylaşım + eşleştirme
- [ ] Fotoğraf yükleme (Supabase/S3 storage gerek)

### Faz 6 — Belgeler & PDF ✅
- [x] Yer gösterme + kira kontratı + yönlendirme (alıcı/satıcı) + broşür + fatura PDF
- [x] PDF okuma ve analiz (pypdf + Gemini OCR)

### Faz 7 — İletişim ✅
- [x] Email gönderme + mesai dışı WhatsApp otomatik yanıt + WA mesaj gönderme
- [ ] SMS gönderme (Netgsm/Twilio API gerek)

### Faz 8 — Muhasebe ✅
- [x] Gelir/gider + cari + kâr/zarar + bütçe + fatura + OCR fiş + banka Excel + AI rapor

### Faz 9-10 — Hesaplamalar + Planlama ✅
- [x] Kira vergisi, değer artış, ROI, aidat + takvim + görev + zamanlayıcı (APScheduler)

### Faz 11-13 — Eğitim + Yedekleme + Toplu ✅
- [x] Diyalog eğitim + Excel export + yedek takip + toplu import (Excel/OCR/rehber/banka)

### Faz 14-15 — Tanıtım + Lead ✅
- [x] Tanıtım sayfası + 14 danışmanlık konusu + lead CRUD + çağrı + sektörel haber + piyasa

### Faz 16-17 — Portal + İleri ✅
- [x] Belge onay + müşteri talep + ilan metni + performans + ekip + envanter + bildirim + hafıza

---

## YAPILACAKLAR — Güncel

### Komut Zekası (10.000+ Diyalog Vizyonu)
- [x] 91 sabit pattern (sıfır maliyet)
- [x] Öğrenilen pattern DB (büyüyen havuz)
- [x] Function calling (AI doğrudan DB işlemi)
- [x] Danışmanlık bilgi bankası (14 konu)
- [x] Hafıza motoru (bağlam, müşteri tanıma, alışkanlık)
- [x] Komut öğrenme: "bunu yapabilir misin?" → yetenek listesi
- [x] 91 pattern = neredeyse her endpoint 3+ varyasyon
- [ ] AI pipeline: anlaşılamayan → otomatik pattern öneri (ileri seviye)

### İlan OCR & Karşılaştırma ✅
- [x] OCR (Gemini Vision) + portföye ekle + 20 ilan hafıza + karşılaştırma + telefon arama

### Depolama ✅
- [x] Kayıt takibi + doluluk uyarısı (%80/%95)

### Oturum ✅
- [x] JWT 30 gün + WhatsApp engelsiz

### Admin Panel ✅
- [x] Eğitim + fiyatlandırma + dashboard + kullanıcı yönetimi + frontend
- [x] Kullanıcı listesi + kredi ekleme API
- [ ] Admin frontend dashboard sayfası (ayrı panel)

### Maliyet Merkezi (Tüm Dış Servisler)
- [x] AI token maliyeti → kredi dönüşümü
- [x] Kredi fiyat tablosu admin API'den yönetilebilir
- [ ] SMS/WhatsApp/telefon maliyeti → kredi (dış servis entegre olunca)

### Sağ Panel İyileştirme ✅
- [x] 12 kategori anlamlı gruplama
- [x] Her butonda açıklama (tooltip)
- [x] İşlem arama açıklamalarda da arar

### Kredi Paneli ✅ (ödeme entegrasyonu hariç)
- [x] Kredi paneli popup (4 tab: genel bakış, satın al, fatura bilgi, faturalarım)
- [x] Paket kartları (Temel/Standart/Profesyonel/Kurumsal + USD+TRY+KDV)
- [x] Fatura bilgileri formu
- [x] Header'da kredi tıklanınca panel açılır
- [ ] Kuveyttürk ödeme entegrasyonu (dış servis)
- [x] Son kullanma tarihi sistemi (model + kredi yükleme uzatma)

### Tamamlanan
- [x] Reklam metni + sunum PDF + ilan metni
- [x] Public sayfalar (Hakkımızda, Fiyatlar, İletişim, KVKK)
- [x] Şifremi unuttum (email token)
- [x] Kayıt: emlakçı/müşteri seçimi
- [x] Sohbet: kopyala + paylaş butonları
- [x] WhatsApp doğrulama (numara taşıma sonrası)

---

## SADECE DIŞ SERVİS GEREKTIREN EKSİKLER

| Özellik | Gerekli Servis |
|---------|---------------|
| SMS gönderme | Netgsm veya Twilio API |
| Fotoğraf yükleme | Supabase veya S3 |
| Google Drive yedekleme | Google OAuth |
| Sesli AI telefon | Twilio Voice |
| Sesli not → metin | Web Speech (frontend var, backend yok) |
| Kredi satın alma | Ödeme entegrasyonu (iyzico/stripe) |
| WhatsApp numara taşıma | Meta Policy 1.4 onay |
| WhatsApp'tan kayıt | Numara taşıma sonrası |
| Sanal tur | 360° çekim servisi |

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
