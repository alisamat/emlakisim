import React, { useState, useEffect, useCallback } from 'react';
import api from '../api';

const SICAKLIK = { sicak: { label: '🔥 Sıcak', renk: '#dc2626', bg: '#fef2f2' }, orta: { label: '🌤 Orta', renk: '#f59e0b', bg: '#fffbeb' }, soguk: { label: '❄️ Soğuk', renk: '#3b82f6', bg: '#eff6ff' } };

function MusteriFormu({ onKaydet, onIptal }) {
  const [form, setForm] = useState({ ad_soyad: '', telefon: '', tc_kimlik: '', islem_turu: 'kira', butce_min: '', butce_max: '', tercih_notlar: '', sicaklik: 'orta' });
  const [yukleniyor, setYuk] = useState(false);
  const d = e => setForm(p => ({ ...p, [e.target.name]: e.target.value }));

  const kaydet = async e => {
    e.preventDefault(); setYuk(true);
    try {
      const r = await api.post('/api/panel/musteriler', form);
      onKaydet(r.data.musteri);
    } catch { } finally { setYuk(false); }
  };

  return (
    <div style={{ background: '#fff', borderRadius: 12, padding: 20, marginBottom: 16, border: '1px solid #e2e8f0' }}>
      <div style={{ fontWeight: 700, fontSize: 15, color: '#1e293b', marginBottom: 16 }}>Yeni Müşteri</div>
      <form onSubmit={kaydet}>
        <div className="grid-2" style={{ marginBottom: 12 }}>
          <div><label className="etiket">Ad Soyad *</label><input className="input" name="ad_soyad" value={form.ad_soyad} onChange={d} required /></div>
          <div><label className="etiket">Telefon</label><input className="input" name="telefon" value={form.telefon} onChange={d} /></div>
        </div>
        <div className="grid-2" style={{ marginBottom: 12 }}>
          <div><label className="etiket">TC Kimlik</label><input className="input" name="tc_kimlik" value={form.tc_kimlik} onChange={d} maxLength={11} /></div>
          <div>
            <label className="etiket">İşlem Türü</label>
            <select className="input" name="islem_turu" value={form.islem_turu} onChange={d}>
              <option value="kira">Kiralama</option>
              <option value="satis">Satış</option>
            </select>
          </div>
        </div>
        <div className="grid-2" style={{ marginBottom: 12 }}>
          <div><label className="etiket">Min Bütçe (TL)</label><input className="input" name="butce_min" type="number" value={form.butce_min} onChange={d} /></div>
          <div><label className="etiket">Max Bütçe (TL)</label><input className="input" name="butce_max" type="number" value={form.butce_max} onChange={d} /></div>
        </div>
        <div style={{ marginBottom: 12 }}>
          <label className="etiket">Tercihler / Notlar</label>
          <textarea className="input" name="tercih_notlar" value={form.tercih_notlar} onChange={d} rows={2} style={{ resize: 'vertical' }} />
        </div>
        <div style={{ marginBottom: 16 }}>
          <label className="etiket">Sıcaklık</label>
          <select className="input" name="sicaklik" value={form.sicaklik} onChange={d}>
            <option value="sicak">🔥 Sıcak</option>
            <option value="orta">🌤 Orta</option>
            <option value="soguk">❄️ Soğuk</option>
          </select>
        </div>
        <div style={{ display: 'flex', gap: 10 }}>
          <button className="btn-yesil" type="submit" disabled={yukleniyor}>{yukleniyor ? 'Kaydediliyor...' : 'Kaydet'}</button>
          <button className="btn-gri" type="button" onClick={onIptal}>İptal</button>
        </div>
      </form>
    </div>
  );
}

function MusteriKarti({ m }) {
  const s = SICAKLIK[m.sicaklik] || SICAKLIK.orta;
  return (
    <div style={{ background: '#fff', borderRadius: 12, padding: '14px 16px', marginBottom: 10, border: '1px solid #e2e8f0', borderLeft: `3px solid ${s.renk}` }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div style={{ flex: 1 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4, flexWrap: 'wrap' }}>
            <span style={{ fontWeight: 700, fontSize: 15, color: '#0f172a' }}>{m.ad_soyad}</span>
            <span style={{ background: s.bg, color: s.renk, borderRadius: 6, padding: '2px 8px', fontSize: 11, fontWeight: 700 }}>{s.label}</span>
            <span style={{ background: m.islem_turu === 'kira' ? '#eff6ff' : '#fef3c7', color: m.islem_turu === 'kira' ? '#1d4ed8' : '#92400e', borderRadius: 6, padding: '2px 8px', fontSize: 11, fontWeight: 600 }}>
              {m.islem_turu === 'kira' ? 'Kiralık' : 'Satılık'}
            </span>
          </div>
          {m.telefon && <div style={{ fontSize: 13, color: '#64748b' }}>📞 {m.telefon}</div>}
          {(m.butce_min || m.butce_max) && (
            <div style={{ fontSize: 13, color: '#64748b', marginTop: 2 }}>
              💰 {m.butce_min ? Number(m.butce_min).toLocaleString('tr-TR') : '—'} — {m.butce_max ? Number(m.butce_max).toLocaleString('tr-TR') : '—'} TL
            </div>
          )}
          {m.tercih_notlar && <div style={{ fontSize: 13, color: '#94a3b8', marginTop: 4 }}>{m.tercih_notlar}</div>}
        </div>
      </div>
    </div>
  );
}

export default function Musteriler() {
  const [musteriler, setMusteriler] = useState([]);
  const [formAcik, setFormAcik]     = useState(false);
  const [yukleniyor, setYuk]        = useState(false);
  const [filtre, setFiltre]         = useState('');

  const yukle = useCallback(async () => {
    setYuk(true);
    try {
      const r = await api.get('/api/panel/musteriler');
      setMusteriler(r.data.musteriler || []);
    } catch { } finally { setYuk(false); }
  }, []);

  useEffect(() => { yukle(); }, [yukle]);

  const onKaydet = m => { setMusteriler(p => [m, ...p]); setFormAcik(false); };

  const liste = filtre ? musteriler.filter(m => m.sicaklik === filtre) : musteriler;

  return (
    <>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
        <h1 style={{ fontSize: 20, fontWeight: 800, color: '#0f172a' }}>👥 Müşteriler</h1>
        <button className="btn-yesil" onClick={() => setFormAcik(p => !p)}>+ Ekle</button>
      </div>

      {formAcik && <MusteriFormu onKaydet={onKaydet} onIptal={() => setFormAcik(false)} />}

      {/* Filtre */}
      <div style={{ display: 'flex', gap: 8, marginBottom: 16, flexWrap: 'wrap' }}>
        {[['', 'Tümü'], ['sicak', '🔥 Sıcak'], ['orta', '🌤 Orta'], ['soguk', '❄️ Soğuk']].map(([v, l]) => (
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
          <div style={{ fontSize: 32, marginBottom: 8 }}>👥</div>
          {filtre ? 'Bu filtrede müşteri yok' : 'Henüz müşteri eklenmedi'}
        </div>
      ) : (
        liste.map(m => <MusteriKarti key={m.id} m={m} />)
      )}
    </>
  );
}
