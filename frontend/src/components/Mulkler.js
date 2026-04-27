import React, { useState, useEffect, useCallback } from 'react';
import Layout from './Layout';
import api from '../api';

function MulkFormu({ onKaydet, onIptal }) {
  const [form, setForm] = useState({ baslik: '', adres: '', sehir: '', ilce: '', tip: 'daire', islem_turu: 'kira', fiyat: '', metrekare: '', oda_sayisi: '', ada: '', parsel: '', notlar: '' });
  const [yukleniyor, setYuk] = useState(false);
  const d = e => setForm(p => ({ ...p, [e.target.name]: e.target.value }));

  const kaydet = async e => {
    e.preventDefault(); setYuk(true);
    try {
      const r = await api.post('/api/panel/mulkler', form);
      onKaydet(r.data.mulk);
    } catch { } finally { setYuk(false); }
  };

  return (
    <div style={{ background: '#fff', borderRadius: 12, padding: 20, marginBottom: 16, border: '1px solid #e2e8f0' }}>
      <div style={{ fontWeight: 700, fontSize: 15, color: '#1e293b', marginBottom: 16 }}>Yeni Mülk</div>
      <form onSubmit={kaydet}>
        <div style={{ marginBottom: 12 }}>
          <label className="etiket">Başlık</label>
          <input className="input" name="baslik" value={form.baslik} onChange={d} placeholder="Kadıköy 3+1 Kiralık Daire" />
        </div>
        <div style={{ marginBottom: 12 }}>
          <label className="etiket">Adres</label>
          <input className="input" name="adres" value={form.adres} onChange={d} />
        </div>
        <div className="grid-2" style={{ marginBottom: 12 }}>
          <div><label className="etiket">Şehir</label><input className="input" name="sehir" value={form.sehir} onChange={d} /></div>
          <div><label className="etiket">İlçe</label><input className="input" name="ilce" value={form.ilce} onChange={d} /></div>
        </div>
        <div className="grid-2" style={{ marginBottom: 12 }}>
          <div>
            <label className="etiket">Tip</label>
            <select className="input" name="tip" value={form.tip} onChange={d}>
              <option value="daire">Daire</option>
              <option value="villa">Villa</option>
              <option value="arsa">Arsa</option>
              <option value="dukkan">Dükkan</option>
              <option value="ofis">Ofis</option>
            </select>
          </div>
          <div>
            <label className="etiket">İşlem Türü</label>
            <select className="input" name="islem_turu" value={form.islem_turu} onChange={d}>
              <option value="kira">Kiralık</option>
              <option value="satis">Satılık</option>
            </select>
          </div>
        </div>
        <div className="grid-2" style={{ marginBottom: 12 }}>
          <div><label className="etiket">Fiyat (TL)</label><input className="input" name="fiyat" type="number" value={form.fiyat} onChange={d} /></div>
          <div><label className="etiket">m²</label><input className="input" name="metrekare" type="number" value={form.metrekare} onChange={d} /></div>
        </div>
        <div className="grid-2" style={{ marginBottom: 12 }}>
          <div><label className="etiket">Oda Sayısı</label><input className="input" name="oda_sayisi" value={form.oda_sayisi} onChange={d} placeholder="3+1" /></div>
          <div><label className="etiket">Ada/Parsel</label>
            <div style={{ display: 'flex', gap: 6 }}>
              <input className="input" name="ada" value={form.ada} onChange={d} placeholder="Ada" />
              <input className="input" name="parsel" value={form.parsel} onChange={d} placeholder="Parsel" />
            </div>
          </div>
        </div>
        <div style={{ marginBottom: 16 }}>
          <label className="etiket">Notlar</label>
          <textarea className="input" name="notlar" value={form.notlar} onChange={d} rows={2} style={{ resize: 'vertical' }} />
        </div>
        <div style={{ display: 'flex', gap: 10 }}>
          <button className="btn-yesil" type="submit" disabled={yukleniyor}>{yukleniyor ? 'Kaydediliyor...' : 'Kaydet'}</button>
          <button className="btn-gri" type="button" onClick={onIptal}>İptal</button>
        </div>
      </form>
    </div>
  );
}

function MulkKarti({ m }) {
  const renk = m.islem_turu === 'kira' ? '#3b82f6' : '#f59e0b';
  return (
    <div style={{ background: '#fff', borderRadius: 12, padding: '14px 16px', marginBottom: 10, border: '1px solid #e2e8f0', borderLeft: `3px solid ${renk}` }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 6, flexWrap: 'wrap' }}>
        <span style={{ fontWeight: 700, fontSize: 15, color: '#0f172a' }}>{m.baslik || m.adres || '—'}</span>
        <span style={{ background: m.islem_turu === 'kira' ? '#eff6ff' : '#fef3c7', color: renk, borderRadius: 6, padding: '2px 8px', fontSize: 11, fontWeight: 700 }}>
          {m.islem_turu === 'kira' ? 'Kiralık' : 'Satılık'}
        </span>
      </div>
      {m.adres && <div style={{ fontSize: 13, color: '#64748b' }}>📍 {m.adres}</div>}
      <div style={{ display: 'flex', gap: 12, marginTop: 6, flexWrap: 'wrap' }}>
        {m.fiyat && <span style={{ fontSize: 13, color: '#374151', fontWeight: 600 }}>💰 {Number(m.fiyat).toLocaleString('tr-TR')} TL</span>}
        {m.metrekare && <span style={{ fontSize: 13, color: '#64748b' }}>{m.metrekare} m²</span>}
        {m.oda_sayisi && <span style={{ fontSize: 13, color: '#64748b' }}>{m.oda_sayisi}</span>}
      </div>
    </div>
  );
}

export default function Mulkler() {
  const [mulkler, setMulkler] = useState([]);
  const [formAcik, setFormAcik] = useState(false);
  const [yukleniyor, setYuk]   = useState(false);

  const yukle = useCallback(async () => {
    setYuk(true);
    try { const r = await api.get('/api/panel/mulkler'); setMulkler(r.data.mulkler || []); }
    catch { } finally { setYuk(false); }
  }, []);

  useEffect(() => { yukle(); }, [yukle]);

  return (
    <Layout>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
        <h1 style={{ fontSize: 20, fontWeight: 800, color: '#0f172a' }}>🏢 Portföy</h1>
        <button className="btn-yesil" onClick={() => setFormAcik(p => !p)}>+ Ekle</button>
      </div>

      {formAcik && <MulkFormu onKaydet={m => { setMulkler(p => [m, ...p]); setFormAcik(false); }} onIptal={() => setFormAcik(false)} />}

      {yukleniyor ? (
        <div style={{ textAlign: 'center', color: '#94a3b8', padding: 40 }}>Yükleniyor…</div>
      ) : mulkler.length === 0 ? (
        <div style={{ textAlign: 'center', color: '#94a3b8', padding: 40, background: '#fff', borderRadius: 12 }}>
          <div style={{ fontSize: 32, marginBottom: 8 }}>🏢</div>
          Henüz mülk eklenmedi
        </div>
      ) : (
        mulkler.map(m => <MulkKarti key={m.id} m={m} />)
      )}
    </Layout>
  );
}
