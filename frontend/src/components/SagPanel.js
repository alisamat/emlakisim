import React, { useState } from 'react';

const MENU = [
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
      { ikon: '📌', ad: 'Görev Ekle', mesaj: 'Yeni görev ekle', aciklama: 'Sohbetten hızlı görev oluştur' },
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
    baslik: '🧮 Hesaplamalar',
    items: [
      { ikon: '🧮', ad: 'Hesaplama Araçları', tab: 'hesaplamalar', aciklama: 'Kira vergisi, ROI, değer artış, aidat analizi' },
    ],
  },
  {
    baslik: '📅 Planlama & Takip',
    items: [
      { ikon: '📋', ad: 'Görevler', tab: 'planlama', aciklama: 'Görev yönetimi, öncelik, durum takibi' },
      { ikon: '📅', ad: 'Takvim', tab: 'takvim', aciklama: 'Aylık takvim görünümü' },
      { ikon: '📋', ad: 'Süreç Takip', tab: 'surec', aciklama: 'Tapu devri, kredi süreci adım takibi' },
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
    baslik: '📒 Emlakçılar & Gruplar',
    items: [
      { ikon: '📒', ad: 'Emlakçı Dizini', tab: 'emlakcilar', aciklama: 'Dış emlakçı rehberi, iletişim bilgileri' },
      { ikon: '👥', ad: 'Gruplar', tab: 'gruplar', aciklama: 'İşbirliği grupları, portföy/talep paylaşımı, eşleştirme' },
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
      { ikon: '🛡', ad: 'Platform Admin', tab: 'admin_dash', aciklama: 'Kullanıcılar, gelir, fiyatlandırma, kredi yönetimi' },
      { ikon: '🛠', ad: 'AI & Pattern', tab: 'admin', aciklama: 'AI eğitim, pattern yönetimi, maliyet raporu' },
      { ikon: '👤', ad: 'Profil', tab: 'profil', aciklama: 'Kişisel bilgiler' },
    ],
  },
];

export default function SagPanel({ onOpenTab, onMesajGonder, acik }) {
  const [arama, setArama] = useState('');
  const [acikKategoriler, setAcikKategoriler] = useState(() => {
    const init = {};
    MENU.forEach((k, i) => { init[i] = !!k.acik; });
    return init;
  });

  const toggle = i => setAcikKategoriler(p => ({ ...p, [i]: !p[i] }));

  const filtrelenmis = arama.trim()
    ? MENU.map(k => ({
        ...k,
        items: k.items.filter(it =>
          it.ad.toLowerCase().includes(arama.toLowerCase()) ||
          (it.aciklama || '').toLowerCase().includes(arama.toLowerCase())
        ),
      })).filter(k => k.items.length > 0)
    : MENU;

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
