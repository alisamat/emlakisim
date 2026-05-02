import React, { useState } from 'react';
import api from '../api';

const STILLER = [
  { id: 'modern', ad: 'Modern', ikon: '🪑', aciklama: 'Minimalist, açık renkler, temiz çizgiler' },
  { id: 'klasik', ad: 'Klasik', ikon: '🛋', aciklama: 'Sıcak renkler, geleneksel motifler' },
  { id: 'minimalist', ad: 'Minimalist', ikon: '⬜', aciklama: 'Ultra sade, az mobilya, geniş alan' },
  { id: 'luks', ad: 'Lüks', ikon: '✨', aciklama: 'Mermer, altın detay, tasarım mobilya' },
  { id: 'genc', ad: 'Genç', ikon: '🎨', aciklama: 'Renkli, fonksiyonel, kompakt' },
];

export default function SanalStaging() {
  const [resim, setResim] = useState(null);
  const [resimSrc, setResimSrc] = useState(null);
  const [stil, setStil] = useState('modern');
  const [sonuc, setSonuc] = useState(null);
  const [yuk, setYuk] = useState(false);

  const resimSec = (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = (ev) => {
      setResimSrc(ev.target.result);
      setResim(ev.target.result.split(',')[1]);
      setSonuc(null);
    };
    reader.readAsDataURL(file);
  };

  const duzenlemeYap = async () => {
    if (!resim) return;
    setYuk(true); setSonuc(null);
    try {
      const r = await api.post('/api/panel/sanal-staging', { image: resim, stil });
      setSonuc(r.data.staging);
    } catch (e) { alert(e.response?.data?.message || 'Hata'); }
    finally { setYuk(false); }
  };

  return (
    <>
      <h1 style={{ fontSize: 20, fontWeight: 800, color: 'var(--text-primary)', marginBottom: 16 }}>🪑 AI Sanal Ev Düzenleme</h1>

      {/* Fotoğraf yükle */}
      <div style={{ background: 'var(--bg-card)', borderRadius: 12, padding: 20, marginBottom: 16, border: '1px solid var(--border)' }}>
        {!resimSrc ? (
          <label style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 40, border: '2px dashed var(--border)', borderRadius: 12, cursor: 'pointer', fontSize: 14 }}>
            📸 Boş oda fotoğrafı yükle
            <input type="file" accept="image/*" onChange={resimSec} style={{ display: 'none' }} />
          </label>
        ) : (
          <div>
            <img src={resimSrc} alt="Oda" style={{ width: '100%', maxHeight: 300, objectFit: 'contain', borderRadius: 8 }} />
            <label style={{ display: 'block', fontSize: 12, color: '#64748b', marginTop: 8, cursor: 'pointer' }}>
              📸 Farklı fotoğraf seç
              <input type="file" accept="image/*" onChange={resimSec} style={{ display: 'none' }} />
            </label>
          </div>
        )}
      </div>

      {/* Stil seçimi */}
      {resimSrc && (
        <div style={{ background: 'var(--bg-card)', borderRadius: 12, padding: 20, marginBottom: 16, border: '1px solid var(--border)' }}>
          <div style={{ fontWeight: 700, fontSize: 14, marginBottom: 12 }}>🎨 Dekorasyon Stili</div>
          <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
            {STILLER.map(s => (
              <button key={s.id} onClick={() => setStil(s.id)} style={{
                padding: '10px 16px', borderRadius: 8, cursor: 'pointer', fontSize: 13, border: `2px solid ${stil === s.id ? '#16a34a' : 'var(--border)'}`,
                background: stil === s.id ? '#f0fdf4' : 'var(--bg-card)', color: 'var(--text-primary)',
              }}>
                {s.ikon} {s.ad}
                <div style={{ fontSize: 10, color: '#94a3b8', marginTop: 2 }}>{s.aciklama}</div>
              </button>
            ))}
          </div>
          <button className="btn-yesil" onClick={duzenlemeYap} disabled={yuk} style={{ marginTop: 16, width: '100%' }}>
            {yuk ? '🔄 AI düzenliyor...' : '🪑 Sanal Düzenleme Yap'}
          </button>
        </div>
      )}

      {/* Sonuç */}
      {sonuc && !sonuc.hata && (
        <div style={{ background: 'var(--bg-card)', borderRadius: 12, padding: 20, border: '1px solid var(--border)' }}>
          <div style={{ fontWeight: 700, fontSize: 15, marginBottom: 12 }}>🪑 Düzenleme Planı — {sonuc.oda_tipi}</div>

          <div style={{ fontSize: 13, color: 'var(--text-secondary)', marginBottom: 12 }}>{sonuc.mevcut_durum}</div>

          {/* Renk paleti */}
          {sonuc.renk_paleti && (
            <div style={{ display: 'flex', gap: 8, marginBottom: 12, alignItems: 'center' }}>
              <span style={{ fontSize: 12, fontWeight: 700 }}>🎨 Palet:</span>
              {sonuc.renk_paleti.map((r, i) => (
                <span key={i} style={{ padding: '4px 12px', borderRadius: 6, background: '#f1f5f9', fontSize: 12 }}>{r}</span>
              ))}
            </div>
          )}

          {/* Mobilyalar */}
          {sonuc.onerilen_mobilyalar?.length > 0 && (
            <div style={{ marginBottom: 16 }}>
              <div style={{ fontSize: 13, fontWeight: 700, marginBottom: 8 }}>🪑 Önerilen Mobilyalar</div>
              {sonuc.onerilen_mobilyalar.map((m, i) => (
                <div key={i} style={{ display: 'flex', justifyContent: 'space-between', padding: '6px 0', borderBottom: '1px solid var(--border-light, #f1f5f9)', fontSize: 12 }}>
                  <div><strong>{m.ad}</strong> — {m.konum} <span style={{ color: '#94a3b8' }}>({m.renk})</span></div>
                  <span style={{ fontWeight: 600 }}>~{Number(m.tahmini_fiyat_tl || 0).toLocaleString('tr-TR')} TL</span>
                </div>
              ))}
            </div>
          )}

          {/* Dekorasyon */}
          {sonuc.dekorasyon_onerileri?.length > 0 && (
            <div style={{ marginBottom: 16 }}>
              <div style={{ fontSize: 13, fontWeight: 700, marginBottom: 8 }}>🖼 Dekorasyon Önerileri</div>
              {sonuc.dekorasyon_onerileri.map((d, i) => (
                <div key={i} style={{ fontSize: 12, padding: '4px 0' }}>• <strong>{d.ad}</strong>: {d.aciklama}</div>
              ))}
            </div>
          )}

          {/* Toplam maliyet */}
          <div style={{ padding: 12, background: '#f0fdf4', borderRadius: 8, marginBottom: 12 }}>
            <div style={{ fontSize: 14, fontWeight: 700 }}>💰 Toplam Tahmini: {Number(sonuc.toplam_tahmini_maliyet_tl || 0).toLocaleString('tr-TR')} TL</div>
            <div style={{ fontSize: 12, color: '#16a34a', marginTop: 4 }}>📈 Değer artışı: {sonuc.deger_artisi_tahmini}</div>
          </div>

          {/* Sonuç açıklama */}
          <div style={{ padding: 12, background: '#eff6ff', borderRadius: 8, fontSize: 13 }}>
            ✨ {sonuc.sonuc_aciklama}
          </div>
          <div style={{ fontSize: 11, color: '#94a3b8', marginTop: 8 }}>👤 Hedef kitle: {sonuc.hedef_kitle_uyumu}</div>
        </div>
      )}
    </>
  );
}
