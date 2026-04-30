import React, { useState, useEffect } from 'react';
import api from '../api';

export default function MuhasebeRapor() {
  const [rapor, setRapor] = useState([]);
  const [ozet, setOzet] = useState({});
  const [aiRapor, setAiRapor] = useState('');
  const [yuk, setYuk] = useState(false);

  useEffect(() => {
    Promise.all([
      api.get('/api/panel/muhasebe/rapor'),
      api.get('/api/panel/muhasebe/ozet'),
    ]).then(([r, o]) => {
      setRapor(r.data.rapor || []);
      setOzet(o.data);
    }).catch(() => {});
  }, []);

  const aiOzetUret = async () => {
    setYuk(true);
    try {
      const veri = `Toplam gelir: ${ozet.gelir} TL, toplam gider: ${ozet.gider} TL, net: ${ozet.gelir - ozet.gider} TL. Aylık dağılım: ${rapor.map(r => `${r.ay}: gelir ${r.gelir}, gider ${r.gider}, kar ${r.kar}`).join('; ')}`;
      const r = await api.post('/api/panel/gelismis/metin-analiz', { metin: `Bu bir emlak ofisinin muhasebe verisidir. Analiz et ve Türkçe özet rapor yaz:\n${veri}` });
      setAiRapor(r.data.analiz || 'Rapor oluşturulamadı');
    } catch { setAiRapor('Hata oluştu'); } finally { setYuk(false); }
  };

  const f = v => Number(v || 0).toLocaleString('tr-TR');
  const AY = { '01': 'Oca', '02': 'Şub', '03': 'Mar', '04': 'Nis', '05': 'May', '06': 'Haz', '07': 'Tem', '08': 'Ağu', '09': 'Eyl', '10': 'Eki', '11': 'Kas', '12': 'Ara' };

  return (
    <>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
        <h1 style={{ fontSize: 20, fontWeight: 800, color: 'var(--text-primary)' }}>📊 Muhasebe Raporu</h1>
        <button className="btn-yesil" onClick={aiOzetUret} disabled={yuk} style={{ fontSize: 13 }}>
          {yuk ? '...' : '🤖 AI Özet Üret'}
        </button>
      </div>

      {/* Genel Özet */}
      <div className="grid-3" style={{ marginBottom: 16 }}>
        <div style={{ background: '#f0fdf4', borderRadius: 12, padding: 14, textAlign: 'center' }}>
          <div style={{ fontSize: 11, color: '#16a34a', fontWeight: 600 }}>Toplam Gelir</div>
          <div style={{ fontSize: 18, fontWeight: 800, color: '#16a34a' }}>{f(ozet.gelir)} TL</div>
        </div>
        <div style={{ background: '#fef2f2', borderRadius: 12, padding: 14, textAlign: 'center' }}>
          <div style={{ fontSize: 11, color: '#dc2626', fontWeight: 600 }}>Toplam Gider</div>
          <div style={{ fontSize: 18, fontWeight: 800, color: '#dc2626' }}>{f(ozet.gider)} TL</div>
        </div>
        <div style={{ background: (ozet.gelir - ozet.gider) >= 0 ? '#f0fdf4' : '#fef2f2', borderRadius: 12, padding: 14, textAlign: 'center' }}>
          <div style={{ fontSize: 11, fontWeight: 600 }}>Net</div>
          <div style={{ fontSize: 18, fontWeight: 800, color: (ozet.gelir - ozet.gider) >= 0 ? '#16a34a' : '#dc2626' }}>{f(ozet.gelir - ozet.gider)} TL</div>
        </div>
      </div>

      {/* AI Rapor */}
      {aiRapor && (
        <div style={{ background: '#eff6ff', borderRadius: 12, padding: 16, marginBottom: 16, border: '1px solid #bfdbfe' }}>
          <div style={{ fontWeight: 700, fontSize: 13, color: '#1d4ed8', marginBottom: 8 }}>🤖 AI Analiz Raporu</div>
          <div style={{ fontSize: 13, color: '#1e40af', lineHeight: 1.7, whiteSpace: 'pre-wrap' }}>{aiRapor}</div>
        </div>
      )}

      {/* Aylık Tablo */}
      <div style={{ background: 'var(--bg-card)', borderRadius: 12, padding: 16, border: '1px solid var(--border)' }}>
        <div style={{ fontWeight: 700, fontSize: 14, marginBottom: 12 }}>📅 Aylık Dağılım</div>
        {rapor.length === 0 ? (
          <div style={{ fontSize: 13, color: '#94a3b8' }}>Henüz veri yok</div>
        ) : (
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
              <thead>
                <tr style={{ borderBottom: '2px solid var(--border)' }}>
                  <th style={{ textAlign: 'left', padding: '8px 4px' }}>Ay</th>
                  <th style={{ textAlign: 'right', padding: '8px 4px', color: '#16a34a' }}>Gelir</th>
                  <th style={{ textAlign: 'right', padding: '8px 4px', color: '#dc2626' }}>Gider</th>
                  <th style={{ textAlign: 'right', padding: '8px 4px' }}>Kâr/Zarar</th>
                </tr>
              </thead>
              <tbody>
                {rapor.map(r => (
                  <tr key={r.ay} style={{ borderBottom: '1px solid var(--border-light)' }}>
                    <td style={{ padding: '8px 4px', fontWeight: 600 }}>{AY[r.ay.split('-')[1]] || r.ay.split('-')[1]} {r.ay.split('-')[0]}</td>
                    <td style={{ textAlign: 'right', padding: '8px 4px', color: '#16a34a' }}>{f(r.gelir)}</td>
                    <td style={{ textAlign: 'right', padding: '8px 4px', color: '#dc2626' }}>{f(r.gider)}</td>
                    <td style={{ textAlign: 'right', padding: '8px 4px', fontWeight: 700, color: r.kar >= 0 ? '#16a34a' : '#dc2626' }}>{r.kar >= 0 ? '+' : ''}{f(r.kar)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </>
  );
}
