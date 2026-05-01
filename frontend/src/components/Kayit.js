import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../App';
import api from '../api';

export default function Kayit() {
  const { girisYap } = useAuth();
  const nav = useNavigate();
  const [form, setForm] = useState({ ad_soyad: '', email: '', telefon: '', acente_adi: '', yetki_no: '', sifre: '', kullanici_tipi: 'emlakci' });
  const [yukleniyor, setYuk] = useState(false);
  const [hata, setHata] = useState('');

  const degistir = e => setForm(p => ({ ...p, [e.target.name]: e.target.value }));

  const gonder = async e => {
    e.preventDefault();
    setYuk(true); setHata('');
    try {
      const r = await api.post('/api/auth/kayit', form);
      girisYap(r.data.token, r.data.user);
      nav('/');
    } catch (err) {
      setHata(err.response?.data?.message || 'Kayıt başarısız.');
    } finally { setYuk(false); }
  };

  return (
    <div style={{ minHeight: '100vh', background: '#f0fdf4', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 16 }}>
      <div style={{ width: '100%', maxWidth: 440 }}>
        <div style={{ textAlign: 'center', marginBottom: 28 }}>
          <div style={{ fontSize: 48, marginBottom: 8 }}>🏠</div>
          <h1 style={{ fontSize: 24, fontWeight: 800, color: '#0f172a' }}>Emlakisim</h1>
          <p style={{ fontSize: 13, color: '#64748b', marginTop: 4 }}>Emlakçı AI Asistanı</p>
        </div>

        <div className="kart">
          <div style={{ fontWeight: 700, fontSize: 16, color: '#1e293b', marginBottom: 12 }}>Hesap Oluştur</div>

          {/* Kullanıcı tipi seçimi */}
          <div style={{ display: 'flex', gap: 8, marginBottom: 16 }}>
            {[['emlakci', '🏢 Emlakçı'], ['musteri', '👤 Müşteri']].map(([v, l]) => (
              <button key={v} type="button" onClick={() => setForm(p => ({ ...p, kullanici_tipi: v }))} style={{
                flex: 1, padding: '10px', borderRadius: 8, fontSize: 14, fontWeight: 600, cursor: 'pointer',
                background: form.kullanici_tipi === v ? '#f0fdf4' : '#fff',
                color: form.kullanici_tipi === v ? '#16a34a' : '#374151',
                border: `2px solid ${form.kullanici_tipi === v ? '#16a34a' : '#e2e8f0'}`,
              }}>{l}</button>
            ))}
          </div>

          {hata && <div className="hata" style={{ marginBottom: 14 }}>{hata}</div>}

          <form onSubmit={gonder}>
            <div className="grid-2" style={{ marginBottom: 14 }}>
              <div>
                <label className="etiket">Ad Soyad *</label>
                <input className="input" name="ad_soyad" value={form.ad_soyad} onChange={degistir} required />
              </div>
              <div>
                <label className="etiket">Telefon (WhatsApp) *</label>
                <input className="input" name="telefon" type="tel" value={form.telefon} onChange={degistir} required placeholder="05xx..." />
              </div>
            </div>

            <div style={{ marginBottom: 14 }}>
              <label className="etiket">E-posta *</label>
              <input className="input" name="email" type="email" value={form.email} onChange={degistir} required />
            </div>

            <div className="grid-2" style={{ marginBottom: 14 }}>
              <div>
                <label className="etiket">Acente / Şirket Adı</label>
                <input className="input" name="acente_adi" value={form.acente_adi} onChange={degistir} />
              </div>
              <div>
                <label className="etiket">Yetki Belgesi No</label>
                <input className="input" name="yetki_no" value={form.yetki_no} onChange={degistir} />
              </div>
            </div>

            <div style={{ marginBottom: 20 }}>
              <label className="etiket">Şifre *</label>
              <input className="input" name="sifre" type="password" value={form.sifre} onChange={degistir} required />
            </div>

            <button className="btn-yesil" type="submit" disabled={yukleniyor} style={{ width: '100%' }}>
              {yukleniyor ? 'Kayıt oluşturuluyor...' : 'Kayıt Ol'}
            </button>
          </form>

          <div style={{ textAlign: 'center', marginTop: 16, fontSize: 13, color: '#64748b' }}>
            Zaten hesabın var mı? <Link to="/giris" style={{ color: '#16a34a', fontWeight: 600 }}>Giriş Yap</Link>
          </div>
        </div>

        <div style={{ textAlign: 'center', marginTop: 24, display: 'flex', gap: 12, justifyContent: 'center', flexWrap: 'wrap' }}>
          {[['hakkimizda', 'Hakkımızda'], ['fiyatlar', 'Fiyatlar'], ['iletisim', 'İletişim'], ['kvkk', 'KVKK'], ['gizlilik', 'Gizlilik']].map(([yol, ad]) => (
            <a key={yol} href={`https://backend-production-9ffc.up.railway.app/${yol}`} target="_blank" rel="noreferrer"
              style={{ fontSize: 11, color: '#94a3b8', textDecoration: 'none' }}>{ad}</a>
          ))}
        </div>
      </div>
    </div>
  );
}
