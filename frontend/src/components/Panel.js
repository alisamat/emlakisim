import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import Layout from './Layout';
import { useAuth } from '../App';
import api from '../api';

const G = '#16a34a';

export default function Panel() {
  const { user } = useAuth();
  const [istatistik, setIstatistik] = useState({ musteriler: 0, mulkler: 0, kayitlar: 0 });

  useEffect(() => {
    Promise.all([
      api.get('/api/panel/musteriler'),
      api.get('/api/panel/mulkler'),
      api.get('/api/panel/yer-gostermeler'),
    ]).then(([m, ml, yg]) => {
      setIstatistik({
        musteriler: m.data.musteriler?.length || 0,
        mulkler:    ml.data.mulkler?.length || 0,
        kayitlar:   yg.data.kayitlar?.length || 0,
      });
    }).catch(() => {});
  }, []);

  const kartlar = [
    { path: '/musteriler', ikon: '👥', baslik: 'Müşteriler', sayi: istatistik.musteriler, renk: '#3b82f6', acik: '#eff6ff' },
    { path: '/mulkler',    ikon: '🏢', baslik: 'Portföy',    sayi: istatistik.mulkler,    renk: '#f59e0b', acik: '#fffbeb' },
    { path: '/kayitlar',   ikon: '📋', baslik: 'Kayıtlar',   sayi: istatistik.kayitlar,   renk: G,         acik: '#f0fdf4' },
  ];

  return (
    <Layout>
      {/* Hoşgeldin */}
      <div style={{ background: '#fff', borderRadius: 16, padding: '20px 24px', marginBottom: 20, border: `1px solid #e2e8f0` }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
          <div style={{ width: 52, height: 52, borderRadius: '50%', background: G, display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#fff', fontSize: 22, fontWeight: 700, flexShrink: 0 }}>
            {(user?.ad_soyad || '?')[0].toUpperCase()}
          </div>
          <div>
            <div style={{ fontWeight: 700, fontSize: 16, color: '#0f172a' }}>Merhaba, {user?.ad_soyad?.split(' ')[0]} 👋</div>
            <div style={{ fontSize: 13, color: '#64748b', marginTop: 2 }}>{user?.acente_adi || 'Emlakisim AI Asistanı'}</div>
          </div>
        </div>
      </div>

      {/* İstatistikler */}
      <div className="grid-3" style={{ marginBottom: 20 }}>
        {kartlar.map(k => (
          <Link key={k.path} to={k.path} style={{
            background: '#fff', borderRadius: 12, padding: '16px', border: `1px solid #e2e8f0`,
            display: 'block', textDecoration: 'none',
          }}>
            <div style={{ fontSize: 28, marginBottom: 8 }}>{k.ikon}</div>
            <div style={{ fontSize: 28, fontWeight: 800, color: k.renk }}>{k.sayi}</div>
            <div style={{ fontSize: 13, color: '#64748b', marginTop: 2 }}>{k.baslik}</div>
          </Link>
        ))}
      </div>

      {/* Hızlı Erişim */}
      <div style={{ background: '#fff', borderRadius: 12, padding: 20, marginBottom: 16, border: '1px solid #e2e8f0' }}>
        <div style={{ fontWeight: 700, fontSize: 14, color: '#1e293b', marginBottom: 14 }}>Hızlı İşlem</div>
        <div className="grid-2" style={{ gap: 10 }}>
          <Link to="/musteriler" style={{ background: '#eff6ff', borderRadius: 10, padding: '14px 16px', display: 'block' }}>
            <div style={{ fontSize: 20, marginBottom: 4 }}>👥</div>
            <div style={{ fontWeight: 600, fontSize: 13, color: '#1e40af' }}>Müşteri Ekle</div>
          </Link>
          <Link to="/mulkler" style={{ background: '#fffbeb', borderRadius: 10, padding: '14px 16px', display: 'block' }}>
            <div style={{ fontSize: 20, marginBottom: 4 }}>🏢</div>
            <div style={{ fontWeight: 600, fontSize: 13, color: '#92400e' }}>Mülk Ekle</div>
          </Link>
          <Link to="/kayitlar" style={{ background: '#f0fdf4', borderRadius: 10, padding: '14px 16px', display: 'block' }}>
            <div style={{ fontSize: 20, marginBottom: 4 }}>📋</div>
            <div style={{ fontWeight: 600, fontSize: 13, color: '#15803d' }}>Yer Gösterme</div>
          </Link>
          <Link to="/profil" style={{ background: '#f8fafc', borderRadius: 10, padding: '14px 16px', display: 'block' }}>
            <div style={{ fontSize: 20, marginBottom: 4 }}>⚙️</div>
            <div style={{ fontWeight: 600, fontSize: 13, color: '#374151' }}>Profil</div>
          </Link>
        </div>
      </div>

      {/* WhatsApp Bilgi */}
      <div style={{ background: '#f0fdf4', border: '1px solid #bbf7d0', borderRadius: 12, padding: '16px 20px', display: 'flex', gap: 12, alignItems: 'flex-start' }}>
        <span style={{ fontSize: 24 }}>💬</span>
        <div>
          <div style={{ fontWeight: 700, color: G, fontSize: 14, marginBottom: 4 }}>WhatsApp AI Asistanı</div>
          <div style={{ fontSize: 13, color: '#374151', lineHeight: 1.6 }}>
            WhatsApp'tan numaramıza yazarak müşteri ekle, mülk kaydet, yer gösterme belgesi oluştur — hepsi doğal dille.
          </div>
        </div>
      </div>
    </Layout>
  );
}
