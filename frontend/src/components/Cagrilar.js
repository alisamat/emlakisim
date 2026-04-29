import React, { useState, useEffect, useCallback } from 'react';
import api from '../api';

const YON = { gelen: '📞 Gelen', giden: '📲 Giden', kacirilmis: '❌ Kaçırılmış' };

export default function Cagrilar() {
  const [cagrilar, setCagrilar] = useState([]);
  const [formAcik, setFormAcik] = useState(false);
  const [form, setForm] = useState({ telefon: '', yon: 'gelen', sure_sn: '', notlar: '' });
  const [yuk, setYuk] = useState(false);
  const d = e => setForm(p => ({ ...p, [e.target.name]: e.target.value }));

  const yukle = useCallback(async () => {
    setYuk(true);
    try { const r = await api.get('/api/panel/lead/cagri'); setCagrilar(r.data.cagrilar || []); }
    catch {} finally { setYuk(false); }
  }, []);

  useEffect(() => { yukle(); }, [yukle]);

  const kaydet = async e => {
    e.preventDefault(); setYuk(true);
    try {
      await api.post('/api/panel/lead/cagri', form);
      yukle(); setFormAcik(false); setForm({ telefon: '', yon: 'gelen', sure_sn: '', notlar: '' });
    } catch {} finally { setYuk(false); }
  };

  const kacirilmis = cagrilar.filter(c => c.yon === 'kacirilmis').length;

  return (
    <>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
        <h1 style={{ fontSize: 20, fontWeight: 800, color: '#0f172a' }}>📞 Çağrı Kayıtları</h1>
        <button className="btn-yesil" onClick={() => setFormAcik(p => !p)}>+ Kayıt Ekle</button>
      </div>

      {kacirilmis > 0 && (
        <div style={{ background: '#fef2f2', borderRadius: 12, padding: 12, marginBottom: 16, border: '1px solid #fecaca' }}>
          <span style={{ fontWeight: 700, color: '#dc2626', fontSize: 13 }}>❌ {kacirilmis} kaçırılmış çağrı</span>
        </div>
      )}

      {formAcik && (
        <div style={{ background: '#fff', borderRadius: 12, padding: 20, marginBottom: 16, border: '1px solid #e2e8f0' }}>
          <form onSubmit={kaydet}>
            <div className="grid-2" style={{ marginBottom: 12 }}>
              <div><label className="etiket">Telefon</label><input className="input" name="telefon" value={form.telefon} onChange={d} required /></div>
              <div><label className="etiket">Yön</label>
                <select className="input" name="yon" value={form.yon} onChange={d}>
                  {Object.entries(YON).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
                </select>
              </div>
            </div>
            <div className="grid-2" style={{ marginBottom: 12 }}>
              <div><label className="etiket">Süre (saniye)</label><input className="input" name="sure_sn" type="number" value={form.sure_sn} onChange={d} /></div>
              <div><label className="etiket">Notlar</label><input className="input" name="notlar" value={form.notlar} onChange={d} /></div>
            </div>
            <div style={{ display: 'flex', gap: 10 }}>
              <button className="btn-yesil" type="submit">Kaydet</button>
              <button className="btn-gri" type="button" onClick={() => setFormAcik(false)}>İptal</button>
            </div>
          </form>
        </div>
      )}

      {yuk ? <div style={{ textAlign: 'center', color: '#94a3b8', padding: 40 }}>Yükleniyor…</div> :
        cagrilar.length === 0 ? <div style={{ textAlign: 'center', color: '#94a3b8', padding: 40, background: '#fff', borderRadius: 12 }}>Henüz çağrı kaydı yok</div> :
        cagrilar.map(c => (
          <div key={c.id} style={{
            background: '#fff', borderRadius: 12, padding: '10px 16px', marginBottom: 6,
            border: '1px solid #e2e8f0', borderLeft: `3px solid ${c.yon === 'kacirilmis' ? '#dc2626' : c.yon === 'gelen' ? '#3b82f6' : '#16a34a'}`,
            display: 'flex', justifyContent: 'space-between', alignItems: 'center',
          }}>
            <div>
              <span style={{ fontSize: 13, fontWeight: 600 }}>{YON[c.yon] || c.yon}</span>
              <span style={{ marginLeft: 8, fontSize: 13, color: '#64748b' }}>{c.telefon}</span>
              {c.sure_sn && <span style={{ marginLeft: 8, fontSize: 12, color: '#94a3b8' }}>{Math.floor(c.sure_sn / 60)}:{String(c.sure_sn % 60).padStart(2, '0')}</span>}
              {c.notlar && <div style={{ fontSize: 12, color: '#94a3b8', marginTop: 2 }}>{c.notlar}</div>}
            </div>
            <span style={{ fontSize: 11, color: '#cbd5e1' }}>{c.olusturma ? new Date(c.olusturma).toLocaleString('tr-TR') : ''}</span>
          </div>
        ))
      }
    </>
  );
}
