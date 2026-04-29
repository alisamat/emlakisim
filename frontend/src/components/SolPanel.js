import React, { useState, useEffect, useCallback } from 'react';
import api from '../api';

export default function SolPanel({ kredi, sohbetId, onYeniSohbet, onSohbetSec, acik }) {
  const [sohbetler, setSohbetler] = useState([]);
  const [arama, setArama] = useState('');

  const yukle = useCallback(async () => {
    try {
      const r = await api.get('/api/panel/sohbetler');
      setSohbetler(r.data.sohbetler || []);
    } catch {}
  }, []);

  useEffect(() => { yukle(); }, [yukle]);
  useEffect(() => { if (sohbetId) yukle(); }, [sohbetId, yukle]);

  const sohbetSil = async (e, id) => {
    e.stopPropagation();
    if (!window.confirm('Bu sohbeti silmek istediğinize emin misiniz?')) return;
    try {
      await api.delete(`/api/panel/sohbetler/${id}`);
      setSohbetler(p => p.filter(s => s.id !== id));
      if (sohbetId === id) onYeniSohbet();
    } catch {}
  };

  const filtrelenmis = arama.trim()
    ? sohbetler.filter(s => (s.baslik || '').toLowerCase().includes(arama.toLowerCase()))
    : sohbetler;

  return (
    <div className={`sol-panel${acik ? ' acik' : ''}`}>
      {/* Kredi */}
      <div className="sol-panel-kredi">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <span style={{ fontSize: 12, fontWeight: 700, color: '#374151' }}>💎 Kontor</span>
          <span style={{ fontSize: 12, fontWeight: 700, color: '#16a34a' }}>{kredi ?? 0}</span>
        </div>
        <div className="sol-panel-kredi-bar">
          <div className="sol-panel-kredi-bar-dolu" style={{ width: `${Math.min((kredi || 0) / 100 * 100, 100)}%` }} />
        </div>
      </div>

      {/* Yeni Sohbet */}
      <button className="sol-panel-yeni" onClick={onYeniSohbet}>+ Yeni Sohbet</button>

      {/* Arama */}
      <div style={{ padding: '0 12px', marginBottom: 4 }}>
        <input
          style={{
            width: '100%', padding: '6px 10px', border: '1px solid #e2e8f0',
            borderRadius: 6, fontSize: 12, outline: 'none',
          }}
          placeholder="🔍 Sohbet ara..."
          value={arama}
          onChange={e => setArama(e.target.value)}
        />
      </div>

      {/* Sohbet Geçmişi */}
      <div className="sol-panel-baslik">
        Sohbet Geçmişi
        <span style={{ fontSize: 10, color: '#cbd5e1', marginLeft: 4 }}>({filtrelenmis.length})</span>
      </div>
      <div className="sol-panel-liste">
        {filtrelenmis.length === 0 ? (
          <div style={{ padding: '12px 16px', fontSize: 12, color: '#94a3b8' }}>
            {arama ? 'Sonuç bulunamadı' : 'Henüz sohbet yok'}
          </div>
        ) : (
          filtrelenmis.map(s => (
            <div
              key={s.id}
              className={`sol-panel-sohbet${sohbetId === s.id ? ' aktif' : ''}`}
              onClick={() => onSohbetSec(s.id)}
              style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}
            >
              <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', flex: 1 }}>
                💬 {s.baslik || 'Sohbet'}
              </span>
              <button
                onClick={e => sohbetSil(e, s.id)}
                style={{
                  background: 'none', border: 'none', cursor: 'pointer',
                  fontSize: 12, color: '#cbd5e1', padding: '0 4px', flexShrink: 0,
                }}
                title="Sohbeti sil"
              >✕</button>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
