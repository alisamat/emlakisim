import React, { useState, useEffect } from 'react';
import api from '../api';

export default function KarZarar() {
  const [kayitlar, setKayitlar] = useState([]);
  const [donem, setDonem] = useState('ay'); // ay, yil, tum

  useEffect(() => {
    api.get('/api/panel/muhasebe/gelir-gider').then(r => setKayitlar(r.data.kayitlar || [])).catch(() => {});
  }, []);

  const simdi = new Date();
  const filtrele = k => {
    const t = new Date(k.tarih);
    if (donem === 'ay') return t.getMonth() === simdi.getMonth() && t.getFullYear() === simdi.getFullYear();
    if (donem === 'yil') return t.getFullYear() === simdi.getFullYear();
    return true;
  };

  const filtrelenmis = kayitlar.filter(filtrele);
  const gelir = filtrelenmis.filter(k => k.tip === 'gelir').reduce((t, k) => t + k.tutar, 0);
  const gider = filtrelenmis.filter(k => k.tip === 'gider').reduce((t, k) => t + k.tutar, 0);
  const kar = gelir - gider;

  // Kategori bazlı analiz
  const gelirKat = {}; const giderKat = {};
  filtrelenmis.forEach(k => {
    const hedef = k.tip === 'gelir' ? gelirKat : giderKat;
    hedef[k.kategori || 'Diğer'] = (hedef[k.kategori || 'Diğer'] || 0) + k.tutar;
  });

  const f = v => Number(v).toLocaleString('tr-TR');

  return (
    <>
      <h1 style={{ fontSize: 20, fontWeight: 800, color: '#0f172a', marginBottom: 16 }}>📊 Kâr / Zarar</h1>

      <div style={{ display: 'flex', gap: 8, marginBottom: 16 }}>
        {[['ay', 'Bu Ay'], ['yil', 'Bu Yıl'], ['tum', 'Tümü']].map(([v, l]) => (
          <button key={v} onClick={() => setDonem(v)} style={{
            padding: '6px 14px', borderRadius: 20, fontSize: 13, fontWeight: 600, cursor: 'pointer',
            background: donem === v ? '#16a34a' : '#fff', color: donem === v ? '#fff' : '#374151',
            border: `1px solid ${donem === v ? '#16a34a' : '#e2e8f0'}`,
          }}>{l}</button>
        ))}
      </div>

      {/* Özet kartları */}
      <div className="grid-3" style={{ marginBottom: 20 }}>
        <div style={{ background: '#f0fdf4', borderRadius: 12, padding: 16, textAlign: 'center' }}>
          <div style={{ fontSize: 12, color: '#16a34a', fontWeight: 600 }}>Gelir</div>
          <div style={{ fontSize: 22, fontWeight: 800, color: '#16a34a' }}>{f(gelir)} TL</div>
        </div>
        <div style={{ background: '#fef2f2', borderRadius: 12, padding: 16, textAlign: 'center' }}>
          <div style={{ fontSize: 12, color: '#dc2626', fontWeight: 600 }}>Gider</div>
          <div style={{ fontSize: 22, fontWeight: 800, color: '#dc2626' }}>{f(gider)} TL</div>
        </div>
        <div style={{ background: kar >= 0 ? '#f0fdf4' : '#fef2f2', borderRadius: 12, padding: 16, textAlign: 'center', border: `2px solid ${kar >= 0 ? '#16a34a' : '#dc2626'}` }}>
          <div style={{ fontSize: 12, color: '#374151', fontWeight: 600 }}>{kar >= 0 ? 'KÂR' : 'ZARAR'}</div>
          <div style={{ fontSize: 22, fontWeight: 800, color: kar >= 0 ? '#16a34a' : '#dc2626' }}>{f(Math.abs(kar))} TL</div>
        </div>
      </div>

      {/* Kâr marjı */}
      {gelir > 0 && (
        <div style={{ background: '#fff', borderRadius: 12, padding: 16, marginBottom: 16, border: '1px solid #e2e8f0' }}>
          <div style={{ fontSize: 13, color: '#64748b', marginBottom: 4 }}>Kâr Marjı</div>
          <div style={{ height: 8, background: '#e2e8f0', borderRadius: 4, overflow: 'hidden' }}>
            <div style={{ height: '100%', background: kar >= 0 ? '#16a34a' : '#dc2626', width: `${Math.min(Math.abs(kar / gelir) * 100, 100)}%`, borderRadius: 4 }} />
          </div>
          <div style={{ fontSize: 14, fontWeight: 700, color: kar >= 0 ? '#16a34a' : '#dc2626', marginTop: 4 }}>%{(kar / gelir * 100).toFixed(1)}</div>
        </div>
      )}

      {/* Kategori bazlı */}
      <div className="grid-2" style={{ gap: 16 }}>
        <div style={{ background: '#fff', borderRadius: 12, padding: 16, border: '1px solid #e2e8f0' }}>
          <div style={{ fontWeight: 700, fontSize: 14, color: '#16a34a', marginBottom: 12 }}>📈 Gelir Dağılımı</div>
          {Object.entries(gelirKat).sort((a, b) => b[1] - a[1]).map(([kat, tutar]) => (
            <div key={kat} style={{ display: 'flex', justifyContent: 'space-between', padding: '4px 0', borderBottom: '1px solid #f1f5f9', fontSize: 13 }}>
              <span>{kat}</span><span style={{ fontWeight: 600, color: '#16a34a' }}>{f(tutar)} TL</span>
            </div>
          ))}
          {Object.keys(gelirKat).length === 0 && <div style={{ fontSize: 12, color: '#94a3b8' }}>Gelir kaydı yok</div>}
        </div>
        <div style={{ background: '#fff', borderRadius: 12, padding: 16, border: '1px solid #e2e8f0' }}>
          <div style={{ fontWeight: 700, fontSize: 14, color: '#dc2626', marginBottom: 12 }}>📉 Gider Dağılımı</div>
          {Object.entries(giderKat).sort((a, b) => b[1] - a[1]).map(([kat, tutar]) => (
            <div key={kat} style={{ display: 'flex', justifyContent: 'space-between', padding: '4px 0', borderBottom: '1px solid #f1f5f9', fontSize: 13 }}>
              <span>{kat}</span><span style={{ fontWeight: 600, color: '#dc2626' }}>{f(tutar)} TL</span>
            </div>
          ))}
          {Object.keys(giderKat).length === 0 && <div style={{ fontSize: 12, color: '#94a3b8' }}>Gider kaydı yok</div>}
        </div>
      </div>
    </>
  );
}
