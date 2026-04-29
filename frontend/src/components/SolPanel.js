import React, { useState, useEffect, useCallback } from 'react';
import api from '../api';

export default function SolPanel({ kredi, sohbetId, onYeniSohbet, onSohbetSec, acik }) {
  const [sohbetler, setSohbetler] = useState([]);

  const yukle = useCallback(async () => {
    try {
      const r = await api.get('/api/panel/sohbetler');
      setSohbetler(r.data.sohbetler || []);
    } catch {}
  }, []);

  useEffect(() => { yukle(); }, [yukle]);

  // Yeni sohbet açıldığında listeyi güncelle
  useEffect(() => { if (sohbetId) yukle(); }, [sohbetId, yukle]);

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

      {/* Sohbet Geçmişi */}
      <div className="sol-panel-baslik">Sohbet Geçmişi</div>
      <div className="sol-panel-liste">
        {sohbetler.length === 0 ? (
          <div style={{ padding: '12px 16px', fontSize: 12, color: '#94a3b8' }}>Henüz sohbet yok</div>
        ) : (
          sohbetler.map(s => (
            <div
              key={s.id}
              className={`sol-panel-sohbet${sohbetId === s.id ? ' aktif' : ''}`}
              onClick={() => onSohbetSec(s.id)}
            >
              💬 {s.baslik || 'Sohbet'}
            </div>
          ))
        )}
      </div>
    </div>
  );
}
