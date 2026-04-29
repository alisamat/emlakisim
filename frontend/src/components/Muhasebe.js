import React, { useState, useEffect, useCallback } from 'react';
import api from '../api';

const KATEGORILER = {
  gelir: ['Komisyon', 'Kira Geliri', 'Danışmanlık', 'Diğer Gelir'],
  gider: ['Ofis Kirası', 'Personel', 'Reklam', 'Ulaşım', 'Fatura', 'Vergi', 'Diğer Gider'],
};

function GelirGiderFormu({ onKaydet, onIptal }) {
  const [form, setForm] = useState({ tip: 'gelir', kategori: '', tutar: '', aciklama: '', tarih: new Date().toISOString().split('T')[0] });
  const [yukleniyor, setYuk] = useState(false);
  const d = e => setForm(p => ({ ...p, [e.target.name]: e.target.value }));

  const kaydet = async e => {
    e.preventDefault(); setYuk(true);
    try {
      const r = await api.post('/api/panel/muhasebe/gelir-gider', form);
      onKaydet(r.data.kayit);
    } catch {} finally { setYuk(false); }
  };

  return (
    <div style={{ background: '#fff', borderRadius: 12, padding: 20, marginBottom: 16, border: '1px solid #e2e8f0' }}>
      <div style={{ fontWeight: 700, fontSize: 15, color: '#1e293b', marginBottom: 16 }}>Yeni Kayıt</div>
      <form onSubmit={kaydet}>
        <div className="grid-2" style={{ marginBottom: 12 }}>
          <div>
            <label className="etiket">Tip</label>
            <select className="input" name="tip" value={form.tip} onChange={d}>
              <option value="gelir">Gelir</option><option value="gider">Gider</option>
            </select>
          </div>
          <div>
            <label className="etiket">Kategori</label>
            <select className="input" name="kategori" value={form.kategori} onChange={d}>
              <option value="">Seçiniz</option>
              {(KATEGORILER[form.tip] || []).map(k => <option key={k} value={k}>{k}</option>)}
            </select>
          </div>
        </div>
        <div className="grid-2" style={{ marginBottom: 12 }}>
          <div><label className="etiket">Tutar (TL)</label><input className="input" name="tutar" type="number" value={form.tutar} onChange={d} required /></div>
          <div><label className="etiket">Tarih</label><input className="input" name="tarih" type="date" value={form.tarih} onChange={d} /></div>
        </div>
        <div style={{ marginBottom: 16 }}>
          <label className="etiket">Açıklama</label>
          <input className="input" name="aciklama" value={form.aciklama} onChange={d} />
        </div>
        <div style={{ display: 'flex', gap: 10 }}>
          <button className="btn-yesil" type="submit" disabled={yukleniyor}>{yukleniyor ? 'Kaydediliyor...' : 'Kaydet'}</button>
          <button className="btn-gri" type="button" onClick={onIptal}>İptal</button>
        </div>
      </form>
    </div>
  );
}

export default function Muhasebe() {
  const [kayitlar, setKayitlar] = useState([]);
  const [ozet, setOzet] = useState({ gelir: 0, gider: 0, net: 0 });
  const [formAcik, setFormAcik] = useState(false);
  const [yukleniyor, setYuk] = useState(false);
  const [filtre, setFiltre] = useState('');

  const yukle = useCallback(async () => {
    setYuk(true);
    try {
      const [k, o] = await Promise.all([
        api.get('/api/panel/muhasebe/gelir-gider'),
        api.get('/api/panel/muhasebe/ozet'),
      ]);
      setKayitlar(k.data.kayitlar || []);
      setOzet(o.data);
    } catch {} finally { setYuk(false); }
  }, []);

  useEffect(() => { yukle(); }, [yukle]);

  const onKaydet = k => { setKayitlar(p => [k, ...p]); setFormAcik(false); yukle(); };

  const sil = async id => {
    if (!window.confirm('Bu kaydı silmek istediğinize emin misiniz?')) return;
    try { await api.delete(`/api/panel/muhasebe/gelir-gider/${id}`); setKayitlar(p => p.filter(x => x.id !== id)); yukle(); } catch {}
  };

  const liste = filtre ? kayitlar.filter(k => k.tip === filtre) : kayitlar;

  return (
    <>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
        <h1 style={{ fontSize: 20, fontWeight: 800, color: '#0f172a' }}>💰 Muhasebe</h1>
        <button className="btn-yesil" onClick={() => setFormAcik(p => !p)}>+ Ekle</button>
      </div>

      {/* Özet kartları */}
      <div className="grid-3" style={{ marginBottom: 16 }}>
        <div style={{ background: '#f0fdf4', borderRadius: 12, padding: 16, textAlign: 'center' }}>
          <div style={{ fontSize: 12, color: '#16a34a', fontWeight: 600 }}>Gelir</div>
          <div style={{ fontSize: 20, fontWeight: 800, color: '#16a34a' }}>{Number(ozet.gelir).toLocaleString('tr-TR')} TL</div>
        </div>
        <div style={{ background: '#fef2f2', borderRadius: 12, padding: 16, textAlign: 'center' }}>
          <div style={{ fontSize: 12, color: '#dc2626', fontWeight: 600 }}>Gider</div>
          <div style={{ fontSize: 20, fontWeight: 800, color: '#dc2626' }}>{Number(ozet.gider).toLocaleString('tr-TR')} TL</div>
        </div>
        <div style={{ background: ozet.net >= 0 ? '#f0fdf4' : '#fef2f2', borderRadius: 12, padding: 16, textAlign: 'center' }}>
          <div style={{ fontSize: 12, color: '#374151', fontWeight: 600 }}>Net</div>
          <div style={{ fontSize: 20, fontWeight: 800, color: ozet.net >= 0 ? '#16a34a' : '#dc2626' }}>{Number(ozet.net).toLocaleString('tr-TR')} TL</div>
        </div>
      </div>

      {formAcik && <GelirGiderFormu onKaydet={onKaydet} onIptal={() => setFormAcik(false)} />}

      {/* Filtre */}
      <div style={{ display: 'flex', gap: 8, marginBottom: 16 }}>
        {[['', 'Tümü'], ['gelir', '📈 Gelir'], ['gider', '📉 Gider']].map(([v, l]) => (
          <button key={v} onClick={() => setFiltre(v)} style={{
            padding: '6px 14px', borderRadius: 20, fontSize: 13, fontWeight: 600, cursor: 'pointer',
            background: filtre === v ? '#16a34a' : '#fff', color: filtre === v ? '#fff' : '#374151',
            border: `1px solid ${filtre === v ? '#16a34a' : '#e2e8f0'}`,
          }}>{l}</button>
        ))}
      </div>

      {yukleniyor ? (
        <div style={{ textAlign: 'center', color: '#94a3b8', padding: 40 }}>Yükleniyor…</div>
      ) : liste.length === 0 ? (
        <div style={{ textAlign: 'center', color: '#94a3b8', padding: 40, background: '#fff', borderRadius: 12 }}>
          <div style={{ fontSize: 32, marginBottom: 8 }}>💰</div>
          Henüz kayıt yok
        </div>
      ) : (
        liste.map(k => (
          <div key={k.id} style={{
            background: '#fff', borderRadius: 12, padding: '12px 16px', marginBottom: 8,
            border: '1px solid #e2e8f0', borderLeft: `3px solid ${k.tip === 'gelir' ? '#16a34a' : '#dc2626'}`,
            display: 'flex', justifyContent: 'space-between', alignItems: 'center',
          }}>
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 2 }}>
                <span style={{ fontWeight: 600, fontSize: 14, color: k.tip === 'gelir' ? '#16a34a' : '#dc2626' }}>
                  {k.tip === 'gelir' ? '+' : '-'}{Number(k.tutar).toLocaleString('tr-TR')} TL
                </span>
                {k.kategori && <span style={{ fontSize: 11, background: '#f1f5f9', borderRadius: 6, padding: '2px 8px', color: '#475569' }}>{k.kategori}</span>}
              </div>
              {k.aciklama && <div style={{ fontSize: 12, color: '#94a3b8' }}>{k.aciklama}</div>}
              <div style={{ fontSize: 11, color: '#cbd5e1', marginTop: 2 }}>{k.tarih ? new Date(k.tarih).toLocaleDateString('tr-TR') : ''}</div>
            </div>
            <button onClick={() => sil(k.id)} style={{ background: 'none', border: 'none', cursor: 'pointer', fontSize: 14, color: '#94a3b8' }}>🗑</button>
          </div>
        ))
      )}
    </>
  );
}
