import React, { useState, useEffect, useCallback } from 'react';
import api from '../api';

const ETIKETLER = {
  not: { ikon: '📝', ad: 'Not', renk: '#3b82f6' },
  hatirlatici: { ikon: '🧠', ad: 'Hatırlatma', renk: '#f59e0b' },
  gosterim: { ikon: '🏠', ad: 'Gösterim', renk: '#16a34a' },
  onemli: { ikon: '⭐', ad: 'Önemli', renk: '#f59e0b' },
  acil: { ikon: '🔴', ad: 'Acil', renk: '#dc2626' },
  sesli_not: { ikon: '🎤', ad: 'Sesli Not', renk: '#8b5cf6' },
};

export default function Notlar() {
  const [notlar, setNotlar] = useState([]);
  const [formAcik, setFormAcik] = useState(false);
  const [form, setForm] = useState({ icerik: '', etiket: 'not' });
  const [filtre, setFiltre] = useState('');
  const [arama, setArama] = useState('');
  const [tamamlananGoster, setTamamlananGoster] = useState(false);
  const [yuk, setYuk] = useState(false);
  const [duzenle, setDuzenle] = useState(null);

  const yukle = useCallback(async () => {
    setYuk(true);
    try {
      const params = new URLSearchParams();
      if (filtre) params.set('etiket', filtre);
      if (arama) params.set('arama', arama);
      if (tamamlananGoster) params.set('tamamlandi', 'true');
      const r = await api.get(`/api/panel/notlar?${params}`);
      setNotlar(r.data.notlar || []);
    } catch {} finally { setYuk(false); }
  }, [filtre, arama, tamamlananGoster]);

  useEffect(() => { yukle(); }, [yukle]);

  const kaydet = async () => {
    if (!form.icerik.trim()) return;
    try {
      if (duzenle) {
        await api.put(`/api/panel/notlar/${duzenle.id}`, form);
      } else {
        await api.post('/api/panel/notlar', form);
      }
      setForm({ icerik: '', etiket: 'not' }); setFormAcik(false); setDuzenle(null); yukle();
    } catch {}
  };

  const sil = async (id) => {
    if (!window.confirm('Bu notu silmek istediğinize emin misiniz?')) return;
    try { await api.delete(`/api/panel/notlar/${id}`); yukle(); } catch {}
  };

  const tamamla = async (id, durum) => {
    try { await api.put(`/api/panel/notlar/${id}`, { tamamlandi: durum }); yukle(); } catch {}
  };

  const goreveDonustur = async (id) => {
    try {
      const r = await api.post(`/api/panel/notlar/${id}/goreve-donustur`);
      alert(r.data.mesaj || 'Göreve dönüştürüldü');
      yukle();
    } catch {}
  };

  return (
    <>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
        <h1 style={{ fontSize: 20, fontWeight: 800, color: 'var(--text-primary)' }}>📝 Notlar</h1>
        <button className="btn-yesil" onClick={() => { setDuzenle(null); setForm({ icerik: '', etiket: 'not' }); setFormAcik(p => !p); }}>+ Not Ekle</button>
      </div>

      {/* Arama */}
      <input className="input" placeholder="🔍 Notlarda ara..." value={arama} onChange={e => setArama(e.target.value)} style={{ width: '100%', marginBottom: 12 }} />

      {/* Filtreler */}
      <div style={{ display: 'flex', gap: 6, marginBottom: 16, flexWrap: 'wrap', alignItems: 'center' }}>
        {[['', 'Tümü'], ['not', '📝 Not'], ['hatirlatici', '🧠 Hatırlatma'], ['gosterim', '🏠 Gösterim'], ['onemli', '⭐ Önemli'], ['acil', '🔴 Acil'], ['sesli_not', '🎤 Sesli']].map(([k, v]) => (
          <button key={k} onClick={() => setFiltre(k)} style={{
            padding: '5px 12px', borderRadius: 16, fontSize: 12, cursor: 'pointer',
            background: filtre === k ? '#16a34a' : 'var(--bg-card)', color: filtre === k ? '#fff' : 'var(--text-primary)',
            border: `1px solid ${filtre === k ? '#16a34a' : 'var(--border)'}`,
          }}>{v}</button>
        ))}
        <span style={{ color: 'var(--border)' }}>|</span>
        <button onClick={() => setTamamlananGoster(p => !p)} style={{
          padding: '5px 12px', borderRadius: 16, fontSize: 12, cursor: 'pointer',
          background: tamamlananGoster ? '#f0fdf4' : 'var(--bg-card)', color: tamamlananGoster ? '#16a34a' : '#94a3b8',
          border: `1px solid ${tamamlananGoster ? '#bbf7d0' : 'var(--border)'}`,
        }}>{tamamlananGoster ? '✅ Tamamlananlar' : '📌 Aktifler'}</button>
      </div>

      {/* Form */}
      {formAcik && (
        <div style={{ background: 'var(--bg-card)', borderRadius: 12, padding: 16, marginBottom: 16, border: '1px solid var(--border)' }}>
          <textarea className="input" value={form.icerik} onChange={e => setForm(p => ({ ...p, icerik: e.target.value }))}
            rows={3} style={{ resize: 'vertical', width: '100%', marginBottom: 8 }} placeholder="Notunuzu yazın..." autoFocus />
          <div style={{ display: 'flex', gap: 6, marginBottom: 12, flexWrap: 'wrap' }}>
            {Object.entries(ETIKETLER).map(([k, v]) => (
              <button key={k} onClick={() => setForm(p => ({ ...p, etiket: k }))} style={{
                padding: '4px 10px', borderRadius: 6, fontSize: 11, cursor: 'pointer',
                background: form.etiket === k ? v.renk : 'var(--bg-card)', color: form.etiket === k ? '#fff' : 'var(--text-primary)',
                border: `1px solid ${form.etiket === k ? v.renk : 'var(--border)'}`,
              }}>{v.ikon} {v.ad}</button>
            ))}
          </div>
          <div style={{ display: 'flex', gap: 8 }}>
            <button className="btn-yesil" onClick={kaydet} style={{ fontSize: 13 }}>{duzenle ? 'Güncelle' : 'Kaydet'}</button>
            <button className="btn-gri" onClick={() => { setFormAcik(false); setDuzenle(null); }} style={{ fontSize: 13 }}>İptal</button>
          </div>
        </div>
      )}

      {/* Not Listesi */}
      {yuk ? (
        <div style={{ textAlign: 'center', color: '#94a3b8', padding: 40 }}>Yükleniyor...</div>
      ) : notlar.length === 0 ? (
        <div style={{ textAlign: 'center', color: '#94a3b8', padding: 40, background: 'var(--bg-card)', borderRadius: 12 }}>
          {arama ? 'Aramayla eşleşen not yok' : 'Henüz not eklenmedi'}
        </div>
      ) : (
        notlar.map(n => {
          const e = ETIKETLER[n.etiket] || ETIKETLER.not;
          return (
            <div key={n.id} style={{
              background: 'var(--bg-card)', borderRadius: 12, padding: '12px 16px', marginBottom: 8,
              border: '1px solid var(--border)', borderLeft: `3px solid ${e.renk}`,
              opacity: n.tamamlandi ? 0.5 : 1,
            }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                <div style={{ flex: 1 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 4 }}>
                    <button onClick={() => tamamla(n.id, !n.tamamlandi)} style={{
                      width: 18, height: 18, borderRadius: 4, border: `2px solid ${e.renk}`,
                      background: n.tamamlandi ? e.renk : 'transparent', cursor: 'pointer',
                      display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#fff', fontSize: 10, flexShrink: 0,
                    }}>{n.tamamlandi ? '✓' : ''}</button>
                    <span style={{ fontSize: 11, background: `${e.renk}15`, color: e.renk, padding: '1px 8px', borderRadius: 4 }}>{e.ikon} {e.ad}</span>
                    {n.musteri_ad && <span style={{ fontSize: 11, color: '#64748b' }}>👤 {n.musteri_ad}</span>}
                    {n.mulk_ad && <span style={{ fontSize: 11, color: '#64748b' }}>🏢 {n.mulk_ad}</span>}
                  </div>
                  <div style={{ fontSize: 13, color: 'var(--text-primary)', lineHeight: 1.5, textDecoration: n.tamamlandi ? 'line-through' : 'none' }}>
                    {n.icerik}
                  </div>
                  <div style={{ fontSize: 11, color: '#94a3b8', marginTop: 4 }}>
                    {n.olusturma && new Date(n.olusturma).toLocaleString('tr-TR', { day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit' })}
                    {n.hatirlatma && ` · ⏰ ${new Date(n.hatirlatma).toLocaleString('tr-TR', { day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit' })}`}
                  </div>
                </div>
                <div style={{ display: 'flex', gap: 4, flexShrink: 0 }}>
                  <button onClick={() => goreveDonustur(n.id)} title="Göreve dönüştür" style={{ background: 'none', border: 'none', cursor: 'pointer', fontSize: 14, color: '#16a34a' }}>📌</button>
                  <button onClick={() => { setDuzenle(n); setForm({ icerik: n.icerik, etiket: n.etiket }); setFormAcik(true); }} title="Düzenle" style={{ background: 'none', border: 'none', cursor: 'pointer', fontSize: 14, color: '#3b82f6' }}>✏️</button>
                  <button onClick={() => sil(n.id)} title="Sil" style={{ background: 'none', border: 'none', cursor: 'pointer', fontSize: 14, color: '#dc2626' }}>🗑</button>
                </div>
              </div>
            </div>
          );
        })
      )}
    </>
  );
}
