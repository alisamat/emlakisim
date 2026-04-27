import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { useAuth } from '../App';

const G = '#16a34a';

export default function Layout({ children }) {
  const { user, cikisYap } = useAuth();
  const { pathname } = useLocation();
  const aktif = p => pathname === p ? 'aktif' : '';

  return (
    <div style={{ minHeight: '100vh', background: '#f8fafc' }}>
      {/* Navbar */}
      <nav style={{ background: '#fff', borderBottom: '1px solid #e2e8f0', position: 'sticky', top: 0, zIndex: 50 }}>
        <div style={{ maxWidth: 860, margin: '0 auto', padding: '0 16px', height: 56, display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <Link to="/" style={{ fontWeight: 800, fontSize: 18, color: G, letterSpacing: -0.5 }}>
            🏠 Emlakisim
          </Link>
          <div className="hide-mobile" style={{ display: 'flex', gap: 4, alignItems: 'center' }}>
            {[['/', 'Panel'], ['/musteriler', 'Müşteriler'], ['/mulkler', 'Portföy'], ['/kayitlar', 'Kayıtlar']].map(([path, label]) => (
              <Link key={path} to={path} style={{
                padding: '6px 12px', borderRadius: 8, fontSize: 14, fontWeight: 600,
                color: pathname === path ? G : '#64748b',
                background: pathname === path ? '#f0fdf4' : 'transparent',
              }}>{label}</Link>
            ))}
            {user && (
              <div style={{ marginLeft: 8, display: 'flex', alignItems: 'center', gap: 8 }}>
                <Link to="/profil" style={{ fontSize: 13, color: '#64748b', fontWeight: 600 }}>{user.ad_soyad?.split(' ')[0]}</Link>
                <button onClick={cikisYap} style={{ fontSize: 12, color: '#94a3b8', background: 'none', border: 'none', cursor: 'pointer' }}>Çıkış</button>
              </div>
            )}
          </div>
          <div className="show-mobile" style={{ fontSize: 13, color: '#64748b', fontWeight: 600 }}>
            {user?.ad_soyad?.split(' ')[0]}
          </div>
        </div>
      </nav>

      {/* İçerik */}
      <main className="layout-main" style={{ maxWidth: 860, margin: '0 auto', padding: '20px 16px' }}>
        {children}
      </main>

      {/* Bottom Nav (mobile) */}
      {user && (
        <nav className="bottom-nav">
          {[
            ['/', '🏠', 'Panel'],
            ['/musteriler', '👥', 'Müşteriler'],
            ['/mulkler', '🏢', 'Portföy'],
            ['/kayitlar', '📋', 'Kayıtlar'],
            ['/profil', '👤', 'Profil'],
          ].map(([path, ikon, label]) => (
            <Link key={path} to={path} className={aktif(path)}>
              <span className="ikon">{ikon}</span>
              {label}
            </Link>
          ))}
        </nav>
      )}
    </div>
  );
}
