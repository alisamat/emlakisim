import React, { useState, useEffect } from 'react';
import api from '../api';

const KATEGORILER = ['Komisyon', 'Kira Geliri', 'Danışmanlık', 'Ofis Kirası', 'Personel', 'Reklam', 'Ulaşım', 'Fatura', 'Vergi', 'Diğer'];

export default function Butce() {
  const [butce, setButce] = useState(() => {
    const kayitli = localStorage.getItem('emlakisim_butce');
    return kayitli ? JSON.parse(kayitli) : {};
  });
  const [gerceklesen, setGerceklesen] = useState({});
  const [mesaj, setMesaj] = useState('');

  useEffect(() => {
    api.get('/api/panel/muhasebe/gelir-gider').then(r => {
      const kayitlar = r.data.kayitlar || [];
      const kat = {};
      kayitlar.forEach(k => {
        const key = k.kategori || 'Diğer';
        kat[key] = (kat[key] || 0) + k.tutar;
      });
      setGerceklesen(kat);
    }).catch(() => {});
  }, []);

  const kaydet = () => {
    localStorage.setItem('emlakisim_butce', JSON.stringify(butce));
    setMesaj('Bütçe kaydedildi!');
    setTimeout(() => setMesaj(''), 2000);
  };

  const f = v => Number(v || 0).toLocaleString('tr-TR');
  const toplamButce = Object.values(butce).reduce((t, v) => t + (parseFloat(v) || 0), 0);
  const toplamGercek = Object.values(gerceklesen).reduce((t, v) => t + v, 0);

  return (
    <>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
        <h1 style={{ fontSize: 20, fontWeight: 800, color: 'var(--text-primary)' }}>💼 Bütçe Planlama</h1>
        <button className="btn-yesil" onClick={kaydet} style={{ fontSize: 13 }}>💾 Kaydet</button>
      </div>

      {mesaj && <div className="basarili" style={{ marginBottom: 12 }}>✅ {mesaj}</div>}

      {/* Özet */}
      <div className="grid-2" style={{ marginBottom: 16, gap: 8 }}>
        <div style={{ background: '#eff6ff', borderRadius: 12, padding: 14, textAlign: 'center' }}>
          <div style={{ fontSize: 12, color: '#1d4ed8', fontWeight: 600 }}>Planlanan Bütçe</div>
          <div style={{ fontSize: 20, fontWeight: 800, color: '#1d4ed8' }}>{f(toplamButce)} TL</div>
        </div>
        <div style={{ background: toplamGercek <= toplamButce ? '#f0fdf4' : '#fef2f2', borderRadius: 12, padding: 14, textAlign: 'center' }}>
          <div style={{ fontSize: 12, fontWeight: 600, color: toplamGercek <= toplamButce ? '#16a34a' : '#dc2626' }}>Gerçekleşen</div>
          <div style={{ fontSize: 20, fontWeight: 800, color: toplamGercek <= toplamButce ? '#16a34a' : '#dc2626' }}>{f(toplamGercek)} TL</div>
        </div>
      </div>

      {/* Kategori bazlı */}
      <div style={{ background: 'var(--bg-card)', borderRadius: 12, padding: 16, border: '1px solid var(--border)' }}>
        <div style={{ fontWeight: 700, fontSize: 14, marginBottom: 12 }}>📊 Kategori Bazlı Bütçe</div>
        {KATEGORILER.map(kat => {
          const plan = parseFloat(butce[kat] || 0);
          const gercek = gerceklesen[kat] || 0;
          const oran = plan > 0 ? (gercek / plan * 100) : 0;
          const asim = gercek > plan && plan > 0;

          return (
            <div key={kat} style={{ marginBottom: 12, padding: '8px 0', borderBottom: '1px solid var(--border-light, #f1f5f9)' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 4 }}>
                <span style={{ fontSize: 13, fontWeight: 600 }}>{kat}</span>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                  <span style={{ fontSize: 12, color: '#64748b' }}>Gerçek: {f(gercek)} TL</span>
                  {asim && <span style={{ fontSize: 10, color: '#dc2626', fontWeight: 700 }}>AŞIM!</span>}
                </div>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <input className="input" type="number" placeholder="Bütçe (TL)" value={butce[kat] || ''}
                  onChange={e => setButce(p => ({ ...p, [kat]: e.target.value }))}
                  style={{ width: 120, fontSize: 13, padding: '6px 8px' }} />
                {plan > 0 && (
                  <div style={{ flex: 1 }}>
                    <div style={{ height: 6, background: '#e2e8f0', borderRadius: 3, overflow: 'hidden' }}>
                      <div style={{ height: '100%', background: asim ? '#dc2626' : '#16a34a', width: `${Math.min(oran, 100)}%`, borderRadius: 3 }} />
                    </div>
                    <div style={{ fontSize: 10, color: asim ? '#dc2626' : '#64748b', marginTop: 2 }}>%{oran.toFixed(0)}</div>
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </>
  );
}
