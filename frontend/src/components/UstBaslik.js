import React, { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../App';
import api from '../api';

export default function UstBaslik({ kredi, onSolToggle, onSagToggle, onSohbetGit, onOpenTab }) {
  const { user, cikisYap } = useAuth();
  const [bildirimler, setBildirimler] = useState([]);
  const [okunmamis, setOkunmamis] = useState(0);
  const [panelAcik, setPanelAcik] = useState(false);

  const yukle = useCallback(async () => {
    try {
      const r = await api.get('/api/panel/bildirim/listele');
      setBildirimler(r.data.bildirimler || []);
      setOkunmamis(r.data.okunmamis || 0);
    } catch {}
  }, []);

  useEffect(() => { yukle(); const t = setInterval(yukle, 60000); return () => clearInterval(t); }, [yukle]);

  const oku = async (b) => {
    if (!b.okundu) {
      await api.put(`/api/panel/bildirim/oku/${b.id}`).catch(() => {});
      setOkunmamis(p => Math.max(0, p - 1));
      setBildirimler(p => p.map(x => x.id === b.id ? { ...x, okundu: true } : x));
    }
    if (b.link && onOpenTab) onOpenTab(b.link);
    setPanelAcik(false);
  };

  const tumunuOku = async () => {
    await api.put('/api/panel/bildirim/tumunu-oku').catch(() => {});
    setOkunmamis(0);
    setBildirimler(p => p.map(x => ({ ...x, okundu: true })));
  };

  return (
    <div className="ust-baslik">
      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
        <button className="mobil-hamburger" onClick={onSolToggle}>☰</button>
        <div className="ust-baslik-logo" onClick={onSohbetGit}>🏠 Emlakisim AI</div>
      </div>
      <div className="ust-baslik-sag">
        <div className="ust-baslik-kredi" style={(kredi ?? 0) < 3 ? { background: '#fef2f2', borderColor: '#fecaca', color: '#dc2626' } : {}}>💎 {kredi ?? 0} Kredi</div>

        {/* Bildirim */}
        <div style={{ position: 'relative' }}>
          <button onClick={() => setPanelAcik(p => !p)} style={{
            background: 'none', border: 'none', fontSize: 18, cursor: 'pointer', position: 'relative', padding: '4px 6px',
          }}>
            🔔
            {okunmamis > 0 && (
              <span style={{
                position: 'absolute', top: 0, right: 0, background: '#dc2626', color: '#fff',
                borderRadius: '50%', width: 16, height: 16, fontSize: 10, fontWeight: 700,
                display: 'flex', alignItems: 'center', justifyContent: 'center',
              }}>{okunmamis}</span>
            )}
          </button>

          {panelAcik && (
            <div style={{
              position: 'absolute', right: 0, top: 36, width: 320, maxHeight: 400,
              background: '#fff', border: '1px solid #e2e8f0', borderRadius: 12,
              boxShadow: '0 8px 24px rgba(0,0,0,0.12)', zIndex: 100, overflow: 'hidden',
            }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', padding: '12px 16px', borderBottom: '1px solid #f1f5f9' }}>
                <span style={{ fontWeight: 700, fontSize: 14 }}>🔔 Bildirimler</span>
                {okunmamis > 0 && <button onClick={tumunuOku} style={{ background: 'none', border: 'none', color: '#16a34a', fontSize: 12, cursor: 'pointer', fontWeight: 600 }}>Tümünü oku</button>}
              </div>
              <div style={{ maxHeight: 340, overflowY: 'auto' }}>
                {bildirimler.length === 0 ? (
                  <div style={{ padding: 20, textAlign: 'center', color: '#94a3b8', fontSize: 13 }}>Bildirim yok</div>
                ) : bildirimler.slice(0, 15).map(b => (
                  <div key={b.id} onClick={() => oku(b)} style={{
                    padding: '10px 16px', borderBottom: '1px solid #f8fafc', cursor: 'pointer',
                    background: b.okundu ? '#fff' : '#f0fdf4',
                  }}>
                    <div style={{ fontSize: 13, fontWeight: b.okundu ? 400 : 600, color: '#1e293b' }}>{b.baslik}</div>
                    {b.icerik && <div style={{ fontSize: 11, color: '#94a3b8', marginTop: 2 }}>{b.icerik}</div>}
                    <div style={{ fontSize: 10, color: '#cbd5e1', marginTop: 2 }}>{new Date(b.olusturma).toLocaleString('tr-TR')}</div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        <span style={{ fontSize: 13, color: '#374151', fontWeight: 600 }}>{user?.ad_soyad?.split(' ')[0]}</span>
        <button className="ust-baslik-btn" onClick={cikisYap}>Çıkış</button>
        <button className="mobil-menu" onClick={onSagToggle}>☰</button>
      </div>
    </div>
  );
}
