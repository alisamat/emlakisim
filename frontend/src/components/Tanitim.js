import React, { useState, useEffect } from 'react';
import api from '../api';
import { useAuth } from '../App';

export default function Tanitim() {
  const { user } = useAuth();
  const [mulkler, setMulkler] = useState([]);
  const [linkKopyalandi, setLinkKopyalandi] = useState(false);
  const [sosyalIcerik, setSosyalIcerik] = useState({});
  const [yukleniyor, setYuk] = useState({});

  useEffect(() => {
    api.get('/api/panel/mulkler').then(r => setMulkler(r.data.mulkler || [])).catch(() => {});
  }, []);

  const tanitimUrl = `${window.location.origin}/e/${user?.id || ''}`;

  const linkKopyala = () => {
    navigator.clipboard.writeText(tanitimUrl).then(() => {
      setLinkKopyalandi(true);
      setTimeout(() => setLinkKopyalandi(false), 2000);
    });
  };

  const sosyalUret = async (mulkId, platform) => {
    setYuk(p => ({ ...p, [`${mulkId}_${platform}`]: true }));
    try {
      const r = await api.post('/api/panel/gelismis/sosyal-medya', { mulk_id: mulkId, platform });
      setSosyalIcerik(p => ({ ...p, [`${mulkId}_${platform}`]: r.data.icerik }));
    } catch {} finally {
      setYuk(p => ({ ...p, [`${mulkId}_${platform}`]: false }));
    }
  };

  const kopyala = (text) => {
    navigator.clipboard.writeText(text);
  };

  return (
    <>
      <h1 style={{ fontSize: 20, fontWeight: 800, color: '#0f172a', marginBottom: 16 }}>🌐 Tanıtım & Paylaşım</h1>

      {/* Tanıtım linki */}
      <div style={{ background: '#fff', borderRadius: 12, padding: 16, marginBottom: 16, border: '1px solid #e2e8f0' }}>
        <div style={{ fontWeight: 700, fontSize: 14, marginBottom: 8 }}>📎 Tanıtım Linkiniz</div>
        <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
          <input className="input" value={tanitimUrl} readOnly style={{ flex: 1, fontSize: 13 }} />
          <button onClick={linkKopyala} className="btn-yesil" style={{ fontSize: 13, whiteSpace: 'nowrap' }}>
            {linkKopyalandi ? '✅ Kopyalandı' : '📋 Kopyala'}
          </button>
        </div>
        <div style={{ fontSize: 12, color: '#94a3b8', marginTop: 6 }}>
          Bu linki müşterilerinize gönderin — portföyünüzü ve iletişim bilgilerinizi görebilirler.
        </div>
      </div>

      {/* Profil önizleme */}
      <div style={{ background: '#f0fdf4', borderRadius: 12, padding: 16, marginBottom: 16, border: '1px solid #bbf7d0' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <div style={{ width: 48, height: 48, borderRadius: '50%', background: '#16a34a', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#fff', fontSize: 20, fontWeight: 700 }}>
            {(user?.ad_soyad || '?')[0].toUpperCase()}
          </div>
          <div>
            <div style={{ fontWeight: 700, fontSize: 16, color: '#1e293b' }}>{user?.ad_soyad}</div>
            <div style={{ fontSize: 13, color: '#64748b' }}>{user?.acente_adi || 'Emlak Danışmanı'}</div>
            <div style={{ fontSize: 12, color: '#94a3b8' }}>📞 {user?.telefon} · 🏢 {mulkler.length} mülk</div>
          </div>
        </div>
      </div>

      {/* Sosyal medya içerik üretme */}
      <div style={{ background: '#fff', borderRadius: 12, padding: 16, marginBottom: 16, border: '1px solid #e2e8f0' }}>
        <div style={{ fontWeight: 700, fontSize: 14, marginBottom: 12 }}>📱 Sosyal Medya İçerik Üret</div>
        <div style={{ fontSize: 12, color: '#64748b', marginBottom: 12 }}>Mülk seçin, AI otomatik paylaşım metni oluştursun.</div>

        {mulkler.length === 0 ? (
          <div style={{ fontSize: 13, color: '#94a3b8' }}>Portföyünüzde mülk yok</div>
        ) : (
          mulkler.slice(0, 10).map(m => (
            <div key={m.id} style={{ padding: '10px 0', borderBottom: '1px solid #f1f5f9' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 6 }}>
                <span style={{ fontWeight: 600, fontSize: 13 }}>{m.baslik || m.adres || '—'}</span>
                <span style={{ fontSize: 12, color: '#64748b' }}>{m.fiyat ? `${Number(m.fiyat).toLocaleString('tr-TR')} TL` : ''}</span>
              </div>
              <div style={{ display: 'flex', gap: 6 }}>
                {['instagram', 'facebook', 'whatsapp'].map(p => (
                  <button key={p} onClick={() => sosyalUret(m.id, p)}
                    disabled={yukleniyor[`${m.id}_${p}`]}
                    style={{
                      padding: '4px 10px', borderRadius: 6, fontSize: 11, fontWeight: 600, cursor: 'pointer',
                      background: p === 'instagram' ? '#fef3c7' : p === 'facebook' ? '#eff6ff' : '#f0fdf4',
                      color: p === 'instagram' ? '#92400e' : p === 'facebook' ? '#1d4ed8' : '#16a34a',
                      border: 'none',
                    }}>
                    {yukleniyor[`${m.id}_${p}`] ? '...' : p === 'instagram' ? '📸 IG' : p === 'facebook' ? '📘 FB' : '💬 WA'}
                  </button>
                ))}
              </div>
              {/* Üretilen içerik */}
              {['instagram', 'facebook', 'whatsapp'].map(p => {
                const key = `${m.id}_${p}`;
                return sosyalIcerik[key] ? (
                  <div key={key} style={{ marginTop: 8, background: '#f8fafc', borderRadius: 8, padding: 10, fontSize: 12, color: '#374151', whiteSpace: 'pre-wrap', position: 'relative' }}>
                    <button onClick={() => kopyala(sosyalIcerik[key])} style={{
                      position: 'absolute', right: 6, top: 6, background: '#16a34a', color: '#fff',
                      border: 'none', borderRadius: 4, padding: '2px 8px', fontSize: 10, cursor: 'pointer',
                    }}>Kopyala</button>
                    {sosyalIcerik[key]}
                  </div>
                ) : null;
              })}
            </div>
          ))
        )}
      </div>
    </>
  );
}
