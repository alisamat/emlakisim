import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../App';
import api from '../api';

export default function Giris() {
  const { girisYap } = useAuth();
  const nav = useNavigate();
  const [form, setForm] = useState({ email: '', sifre: '' });
  const [yukleniyor, setYuk] = useState(false);
  const [hata, setHata] = useState('');

  const gonder = async e => {
    e.preventDefault();
    setYuk(true); setHata('');
    try {
      const r = await api.post('/api/auth/giris', form);
      girisYap(r.data.token, r.data.user);
      nav('/');
    } catch (err) {
      setHata(err.response?.data?.message || 'Giriş başarısız.');
    } finally { setYuk(false); }
  };

  return (
    <div style={{ minHeight: '100vh', background: '#f0fdf4', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 16 }}>
      <div style={{ width: '100%', maxWidth: 400 }}>
        <div style={{ textAlign: 'center', marginBottom: 32 }}>
          <div style={{ fontSize: 48, marginBottom: 8 }}>🏠</div>
          <h1 style={{ fontSize: 24, fontWeight: 800, color: '#0f172a' }}>Emlakisim</h1>
          <p style={{ fontSize: 13, color: '#64748b', marginTop: 4 }}>Emlakçı AI Asistanı</p>
        </div>

        <div className="kart">
          <div style={{ fontWeight: 700, fontSize: 16, color: '#1e293b', marginBottom: 20 }}>Giriş Yap</div>

          {hata && <div className="hata" style={{ marginBottom: 14 }}>{hata}</div>}

          <form onSubmit={gonder}>
            <div style={{ marginBottom: 14 }}>
              <label className="etiket">E-posta</label>
              <input className="input" type="email" value={form.email}
                onChange={e => setForm(p => ({ ...p, email: e.target.value }))} required />
            </div>
            <div style={{ marginBottom: 20 }}>
              <label className="etiket">Şifre</label>
              <input className="input" type="password" value={form.sifre}
                onChange={e => setForm(p => ({ ...p, sifre: e.target.value }))} required />
            </div>
            <button className="btn-yesil" type="submit" disabled={yukleniyor} style={{ width: '100%' }}>
              {yukleniyor ? 'Giriş yapılıyor...' : 'Giriş Yap'}
            </button>
          </form>

          <div style={{ textAlign: 'center', marginTop: 12, fontSize: 13 }}>
            <button onClick={async () => {
              const email = window.prompt('Şifre sıfırlama için email adresinizi girin:');
              if (email) {
                try { await api.post('/api/auth/sifre-sifirla', { email }); alert('Şifre sıfırlama bağlantısı email adresinize gönderildi.'); }
                catch { alert('Bir hata oluştu.'); }
              }
            }} style={{ background: 'none', border: 'none', color: '#64748b', fontSize: 13, cursor: 'pointer' }}>
              Şifremi unuttum
            </button>
          </div>
          <div style={{ textAlign: 'center', marginTop: 8, fontSize: 13, color: '#64748b' }}>
            Hesabın yok mu? <Link to="/kayit" style={{ color: '#16a34a', fontWeight: 600 }}>Kayıt Ol</Link>
          </div>
        </div>
      </div>
    </div>
  );
}
