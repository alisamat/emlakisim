import React, { useState } from 'react';

const ADMIN_EMAIL = 'alisamat@gmail.com';
const ADMIN_TEL   = '05323769426';

const MENU = (isAdmin) => [
  {
    baslik: '🏆 Performans',
    items: [
      { ikon: '🏆', ad: 'Performans & Analiz', tab: 'performans', aciklama: 'KPI, gelir, sektör haberleri' },
      { ikon: '📰', ad: 'Sektör Haberleri', mesaj: 'Emlak sektöründeki son gelişmeler neler?', aciklama: 'AI ile güncel piyasa bilgisi' },
    ],
  },
  {
    baslik: '⚡ Hızlı İşlem',
    acik: true,
    items: [
      { ikon: '👥', ad: 'Müşteri Ekle', tab: 'musteriler', aciklama: 'Yeni müşteri kaydı oluştur' },
      { ikon: '🏢', ad: 'Mülk Ekle', tab: 'mulkler', aciklama: 'Portföye yeni mülk ekle' },
      { ikon: '📋', ad: 'Yer Gösterme', tab: 'kayitlar', aciklama: 'Yer gösterme kayıtları' },
      { ikon: '📌', ad: 'Görev Ekle', tab: 'planlama', aciklama: 'Görev oluştur, randevu planla' },
    ],
  },
  {
    baslik: '👥 Müşteriler',
    items: [
      { ikon: '📋', ad: 'Müşteri Listesi', tab: 'musteriler', aciklama: 'Tüm müşterileri görüntüle, ara, filtrele' },
      { ikon: '📝', ad: 'Talepler & Geri Bildirim', tab: 'talepler', aciklama: 'Müşteri talepleri ve görüşme geri bildirimleri' },
      { ikon: '🔗', ad: 'Eşleştirme', tab: 'eslestirme', aciklama: 'Müşteri-mülk otomatik eşleştirme ve puanlama' },
    ],
  },
  {
    baslik: '🏢 Portföy',
    items: [
      { ikon: '🏠', ad: 'Mülk Listesi', tab: 'mulkler', aciklama: 'Portföyü yönet, ara, filtrele' },
      { ikon: '📸', ad: 'İlan OCR & Karşılaştır', tab: 'ilan_ocr', aciklama: 'İlan fotoğrafı çek → bilgi çıkar → karşılaştır → portföye ekle' },
      { ikon: '🖊', ad: 'Resim İşaretleme', tab: 'isaretleme', aciklama: 'Fotoğraf üzerine daire/dikdörtgen çizerek işaretle, kaydet, paylaş' },
      { ikon: '📸', ad: 'AI Görsel Analiz', tab: 'gorsel_analiz', aciklama: 'Fotoğraftan konut değerleme, durum puanı, renovasyon önerisi' },
      { ikon: '🪑', ad: 'Sanal Ev Düzenleme', tab: 'sanal_staging', aciklama: 'AI ile boş odayı mobilyalı göster, stil seç, maliyet hesapla' },
      { ikon: '📄', ad: 'Belge Oluştur', tab: 'belgeler', aciklama: 'Yer gösterme, kontrat, yönlendirme PDF' },
    ],
  },
  {
    baslik: '📅 Planlama & Takip',
    items: [
      { ikon: '📝', ad: 'Notlar', tab: 'notlar', aciklama: 'Notlar, hatırlatmalar, gösterim notları, sesli notlar' },
      { ikon: '📋', ad: 'Görevler', tab: 'planlama', aciklama: 'Görev yönetimi, öncelik, durum takibi' },
      { ikon: '📅', ad: 'Takvim', tab: 'takvim', aciklama: 'Aylık takvim görünümü' },
      { ikon: '📋', ad: 'Süreç Takip', tab: 'surec', aciklama: 'Tapu devri, kredi süreci adım takibi' },
      { ikon: '🕐', ad: 'İşlem Geçmişi', tab: 'islem_gecmisi', aciklama: 'Yapılan tüm işlemler, geri alma' },
    ],
  },
  {
    baslik: '📒 Emlakçılar & Gruplar',
    items: [
      { ikon: '📒', ad: 'Emlakçı Dizini', tab: 'emlakcilar', aciklama: 'Dış emlakçı rehberi, iletişim bilgileri' },
      { ikon: '👥', ad: 'Gruplar', tab: 'gruplar', aciklama: 'İşbirliği grupları, portföy/talep paylaşımı, eşleştirme' },
    ],
  },
  {
    baslik: '💰 Muhasebe & Finans',
    items: [
      { ikon: '📊', ad: 'Gelir/Gider', tab: 'muhasebe', aciklama: 'Gelir ve gider kayıtları, fiş OCR' },
      { ikon: '📈', ad: 'Kâr/Zarar', tab: 'karzarar', aciklama: 'Dönemsel kâr/zarar, kategori dağılımı' },
      { ikon: '📒', ad: 'Cari Hesaplar', tab: 'cariler', aciklama: 'Müşteri borç/alacak takibi' },
      { ikon: '🧾', ad: 'Faturalar', tab: 'faturalar', aciklama: 'Fatura oluştur, takip et, PDF indir' },
      { ikon: '💼', ad: 'Bütçe Planlama', tab: 'butce', aciklama: 'Kategori bazlı bütçe ve gerçekleşen karşılaştırma' },
      { ikon: '📊', ad: 'Muhasebe Raporu', tab: 'muhrapor', aciklama: 'Aylık tablo + AI analiz raporu' },
    ],
  },
  {
    baslik: '🗺 Piyasa & Tahmin',
    items: [
      { ikon: '🗺', ad: 'Isı Haritası & Tahmin', tab: 'isi_haritasi', aciklama: 'İlçe bazlı fiyat, talep, getiri analizi + satıcı tahmin' },
      { ikon: '📍', ad: 'Mahalle Analizi', mesaj: 'Kadıköy Moda mahallesi nasıl?', aciklama: 'AI ile mahalle puanlama, yatırım önerisi' },
    ],
  },
  {
    baslik: '🧮 Hesaplamalar',
    items: [
      { ikon: '🧮', ad: 'Hesaplama Araçları', tab: 'hesaplamalar', aciklama: 'Kira vergisi, ROI, değer artış, aidat analizi' },
    ],
  },
  {
    baslik: '✉️ İletişim & Lead',
    items: [
      { ikon: '📞', ad: 'İletişim Geçmişi', tab: 'iletisim', aciklama: 'Müşteri bazlı tüm iletişim kayıtları' },
      { ikon: '🎯', ad: 'Lead Yönetimi', tab: 'leadler', aciklama: 'Potansiyel müşteri takibi ve durum' },
      { ikon: '📞', ad: 'Çağrı Kayıtları', tab: 'cagrilar', aciklama: 'Gelen/giden/kaçırılmış çağrılar' },
    ],
  },
  {
    baslik: '🌐 Tanıtım & Paylaşım',
    items: [
      { ikon: '🌐', ad: 'Tanıtım & Sosyal Medya', tab: 'tanitim', aciklama: 'Portföy linki, sosyal medya içerik üretimi' },
    ],
  },
  {
    baslik: '📦 Toplu İşlem & Veri',
    items: [
      { ikon: '📦', ad: 'Toplu İşlemler', tab: 'toplu', aciklama: 'Excel/fotoğraf/rehberden toplu veri aktarımı' },
      { ikon: '💾', ad: 'Yedekleme', tab: 'yedekleme', aciklama: 'Veri export, email ile gönder, yedek takip' },
    ],
  },
  {
    baslik: '🏢 Ofis & Ekip',
    items: [
      { ikon: '👔', ad: 'Danışman Yönetimi', tab: 'ekip', aciklama: 'Ofis danışmanları ve müşteri ataması' },
      { ikon: '📦', ad: 'Ofis Envanter', tab: 'envanter', aciklama: 'Ofis malzeme takibi, stok uyarısı' },
    ],
  },
  {
    baslik: '⚙️ Yönetim',
    items: [
      { ikon: '⚙️', ad: 'Ayarlar', tab: 'ayarlar', aciklama: 'Profil, logo, tema, şifre değiştirme' },
      ...(isAdmin ? [
        { ikon: '🛡', ad: 'Platform Admin', tab: 'admin_dash', aciklama: 'Kullanıcılar, gelir, fiyatlandırma, kredi yönetimi' },
        { ikon: '🛠', ad: 'AI & Pattern', tab: 'admin', aciklama: 'AI eğitim, pattern yönetimi, maliyet raporu' },
      ] : []),
      { ikon: '👤', ad: 'Profil', tab: 'profil', aciklama: 'Kişisel bilgiler' },
    ],
  },
];

export default function SagPanel({ onOpenTab, onMesajGonder, acik, user }) {
  const isAdmin = user?.email === ADMIN_EMAIL || user?.telefon === ADMIN_TEL;
  const menuItems = MENU(isAdmin);
  const [arama, setArama] = useState('');
  const [acikKategoriler, setAcikKategoriler] = useState(() => {
    const init = {};
    menuItems.forEach((k, i) => { init[i] = !!k.acik; });
    return init;
  });

  const toggle = i => setAcikKategoriler(p => ({ ...p, [i]: !p[i] }));

  const filtrelenmis = arama.trim()
    ? menuItems.map(k => ({
        ...k,
        items: k.items.filter(it =>
          it.ad.toLowerCase().includes(arama.toLowerCase()) ||
          (it.aciklama || '').toLowerCase().includes(arama.toLowerCase())
        ),
      })).filter(k => k.items.length > 0)
    : menuItems;

  return (
    <div className={`sag-panel${acik ? ' acik' : ''}`}>
      <div className="sag-panel-baslik">📌 İşlem Menüsü</div>
      <input
        className="sag-panel-ara"
        placeholder="İşlem ara..."
        value={arama}
        onChange={e => setArama(e.target.value)}
      />
      {filtrelenmis.map((k, i) => (
        <div key={i}>
          <div className="sag-panel-kategori" onClick={() => toggle(i)}>
            <span>{k.baslik}</span>
            <span className={`sag-panel-chevron${acikKategoriler[i] ? ' acik' : ''}`}>▶</span>
          </div>
          {acikKategoriler[i] && k.items.map((item, j) => (
            <div
              key={j}
              className="sag-panel-item"
              onClick={() => {
                if (item.tab) onOpenTab(item.tab);
                else if (item.mesaj) onMesajGonder(item.mesaj);
              }}
              title={item.aciklama || ''}
            >
              <span>{item.ikon}</span>
              <div style={{ flex: 1 }}>
                <div>{item.ad}</div>
                {item.aciklama && <div style={{ fontSize: 10, color: '#94a3b8', marginTop: 1 }}>{item.aciklama}</div>}
              </div>
            </div>
          ))}
        </div>
      ))}
    </div>
  );
}
