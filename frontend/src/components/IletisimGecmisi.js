import React, { useState, useEffect } from 'react';
import api from '../api';

const TIP_IKON = { telefon: '📞', whatsapp: '💬', email: '📧', yuz_yuze: '🤝', yer_gosterme: '🏠' };

export default function IletisimGecmisi() {
  const [musteriler, setMusteriler] = useState([]);
  const [secili, setSecili] = useState(null);
  const [kayitlar, setKayitlar] = useState([]);
  const [form, setForm] = useState({ tip: 'telefon', yon: 'giden', ozet: '' });

  useEffect(() => {
    api.get('/api/panel/musteriler').then(r => setMusteriler(r.data.musteriler || [])).catch(() => {});
  }, []);

  const musteriSec = async (m) => {
    setSecili(m);
    try { const r = await api.get(`/api/panel/gelismis/iletisim-gecmisi/${m.id}`); setKayitlar(r.data.kayitlar || []); }
    catch { setKayitlar([]); }
  };

  const kayitEkle = async () => {
    if (!secili || !form.ozet.trim()) return;
    try {
      await api.post('/api/panel/gelismis/iletisim-kayit', { musteri_id: secili.id, ...form });
      const r = await api.get(`/api/panel/gelismis/iletisim-gecmisi/${secili.id}`);
      setKayitlar(r.data.kayitlar || []);
      setForm(p => ({ ...p, ozet: '' }));
    } catch {}
  };

  return (
    <>
      <h1 style={{ fontSize: 20, fontWeight: 800, color: 'var(--text-primary)', marginBottom: 16 }}>📞 İletişim Geçmişi</h1>

      {!secili ? (
        <>
          <p style={{ fontSize: 13, color: 'var(--text-secondary)', marginBottom: 12 }}>Müşteri seçin, iletişim geçmişini görün</p>
          {musteriler.map(m => (
            <div key={m.id} onClick={() => musteriSec(m)} style={{
              background: 'var(--bg-card)', borderRadius: 10, padding: '10px 14px', marginBottom: 6,
              border: '1px solid var(--border)', cursor: 'pointer',
            }}>
              <span style={{ fontWeight: 600, fontSize: 13 }}>{m.ad_soyad}</span>
              <span style={{ marginLeft: 8, fontSize: 12, color: 'var(--text-muted)' }}>{m.telefon || ''}</span>
            </div>
          ))}
        </>
      ) : (
        <>
          <button onClick={() => { setSecili(null); setKayitlar([]); }} className="btn-gri" style={{ marginBottom: 12, fontSize: 13 }}>← Geri</button>

          <div style={{ background: 'var(--bg-card)', borderRadius: 12, padding: 14, marginBottom: 12, border: '1px solid var(--border)' }}>
            <div style={{ fontWeight: 700, fontSize: 16 }}>{secili.ad_soyad}</div>
            <div style={{ fontSize: 12, color: 'var(--text-secondary)' }}>{secili.telefon || ''} · {secili.islem_turu === 'kira' ? 'Kiralık' : 'Satılık'}</div>
          </div>

          {/* Kayıt ekleme */}
          <div style={{ background: 'var(--bg-card)', borderRadius: 12, padding: 14, marginBottom: 12, border: '1px solid var(--border)' }}>
            <div style={{ display: 'flex', gap: 8, marginBottom: 8 }}>
              <select className="input" value={form.tip} onChange={e => setForm(p => ({ ...p, tip: e.target.value }))} style={{ width: 120 }}>
                {Object.entries(TIP_IKON).map(([k, v]) => <option key={k} value={k}>{v} {k}</option>)}
              </select>
              <select className="input" value={form.yon} onChange={e => setForm(p => ({ ...p, yon: e.target.value }))} style={{ width: 90 }}>
                <option value="giden">Giden</option><option value="gelen">Gelen</option>
              </select>
            </div>
            <div style={{ display: 'flex', gap: 8 }}>
              <input className="input" placeholder="Görüşme özeti..." value={form.ozet} onChange={e => setForm(p => ({ ...p, ozet: e.target.value }))} style={{ flex: 1 }} />
              <button className="btn-yesil" onClick={kayitEkle} style={{ fontSize: 13 }}>Ekle</button>
            </div>
          </div>

          {/* Geçmiş */}
          <div style={{ fontSize: 13, fontWeight: 700, marginBottom: 8 }}>Geçmiş ({kayitlar.length})</div>
          {kayitlar.length === 0 ? <div style={{ fontSize: 13, color: 'var(--text-muted)' }}>Henüz kayıt yok</div> :
            kayitlar.map(k => (
              <div key={k.id} style={{
                background: 'var(--bg-card)', borderRadius: 8, padding: '8px 12px', marginBottom: 4,
                border: '1px solid var(--border)',
                borderLeft: `3px solid ${k.yon === 'gelen' ? '#3b82f6' : '#16a34a'}`,
              }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 12 }}>
                  <span>{TIP_IKON[k.tip] || '📌'} {k.tip} · {k.yon === 'gelen' ? '← Gelen' : '→ Giden'}</span>
                  <span style={{ color: 'var(--text-muted)' }}>{new Date(k.olusturma).toLocaleString('tr-TR')}</span>
                </div>
                {k.ozet && <div style={{ fontSize: 13, marginTop: 2 }}>{k.ozet}</div>}
              </div>
            ))
          }
        </>
      )}
    </>
  );
}
