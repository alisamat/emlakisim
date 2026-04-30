import React, { useState, useEffect } from 'react';
import api from '../api';

export default function AdminPanel() {
  const [egitim, setEgitim] = useState({});
  const [patterns, setPatterns] = useState([]);
  const [anlasilamayan, setAnlasilamayan] = useState([]);
  const [yeniPattern, setYeniPattern] = useState({ pattern: '', islem: '' });
  const [maliyet, setMaliyet] = useState(null);

  useEffect(() => {
    Promise.all([
      api.get('/api/panel/egitim/istatistik'),
      api.get('/api/panel/egitim/patterns'),
      api.get('/api/panel/egitim/anlasilamayan'),
    ]).then(([e, p, a]) => {
      setEgitim(e.data);
      setPatterns(p.data.patterns || []);
      setAnlasilamayan(a.data.kayitlar || []);
    }).catch(() => {});
    api.get('/api/panel/egitim/maliyet-rapor').then(r => setMaliyet(r.data)).catch(() => {});
  }, []);

  const patternEkle = async () => {
    if (!yeniPattern.pattern || !yeniPattern.islem) return;
    try {
      await api.post('/api/panel/egitim/patterns', yeniPattern);
      setYeniPattern({ pattern: '', islem: '' });
      const r = await api.get('/api/panel/egitim/patterns');
      setPatterns(r.data.patterns || []);
    } catch {}
  };

  const patternSil = async (id) => {
    try { await api.delete(`/api/panel/egitim/patterns/${id}`); setPatterns(p => p.filter(x => x.id !== id)); } catch {}
  };

  return (
    <>
      <h1 style={{ fontSize: 20, fontWeight: 800, color: 'var(--text-primary)', marginBottom: 16 }}>🛠 Admin Panel</h1>

      {/* AI Eğitim İstatistikleri */}
      <div style={{ background: 'var(--bg-card)', borderRadius: 12, padding: 16, marginBottom: 16, border: '1px solid var(--border)' }}>
        <div style={{ fontWeight: 700, fontSize: 14, marginBottom: 12 }}>🤖 AI Eğitim İstatistikleri</div>
        <div className="grid-2" style={{ gap: 8 }}>
          <div style={{ background: '#f0fdf4', borderRadius: 8, padding: 10, textAlign: 'center' }}>
            <div style={{ fontSize: 20, fontWeight: 800, color: '#16a34a' }}>{egitim.toplam_diyalog || 0}</div>
            <div style={{ fontSize: 11, color: '#64748b' }}>Toplam Diyalog</div>
          </div>
          <div style={{ background: '#eff6ff', borderRadius: 8, padding: 10, textAlign: 'center' }}>
            <div style={{ fontSize: 20, fontWeight: 800, color: '#3b82f6' }}>%{egitim.pattern_oran || 0}</div>
            <div style={{ fontSize: 11, color: '#64748b' }}>Pattern Hit (ücretsiz)</div>
          </div>
          <div style={{ background: '#fef3c7', borderRadius: 8, padding: 10, textAlign: 'center' }}>
            <div style={{ fontSize: 20, fontWeight: 800, color: '#f59e0b' }}>{egitim.ai_hit || 0}</div>
            <div style={{ fontSize: 11, color: '#64748b' }}>AI Çağrısı</div>
          </div>
          <div style={{ background: '#f8fafc', borderRadius: 8, padding: 10, textAlign: 'center' }}>
            <div style={{ fontSize: 20, fontWeight: 800, color: '#8b5cf6' }}>{egitim.ogrenilen_pattern || 0}</div>
            <div style={{ fontSize: 11, color: '#64748b' }}>Öğrenilen Pattern</div>
          </div>
        </div>
      </div>

      {/* Maliyet Raporu */}
      {maliyet && (
        <div style={{ background: 'var(--bg-card)', borderRadius: 12, padding: 16, marginBottom: 16, border: '1px solid var(--border)' }}>
          <div style={{ fontWeight: 700, fontSize: 14, marginBottom: 12 }}>💰 Maliyet Raporu</div>
          <div className="grid-3" style={{ gap: 8, marginBottom: 12 }}>
            <div style={{ background: '#f0fdf4', borderRadius: 8, padding: 10, textAlign: 'center' }}>
              <div style={{ fontSize: 18, fontWeight: 800, color: '#16a34a' }}>{maliyet.toplam_kredi}</div>
              <div style={{ fontSize: 11, color: '#64748b' }}>Harcanan Kredi</div>
            </div>
            <div style={{ background: '#eff6ff', borderRadius: 8, padding: 10, textAlign: 'center' }}>
              <div style={{ fontSize: 18, fontWeight: 800, color: '#3b82f6' }}>${maliyet.toplam_usd?.toFixed(4)}</div>
              <div style={{ fontSize: 11, color: '#64748b' }}>AI Maliyeti</div>
            </div>
            <div style={{ background: '#f8fafc', borderRadius: 8, padding: 10, textAlign: 'center' }}>
              <div style={{ fontSize: 18, fontWeight: 800, color: '#475569' }}>{maliyet.islem_sayisi}</div>
              <div style={{ fontSize: 11, color: '#64748b' }}>Toplam İşlem</div>
            </div>
          </div>
          {maliyet.tip_bazli && Object.entries(maliyet.tip_bazli).sort((a, b) => b[1].sayi - a[1].sayi).slice(0, 8).map(([tip, v]) => (
            <div key={tip} style={{ display: 'flex', justifyContent: 'space-between', padding: '3px 0', fontSize: 12, borderBottom: '1px solid var(--border-light, #f1f5f9)' }}>
              <span>{tip}</span>
              <span style={{ color: 'var(--text-muted)' }}>{v.sayi}x · {v.kredi.toFixed(1)} kredi</span>
            </div>
          ))}
        </div>
      )}

      {/* Pattern Ekleme */}
      <div style={{ background: 'var(--bg-card)', borderRadius: 12, padding: 16, marginBottom: 16, border: '1px solid var(--border)' }}>
        <div style={{ fontWeight: 700, fontSize: 14, marginBottom: 12 }}>➕ Yeni Pattern Ekle</div>
        <div style={{ display: 'flex', gap: 8, marginBottom: 8 }}>
          <input className="input" placeholder="Regex pattern (ör: müşteri.*ara)" value={yeniPattern.pattern}
            onChange={e => setYeniPattern(p => ({ ...p, pattern: e.target.value }))} style={{ flex: 2 }} />
          <input className="input" placeholder="Komut (ör: musteri_liste)" value={yeniPattern.islem}
            onChange={e => setYeniPattern(p => ({ ...p, islem: e.target.value }))} style={{ flex: 1 }} />
          <button className="btn-yesil" onClick={patternEkle} style={{ fontSize: 13 }}>Ekle</button>
        </div>
        <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>Komutlar: musteri_ekle, musteri_liste, mulk_ekle, mulk_liste, rapor, gorev_ekle, fatura_ekle, yardim</div>
      </div>

      {/* Mevcut Patterns */}
      {patterns.length > 0 && (
        <div style={{ background: 'var(--bg-card)', borderRadius: 12, padding: 16, marginBottom: 16, border: '1px solid var(--border)' }}>
          <div style={{ fontWeight: 700, fontSize: 14, marginBottom: 8 }}>📋 Öğrenilen Patterns ({patterns.length})</div>
          {patterns.map(p => (
            <div key={p.id} style={{ display: 'flex', justifyContent: 'space-between', padding: '4px 0', borderBottom: '1px solid var(--border-light, #f1f5f9)', fontSize: 12 }}>
              <span><code>{p.pattern}</code> → <strong>{p.islem}</strong> <span style={{ color: 'var(--text-muted)' }}>({p.kullanim}x)</span></span>
              <button onClick={() => patternSil(p.id)} style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#dc2626', fontSize: 12 }}>✕</button>
            </div>
          ))}
        </div>
      )}

      {/* Anlaşılamayan Mesajlar */}
      {anlasilamayan.length > 0 && (
        <div style={{ background: 'var(--bg-card)', borderRadius: 12, padding: 16, border: '1px solid var(--border)' }}>
          <div style={{ fontWeight: 700, fontSize: 14, marginBottom: 8 }}>❓ AI'ya Giden Mesajlar (pattern'a dönüştürülebilir)</div>
          {anlasilamayan.slice(0, 15).map(k => (
            <div key={k.id} style={{ padding: '4px 0', borderBottom: '1px solid var(--border-light, #f1f5f9)', fontSize: 12, color: 'var(--text-secondary)' }}>
              "{k.mesaj}" <span style={{ color: 'var(--text-muted)' }}>({new Date(k.olusturma).toLocaleDateString('tr-TR')})</span>
            </div>
          ))}
        </div>
      )}
    </>
  );
}
