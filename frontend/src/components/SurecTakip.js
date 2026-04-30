import React, { useState, useEffect, useCallback } from 'react';
import api from '../api';

const TIP_LABEL = { tapu_devri: '📋 Tapu Devri', kredi: '🏦 Kredi', ekspertiz: '📊 Ekspertiz', iskan: '🏠 İskan', imar: '📐 İmar' };
const DURUM_RENK = { basladi: '#3b82f6', devam: '#f59e0b', bekliyor: '#94a3b8', tamamlandi: '#16a34a' };

export default function SurecTakip() {
  const [surecler, setSurecler] = useState([]);
  const [formAcik, setFormAcik] = useState(false);
  const [form, setForm] = useState({ tip: 'tapu_devri', baslik: '' });
  const [secili, setSecili] = useState(null);
  const [yuk, setYuk] = useState(false);

  const yukle = useCallback(async () => {
    setYuk(true);
    try { const r = await api.get('/api/panel/surec'); setSurecler(r.data.surecler || []); }
    catch {} finally { setYuk(false); }
  }, []);

  useEffect(() => { yukle(); }, [yukle]);

  const ekle = async () => {
    try { await api.post('/api/panel/surec', form); yukle(); setFormAcik(false); }
    catch {}
  };

  const adimGuncelle = async (surec, adimIdx, yeniDurum) => {
    const adimlar = [...surec.adimlar];
    adimlar[adimIdx] = { ...adimlar[adimIdx], durum: yeniDurum };
    const tumu = adimlar.every(a => a.durum === 'tamamlandi');
    try {
      await api.put(`/api/panel/surec/${surec.id}`, { adimlar, durum: tumu ? 'tamamlandi' : 'devam' });
      yukle();
    } catch {}
  };

  return (
    <>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
        <h1 style={{ fontSize: 20, fontWeight: 800, color: 'var(--text-primary)' }}>📋 Süreç Takip</h1>
        <button className="btn-yesil" onClick={() => setFormAcik(p => !p)}>+ Yeni Süreç</button>
      </div>

      {formAcik && (
        <div style={{ background: 'var(--bg-card)', borderRadius: 12, padding: 20, marginBottom: 16, border: '1px solid var(--border)' }}>
          <div className="grid-2" style={{ marginBottom: 12 }}>
            <div><label className="etiket">Tip</label>
              <select className="input" value={form.tip} onChange={e => setForm(p => ({ ...p, tip: e.target.value }))}>
                {Object.entries(TIP_LABEL).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
              </select>
            </div>
            <div><label className="etiket">Başlık</label><input className="input" value={form.baslik} onChange={e => setForm(p => ({ ...p, baslik: e.target.value }))} placeholder="Kadıköy dairesi tapu devri" /></div>
          </div>
          <div style={{ display: 'flex', gap: 10 }}>
            <button className="btn-yesil" onClick={ekle}>Oluştur</button>
            <button className="btn-gri" onClick={() => setFormAcik(false)}>İptal</button>
          </div>
        </div>
      )}

      {yuk ? <div style={{ textAlign: 'center', padding: 40, color: '#94a3b8' }}>Yükleniyor...</div> :
        surecler.length === 0 ? <div style={{ textAlign: 'center', padding: 40, color: '#94a3b8', background: 'var(--bg-card)', borderRadius: 12 }}>Henüz süreç yok</div> :
        surecler.map(s => {
          const tamamlanan = (s.adimlar || []).filter(a => a.durum === 'tamamlandi').length;
          const toplam = (s.adimlar || []).length;
          const oran = toplam > 0 ? (tamamlanan / toplam * 100) : 0;

          return (
            <div key={s.id} style={{ background: 'var(--bg-card)', borderRadius: 12, padding: 16, marginBottom: 10, border: '1px solid var(--border)', borderLeft: `3px solid ${DURUM_RENK[s.durum] || '#94a3b8'}` }}>
              <div onClick={() => setSecili(secili === s.id ? null : s.id)} style={{ cursor: 'pointer' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 6 }}>
                  <span style={{ fontWeight: 700, fontSize: 14 }}>{TIP_LABEL[s.tip] || s.tip} — {s.baslik || '—'}</span>
                  <span style={{ fontSize: 12, color: DURUM_RENK[s.durum], fontWeight: 600 }}>{tamamlanan}/{toplam}</span>
                </div>
                <div style={{ height: 6, background: '#e2e8f0', borderRadius: 3, overflow: 'hidden' }}>
                  <div style={{ height: '100%', background: '#16a34a', width: `${oran}%`, borderRadius: 3, transition: 'width 0.3s' }} />
                </div>
              </div>

              {secili === s.id && (
                <div style={{ marginTop: 12 }}>
                  {(s.adimlar || []).map((a, i) => (
                    <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '6px 0', borderBottom: '1px solid var(--border-light, #f1f5f9)' }}>
                      <button onClick={() => adimGuncelle(s, i, a.durum === 'tamamlandi' ? 'bekliyor' : 'tamamlandi')} style={{
                        width: 20, height: 20, borderRadius: 4, cursor: 'pointer',
                        border: `2px solid ${a.durum === 'tamamlandi' ? '#16a34a' : '#e2e8f0'}`,
                        background: a.durum === 'tamamlandi' ? '#16a34a' : 'transparent',
                        color: '#fff', fontSize: 12, display: 'flex', alignItems: 'center', justifyContent: 'center',
                      }}>{a.durum === 'tamamlandi' ? '✓' : ''}</button>
                      <span style={{ fontSize: 13, textDecoration: a.durum === 'tamamlandi' ? 'line-through' : 'none', color: a.durum === 'tamamlandi' ? '#94a3b8' : 'var(--text-primary)' }}>{a.ad}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          );
        })
      }
    </>
  );
}
