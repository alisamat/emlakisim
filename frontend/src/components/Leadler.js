import React, { useState, useEffect, useCallback } from 'react';
import api from '../api';

const DURUM = {
  yeni: { label: '🆕 Yeni', renk: '#3b82f6', bg: '#eff6ff' },
  iletisimde: { label: '📞 İletişimde', renk: '#f59e0b', bg: '#fffbeb' },
  musteri_oldu: { label: '✅ Müşteri', renk: '#16a34a', bg: '#f0fdf4' },
  kayip: { label: '❌ Kayıp', renk: '#94a3b8', bg: '#f8fafc' },
};

const KAYNAK = { whatsapp: '💬 WhatsApp', web: '🌐 Web', telefon: '📞 Telefon', referans: '👥 Referans', ilan: '📋 İlan' };

function LeadFormu({ onKaydet, onIptal }) {
  const [form, setForm] = useState({ ad_soyad: '', telefon: '', email: '', kaynak: 'web', ilk_mesaj: '' });
  const [yuk, setYuk] = useState(false);
  const d = e => setForm(p => ({ ...p, [e.target.name]: e.target.value }));
  const kaydet = async e => {
    e.preventDefault(); setYuk(true);
    try { const r = await api.post('/api/panel/lead/ekle', form); onKaydet(r.data.lead); }
    catch {} finally { setYuk(false); }
  };
  return (
    <div style={{ background: '#fff', borderRadius: 12, padding: 20, marginBottom: 16, border: '1px solid #e2e8f0' }}>
      <div style={{ fontWeight: 700, fontSize: 15, marginBottom: 16 }}>Yeni Lead</div>
      <form onSubmit={kaydet}>
        <div className="grid-2" style={{ marginBottom: 12 }}>
          <div><label className="etiket">Ad Soyad</label><input className="input" name="ad_soyad" value={form.ad_soyad} onChange={d} required /></div>
          <div><label className="etiket">Telefon</label><input className="input" name="telefon" value={form.telefon} onChange={d} /></div>
        </div>
        <div className="grid-2" style={{ marginBottom: 12 }}>
          <div><label className="etiket">Email</label><input className="input" name="email" value={form.email} onChange={d} /></div>
          <div><label className="etiket">Kaynak</label>
            <select className="input" name="kaynak" value={form.kaynak} onChange={d}>
              {Object.entries(KAYNAK).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
            </select>
          </div>
        </div>
        <div style={{ marginBottom: 16 }}>
          <label className="etiket">İlk Mesaj / Not</label>
          <textarea className="input" name="ilk_mesaj" value={form.ilk_mesaj} onChange={d} rows={2} style={{ resize: 'vertical' }} />
        </div>
        <div style={{ display: 'flex', gap: 10 }}>
          <button className="btn-yesil" type="submit" disabled={yuk}>{yuk ? '...' : 'Kaydet'}</button>
          <button className="btn-gri" type="button" onClick={onIptal}>İptal</button>
        </div>
      </form>
    </div>
  );
}

export default function Leadler() {
  const [leadler, setLeadler] = useState([]);
  const [istat, setIstat] = useState({});
  const [formAcik, setFormAcik] = useState(false);
  const [yuk, setYuk] = useState(false);
  const [filtre, setFiltre] = useState('');

  const yukle = useCallback(async () => {
    setYuk(true);
    try {
      const [l, i] = await Promise.all([api.get('/api/panel/lead/listele'), api.get('/api/panel/lead/istatistik')]);
      setLeadler(l.data.leadler || []); setIstat(i.data);
    } catch {} finally { setYuk(false); }
  }, []);

  useEffect(() => { yukle(); }, [yukle]);

  const durumDegistir = async (id, durum) => {
    try {
      await api.put(`/api/panel/lead/${id}`, { durum });
      setLeadler(p => p.map(l => l.id === id ? { ...l, durum } : l));
    } catch {}
  };

  const sil = async id => {
    if (!window.confirm('Silmek istediğinize emin misiniz?')) return;
    try { await api.delete(`/api/panel/lead/${id}`); setLeadler(p => p.filter(l => l.id !== id)); } catch {}
  };

  const liste = filtre ? leadler.filter(l => l.durum === filtre) : leadler;

  return (
    <>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
        <h1 style={{ fontSize: 20, fontWeight: 800, color: '#0f172a' }}>🎯 Lead Yönetimi</h1>
        <button className="btn-yesil" onClick={() => setFormAcik(p => !p)}>+ Lead Ekle</button>
      </div>

      {/* İstatistik */}
      <div className="grid-2" style={{ marginBottom: 16, gap: 8 }}>
        {[['yeni', '🆕', istat.yeni], ['iletisimde', '📞', istat.iletisimde], ['musteri_oldu', '✅', istat.musteri_oldu], ['kayip', '❌', istat.toplam - (istat.yeni || 0) - (istat.iletisimde || 0) - (istat.musteri_oldu || 0)]].map(([k, i, v]) => (
          <div key={k} style={{ background: '#f8fafc', borderRadius: 8, padding: 10, textAlign: 'center', cursor: 'pointer', border: filtre === k ? '2px solid #16a34a' : '1px solid #e2e8f0' }} onClick={() => setFiltre(filtre === k ? '' : k)}>
            <div style={{ fontSize: 18 }}>{i}</div>
            <div style={{ fontSize: 16, fontWeight: 800 }}>{v || 0}</div>
          </div>
        ))}
      </div>

      {formAcik && <LeadFormu onKaydet={l => { setLeadler(p => [l, ...p]); setFormAcik(false); }} onIptal={() => setFormAcik(false)} />}

      {yuk ? <div style={{ textAlign: 'center', color: '#94a3b8', padding: 40 }}>Yükleniyor…</div> :
        liste.length === 0 ? <div style={{ textAlign: 'center', color: '#94a3b8', padding: 40, background: '#fff', borderRadius: 12 }}><div style={{ fontSize: 32, marginBottom: 8 }}>🎯</div>Henüz lead yok</div> :
        liste.map(l => {
          const d = DURUM[l.durum] || DURUM.yeni;
          return (
            <div key={l.id} style={{ background: '#fff', borderRadius: 12, padding: '12px 16px', marginBottom: 8, border: '1px solid #e2e8f0', borderLeft: `3px solid ${d.renk}` }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                <div style={{ flex: 1 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4, flexWrap: 'wrap' }}>
                    <span style={{ fontWeight: 700, fontSize: 14 }}>{l.ad_soyad || '—'}</span>
                    <span style={{ background: d.bg, color: d.renk, borderRadius: 6, padding: '2px 8px', fontSize: 11, fontWeight: 700 }}>{d.label}</span>
                    {l.kaynak && <span style={{ fontSize: 11, color: '#94a3b8' }}>{KAYNAK[l.kaynak] || l.kaynak}</span>}
                  </div>
                  {l.telefon && <div style={{ fontSize: 12, color: '#64748b' }}>📞 {l.telefon}</div>}
                  {l.ilk_mesaj && <div style={{ fontSize: 12, color: '#94a3b8', marginTop: 2 }}>{l.ilk_mesaj}</div>}
                </div>
                <div style={{ display: 'flex', gap: 4 }}>
                  <select value={l.durum} onChange={e => durumDegistir(l.id, e.target.value)}
                    style={{ fontSize: 11, border: '1px solid #e2e8f0', borderRadius: 4, padding: '2px 4px' }}>
                    {Object.entries(DURUM).map(([k, v]) => <option key={k} value={k}>{v.label}</option>)}
                  </select>
                  <button onClick={() => sil(l.id)} style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#94a3b8', fontSize: 13 }}>🗑</button>
                </div>
              </div>
            </div>
          );
        })
      }
    </>
  );
}
