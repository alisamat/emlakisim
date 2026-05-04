import React, { useState, useEffect } from 'react';
import api from '../api';

export default function Haberler() {
  const [haberler, setHaberler] = useState([]);
  const [yuk, setYuk] = useState(true);

  useEffect(() => {
    setYuk(true);
    api.get('/api/panel/haberler').then(r => setHaberler(r.data.haberler || [])).catch(() => {}).finally(() => setYuk(false));
  }, []);

  return (
    <>
      <h1 style={{ fontSize: 20, fontWeight: 800, color: 'var(--text-primary)', marginBottom: 16 }}>📰 Emlak Sektörü Haberleri</h1>

      {yuk ? (
        <div style={{ textAlign: 'center', padding: 40, color: '#94a3b8' }}>
          <div style={{ fontSize: 24, marginBottom: 8 }}>📰</div>
          Haberler yükleniyor...
        </div>
      ) : haberler.length === 0 ? (
        <div style={{ textAlign: 'center', padding: 40, color: '#94a3b8', background: 'var(--bg-card)', borderRadius: 12 }}>
          Henüz haber yok. Biraz sonra tekrar deneyin.
        </div>
      ) : (
        haberler.map((h, i) => (
          <a key={h.id || i} href={h.url} target="_blank" rel="noopener noreferrer" style={{ textDecoration: 'none', color: 'inherit' }}>
            <div style={{
              background: 'var(--bg-card)', borderRadius: 10, padding: '14px 16px', marginBottom: 8,
              border: '1px solid var(--border)', cursor: 'pointer',
              transition: 'box-shadow 0.2s',
            }}
              onMouseOver={e => e.currentTarget.style.boxShadow = '0 2px 8px rgba(0,0,0,0.08)'}
              onMouseOut={e => e.currentTarget.style.boxShadow = 'none'}
            >
              <div style={{ fontWeight: 700, fontSize: 14, color: 'var(--text-primary)', marginBottom: 4, lineHeight: 1.4 }}>
                {h.baslik}
              </div>
              {h.ozet && (
                <div style={{ fontSize: 12, color: '#64748b', marginBottom: 6, lineHeight: 1.4 }}>
                  {h.ozet.slice(0, 150)}{h.ozet.length > 150 ? '...' : ''}
                </div>
              )}
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ fontSize: 11, color: '#94a3b8' }}>
                  {h.kaynak && <span style={{ background: '#f1f5f9', padding: '1px 6px', borderRadius: 4, marginRight: 6 }}>{h.kaynak}</span>}
                  {h.tarih}
                </span>
                <span style={{ fontSize: 11, color: '#3b82f6' }}>Haberi oku →</span>
              </div>
            </div>
          </a>
        ))
      )}

      <div style={{ textAlign: 'center', marginTop: 16, fontSize: 11, color: '#94a3b8' }}>
        Haberler Google News RSS'den alınmaktadır. Günde 1 kez güncellenir.
      </div>
    </>
  );
}
