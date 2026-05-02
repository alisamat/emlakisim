import React, { useState, useEffect } from 'react';
import api from '../api';

export default function IsiHaritasi() {
  const [harita, setHarita] = useState([]);
  const [tahminler, setTahminler] = useState([]);
  const [tab, setTab] = useState('harita');
  const [yuk, setYuk] = useState(true);

  useEffect(() => {
    Promise.all([
      api.get('/api/panel/isi-haritasi'),
      api.get('/api/panel/tahmin/satici'),
    ]).then(([h, t]) => {
      setHarita(h.data.harita || []);
      setTahminler(t.data.tahminler || []);
    }).catch(() => {}).finally(() => setYuk(false));
  }, []);

  const f = (v) => v ? Number(v).toLocaleString('tr-TR') : '—';
  const isiRenk = (skor) => skor >= 70 ? '#dc2626' : skor >= 50 ? '#f59e0b' : skor >= 30 ? '#3b82f6' : '#94a3b8';

  if (yuk) return <div style={{ textAlign: 'center', padding: 40, color: '#94a3b8' }}>Yükleniyor...</div>;

  return (
    <>
      <h1 style={{ fontSize: 20, fontWeight: 800, color: 'var(--text-primary)', marginBottom: 16 }}>🗺 Piyasa Analizi & Tahmin</h1>

      <div style={{ display: 'flex', gap: 8, marginBottom: 16 }}>
        {[['harita', '🗺 Isı Haritası'], ['tahmin', '🔮 Satıcı Tahmin']].map(([k, v]) => (
          <button key={k} onClick={() => setTab(k)} style={{
            padding: '8px 16px', borderRadius: 8, fontSize: 13, cursor: 'pointer',
            background: tab === k ? '#16a34a' : 'var(--bg-card)', color: tab === k ? '#fff' : 'var(--text-primary)',
            border: `1px solid ${tab === k ? '#16a34a' : 'var(--border)'}`,
          }}>{v}</button>
        ))}
      </div>

      {tab === 'harita' && (
        <div style={{ background: 'var(--bg-card)', borderRadius: 12, padding: 16, border: '1px solid var(--border)' }}>
          {harita.length === 0 ? (
            <div style={{ textAlign: 'center', padding: 30, color: '#94a3b8' }}>Portföyünüze mülk ekleyin — harita otomatik oluşsun</div>
          ) : (
            <div style={{ overflowX: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
                <thead>
                  <tr style={{ borderBottom: '2px solid var(--border)', textAlign: 'left' }}>
                    <th style={{ padding: 8 }}>İlçe</th>
                    <th style={{ padding: 8, textAlign: 'center' }}>Isı</th>
                    <th style={{ padding: 8, textAlign: 'right' }}>Mülk</th>
                    <th style={{ padding: 8, textAlign: 'right' }}>Talep</th>
                    <th style={{ padding: 8, textAlign: 'right' }}>Ort. Satış</th>
                    <th style={{ padding: 8, textAlign: 'right' }}>Ort. Kira</th>
                    <th style={{ padding: 8, textAlign: 'right' }}>m² Fiyat</th>
                    <th style={{ padding: 8, textAlign: 'right' }}>Getiri</th>
                  </tr>
                </thead>
                <tbody>
                  {harita.map((h, i) => (
                    <tr key={i} style={{ borderBottom: '1px solid var(--border-light, #f1f5f9)' }}>
                      <td style={{ padding: 8, fontWeight: 600 }}>{h.ilce}</td>
                      <td style={{ padding: 8, textAlign: 'center' }}>
                        <span style={{ display: 'inline-block', width: 12, height: 12, borderRadius: 6, background: isiRenk(h.isi_skoru), marginRight: 4 }} />
                        {h.isi_skoru}
                      </td>
                      <td style={{ padding: 8, textAlign: 'right' }}>{h.mulk_sayisi}</td>
                      <td style={{ padding: 8, textAlign: 'right' }}>{h.talep_sayisi}</td>
                      <td style={{ padding: 8, textAlign: 'right' }}>{f(h.ort_satis_fiyat)} TL</td>
                      <td style={{ padding: 8, textAlign: 'right' }}>{f(h.ort_kira_fiyat)} TL</td>
                      <td style={{ padding: 8, textAlign: 'right' }}>{f(h.m2_fiyat)} TL</td>
                      <td style={{ padding: 8, textAlign: 'right', color: h.kira_getirisi >= 5 ? '#16a34a' : '#f59e0b' }}>%{h.kira_getirisi}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {tab === 'tahmin' && (
        <div style={{ background: 'var(--bg-card)', borderRadius: 12, padding: 16, border: '1px solid var(--border)' }}>
          {tahminler.length === 0 ? (
            <div style={{ textAlign: 'center', padding: 30, color: '#94a3b8' }}>Müşteri ekleyin — tahminler otomatik oluşsun</div>
          ) : (
            tahminler.slice(0, 20).map((t, i) => (
              <div key={i} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '10px 0', borderBottom: '1px solid var(--border-light, #f1f5f9)' }}>
                <div>
                  <div style={{ fontWeight: 600, fontSize: 14 }}>{t.ad_soyad}</div>
                  <div style={{ fontSize: 11, color: '#94a3b8' }}>{t.telefon || '—'} · {t.islem_turu || '?'}</div>
                  {t.detaylar?.slice(0, 3).map((d, j) => (
                    <div key={j} style={{ fontSize: 11, color: '#64748b' }}>{d}</div>
                  ))}
                </div>
                <div style={{ textAlign: 'right' }}>
                  <div style={{ fontSize: 24, fontWeight: 800, color: t.puan >= 75 ? '#16a34a' : t.puan >= 50 ? '#f59e0b' : t.puan >= 25 ? '#fb923c' : '#94a3b8' }}>
                    {t.puan}
                  </div>
                  <div style={{ fontSize: 10, color: '#94a3b8' }}>{t.yorum}</div>
                </div>
              </div>
            ))
          )}
        </div>
      )}
    </>
  );
}
