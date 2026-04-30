import React, { useState, useEffect, useCallback } from 'react';
import api from '../api';

export default function Ekip() {
  const [danismanlar, setDanismanlar] = useState([]);
  const [formAcik, setFormAcik] = useState(false);
  const [form, setForm] = useState({ ad_soyad: '', telefon: '', email: '', uzmanlik: '' });
  const [yuk, setYuk] = useState(false);

  const yukle = useCallback(async () => {
    setYuk(true);
    try { const r = await api.get('/api/panel/ekip/danismanlar'); setDanismanlar(r.data.danismanlar || []); }
    catch {} finally { setYuk(false); }
  }, []);

  useEffect(() => { yukle(); }, [yukle]);

  const ekle = async e => {
    e.preventDefault();
    try { await api.post('/api/panel/ekip/danismanlar', form); yukle(); setFormAcik(false); setForm({ ad_soyad: '', telefon: '', email: '', uzmanlik: '' }); }
    catch {}
  };

  const sil = async id => {
    if (!window.confirm('Danışmanı silmek istediğinize emin misiniz?')) return;
    try { await api.delete(`/api/panel/ekip/danismanlar/${id}`); yukle(); } catch {}
  };

  return (
    <>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
        <h1 style={{ fontSize: 20, fontWeight: 800, color: 'var(--text-primary)' }}>👔 Ekip Yönetimi</h1>
        <button className="btn-yesil" onClick={() => setFormAcik(p => !p)}>+ Danışman Ekle</button>
      </div>

      {formAcik && (
        <div style={{ background: 'var(--bg-card)', borderRadius: 12, padding: 20, marginBottom: 16, border: '1px solid var(--border)' }}>
          <form onSubmit={ekle}>
            <div className="grid-2" style={{ marginBottom: 12 }}>
              <div><label className="etiket">Ad Soyad</label><input className="input" value={form.ad_soyad} onChange={e => setForm(p => ({ ...p, ad_soyad: e.target.value }))} required /></div>
              <div><label className="etiket">Telefon</label><input className="input" value={form.telefon} onChange={e => setForm(p => ({ ...p, telefon: e.target.value }))} /></div>
            </div>
            <div className="grid-2" style={{ marginBottom: 16 }}>
              <div><label className="etiket">Email</label><input className="input" value={form.email} onChange={e => setForm(p => ({ ...p, email: e.target.value }))} /></div>
              <div><label className="etiket">Uzmanlık</label><input className="input" value={form.uzmanlik} onChange={e => setForm(p => ({ ...p, uzmanlik: e.target.value }))} placeholder="Kiralık, Satılık, Ticari..." /></div>
            </div>
            <div style={{ display: 'flex', gap: 10 }}>
              <button className="btn-yesil" type="submit">Kaydet</button>
              <button className="btn-gri" type="button" onClick={() => setFormAcik(false)}>İptal</button>
            </div>
          </form>
        </div>
      )}

      <div style={{ fontSize: 13, color: 'var(--text-secondary)', marginBottom: 12 }}>{danismanlar.length} danışman</div>

      {yuk ? <div style={{ textAlign: 'center', padding: 40, color: '#94a3b8' }}>Yükleniyor...</div> :
        danismanlar.length === 0 ? <div style={{ textAlign: 'center', padding: 40, color: '#94a3b8', background: 'var(--bg-card)', borderRadius: 12 }}>Henüz danışman eklenmedi</div> :
        danismanlar.map(d => (
          <div key={d.id} style={{ background: 'var(--bg-card)', borderRadius: 12, padding: '12px 16px', marginBottom: 8, border: '1px solid var(--border)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div>
              <div style={{ fontWeight: 700, fontSize: 14 }}>{d.ad_soyad}</div>
              <div style={{ fontSize: 12, color: 'var(--text-secondary)' }}>
                {d.telefon && `📞 ${d.telefon}`} {d.email && `· ${d.email}`}
                {d.uzmanlik && <span style={{ marginLeft: 8, background: '#eff6ff', color: '#1d4ed8', borderRadius: 6, padding: '1px 8px', fontSize: 11 }}>{d.uzmanlik}</span>}
              </div>
            </div>
            <button onClick={() => sil(d.id)} style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#94a3b8', fontSize: 14 }}>🗑</button>
          </div>
        ))
      }
    </>
  );
}
