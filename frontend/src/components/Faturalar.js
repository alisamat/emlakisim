import React, { useState, useEffect, useCallback } from 'react';
import api from '../api';

const DURUM = {
  bekliyor: { label: '⏳ Bekliyor', renk: '#f59e0b', bg: '#fffbeb' },
  odendi:   { label: '✅ Ödendi', renk: '#16a34a', bg: '#f0fdf4' },
  gecikti:  { label: '⚠️ Gecikti', renk: '#dc2626', bg: '#fef2f2' },
  iptal:    { label: '❌ İptal', renk: '#94a3b8', bg: '#f8fafc' },
};

function FaturaFormu({ onKaydet, onIptal }) {
  const [form, setForm] = useState({ tip: 'hizmet', alici_ad: '', tutar: '', kdv_oran: '20', vade_tarihi: '', kalemler: [{ aciklama: '', tutar: '' }] });
  const [yuk, setYuk] = useState(false);
  const d = e => setForm(p => ({ ...p, [e.target.name]: e.target.value }));

  const kalemEkle = () => setForm(p => ({ ...p, kalemler: [...p.kalemler, { aciklama: '', tutar: '' }] }));
  const kalemDegistir = (i, k, v) => setForm(p => ({ ...p, kalemler: p.kalemler.map((x, j) => j === i ? { ...x, [k]: v } : x) }));

  const kaydet = async e => {
    e.preventDefault(); setYuk(true);
    try {
      const r = await api.post('/api/panel/fatura/ekle', form);
      onKaydet(r.data.fatura);
    } catch {} finally { setYuk(false); }
  };

  return (
    <div style={{ background: '#fff', borderRadius: 12, padding: 20, marginBottom: 16, border: '1px solid #e2e8f0' }}>
      <div style={{ fontWeight: 700, fontSize: 15, marginBottom: 16 }}>Yeni Fatura</div>
      <form onSubmit={kaydet}>
        <div className="grid-2" style={{ marginBottom: 12 }}>
          <div>
            <label className="etiket">Tip</label>
            <select className="input" name="tip" value={form.tip} onChange={d}>
              <option value="hizmet">Hizmet</option><option value="komisyon">Komisyon</option>
              <option value="satis">Satış</option><option value="kiralama">Kiralama</option>
            </select>
          </div>
          <div><label className="etiket">Alıcı Ad</label><input className="input" name="alici_ad" value={form.alici_ad} onChange={d} /></div>
        </div>
        <div style={{ fontWeight: 600, fontSize: 13, marginBottom: 8 }}>Kalemler</div>
        {form.kalemler.map((k, i) => (
          <div key={i} className="grid-2" style={{ marginBottom: 8 }}>
            <input className="input" placeholder="Açıklama" value={k.aciklama} onChange={e => kalemDegistir(i, 'aciklama', e.target.value)} />
            <input className="input" type="number" placeholder="Tutar (TL)" value={k.tutar} onChange={e => kalemDegistir(i, 'tutar', e.target.value)} />
          </div>
        ))}
        <button type="button" onClick={kalemEkle} style={{ background: 'none', border: 'none', color: '#16a34a', fontSize: 12, cursor: 'pointer', marginBottom: 12 }}>+ Kalem Ekle</button>
        <div className="grid-2" style={{ marginBottom: 12 }}>
          <div><label className="etiket">Ara Toplam (TL)</label><input className="input" name="tutar" type="number" value={form.tutar} onChange={d} /></div>
          <div><label className="etiket">KDV %</label><input className="input" name="kdv_oran" type="number" value={form.kdv_oran} onChange={d} /></div>
        </div>
        <div style={{ marginBottom: 16 }}>
          <label className="etiket">Vade Tarihi</label><input className="input" name="vade_tarihi" type="date" value={form.vade_tarihi} onChange={d} />
        </div>
        <div style={{ display: 'flex', gap: 10 }}>
          <button className="btn-yesil" type="submit" disabled={yuk}>{yuk ? '...' : 'Oluştur'}</button>
          <button className="btn-gri" type="button" onClick={onIptal}>İptal</button>
        </div>
      </form>
    </div>
  );
}

export default function Faturalar() {
  const [faturalar, setFaturalar] = useState([]);
  const [ozet, setOzet] = useState({});
  const [formAcik, setFormAcik] = useState(false);
  const [yuk, setYuk] = useState(false);
  const [filtre, setFiltre] = useState('');

  const yukle = useCallback(async () => {
    setYuk(true);
    try {
      const [f, o] = await Promise.all([api.get('/api/panel/fatura/listele'), api.get('/api/panel/fatura/ozet')]);
      setFaturalar(f.data.faturalar || []); setOzet(o.data);
    } catch {} finally { setYuk(false); }
  }, []);

  useEffect(() => { yukle(); }, [yukle]);

  const durumDegistir = async (id, durum) => {
    try { await api.put(`/api/panel/fatura/${id}`, { durum }); yukle(); } catch {}
  };

  const pdfIndir = async (id) => {
    try {
      const r = await api.get(`/api/panel/fatura/${id}/pdf`, { responseType: 'blob' });
      const url = URL.createObjectURL(new Blob([r.data]));
      const a = document.createElement('a'); a.href = url; a.download = `fatura_${id}.pdf`; a.click();
    } catch {}
  };

  const liste = filtre ? faturalar.filter(f => f.durum === filtre) : faturalar;

  return (
    <>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
        <h1 style={{ fontSize: 20, fontWeight: 800, color: '#0f172a' }}>🧾 Faturalar</h1>
        <button className="btn-yesil" onClick={() => setFormAcik(p => !p)}>+ Fatura</button>
      </div>

      <div className="grid-2" style={{ marginBottom: 16, gap: 8 }}>
        <div style={{ background: '#f0fdf4', borderRadius: 8, padding: 10, textAlign: 'center' }}>
          <div style={{ fontSize: 12, color: '#16a34a', fontWeight: 600 }}>Ödenen</div>
          <div style={{ fontSize: 18, fontWeight: 800, color: '#16a34a' }}>{Number(ozet.odenen || 0).toLocaleString('tr-TR')} TL</div>
        </div>
        <div style={{ background: '#fffbeb', borderRadius: 8, padding: 10, textAlign: 'center' }}>
          <div style={{ fontSize: 12, color: '#f59e0b', fontWeight: 600 }}>Bekleyen</div>
          <div style={{ fontSize: 18, fontWeight: 800, color: '#f59e0b' }}>{Number(ozet.bekleyen || 0).toLocaleString('tr-TR')} TL</div>
        </div>
      </div>

      {formAcik && <FaturaFormu onKaydet={f => { setFaturalar(p => [f, ...p]); setFormAcik(false); yukle(); }} onIptal={() => setFormAcik(false)} />}

      <div style={{ display: 'flex', gap: 8, marginBottom: 16, flexWrap: 'wrap' }}>
        {[['', 'Tümü'], ...Object.entries(DURUM).map(([k, v]) => [k, v.label])].map(([v, l]) => (
          <button key={v} onClick={() => setFiltre(v)} style={{
            padding: '6px 14px', borderRadius: 20, fontSize: 12, fontWeight: 600, cursor: 'pointer',
            background: filtre === v ? '#16a34a' : '#fff', color: filtre === v ? '#fff' : '#374151',
            border: `1px solid ${filtre === v ? '#16a34a' : '#e2e8f0'}`,
          }}>{l}</button>
        ))}
      </div>

      {yuk ? <div style={{ textAlign: 'center', color: '#94a3b8', padding: 40 }}>Yükleniyor…</div> :
        liste.length === 0 ? <div style={{ textAlign: 'center', color: '#94a3b8', padding: 40, background: '#fff', borderRadius: 12 }}>Henüz fatura yok</div> :
        liste.map(f => {
          const d = DURUM[f.durum] || DURUM.bekliyor;
          return (
            <div key={f.id} style={{ background: '#fff', borderRadius: 12, padding: '12px 16px', marginBottom: 8, border: '1px solid #e2e8f0', borderLeft: `3px solid ${d.renk}` }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 2 }}>
                    <span style={{ fontWeight: 700, fontSize: 14 }}>{f.fatura_no}</span>
                    <span style={{ background: d.bg, color: d.renk, borderRadius: 6, padding: '2px 8px', fontSize: 11, fontWeight: 700 }}>{d.label}</span>
                    <span style={{ fontSize: 11, color: '#94a3b8' }}>{f.tip}</span>
                  </div>
                  <div style={{ fontSize: 13, color: '#374151' }}>{f.alici_ad || '—'} · <strong>{Number(f.toplam).toLocaleString('tr-TR')} TL</strong></div>
                </div>
                <div style={{ display: 'flex', gap: 6 }}>
                  <button onClick={() => pdfIndir(f.id)} style={{ background: '#f0fdf4', border: '1px solid #bbf7d0', borderRadius: 6, padding: '4px 10px', fontSize: 11, cursor: 'pointer', color: '#16a34a', fontWeight: 600 }}>PDF</button>
                  {f.durum === 'bekliyor' && <button onClick={() => durumDegistir(f.id, 'odendi')} style={{ background: '#eff6ff', border: '1px solid #bfdbfe', borderRadius: 6, padding: '4px 10px', fontSize: 11, cursor: 'pointer', color: '#1d4ed8', fontWeight: 600 }}>Ödendi</button>}
                </div>
              </div>
            </div>
          );
        })
      }
    </>
  );
}
