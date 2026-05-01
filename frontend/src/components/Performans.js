import React, { useState, useEffect } from 'react';
import api from '../api';

export default function Performans() {
  const [veri, setVeri] = useState({});
  const [sektor, setSektor] = useState('');
  const [stratejik, setStratejik] = useState([]);
  const [piyasa, setPiyasa] = useState('');
  const [yuk, setYuk] = useState({});

  useEffect(() => {
    Promise.all([
      api.get('/api/panel/musteriler'),
      api.get('/api/panel/mulkler'),
      api.get('/api/panel/muhasebe/ozet'),
      api.get('/api/panel/lead/istatistik'),
      api.get('/api/panel/planlama/bugun'),
      api.get('/api/panel/egitim/istatistik'),
    ]).then(([m, p, mh, l, pl, eg]) => {
      setVeri({
        musteri: (m.data.musteriler || []).length,
        mulk: (p.data.mulkler || []).length,
        gelir: mh.data.gelir || 0,
        gider: mh.data.gider || 0,
        lead_yeni: l.data.yeni || 0,
        lead_toplam: l.data.toplam || 0,
        bugun_gorev: (pl.data.bugun || []).length,
        yaklasan: (pl.data.yaklasan || []).length,
        pattern_oran: eg.data.pattern_oran || 0,
        toplam_diyalog: eg.data.toplam_diyalog || 0,
      });
    }).catch(() => {});
    api.get('/api/panel/gelismis/zeka/stratejik').then(r => setStratejik(r.data.oneriler || [])).catch(() => {});
  }, []);

  const sektorGetir = async () => {
    setYuk(p => ({ ...p, sektor: true }));
    try { const r = await api.post('/api/panel/gelismis/sektor-haberleri', { konu: 'emlak piyasası' }); setSektor(r.data.icerik || ''); }
    catch {} finally { setYuk(p => ({ ...p, sektor: false })); }
  };

  const piyasaGetir = async () => {
    setYuk(p => ({ ...p, piyasa: true }));
    try { const r = await api.post('/api/panel/gelismis/piyasa-analizi', { sehir: 'İstanbul', tip: 'daire' }); setPiyasa(r.data.analiz || ''); }
    catch {} finally { setYuk(p => ({ ...p, piyasa: false })); }
  };

  const f = v => Number(v || 0).toLocaleString('tr-TR');
  const kar = (veri.gelir || 0) - (veri.gider || 0);

  return (
    <>
      <h1 style={{ fontSize: 20, fontWeight: 800, color: 'var(--text-primary)', marginBottom: 16 }}>🏆 Performans & Analiz</h1>

      {/* KPI kartları */}
      <div className="grid-3" style={{ marginBottom: 16 }}>
        {[
          { label: 'Müşteri', deger: veri.musteri, ikon: '👥', renk: '#3b82f6' },
          { label: 'Portföy', deger: veri.mulk, ikon: '🏢', renk: '#f59e0b' },
          { label: 'Yeni Lead', deger: veri.lead_yeni, ikon: '🎯', renk: '#8b5cf6' },
        ].map(k => (
          <div key={k.label} style={{ background: 'var(--bg-card)', borderRadius: 12, padding: 14, textAlign: 'center', border: '1px solid var(--border)' }}>
            <div style={{ fontSize: 24, marginBottom: 4 }}>{k.ikon}</div>
            <div style={{ fontSize: 24, fontWeight: 800, color: k.renk }}>{k.deger || 0}</div>
            <div style={{ fontSize: 12, color: 'var(--text-secondary)' }}>{k.label}</div>
          </div>
        ))}
      </div>

      <div className="grid-2" style={{ marginBottom: 16, gap: 12 }}>
        <div style={{ background: 'var(--bg-card)', borderRadius: 12, padding: 14, border: '1px solid var(--border)' }}>
          <div style={{ fontSize: 12, color: 'var(--text-secondary)', marginBottom: 4 }}>💰 Net Gelir</div>
          <div style={{ fontSize: 20, fontWeight: 800, color: kar >= 0 ? '#16a34a' : '#dc2626' }}>{f(kar)} TL</div>
          <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>Gelir: {f(veri.gelir)} · Gider: {f(veri.gider)}</div>
        </div>
        <div style={{ background: 'var(--bg-card)', borderRadius: 12, padding: 14, border: '1px solid var(--border)' }}>
          <div style={{ fontSize: 12, color: 'var(--text-secondary)', marginBottom: 4 }}>📅 Bugün</div>
          <div style={{ fontSize: 20, fontWeight: 800, color: '#16a34a' }}>{veri.bugun_gorev || 0} görev</div>
          <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>{veri.yaklasan || 0} yaklaşan</div>
        </div>
      </div>

      {/* AI Verimlilik */}
      <div style={{ background: 'var(--bg-card)', borderRadius: 12, padding: 14, marginBottom: 16, border: '1px solid var(--border)' }}>
        <div style={{ fontSize: 12, color: 'var(--text-secondary)', marginBottom: 4 }}>🤖 AI Verimlilik</div>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <span style={{ fontSize: 18, fontWeight: 800, color: '#16a34a' }}>%{veri.pattern_oran || 0}</span>
            <span style={{ fontSize: 12, color: 'var(--text-muted)', marginLeft: 8 }}>sıfır maliyetli işlem</span>
          </div>
          <span style={{ fontSize: 12, color: 'var(--text-muted)' }}>{veri.toplam_diyalog || 0} toplam diyalog</span>
        </div>
      </div>

      {/* Stratejik Öneriler */}
      {stratejik.length > 0 && (
        <div style={{ background: '#fffbeb', borderRadius: 12, padding: 16, marginBottom: 16, border: '1px solid #fde68a' }}>
          <div style={{ fontWeight: 700, fontSize: 14, color: '#92400e', marginBottom: 8 }}>🎯 Stratejik Öneriler</div>
          {stratejik.map((o, i) => (
            <div key={i} style={{ padding: '6px 0', borderBottom: '1px solid #fef3c7', fontSize: 13 }}>
              <div style={{ fontWeight: 600, color: '#78350f' }}>{o.baslik}</div>
              <div style={{ color: '#92400e', fontSize: 12, marginTop: 2 }}>{o.mesaj}</div>
            </div>
          ))}
        </div>
      )}

      {/* Sektörel Bilgi */}
      <div className="grid-2" style={{ gap: 12, marginBottom: 16 }}>
        <button onClick={sektorGetir} disabled={yuk.sektor} style={{
          padding: 16, borderRadius: 12, border: '2px solid var(--border)', background: 'var(--bg-card)',
          cursor: 'pointer', textAlign: 'left', fontSize: 14, fontWeight: 600,
        }}>
          {yuk.sektor ? '⏳ Yükleniyor...' : '📰 Sektör Haberleri'}
        </button>
        <button onClick={piyasaGetir} disabled={yuk.piyasa} style={{
          padding: 16, borderRadius: 12, border: '2px solid var(--border)', background: 'var(--bg-card)',
          cursor: 'pointer', textAlign: 'left', fontSize: 14, fontWeight: 600,
        }}>
          {yuk.piyasa ? '⏳ Yükleniyor...' : '📊 Piyasa Analizi (İstanbul)'}
        </button>
      </div>

      {sektor && (
        <div style={{ background: '#eff6ff', borderRadius: 12, padding: 16, marginBottom: 12, border: '1px solid #bfdbfe' }}>
          <div style={{ fontWeight: 700, fontSize: 13, color: '#1d4ed8', marginBottom: 8 }}>📰 Sektör Haberleri</div>
          <div style={{ fontSize: 13, color: '#1e40af', lineHeight: 1.7, whiteSpace: 'pre-wrap' }}>{sektor}</div>
        </div>
      )}

      {piyasa && (
        <div style={{ background: '#f0fdf4', borderRadius: 12, padding: 16, marginBottom: 12, border: '1px solid #bbf7d0' }}>
          <div style={{ fontWeight: 700, fontSize: 13, color: '#16a34a', marginBottom: 8 }}>📊 Piyasa Analizi</div>
          <div style={{ fontSize: 13, color: '#166534', lineHeight: 1.7, whiteSpace: 'pre-wrap' }}>{piyasa}</div>
        </div>
      )}
    </>
  );
}
