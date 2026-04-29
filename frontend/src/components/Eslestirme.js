import React, { useState, useEffect, useCallback } from 'react';
import api from '../api';

export default function Eslestirme() {
  const [musteriler, setMusteriler] = useState([]);
  const [mulkler, setMulkler] = useState([]);
  const [seciliMusteri, setSeciliMusteri] = useState(null);
  const [eslesimler, setEslesimler] = useState([]);
  const [yukleniyor, setYuk] = useState(false);

  const yukle = useCallback(async () => {
    setYuk(true);
    try {
      const [m, p] = await Promise.all([
        api.get('/api/panel/musteriler'),
        api.get('/api/panel/mulkler'),
      ]);
      setMusteriler(m.data.musteriler || []);
      setMulkler(p.data.mulkler || []);
    } catch {} finally { setYuk(false); }
  }, []);

  useEffect(() => { yukle(); }, [yukle]);

  const eslesDir = (musteri) => {
    setSeciliMusteri(musteri);
    // Basit eşleştirme: işlem türü + bütçe aralığı
    const sonuclar = mulkler.map(mulk => {
      let puan = 0;
      let nedenler = [];

      // İşlem türü eşleşmesi
      if (mulk.islem_turu === musteri.islem_turu) {
        puan += 30;
        nedenler.push('İşlem türü uyumlu');
      }

      // Bütçe eşleşmesi
      if (mulk.fiyat && musteri.butce_min && musteri.butce_max) {
        if (mulk.fiyat >= musteri.butce_min && mulk.fiyat <= musteri.butce_max) {
          puan += 40;
          nedenler.push('Bütçeye uygun');
        } else if (mulk.fiyat >= musteri.butce_min * 0.8 && mulk.fiyat <= musteri.butce_max * 1.2) {
          puan += 20;
          nedenler.push('Bütçeye yakın (±%20)');
        }
      } else if (mulk.islem_turu === musteri.islem_turu) {
        puan += 10; // bütçe bilgisi yok ama tür uyumlu
      }

      // Tercih notları anahtar kelime eşleşmesi
      if (musteri.tercih_notlar && mulk.baslik) {
        const tercihler = musteri.tercih_notlar.toLowerCase().split(/[\s,]+/);
        const baslik = (mulk.baslik + ' ' + (mulk.adres || '') + ' ' + (mulk.sehir || '') + ' ' + (mulk.ilce || '')).toLowerCase();
        const eslesen = tercihler.filter(t => t.length > 2 && baslik.includes(t));
        if (eslesen.length > 0) {
          puan += eslesen.length * 10;
          nedenler.push(`Tercih eşleşmesi: ${eslesen.join(', ')}`);
        }
      }

      return { mulk, puan, nedenler };
    })
    .filter(e => e.puan > 0)
    .sort((a, b) => b.puan - a.puan)
    .slice(0, 10);

    setEslesimler(sonuclar);
  };

  const puanRenk = p => p >= 60 ? '#16a34a' : p >= 30 ? '#f59e0b' : '#94a3b8';

  return (
    <>
      <h1 style={{ fontSize: 20, fontWeight: 800, color: '#0f172a', marginBottom: 16 }}>🔗 Eşleştirme</h1>

      {!seciliMusteri ? (
        <>
          <p style={{ fontSize: 13, color: '#64748b', marginBottom: 16 }}>Müşteri seçin, uygun mülkleri otomatik bulalım</p>
          {yukleniyor ? <div style={{ textAlign: 'center', color: '#94a3b8', padding: 40 }}>Yükleniyor…</div> :
            musteriler.length === 0 ? <div style={{ textAlign: 'center', color: '#94a3b8', padding: 40, background: '#fff', borderRadius: 12 }}>Henüz müşteri yok</div> :
            musteriler.map(m => (
              <div key={m.id} onClick={() => eslesDir(m)} style={{
                background: '#fff', borderRadius: 12, padding: '12px 16px', marginBottom: 8,
                border: '1px solid #e2e8f0', cursor: 'pointer',
              }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <div>
                    <span style={{ fontWeight: 700, fontSize: 14 }}>{m.ad_soyad}</span>
                    <span style={{ marginLeft: 8, fontSize: 12, color: '#64748b' }}>
                      {m.islem_turu === 'kira' ? '🔵 Kiralık' : '🟡 Satılık'}
                      {m.butce_max ? ` · ${Number(m.butce_max).toLocaleString('tr-TR')} TL` : ''}
                    </span>
                  </div>
                  <span style={{ fontSize: 13, color: '#16a34a', fontWeight: 600 }}>Eşleştir →</span>
                </div>
              </div>
            ))
          }
        </>
      ) : (
        <>
          <button onClick={() => { setSeciliMusteri(null); setEslesimler([]); }} className="btn-gri" style={{ marginBottom: 16, fontSize: 13 }}>
            ← Müşteri Listesine Dön
          </button>

          <div style={{ background: '#eff6ff', borderRadius: 12, padding: 14, marginBottom: 16, border: '1px solid #bfdbfe' }}>
            <div style={{ fontWeight: 700, fontSize: 14, color: '#1d4ed8' }}>👤 {seciliMusteri.ad_soyad}</div>
            <div style={{ fontSize: 12, color: '#1e40af', marginTop: 4 }}>
              {seciliMusteri.islem_turu === 'kira' ? 'Kiralık' : 'Satılık'}
              {seciliMusteri.butce_min || seciliMusteri.butce_max ? ` · ${seciliMusteri.butce_min ? Number(seciliMusteri.butce_min).toLocaleString('tr-TR') : '?'} - ${seciliMusteri.butce_max ? Number(seciliMusteri.butce_max).toLocaleString('tr-TR') : '?'} TL` : ''}
              {seciliMusteri.tercih_notlar ? ` · ${seciliMusteri.tercih_notlar}` : ''}
            </div>
          </div>

          <div style={{ fontWeight: 700, fontSize: 14, color: '#1e293b', marginBottom: 12 }}>
            🏢 Uygun Mülkler ({eslesimler.length})
          </div>

          {eslesimler.length === 0 ? (
            <div style={{ textAlign: 'center', color: '#94a3b8', padding: 40, background: '#fff', borderRadius: 12 }}>
              Uygun mülk bulunamadı
            </div>
          ) : (
            eslesimler.map((e, i) => (
              <div key={e.mulk.id} style={{
                background: '#fff', borderRadius: 12, padding: '14px 16px', marginBottom: 8,
                border: '1px solid #e2e8f0', borderLeft: `3px solid ${puanRenk(e.puan)}`,
              }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                  <div style={{ flex: 1 }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
                      <span style={{ fontWeight: 700, fontSize: 14 }}>{e.mulk.baslik || e.mulk.adres || '—'}</span>
                      <span style={{
                        background: puanRenk(e.puan) + '20', color: puanRenk(e.puan),
                        borderRadius: 6, padding: '2px 8px', fontSize: 12, fontWeight: 700,
                      }}>%{e.puan}</span>
                    </div>
                    {e.mulk.adres && <div style={{ fontSize: 12, color: '#64748b' }}>📍 {e.mulk.adres}</div>}
                    {e.mulk.fiyat && <div style={{ fontSize: 13, fontWeight: 600, color: '#374151', marginTop: 2 }}>💰 {Number(e.mulk.fiyat).toLocaleString('tr-TR')} TL</div>}
                    <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', marginTop: 6 }}>
                      {e.nedenler.map((n, j) => (
                        <span key={j} style={{ fontSize: 11, background: '#f0fdf4', border: '1px solid #bbf7d0', borderRadius: 6, padding: '2px 8px', color: '#16a34a' }}>{n}</span>
                      ))}
                    </div>
                  </div>
                </div>
              </div>
            ))
          )}
        </>
      )}
    </>
  );
}
