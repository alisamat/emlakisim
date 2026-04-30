import React, { useState, useEffect } from 'react';
import { useAuth } from '../App';
import api from '../api';

export default function Ayarlar() {
  const { user, setUser } = useAuth();
  const [profilForm, setProfilForm] = useState({
    ad_soyad: user?.ad_soyad || '', telefon: user?.telefon || '',
    acente_adi: user?.acente_adi || '', yetki_no: user?.yetki_no || '',
  });
  const [sifreForm, setSifreForm] = useState({ eski_sifre: '', yeni_sifre: '', yeni_tekrar: '' });
  const [logo, setLogo] = useState(localStorage.getItem('emlakisim_logo') || '');
  const [tema, setTema] = useState(localStorage.getItem('emlakisim_tema') || 'acik');
  const [mesaj, setMesaj] = useState('');
  const [yuk, setYuk] = useState(false);

  // Dark mode uygula
  useEffect(() => {
    document.documentElement.setAttribute('data-tema', tema);
    localStorage.setItem('emlakisim_tema', tema);
  }, [tema]);

  const profilKaydet = async () => {
    setYuk(true); setMesaj('');
    try {
      const r = await api.put('/api/auth/profil', profilForm);
      setUser(r.data.user);
      setMesaj('Profil güncellendi');
    } catch { setMesaj('Hata oluştu'); } finally { setYuk(false); }
  };

  const logoYukle = (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = (ev) => {
      const dataUrl = ev.target.result;
      localStorage.setItem('emlakisim_logo', dataUrl);
      setLogo(dataUrl);
    };
    reader.readAsDataURL(file);
  };

  const logoSil = () => {
    localStorage.removeItem('emlakisim_logo');
    setLogo('');
  };

  const dp = e => setProfilForm(p => ({ ...p, [e.target.name]: e.target.value }));

  return (
    <>
      <h1 style={{ fontSize: 20, fontWeight: 800, color: 'var(--text-primary)', marginBottom: 16 }}>⚙️ Ayarlar</h1>

      {mesaj && <div className="basarili" style={{ marginBottom: 12 }}>✅ {mesaj}</div>}

      {/* Profil Ayarları */}
      <div style={{ background: 'var(--bg-card)', borderRadius: 12, padding: 20, marginBottom: 16, border: '1px solid var(--border)' }}>
        <div style={{ fontWeight: 700, fontSize: 15, marginBottom: 16, color: 'var(--text-primary)' }}>👤 Profil Ayarları</div>
        <div className="grid-2" style={{ marginBottom: 12 }}>
          <div><label className="etiket">Ad Soyad</label><input className="input" name="ad_soyad" value={profilForm.ad_soyad} onChange={dp} /></div>
          <div><label className="etiket">Telefon</label><input className="input" name="telefon" value={profilForm.telefon} onChange={dp} /></div>
        </div>
        <div className="grid-2" style={{ marginBottom: 16 }}>
          <div><label className="etiket">Acente / Şirket</label><input className="input" name="acente_adi" value={profilForm.acente_adi} onChange={dp} /></div>
          <div><label className="etiket">Yetki Belgesi No</label><input className="input" name="yetki_no" value={profilForm.yetki_no} onChange={dp} /></div>
        </div>
        <button className="btn-yesil" onClick={profilKaydet} disabled={yuk}>{yuk ? '...' : 'Kaydet'}</button>
      </div>

      {/* Şifre Değiştirme */}
      <div style={{ background: 'var(--bg-card)', borderRadius: 12, padding: 20, marginBottom: 16, border: '1px solid var(--border)' }}>
        <div style={{ fontWeight: 700, fontSize: 15, marginBottom: 16, color: 'var(--text-primary)' }}>🔒 Şifre Değiştir</div>
        <div className="grid-2" style={{ marginBottom: 12 }}>
          <div><label className="etiket">Eski Şifre</label><input className="input" type="password" value={sifreForm.eski_sifre} onChange={e => setSifreForm(p => ({ ...p, eski_sifre: e.target.value }))} /></div>
          <div><label className="etiket">Yeni Şifre</label><input className="input" type="password" value={sifreForm.yeni_sifre} onChange={e => setSifreForm(p => ({ ...p, yeni_sifre: e.target.value }))} /></div>
        </div>
        <button className="btn-yesil" onClick={async () => {
          if (sifreForm.yeni_sifre.length < 4) { setMesaj('Şifre en az 4 karakter'); return; }
          try {
            await api.put('/api/auth/sifre-degistir', sifreForm);
            setMesaj('Şifre değiştirildi'); setSifreForm({ eski_sifre: '', yeni_sifre: '', yeni_tekrar: '' });
          } catch (e) { setMesaj(e.response?.data?.message || 'Hata'); }
        }} style={{ fontSize: 13 }}>Şifre Değiştir</button>
      </div>

      {/* Logo Ayarı */}
      <div style={{ background: 'var(--bg-card)', borderRadius: 12, padding: 20, marginBottom: 16, border: '1px solid var(--border)' }}>
        <div style={{ fontWeight: 700, fontSize: 15, marginBottom: 12, color: 'var(--text-primary)' }}>🖼 Logo</div>
        <div style={{ fontSize: 13, color: 'var(--text-secondary)', marginBottom: 12 }}>
          Logonuz hoşgeldin ekranında ve header'da gösterilir.
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
          {logo ? (
            <img src={logo} alt="Logo" style={{ width: 64, height: 64, borderRadius: 12, objectFit: 'contain', border: '1px solid var(--border)' }} />
          ) : (
            <div style={{ width: 64, height: 64, borderRadius: 12, background: '#16a34a', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 28, color: '#fff' }}>🏠</div>
          )}
          <div>
            <label style={{ background: '#eff6ff', color: '#1d4ed8', border: '1px solid #bfdbfe', borderRadius: 8, padding: '6px 14px', fontSize: 13, fontWeight: 600, cursor: 'pointer' }}>
              📁 Logo Yükle
              <input type="file" accept="image/*" onChange={logoYukle} style={{ display: 'none' }} />
            </label>
            {logo && <button onClick={logoSil} style={{ background: 'none', border: 'none', color: '#dc2626', fontSize: 12, cursor: 'pointer', marginLeft: 8 }}>Kaldır</button>}
          </div>
        </div>
      </div>

      {/* Tema Ayarı */}
      <div style={{ background: 'var(--bg-card)', borderRadius: 12, padding: 20, marginBottom: 16, border: '1px solid var(--border)' }}>
        <div style={{ fontWeight: 700, fontSize: 15, marginBottom: 12, color: 'var(--text-primary)' }}>🌓 Tema</div>
        <div style={{ display: 'flex', gap: 12 }}>
          {[['acik', '☀️ Açık'], ['karanlik', '🌙 Karanlık']].map(([v, l]) => (
            <button key={v} onClick={() => setTema(v)} style={{
              flex: 1, padding: '14px', borderRadius: 12, fontSize: 14, fontWeight: 600, cursor: 'pointer',
              background: tema === v ? (v === 'karanlik' ? '#1e293b' : '#f0fdf4') : 'var(--bg-card)',
              color: tema === v ? (v === 'karanlik' ? '#fff' : '#16a34a') : 'var(--text-secondary)',
              border: `2px solid ${tema === v ? '#16a34a' : 'var(--border)'}`,
            }}>{l}</button>
          ))}
        </div>
      </div>
    </>
  );
}
