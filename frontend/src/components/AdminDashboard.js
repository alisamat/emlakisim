import React, { useState, useEffect } from 'react';
import api from '../api';

export default function AdminDashboard() {
  const [dash, setDash] = useState(null);
  const [kullanicilar, setKullanicilar] = useState([]);
  const [fiyat, setFiyat] = useState(null);

  useEffect(() => {
    Promise.all([
      api.get('/api/admin/dashboard'),
      api.get('/api/admin/kullanicilar'),
      api.get('/api/admin/fiyatlandirma'),
    ]).then(([d, k, f]) => {
      setDash(d.data);
      setKullanicilar(k.data.kullanicilar || []);
      setFiyat(f.data);
    }).catch(() => {});
  }, []);

  const krediEkle = async (uid) => {
    const miktar = window.prompt('Eklenecek kredi miktarı:');
    if (!miktar) return;
    try {
      const r = await api.put(`/api/admin/kullanicilar/${uid}/kredi`, { miktar: parseFloat(miktar) });
      setKullanicilar(p => p.map(k => k.id === uid ? { ...k, kredi: r.data.yeni_kredi } : k));
    } catch {}
  };

  const f = v => Number(v || 0).toLocaleString('tr-TR');

  return (
    <>
      <h1 style={{ fontSize: 20, fontWeight: 800, color: 'var(--text-primary)', marginBottom: 16 }}>🛡 Platform Admin</h1>

      {/* KPI */}
      {dash && (
        <div className="grid-3" style={{ marginBottom: 16, gap: 8 }}>
          {[
            { label: 'Kullanıcı', deger: dash.kullanicilar, ikon: '👥', renk: '#3b82f6' },
            { label: 'Müşteri', deger: dash.musteriler, ikon: '👤', renk: '#16a34a' },
            { label: 'Mülk', deger: dash.mulkler, ikon: '🏢', renk: '#f59e0b' },
            { label: 'Lead', deger: dash.leadler, ikon: '🎯', renk: '#8b5cf6' },
            { label: 'Diyalog', deger: dash.diyaloglar, ikon: '💬', renk: '#06b6d4' },
            { label: 'İşlem', deger: dash.islemler, ikon: '📊', renk: '#ec4899' },
          ].map(k => (
            <div key={k.label} style={{ background: 'var(--bg-card)', borderRadius: 10, padding: 12, textAlign: 'center', border: '1px solid var(--border)' }}>
              <div style={{ fontSize: 20 }}>{k.ikon}</div>
              <div style={{ fontSize: 20, fontWeight: 800, color: k.renk }}>{k.deger || 0}</div>
              <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>{k.label}</div>
            </div>
          ))}
        </div>
      )}

      {/* Gelir */}
      {dash && (
        <div className="grid-2" style={{ marginBottom: 16, gap: 8 }}>
          <div style={{ background: '#f0fdf4', borderRadius: 10, padding: 14, textAlign: 'center' }}>
            <div style={{ fontSize: 12, color: '#16a34a', fontWeight: 600 }}>Toplam Kredi Kullanımı</div>
            <div style={{ fontSize: 22, fontWeight: 800, color: '#16a34a' }}>{f(dash.toplam_kredi_kullanim)}</div>
          </div>
          <div style={{ background: '#eff6ff', borderRadius: 10, padding: 14, textAlign: 'center' }}>
            <div style={{ fontSize: 12, color: '#3b82f6', fontWeight: 600 }}>AI Maliyeti (USD)</div>
            <div style={{ fontSize: 22, fontWeight: 800, color: '#3b82f6' }}>${dash.toplam_ai_maliyet_usd?.toFixed(4)}</div>
          </div>
        </div>
      )}

      {/* Fiyatlandırma */}
      {fiyat && (
        <div style={{ background: 'var(--bg-card)', borderRadius: 12, padding: 16, marginBottom: 16, border: '1px solid var(--border)' }}>
          <div style={{ fontWeight: 700, fontSize: 14, marginBottom: 10 }}>💰 Kredi Fiyatlandırma</div>
          <div style={{ fontSize: 12, color: 'var(--text-muted)', marginBottom: 8 }}>USD/TRY Kur: {fiyat.kur} · KDV: %{fiyat.kdv_oran}</div>
          <div className="grid-2" style={{ gap: 6 }}>
            {fiyat.paketler?.map(p => (
              <div key={p.id} style={{ background: '#f8fafc', borderRadius: 8, padding: 8, fontSize: 12 }}>
                <strong>{p.ad}</strong>: {f(p.kredi)} kredi · ${p.usd}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Kullanıcılar */}
      <div style={{ background: 'var(--bg-card)', borderRadius: 12, padding: 16, border: '1px solid var(--border)' }}>
        <div style={{ fontWeight: 700, fontSize: 14, marginBottom: 10 }}>👥 Kullanıcılar ({kullanicilar.length})</div>
        {kullanicilar.map(k => (
          <div key={k.id} style={{
            display: 'flex', justifyContent: 'space-between', alignItems: 'center',
            padding: '8px 0', borderBottom: '1px solid var(--border-light, #f1f5f9)', fontSize: 13,
          }}>
            <div>
              <span style={{ fontWeight: 600 }}>{k.ad_soyad}</span>
              <span style={{ marginLeft: 8, color: 'var(--text-muted)', fontSize: 11 }}>{k.email}</span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <span style={{ fontWeight: 700, color: '#16a34a' }}>{f(k.kredi)} kr</span>
              <button onClick={() => krediEkle(k.id)} style={{
                background: '#eff6ff', border: '1px solid #bfdbfe', borderRadius: 6,
                padding: '3px 10px', fontSize: 11, cursor: 'pointer', color: '#1d4ed8', fontWeight: 600,
              }}>+ Kredi</button>
            </div>
          </div>
        ))}
      </div>
    </>
  );
}
