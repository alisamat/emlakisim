import React, { useState } from 'react';

const MENU = [
  {
    baslik: '⚡ Hızlı İşlem',
    acik: true,
    items: [
      { ikon: '👥', ad: 'Müşteri Ekle', tab: 'musteriler' },
      { ikon: '🏢', ad: 'Mülk Ekle', tab: 'mulkler' },
      { ikon: '📋', ad: 'Yer Gösterme', tab: 'kayitlar' },
    ],
  },
  {
    baslik: '👥 Müşteriler',
    items: [
      { ikon: '📋', ad: 'Müşteri Listesi', tab: 'musteriler' },
    ],
  },
  {
    baslik: '🏢 Portföy',
    items: [
      { ikon: '🏠', ad: 'Mülk Listesi', tab: 'mulkler' },
    ],
  },
  {
    baslik: '📄 Belgeler',
    items: [
      { ikon: '📋', ad: 'Yer Gösterme Kayıtları', tab: 'kayitlar' },
      { ikon: '📄', ad: 'Belge Oluştur', tab: 'belgeler' },
    ],
  },
  {
    baslik: '✉️ İletişim',
    items: [
      { ikon: '📧', ad: 'Email Gönder', mesaj: 'Email göndermek istiyorum' },
      { ikon: '📤', ad: 'Portföy Email', mesaj: 'Portföy listesini email ile gönder' },
    ],
  },
  {
    baslik: '📊 Hesaplamalar',
    items: [
      { ikon: '💰', ad: 'Kira Getirisi Hesapla', mesaj: 'Kira getirisi hesapla' },
      { ikon: '🧾', ad: 'Kira Vergisi Hesapla', mesaj: 'Kira vergisi hesapla' },
    ],
  },
  {
    baslik: '⚙️ Profil',
    items: [
      { ikon: '👤', ad: 'Profil Ayarları', tab: 'profil' },
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
        items: k.items.filter(it => it.ad.toLowerCase().includes(arama.toLowerCase())),
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
            >
              <span>{item.ikon}</span>
              <span>{item.ad}</span>
            </div>
          ))}
        </div>
      ))}
    </div>
  );
}
