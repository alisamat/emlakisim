import React, { useState, useEffect, useCallback } from 'react';
import api from '../api';

function CariFormu({ onKaydet, onIptal }) {
  const [form, setForm] = useState({ ad: '', tip: 'musteri', telefon: '' });
  const [yuk, setYuk] = useState(false);
  const d = e => setForm(p => ({ ...p, [e.target.name]: e.target.value }));
  const kaydet = async e => {
    e.preventDefault(); setYuk(true);
    try { const r = await api.post('/api/panel/muhasebe/cariler', form); onKaydet(r.data.cari); }
    catch {} finally { setYuk(false); }
  };
  return (
    <div style={{ background: '#fff', borderRadius: 12, padding: 20, marginBottom: 16, border: '1px solid #e2e8f0' }}>
      <div style={{ fontWeight: 700, fontSize: 15, marginBottom: 16 }}>Yeni Cari</div>
      <form onSubmit={kaydet}>
        <div className="grid-2" style={{ marginBottom: 12 }}>
          <div><label className="etiket">Ad</label><input className="input" name="ad" value={form.ad} onChange={d} required /></div>
          <div><label className="etiket">Tip</label>
            <select className="input" name="tip" value={form.tip} onChange={d}>
              <option value="musteri">Müşteri</option><option value="tedarikci">Tedarikçi</option><option value="mal_sahibi">Mal Sahibi</option>
            </select>
          </div>
        </div>
        <div style={{ marginBottom: 16 }}>
          <label className="etiket">Telefon</label><input className="input" name="telefon" value={form.telefon} onChange={d} />
        </div>
        <div style={{ display: 'flex', gap: 10 }}>
          <button className="btn-yesil" type="submit" disabled={yuk}>{yuk ? '...' : 'Kaydet'}</button>
          <button className="btn-gri" type="button" onClick={onIptal}>İptal</button>
        </div>
      </form>
    </div>
  );
}

function HareketFormu({ cariId, onKaydet }) {
  const [form, setForm] = useState({ tip: 'alacak', tutar: '', aciklama: '' });
  const [yuk, setYuk] = useState(false);
  const d = e => setForm(p => ({ ...p, [e.target.name]: e.target.value }));
  const kaydet = async e => {
    e.preventDefault(); setYuk(true);
    try { const r = await api.post(`/api/panel/muhasebe/cariler/${cariId}/hareket`, form); onKaydet(r.data); }
    catch {} finally { setYuk(false); }
  };
  return (
    <form onSubmit={kaydet} style={{ display: 'flex', gap: 8, marginTop: 8, flexWrap: 'wrap' }}>
      <select className="input" name="tip" value={form.tip} onChange={d} style={{ width: 100 }}>
        <option value="alacak">Alacak</option><option value="borc">Borç</option>
      </select>
      <input className="input" name="tutar" type="number" placeholder="Tutar" value={form.tutar} onChange={d} style={{ width: 100 }} required />
      <input className="input" name="aciklama" placeholder="Açıklama" value={form.aciklama} onChange={d} style={{ flex: 1, minWidth: 120 }} />
      <button className="btn-yesil" type="submit" disabled={yuk} style={{ fontSize: 12 }}>{yuk ? '...' : 'Ekle'}</button>
    </form>
  );
}

export default function Cariler() {
  const [cariler, setCariler] = useState([]);
  const [formAcik, setFormAcik] = useState(false);
  const [secili, setSecili] = useState(null);
  const [hareketler, setHareketler] = useState([]);
  const [yuk, setYuk] = useState(false);

  const yukle = useCallback(async () => {
    setYuk(true);
    try { const r = await api.get('/api/panel/muhasebe/cariler'); setCariler(r.data.cariler || []); }
    catch {} finally { setYuk(false); }
  }, []);

  useEffect(() => { yukle(); }, [yukle]);

  const cariSec = async (c) => {
    setSecili(c);
    try { const r = await api.get(`/api/panel/muhasebe/cariler/${c.id}`); setHareketler(r.data.hareketler || []); }
    catch {}
  };

  const hareketEklendi = (data) => {
    setHareketler(p => [data.hareket, ...p]);
    setCariler(p => p.map(c => c.id === secili.id ? { ...c, bakiye: data.bakiye } : c));
    setSecili(s => ({ ...s, bakiye: data.bakiye }));
  };

  const toplamAlacak = cariler.filter(c => c.bakiye > 0).reduce((t, c) => t + c.bakiye, 0);
  const toplamBorc = cariler.filter(c => c.bakiye < 0).reduce((t, c) => t + Math.abs(c.bakiye), 0);
  const f = v => Number(v).toLocaleString('tr-TR');

  return (
    <>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
        <h1 style={{ fontSize: 20, fontWeight: 800, color: '#0f172a' }}>📒 Cari Hesaplar</h1>
        <button className="btn-yesil" onClick={() => setFormAcik(p => !p)}>+ Cari Ekle</button>
      </div>

      <div className="grid-2" style={{ marginBottom: 16, gap: 8 }}>
        <div style={{ background: '#f0fdf4', borderRadius: 8, padding: 12, textAlign: 'center' }}>
          <div style={{ fontSize: 12, color: '#16a34a', fontWeight: 600 }}>Toplam Alacak</div>
          <div style={{ fontSize: 18, fontWeight: 800, color: '#16a34a' }}>{f(toplamAlacak)} TL</div>
        </div>
        <div style={{ background: '#fef2f2', borderRadius: 8, padding: 12, textAlign: 'center' }}>
          <div style={{ fontSize: 12, color: '#dc2626', fontWeight: 600 }}>Toplam Borç</div>
          <div style={{ fontSize: 18, fontWeight: 800, color: '#dc2626' }}>{f(toplamBorc)} TL</div>
        </div>
      </div>

      {formAcik && <CariFormu onKaydet={c => { setCariler(p => [c, ...p]); setFormAcik(false); }} onIptal={() => setFormAcik(false)} />}

      {!secili ? (
        yuk ? <div style={{ textAlign: 'center', color: '#94a3b8', padding: 40 }}>Yükleniyor…</div> :
        cariler.length === 0 ? <div style={{ textAlign: 'center', color: '#94a3b8', padding: 40, background: '#fff', borderRadius: 12 }}>Henüz cari yok</div> :
        cariler.map(c => (
          <div key={c.id} onClick={() => cariSec(c)} style={{
            background: '#fff', borderRadius: 12, padding: '12px 16px', marginBottom: 8,
            border: '1px solid #e2e8f0', cursor: 'pointer',
            borderLeft: `3px solid ${c.bakiye > 0 ? '#16a34a' : c.bakiye < 0 ? '#dc2626' : '#94a3b8'}`,
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div>
                <span style={{ fontWeight: 700, fontSize: 14 }}>{c.ad}</span>
                <span style={{ marginLeft: 8, fontSize: 11, color: '#94a3b8' }}>{c.tip === 'musteri' ? 'Müşteri' : c.tip === 'tedarikci' ? 'Tedarikçi' : 'Mal Sahibi'}</span>
              </div>
              <span style={{ fontWeight: 700, fontSize: 14, color: c.bakiye > 0 ? '#16a34a' : c.bakiye < 0 ? '#dc2626' : '#94a3b8' }}>
                {c.bakiye > 0 ? '+' : ''}{f(c.bakiye)} TL
              </span>
            </div>
          </div>
        ))
      ) : (
        <>
          <button onClick={() => { setSecili(null); setHareketler([]); }} className="btn-gri" style={{ marginBottom: 16, fontSize: 13 }}>← Cari Listesine Dön</button>

          <div style={{ background: '#fff', borderRadius: 12, padding: 16, marginBottom: 16, border: '1px solid #e2e8f0' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
              <div>
                <div style={{ fontWeight: 700, fontSize: 16 }}>{secili.ad}</div>
                <div style={{ fontSize: 12, color: '#94a3b8' }}>{secili.telefon || ''}</div>
              </div>
              <div style={{ textAlign: 'right' }}>
                <div style={{ fontSize: 12, color: '#64748b' }}>Bakiye</div>
                <div style={{ fontSize: 20, fontWeight: 800, color: secili.bakiye >= 0 ? '#16a34a' : '#dc2626' }}>
                  {secili.bakiye >= 0 ? '+' : ''}{f(secili.bakiye)} TL
                </div>
              </div>
            </div>
            <HareketFormu cariId={secili.id} onKaydet={hareketEklendi} />
          </div>

          <div style={{ fontWeight: 700, fontSize: 14, marginBottom: 8 }}>Hareketler</div>
          {hareketler.length === 0 ? <div style={{ fontSize: 13, color: '#94a3b8' }}>Henüz hareket yok</div> :
            hareketler.map(h => (
              <div key={h.id} style={{
                background: '#fff', borderRadius: 8, padding: '8px 14px', marginBottom: 4,
                border: '1px solid #f1f5f9', display: 'flex', justifyContent: 'space-between',
                borderLeft: `3px solid ${h.tip === 'alacak' ? '#16a34a' : '#dc2626'}`,
              }}>
                <div>
                  <span style={{ fontSize: 13, fontWeight: 600, color: h.tip === 'alacak' ? '#16a34a' : '#dc2626' }}>
                    {h.tip === 'alacak' ? '+' : '-'}{f(h.tutar)} TL
                  </span>
                  {h.aciklama && <span style={{ marginLeft: 8, fontSize: 12, color: '#94a3b8' }}>{h.aciklama}</span>}
                </div>
                <span style={{ fontSize: 11, color: '#cbd5e1' }}>{h.tarih ? new Date(h.tarih).toLocaleDateString('tr-TR') : ''}</span>
              </div>
            ))
          }
        </>
      )}
    </>
  );
}
