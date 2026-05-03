import React, { useState, useEffect, useCallback } from 'react';
import api from '../api';

export default function Eslestirme() {
  const [talepler, setTalepler] = useState([]);
  const [secili, setSecili] = useState(null);
  const [eslesimler, setEslesimler] = useState([]);
  const [yuk, setYuk] = useState(true);

  const yukle = useCallback(async () => {
    setYuk(true);
    try {
      const r = await api.get('/api/panel/talepler?durum=aktif&yonu=arayan');
      setTalepler(r.data.talepler || []);
    } catch {} finally { setYuk(false); }
  }, []);

  useEffect(() => { yukle(); }, [yukle]);

  const eslesDir = async (talep) => {
    setSecili(talep);
    try {
      const r = await api.get(`/api/panel/eslestirme?talep_id=${talep.id}`);
      setEslesimler(r.data.eslesimler || []);
    } catch { setEslesimler([]); }
  };

  const f = v => v ? Number(v).toLocaleString('tr-TR') : '—';
  const puanRenk = p => p >= 60 ? '#16a34a' : p >= 30 ? '#f59e0b' : '#94a3b8';

  // Detay sayfası
  if (secili) {
    return (
      <>
        <button onClick={() => { setSecili(null); setEslesimler([]); }} className="btn-gri" style={{ marginBottom: 16, fontSize: 13 }}>← Taleplere Dön</button>

        <div style={{ background: '#eff6ff', borderRadius: 12, padding: 14, marginBottom: 16, border: '1px solid #bfdbfe' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <span style={{ fontWeight: 700, fontSize: 15, color: '#1d4ed8' }}>
              {secili.musteri_ad ? `👤 ${secili.musteri_ad}` : '👤 (isimsiz)'}
            </span>
            <span style={{ fontSize: 12, background: secili.islem_turu === 'kira' ? '#eff6ff' : '#fef3c7', color: secili.islem_turu === 'kira' ? '#2563eb' : '#d97706', padding: '2px 8px', borderRadius: 4 }}>
              {secili.islem_label}
            </span>
          </div>
          <div style={{ fontSize: 13, color: '#1e40af', marginTop: 6, display: 'flex', gap: 12, flexWrap: 'wrap' }}>
            {secili.butce_max && <span>💰 max {f(secili.butce_max)} TL</span>}
            {secili.tercih_oda && <span>🛏 {secili.tercih_oda}</span>}
            {secili.tercih_ilce && <span>📍 {secili.tercih_ilce}</span>}
            {secili.tercih_tip && <span>🏢 {secili.tercih_tip}</span>}
          </div>
          {(secili.istenen?.length > 0 || secili.istenmeyen?.length > 0) && (
            <div style={{ fontSize: 11, marginTop: 6, display: 'flex', gap: 4, flexWrap: 'wrap' }}>
              {secili.istenen?.map((o, i) => <span key={i} style={{ background: '#f0fdf4', color: '#16a34a', padding: '1px 6px', borderRadius: 4 }}>✅ {o}</span>)}
              {secili.istenmeyen?.map((o, i) => <span key={i} style={{ background: '#fef2f2', color: '#dc2626', padding: '1px 6px', borderRadius: 4 }}>❌ {o}</span>)}
            </div>
          )}
        </div>

        <div style={{ fontWeight: 700, fontSize: 14, marginBottom: 12 }}>🏢 Uygun Mülkler ({eslesimler.length})</div>

        {eslesimler.length === 0 ? (
          <div style={{ textAlign: 'center', color: '#94a3b8', padding: 40, background: 'var(--bg-card)', borderRadius: 12 }}>Uygun mülk bulunamadı</div>
        ) : (
          eslesimler.map((e, i) => (
            <div key={i} style={{
              background: 'var(--bg-card)', borderRadius: 10, padding: '12px 16px', marginBottom: 8,
              border: '1px solid var(--border)', borderLeft: `3px solid ${puanRenk(e.puan)}`,
            }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                <div style={{ flex: 1 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
                    <span style={{ fontWeight: 700, fontSize: 14 }}>{e.mulk_baslik}</span>
                    <span style={{ background: puanRenk(e.puan) + '20', color: puanRenk(e.puan), borderRadius: 6, padding: '2px 8px', fontSize: 12, fontWeight: 700 }}>%{e.puan}</span>
                  </div>
                  <div style={{ fontSize: 13, fontWeight: 600, color: '#374151' }}>💰 {e.mulk_fiyat} TL</div>
                  {e.nedenler?.length > 0 && (
                    <div style={{ display: 'flex', gap: 4, flexWrap: 'wrap', marginTop: 6 }}>
                      {e.nedenler.map((n, j) => (
                        <span key={j} style={{ fontSize: 10, background: n.startsWith('❌') ? '#fef2f2' : '#f0fdf4', border: `1px solid ${n.startsWith('❌') ? '#fecaca' : '#bbf7d0'}`, borderRadius: 4, padding: '1px 6px', color: n.startsWith('❌') ? '#dc2626' : '#16a34a' }}>{n}</span>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            </div>
          ))
        )}
      </>
    );
  }

  // Talep listesi
  return (
    <>
      <h1 style={{ fontSize: 20, fontWeight: 800, color: 'var(--text-primary)', marginBottom: 8 }}>🔗 Eşleştirme</h1>
      <p style={{ fontSize: 13, color: '#64748b', marginBottom: 16 }}>Talep seçin → uygun mülkler otomatik bulunur</p>

      {yuk ? (
        <div style={{ textAlign: 'center', padding: 40, color: '#94a3b8' }}>Yükleniyor...</div>
      ) : talepler.length === 0 ? (
        <div style={{ textAlign: 'center', padding: 40, color: '#94a3b8', background: 'var(--bg-card)', borderRadius: 12 }}>
          Aktif talep yok. Sohbetten veya Talepler sayfasından talep ekleyin.
        </div>
      ) : (
        talepler.map(t => (
          <div key={t.id} onClick={() => eslesDir(t)} style={{
            background: 'var(--bg-card)', borderRadius: 10, padding: '12px 16px', marginBottom: 8,
            border: '1px solid var(--border)', cursor: 'pointer',
            borderLeft: `3px solid ${t.islem_turu === 'kira' ? '#3b82f6' : '#f59e0b'}`,
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8, flex: 1, minWidth: 0 }}>
                <span style={{ fontWeight: 700, fontSize: 14, maxWidth: 150, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', display: 'inline-block' }}>
                  {t.musteri_ad || '(isimsiz)'}
                </span>
                <span style={{ fontSize: 12, color: t.islem_turu === 'kira' ? '#2563eb' : '#d97706' }}>
                  {t.islem_label}
                </span>
                {t.butce_max && <span style={{ fontSize: 12, color: '#374151' }}>· {f(t.butce_max)} TL</span>}
                {t.tercih_oda && <span style={{ fontSize: 12, color: '#64748b' }}>· {t.tercih_oda}</span>}
                {t.tercih_ilce && <span style={{ fontSize: 12, color: '#64748b' }}>· {t.tercih_ilce}</span>}
              </div>
              <span style={{ fontSize: 13, color: '#16a34a', fontWeight: 600, flexShrink: 0 }}>Eşleştir →</span>
            </div>
          </div>
        ))
      )}
    </>
  );
}
