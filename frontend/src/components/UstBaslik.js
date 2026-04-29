import React from 'react';
import { useAuth } from '../App';

export default function UstBaslik({ kredi, onSolToggle, onSagToggle, onSohbetGit }) {
  const { user, cikisYap } = useAuth();

  return (
    <div className="ust-baslik">
      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
        <button className="mobil-hamburger" onClick={onSolToggle}>☰</button>
        <div className="ust-baslik-logo" onClick={onSohbetGit}>🏠 Emlakisim AI</div>
      </div>
      <div className="ust-baslik-sag">
        <div className="ust-baslik-kredi">💎 {kredi ?? 0} Kredi</div>
        <span style={{ fontSize: 13, color: '#374151', fontWeight: 600 }}>{user?.ad_soyad?.split(' ')[0]}</span>
        <button className="ust-baslik-btn" onClick={cikisYap}>Çıkış</button>
        <button className="mobil-menu" onClick={onSagToggle}>☰</button>
      </div>
    </div>
  );
}
