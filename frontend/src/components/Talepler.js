import React, { useState, useEffect, useCallback } from 'react';
import api from '../api';

export default function Talepler() {
  const [talepler, setTalepler] = useState([]);
  const [musteriler, setMusteriler] = useState([]);
  const [formAcik, setFormAcik] = useState(false);
  const [form, setForm] = useState({ yonu: 'arayan', islem_turu: 'kira', musteri_id: '', butce_max: '', tercih_oda: '', tercih_ilce: '', notlar: '' });
  const [filtreYon, setFiltreYon] = useState('');
  const [filtreIslem, setFiltreIslem] = useState('');
  const [yuk, setYuk] = useState(true);

  const yukle = useCallback(async () => {
    setYuk(true);
    try {
      const params = new URLSearchParams();
      if (filtreYon) params.set('yonu', filtreYon);
      if (filtreIslem) params.set('islem', filtreIslem);
      params.set('durum', 'aktif');
      const [t, m] = await Promise.all([
        api.get(`/api/panel/talepler?${params}`),
        api.get('/api/panel/musteriler'),
      ]);
      setTalepler(t.data.talepler || []);
      setMusteriler(m.data.musteriler || []);
    } catch {} finally { setYuk(false); }
  }, [filtreYon, filtreIslem]);

  useEffect(() => { yukle(); }, [yukle]);

  const kaydet = async () => {
    try {
      await api.post('/api/panel/talepler', {
        ...form,
        musteri_id: form.musteri_id ? parseInt(form.musteri_id) : null,
        butce_max: form.butce_max ? parseFloat(form.butce_max) : null,
      });
      setFormAcik(false);
      setForm({ yonu: 'arayan', islem_turu: 'kira', musteri_id: '', butce_max: '', tercih_oda: '', tercih_ilce: '', notlar: '' });
      yukle();
    } catch {}
  };

  const sil = async (id) => {
    if (!window.confirm('Bu talebi silmek istediğinize emin misiniz?')) return;
    try { await api.delete(`/api/panel/talepler/${id}`); yukle(); } catch {}
  };

  const durumDegistir = async (id, durum) => {
    try { await api.put(`/api/panel/talepler/${id}`, { durum }); yukle(); } catch {}
  };

  const f = v => v ? Number(v).toLocaleString('tr-TR') : '—';

  return (
    <>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
        <h1 style={{ fontSize: 20, fontWeight: 800, color: 'var(--text-primary)' }}>📋 Talepler</h1>
        <button className="btn-yesil" onClick={() => setFormAcik(p => !p)}>+ Talep Ekle</button>
      </div>

      {/* Filtreler */}
      <div style={{ display: 'flex', gap: 6, marginBottom: 16, flexWrap: 'wrap' }}>
        {[['', 'Tümü'], ['arayan', '🔍 Arayanlar'], ['veren', '🏠 Verenler']].map(([v, l]) => (
          <button key={v} onClick={() => setFiltreYon(v)} style={{
            padding: '5px 12px', borderRadius: 16, fontSize: 12, cursor: 'pointer',
            background: filtreYon === v ? '#16a34a' : 'var(--bg-card)', color: filtreYon === v ? '#fff' : 'var(--text-primary)',
            border: `1px solid ${filtreYon === v ? '#16a34a' : 'var(--border)'}`,
          }}>{l}</button>
        ))}
        <span style={{ color: 'var(--border)' }}>|</span>
        {[['', 'Hepsi'], ['kira', '🔵 Kiralık'], ['satis', '🟡 Satılık']].map(([v, l]) => (
          <button key={v} onClick={() => setFiltreIslem(v)} style={{
            padding: '5px 12px', borderRadius: 16, fontSize: 12, cursor: 'pointer',
            background: filtreIslem === v ? '#475569' : 'var(--bg-card)', color: filtreIslem === v ? '#fff' : 'var(--text-primary)',
            border: `1px solid ${filtreIslem === v ? '#475569' : 'var(--border)'}`,
          }}>{l}</button>
        ))}
      </div>

      {/* Form */}
      {formAcik && (
        <div style={{ background: 'var(--bg-card)', borderRadius: 12, padding: 16, marginBottom: 16, border: '1px solid var(--border)' }}>
          <div className="grid-2" style={{ marginBottom: 10 }}>
            <div>
              <label className="etiket">Yön</label>
              <select className="input" value={form.yonu} onChange={e => setForm(p => ({ ...p, yonu: e.target.value }))}>
                <option value="arayan">🔍 Arıyor (alıcı/kiracı)</option>
                <option value="veren">🏠 Veriyor (satıcı/ev sahibi)</option>
              </select>
            </div>
            <div>
              <label className="etiket">İşlem Türü</label>
              <select className="input" value={form.islem_turu} onChange={e => setForm(p => ({ ...p, islem_turu: e.target.value }))}>
                <option value="kira">Kiralık</option>
                <option value="satis">Satılık</option>
              </select>
            </div>
          </div>
          <div className="grid-2" style={{ marginBottom: 10 }}>
            <div>
              <label className="etiket">Müşteri (opsiyonel)</label>
              <select className="input" value={form.musteri_id} onChange={e => setForm(p => ({ ...p, musteri_id: e.target.value }))}>
                <option value="">— İsimsiz —</option>
                {musteriler.map(m => (
                  <option key={m.id} value={m.id}>{m.ad_soyad}{m.kunye ? ` (${m.kunye})` : ''}</option>
                ))}
              </select>
            </div>
            <div><label className="etiket">Max Bütçe (TL)</label><input className="input" type="number" value={form.butce_max} onChange={e => setForm(p => ({ ...p, butce_max: e.target.value }))} /></div>
          </div>
          <div className="grid-2" style={{ marginBottom: 10 }}>
            <div><label className="etiket">Oda Sayısı</label><input className="input" value={form.tercih_oda} onChange={e => setForm(p => ({ ...p, tercih_oda: e.target.value }))} placeholder="2+1" /></div>
            <div><label className="etiket">İlçe</label><input className="input" value={form.tercih_ilce} onChange={e => setForm(p => ({ ...p, tercih_ilce: e.target.value }))} /></div>
          </div>
          <div style={{ marginBottom: 10 }}>
            <label className="etiket">Notlar</label>
            <textarea className="input" value={form.notlar} onChange={e => setForm(p => ({ ...p, notlar: e.target.value }))} rows={2} style={{ resize: 'vertical' }} placeholder="Ek tercihler, açık mutfak istemiyor vb." />
          </div>
          <div style={{ display: 'flex', gap: 8 }}>
            <button className="btn-yesil" onClick={kaydet} style={{ fontSize: 13 }}>Kaydet</button>
            <button className="btn-gri" onClick={() => setFormAcik(false)} style={{ fontSize: 13 }}>İptal</button>
          </div>
        </div>
      )}

      {/* Liste */}
      {yuk ? (
        <div style={{ textAlign: 'center', padding: 40, color: '#94a3b8' }}>Yükleniyor...</div>
      ) : talepler.length === 0 ? (
        <div style={{ textAlign: 'center', padding: 40, color: '#94a3b8', background: 'var(--bg-card)', borderRadius: 12 }}>
          Talep yok. Sohbetten veya yukarıdaki butonla talep ekleyebilirsiniz.
        </div>
      ) : (
        talepler.map(t => {
          const yonIkon = t.yonu === 'arayan' ? '🔍' : '🏠';
          const renk = t.islem_turu === 'kira' ? '#3b82f6' : '#f59e0b';
          return (
            <div key={t.id} style={{
              background: 'var(--bg-card)', borderRadius: 10, padding: '12px 16px', marginBottom: 8,
              border: '1px solid var(--border)', borderLeft: `3px solid ${renk}`,
            }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                <div style={{ flex: 1 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 4, flexWrap: 'wrap' }}>
                    <span style={{ fontSize: 16 }}>{yonIkon}</span>
                    <span style={{ fontWeight: 700, fontSize: 14 }}>{t.yon_label} · {t.islem_label}</span>
                    {t.musteri_ad && <span style={{ fontSize: 12, color: '#64748b' }}>👤 {t.musteri_ad}</span>}
                    {!t.musteri_id && <span style={{ fontSize: 11, color: '#f59e0b', background: '#fef3c7', padding: '1px 6px', borderRadius: 4 }}>isimsiz</span>}
                  </div>
                  <div style={{ display: 'flex', gap: 12, fontSize: 13, color: '#374151', flexWrap: 'wrap' }}>
                    {t.butce_max && <span>💰 max {f(t.butce_max)} TL</span>}
                    {t.tercih_oda && <span>🛏 {t.tercih_oda}</span>}
                    {t.tercih_ilce && <span>📍 {t.tercih_ilce}</span>}
                    {t.tercih_tip && <span>🏢 {t.tercih_tip}</span>}
                  </div>
                  {(t.istenen?.length > 0 || t.istenmeyen?.length > 0) && (
                    <div style={{ fontSize: 11, marginTop: 4, display: 'flex', gap: 6, flexWrap: 'wrap' }}>
                      {t.istenen?.map((o, i) => <span key={i} style={{ background: '#f0fdf4', color: '#16a34a', padding: '1px 6px', borderRadius: 4 }}>✅ {o}</span>)}
                      {t.istenmeyen?.map((o, i) => <span key={i} style={{ background: '#fef2f2', color: '#dc2626', padding: '1px 6px', borderRadius: 4 }}>❌ {o}</span>)}
                    </div>
                  )}
                  {t.notlar && <div style={{ fontSize: 12, color: '#94a3b8', marginTop: 4 }}>{t.notlar}</div>}
                  {t.mulk_ad && <div style={{ fontSize: 12, color: '#16a34a', marginTop: 4 }}>🏢 {t.mulk_ad}</div>}
                </div>
                <div style={{ display: 'flex', gap: 4, flexShrink: 0 }}>
                  {t.durum === 'aktif' && <button onClick={() => durumDegistir(t.id, 'tamamlandi')} title="Tamamlandı" style={{ background: 'none', border: 'none', cursor: 'pointer', fontSize: 14 }}>✅</button>}
                  {t.durum === 'tamamlandi' && <button onClick={() => durumDegistir(t.id, 'aktif')} title="Aktif yap" style={{ background: 'none', border: 'none', cursor: 'pointer', fontSize: 14 }}>🔄</button>}
                  <button onClick={() => sil(t.id)} title="Sil" style={{ background: 'none', border: 'none', cursor: 'pointer', fontSize: 14, color: '#dc2626' }}>🗑</button>
                </div>
              </div>
            </div>
          );
        })
      )}
    </>
  );
}
