import React, { useState, useEffect, useCallback } from 'react';
import api from '../api';

export default function YerGostermeler() {
  const [kayitlar, setKayitlar] = useState([]);
  const [yukleniyor, setYuk]    = useState(false);

  const yukle = useCallback(async () => {
    setYuk(true);
    try { const r = await api.get('/api/panel/yer-gostermeler'); setKayitlar(r.data.kayitlar || []); }
    catch { } finally { setYuk(false); }
  }, []);

  useEffect(() => { yukle(); }, [yukle]);

  return (
    <>
      <div style={{ marginBottom: 20 }}>
        <h1 style={{ fontSize: 20, fontWeight: 800, color: '#0f172a' }}>📋 Yer Gösterme Kayıtları</h1>
        <p style={{ color: '#64748b', fontSize: 13, marginTop: 4 }}>Toplam {kayitlar.length} kayıt</p>
      </div>

      {yukleniyor ? (
        <div style={{ textAlign: 'center', color: '#94a3b8', padding: 40 }}>Yükleniyor…</div>
      ) : kayitlar.length === 0 ? (
        <div style={{ textAlign: 'center', color: '#94a3b8', padding: 40, background: '#fff', borderRadius: 12 }}>
          <div style={{ fontSize: 32, marginBottom: 8 }}>📭</div>
          Henüz yer gösterme kaydı yok.<br />
          <span style={{ fontSize: 13 }}>WhatsApp'tan yer gösterme belgesi oluşturdukça burada görünür.</span>
        </div>
      ) : (
        kayitlar.map(k => (
          <div key={k.id} style={{ background: '#fff', borderRadius: 12, padding: '14px 16px', marginBottom: 10, border: '1px solid #e2e8f0', borderLeft: '3px solid #16a34a' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
              <div>
                <div style={{ fontSize: 13, color: '#94a3b8', marginBottom: 4 }}>
                  {k.tarih ? new Date(k.tarih).toLocaleDateString('tr-TR') : '—'}
                  {k.musteri_onay && <span style={{ marginLeft: 8, color: '#16a34a', fontWeight: 600 }}>✅ Onaylı</span>}
                </div>
                <div style={{ fontSize: 15, fontWeight: 700, color: '#0f172a' }}>#{k.id}</div>
              </div>
              {k.pdf_url && (
                <button onClick={() => window.open(k.pdf_url, '_blank')} style={{
                  background: '#f0fdf4', border: '1px solid #bbf7d0', color: '#15803d',
                  borderRadius: 8, padding: '7px 14px', fontSize: 13, cursor: 'pointer', fontWeight: 600,
                }}>📄 PDF</button>
              )}
            </div>
          </div>
        ))
      )}
    </>
  );
}
