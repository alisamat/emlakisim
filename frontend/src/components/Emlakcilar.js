import React, { useState, useEffect, useCallback } from 'react';
import api from '../api';

function EmlakciFormu({ onKaydet, onIptal }) {
  const [form, setForm] = useState({ ad_soyad: '', telefon: '', email: '', bolge: '', uzmanlik: '', acente: '', notlar: '' });
  const [yuk, setYuk] = useState(false);
  const d = e => setForm(p => ({ ...p, [e.target.name]: e.target.value }));
  const kaydet = async e => {
    e.preventDefault(); setYuk(true);
    try { const r = await api.post('/api/panel/emlakcilar', form); onKaydet(r.data.emlakci); }
    catch {} finally { setYuk(false); }
  };
  return (
    <div style={{ background: 'var(--bg-card)', borderRadius: 12, padding: 20, marginBottom: 16, border: '1px solid var(--border)' }}>
      <div style={{ fontWeight: 700, fontSize: 15, marginBottom: 16 }}>Yeni Emlakçı</div>
      <form onSubmit={kaydet}>
        <div className="grid-2" style={{ marginBottom: 12 }}>
          <div><label className="etiket">Ad Soyad *</label><input className="input" name="ad_soyad" value={form.ad_soyad} onChange={d} required /></div>
          <div><label className="etiket">Telefon</label><input className="input" name="telefon" value={form.telefon} onChange={d} /></div>
        </div>
        <div className="grid-2" style={{ marginBottom: 12 }}>
          <div><label className="etiket">Bölge</label><input className="input" name="bolge" value={form.bolge} onChange={d} placeholder="Kadıköy, Beyoğlu..." /></div>
          <div><label className="etiket">Uzmanlık</label><input className="input" name="uzmanlik" value={form.uzmanlik} onChange={d} placeholder="Kiralık, Satılık..." /></div>
        </div>
        <div className="grid-2" style={{ marginBottom: 12 }}>
          <div><label className="etiket">Acente</label><input className="input" name="acente" value={form.acente} onChange={d} /></div>
          <div><label className="etiket">Email</label><input className="input" name="email" value={form.email} onChange={d} /></div>
        </div>
        <div style={{ marginBottom: 16 }}>
          <label className="etiket">Notlar</label>
          <textarea className="input" name="notlar" value={form.notlar} onChange={d} rows={2} style={{ resize: 'vertical' }} />
        </div>
        <div style={{ display: 'flex', gap: 10 }}>
          <button className="btn-yesil" type="submit" disabled={yuk}>{yuk ? '...' : 'Kaydet'}</button>
          <button className="btn-gri" type="button" onClick={onIptal}>İptal</button>
        </div>
      </form>
    </div>
  );
}

export default function Emlakcilar() {
  const [emlakcilar, setEmlakcilar] = useState([]);
  const [formAcik, setFormAcik] = useState(false);
  const [arama, setArama] = useState('');
  const [yuk, setYuk] = useState(false);

  const yukle = useCallback(async () => {
    setYuk(true);
    try { const r = await api.get('/api/panel/emlakcilar'); setEmlakcilar(r.data.emlakcilar || []); }
    catch {} finally { setYuk(false); }
  }, []);

  useEffect(() => { yukle(); }, [yukle]);

  const sil = async id => {
    if (!window.confirm('Silmek istediğinize emin misiniz?')) return;
    try { await api.delete(`/api/panel/emlakcilar/${id}`); setEmlakcilar(p => p.filter(e => e.id !== id)); } catch {}
  };

  const liste = arama.trim() ? emlakcilar.filter(e => (e.ad_soyad || '').toLowerCase().includes(arama.toLowerCase()) || (e.bolge || '').toLowerCase().includes(arama.toLowerCase())) : emlakcilar;

  return (
    <>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
        <h1 style={{ fontSize: 20, fontWeight: 800, color: 'var(--text-primary)' }}>📒 Emlakçılar Dizini <span style={{ fontSize: 14, fontWeight: 400, color: 'var(--text-muted)' }}>({emlakcilar.length})</span></h1>
        <button className="btn-yesil" onClick={() => setFormAcik(p => !p)}>+ Ekle</button>
      </div>

      {formAcik && <EmlakciFormu onKaydet={e => { setEmlakcilar(p => [e, ...p]); setFormAcik(false); }} onIptal={() => setFormAcik(false)} />}

      <div style={{ marginBottom: 12 }}>
        <input className="input" placeholder="🔍 Emlakçı ara (isim, bölge)..." value={arama} onChange={e => setArama(e.target.value)} style={{ width: '100%' }} />
      </div>

      {yuk ? <div style={{ textAlign: 'center', color: '#94a3b8', padding: 40 }}>Yükleniyor…</div> :
        liste.length === 0 ? <div style={{ textAlign: 'center', color: '#94a3b8', padding: 40, background: 'var(--bg-card)', borderRadius: 12 }}>Henüz emlakçı yok</div> :
        liste.map(e => (
          <div key={e.id} style={{ background: 'var(--bg-card)', borderRadius: 10, padding: '12px 16px', marginBottom: 8, border: '1px solid var(--border)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div>
              <div style={{ fontWeight: 700, fontSize: 14 }}>{e.ad_soyad}</div>
              <div style={{ fontSize: 12, color: 'var(--text-secondary)' }}>
                {e.telefon && `📞 ${e.telefon}`} {e.bolge && `· 📍 ${e.bolge}`} {e.acente && `· 🏢 ${e.acente}`}
              </div>
              {e.uzmanlik && <span style={{ fontSize: 11, background: '#eff6ff', color: '#1d4ed8', borderRadius: 6, padding: '1px 8px' }}>{e.uzmanlik}</span>}
            </div>
            <button onClick={() => sil(e.id)} style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#94a3b8', fontSize: 14 }}>🗑</button>
          </div>
        ))
      }
    </>
  );
}
