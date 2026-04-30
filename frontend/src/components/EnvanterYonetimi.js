import React, { useState, useEffect, useCallback } from 'react';
import api from '../api';

const KATEGORILER = ['Kırtasiye', 'Temizlik', 'Teknoloji', 'Mobilya', 'Diğer'];

export default function EnvanterYonetimi() {
  const [envanter, setEnvanter] = useState([]);
  const [eksik, setEksik] = useState(0);
  const [formAcik, setFormAcik] = useState(false);
  const [form, setForm] = useState({ ad: '', kategori: 'Kırtasiye', miktar: '', min_miktar: '', birim: 'adet' });
  const d = e => setForm(p => ({ ...p, [e.target.name]: e.target.value }));

  const yukle = useCallback(async () => {
    try { const r = await api.get('/api/panel/ofis/envanter'); setEnvanter(r.data.envanter || []); setEksik(r.data.eksik_sayisi || 0); } catch {}
  }, []);

  useEffect(() => { yukle(); }, [yukle]);

  const ekle = async e => {
    e.preventDefault();
    try { await api.post('/api/panel/ofis/envanter', form); yukle(); setFormAcik(false); } catch {}
  };

  const sil = async id => {
    try { await api.delete(`/api/panel/ofis/envanter/${id}`); yukle(); } catch {}
  };

  const miktarGuncelle = async (id, miktar) => {
    try { await api.put(`/api/panel/ofis/envanter/${id}`, { miktar: parseInt(miktar) }); yukle(); } catch {}
  };

  return (
    <>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
        <h1 style={{ fontSize: 20, fontWeight: 800, color: 'var(--text-primary)' }}>📦 Ofis Envanter</h1>
        <button className="btn-yesil" onClick={() => setFormAcik(p => !p)}>+ Ekle</button>
      </div>

      {eksik > 0 && (
        <div style={{ background: '#fef2f2', borderRadius: 12, padding: 12, marginBottom: 16, border: '1px solid #fecaca' }}>
          <span style={{ fontWeight: 700, color: '#dc2626', fontSize: 13 }}>⚠️ {eksik} malzeme minimum stokun altında!</span>
        </div>
      )}

      {formAcik && (
        <div style={{ background: 'var(--bg-card)', borderRadius: 12, padding: 20, marginBottom: 16, border: '1px solid var(--border)' }}>
          <form onSubmit={ekle}>
            <div className="grid-2" style={{ marginBottom: 12 }}>
              <div><label className="etiket">Malzeme Adı</label><input className="input" name="ad" value={form.ad} onChange={d} required /></div>
              <div><label className="etiket">Kategori</label>
                <select className="input" name="kategori" value={form.kategori} onChange={d}>
                  {KATEGORILER.map(k => <option key={k}>{k}</option>)}
                </select>
              </div>
            </div>
            <div className="grid-2" style={{ marginBottom: 16 }}>
              <div><label className="etiket">Miktar</label><input className="input" name="miktar" type="number" value={form.miktar} onChange={d} /></div>
              <div><label className="etiket">Min Miktar (uyarı)</label><input className="input" name="min_miktar" type="number" value={form.min_miktar} onChange={d} /></div>
            </div>
            <div style={{ display: 'flex', gap: 10 }}>
              <button className="btn-yesil" type="submit">Kaydet</button>
              <button className="btn-gri" type="button" onClick={() => setFormAcik(false)}>İptal</button>
            </div>
          </form>
        </div>
      )}

      {envanter.length === 0 ? (
        <div style={{ textAlign: 'center', padding: 40, color: '#94a3b8', background: 'var(--bg-card)', borderRadius: 12 }}>Henüz malzeme yok</div>
      ) : envanter.map(e => {
        const dusuk = e.min_miktar && e.miktar <= e.min_miktar;
        return (
          <div key={e.id} style={{
            background: 'var(--bg-card)', borderRadius: 10, padding: '10px 14px', marginBottom: 6,
            border: '1px solid var(--border)', borderLeft: `3px solid ${dusuk ? '#dc2626' : '#16a34a'}`,
            display: 'flex', justifyContent: 'space-between', alignItems: 'center',
          }}>
            <div>
              <span style={{ fontWeight: 600, fontSize: 13 }}>{e.ad}</span>
              <span style={{ marginLeft: 8, fontSize: 11, color: 'var(--text-muted)' }}>{e.kategori}</span>
              {dusuk && <span style={{ marginLeft: 8, fontSize: 11, color: '#dc2626', fontWeight: 700 }}>DÜŞÜK!</span>}
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <button onClick={() => miktarGuncelle(e.id, Math.max(0, e.miktar - 1))} style={{ background: '#fef2f2', border: 'none', borderRadius: 4, width: 24, height: 24, cursor: 'pointer', fontSize: 14 }}>-</button>
              <span style={{ fontWeight: 700, fontSize: 14, minWidth: 30, textAlign: 'center' }}>{e.miktar}</span>
              <button onClick={() => miktarGuncelle(e.id, e.miktar + 1)} style={{ background: '#f0fdf4', border: 'none', borderRadius: 4, width: 24, height: 24, cursor: 'pointer', fontSize: 14 }}>+</button>
              <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>{e.birim}</span>
              <button onClick={() => sil(e.id)} style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#94a3b8', fontSize: 12 }}>🗑</button>
            </div>
          </div>
        );
      })}
    </>
  );
}
