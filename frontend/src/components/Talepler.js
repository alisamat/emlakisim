import React, { useState, useEffect } from 'react';
import api from '../api';

export default function Talepler() {
  const [musteriler, setMusteriler] = useState([]);
  const [gbForm, setGbForm] = useState(null); // {musteri_id, mulk_id}
  const [form, setForm] = useState({ puan: 3, yorum: '', ilgi_durumu: 'ilgili', sonraki_adim: 'dusunuyor' });
  const [bildirimler, setBildirimler] = useState([]);
  const [yuk, setYuk] = useState(false);

  useEffect(() => {
    setYuk(true);
    Promise.all([
      api.get('/api/panel/musteriler'),
      api.get('/api/panel/ofis/geri-bildirim'),
    ]).then(([m, g]) => {
      setMusteriler(m.data.musteriler || []);
      setBildirimler(g.data.geri_bildirimler || []);
    }).catch(() => {}).finally(() => setYuk(false));
  }, []);

  const gbKaydet = async () => {
    try {
      await api.post('/api/panel/ofis/geri-bildirim', { ...form, ...gbForm });
      setGbForm(null);
      const r = await api.get('/api/panel/ofis/geri-bildirim');
      setBildirimler(r.data.geri_bildirimler || []);
    } catch {}
  };

  // Talep olan müşteriler (tercih_notlar dolu)
  const talepler = musteriler.filter(m => m.tercih_notlar || m.butce_min || m.butce_max);
  const ILGI = { cok_ilgili: '🟢 Çok İlgili', ilgili: '🟡 İlgili', kararsiz: '🟠 Kararsız', ilgisiz: '🔴 İlgisiz' };

  return (
    <>
      <h1 style={{ fontSize: 20, fontWeight: 800, color: 'var(--text-primary)', marginBottom: 16 }}>📝 Talepler & Geri Bildirim</h1>

      {/* Aktif talepler */}
      <div style={{ fontWeight: 700, fontSize: 14, marginBottom: 8 }}>👥 Müşteri Talepleri ({talepler.length})</div>
      {yuk ? <div style={{ textAlign: 'center', color: '#94a3b8', padding: 20 }}>Yükleniyor...</div> :
        talepler.length === 0 ? <div style={{ fontSize: 13, color: '#94a3b8', marginBottom: 16 }}>Talepli müşteri yok</div> :
        talepler.map(m => (
          <div key={m.id} style={{ background: 'var(--bg-card)', borderRadius: 10, padding: '10px 14px', marginBottom: 6, border: '1px solid var(--border)' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div>
                <span style={{ fontWeight: 600, fontSize: 13 }}>{m.ad_soyad}</span>
                <span style={{ marginLeft: 8, fontSize: 12, color: '#64748b' }}>
                  {m.islem_turu === 'kira' ? 'Kiralık' : 'Satılık'}
                  {m.butce_max ? ` · max ${Number(m.butce_max).toLocaleString('tr-TR')} TL` : ''}
                </span>
              </div>
              <button onClick={() => setGbForm({ musteri_id: m.id })} style={{
                background: '#eff6ff', border: '1px solid #bfdbfe', borderRadius: 6,
                padding: '3px 10px', fontSize: 11, cursor: 'pointer', color: '#1d4ed8', fontWeight: 600,
              }}>Geri Bildirim</button>
            </div>
            {m.tercih_notlar && <div style={{ fontSize: 12, color: '#94a3b8', marginTop: 2 }}>{m.tercih_notlar}</div>}
          </div>
        ))
      }

      {/* Geri bildirim formu */}
      {gbForm && (
        <div style={{ background: '#eff6ff', borderRadius: 12, padding: 16, marginTop: 12, marginBottom: 16, border: '1px solid #bfdbfe' }}>
          <div style={{ fontWeight: 700, fontSize: 14, marginBottom: 12, color: '#1d4ed8' }}>📝 Geri Bildirim</div>
          <div className="grid-2" style={{ marginBottom: 12 }}>
            <div>
              <label className="etiket">Puan (1-5)</label>
              <select className="input" value={form.puan} onChange={e => setForm(p => ({ ...p, puan: e.target.value }))}>
                {[1,2,3,4,5].map(i => <option key={i} value={i}>{'⭐'.repeat(i)}</option>)}
              </select>
            </div>
            <div>
              <label className="etiket">İlgi Durumu</label>
              <select className="input" value={form.ilgi_durumu} onChange={e => setForm(p => ({ ...p, ilgi_durumu: e.target.value }))}>
                {Object.entries(ILGI).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
              </select>
            </div>
          </div>
          <div className="grid-2" style={{ marginBottom: 12 }}>
            <div>
              <label className="etiket">Sonraki Adım</label>
              <select className="input" value={form.sonraki_adim} onChange={e => setForm(p => ({ ...p, sonraki_adim: e.target.value }))}>
                <option value="tekrar_gosterme">Tekrar Gösterme</option>
                <option value="teklif">Teklif Yapılacak</option>
                <option value="dusunuyor">Düşünüyor</option>
                <option value="vazgecti">Vazgeçti</option>
              </select>
            </div>
            <div><label className="etiket">Yorum</label><input className="input" value={form.yorum} onChange={e => setForm(p => ({ ...p, yorum: e.target.value }))} /></div>
          </div>
          <div style={{ display: 'flex', gap: 8 }}>
            <button className="btn-yesil" onClick={gbKaydet} style={{ fontSize: 13 }}>Kaydet</button>
            <button className="btn-gri" onClick={() => setGbForm(null)} style={{ fontSize: 13 }}>İptal</button>
          </div>
        </div>
      )}

      {/* Geçmiş geri bildirimler */}
      {bildirimler.length > 0 && (
        <>
          <div style={{ fontWeight: 700, fontSize: 14, marginTop: 16, marginBottom: 8 }}>📊 Son Geri Bildirimler</div>
          {bildirimler.slice(0, 10).map(g => (
            <div key={g.id} style={{ background: 'var(--bg-card)', borderRadius: 8, padding: '8px 12px', marginBottom: 4, border: '1px solid var(--border)', fontSize: 12 }}>
              <span>{'⭐'.repeat(g.puan || 0)}</span>
              <span style={{ marginLeft: 8, color: '#64748b' }}>{ILGI[g.ilgi_durumu] || ''}</span>
              {g.yorum && <span style={{ marginLeft: 8, color: '#94a3b8' }}>{g.yorum}</span>}
              <span style={{ float: 'right', color: '#cbd5e1' }}>{g.olusturma ? new Date(g.olusturma).toLocaleDateString('tr-TR') : ''}</span>
            </div>
          ))}
        </>
      )}
    </>
  );
}
