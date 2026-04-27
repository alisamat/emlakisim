import React, { useState } from 'react';
import Layout from './Layout';
import { useAuth } from '../App';
import api from '../api';

export default function Profil() {
  const { user, setUser, cikisYap } = useAuth();
  const [form, setForm] = useState({ ad_soyad: user?.ad_soyad || '', telefon: user?.telefon || '', acente_adi: user?.acente_adi || '', yetki_no: user?.yetki_no || '' });
  const [yukleniyor, setYuk] = useState(false);
  const [mesaj, setMesaj]   = useState('');
  const [hata, setHata]     = useState('');

  const kaydet = async e => {
    e.preventDefault(); setYuk(true); setHata(''); setMesaj('');
    try {
      const r = await api.put('/api/auth/profil', form);
      setUser(r.data.user);
      setMesaj('Profil güncellendi.');
    } catch (err) {
      setHata(err.response?.data?.message || 'Güncelleme başarısız.');
    } finally { setYuk(false); }
  };

  return (
    <Layout>
      <div style={{ maxWidth: 520, margin: '0 auto' }}>
        <h1 style={{ fontSize: 20, fontWeight: 800, color: '#0f172a', marginBottom: 20 }}>👤 Profil</h1>

        {/* Kart */}
        <div style={{ background: '#f0fdf4', borderRadius: 12, padding: '16px 20px', marginBottom: 20, display: 'flex', alignItems: 'center', gap: 14, border: '1px solid #bbf7d0' }}>
          <div style={{ width: 48, height: 48, borderRadius: '50%', background: '#16a34a', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 22, color: '#fff', fontWeight: 700, flexShrink: 0 }}>
            {(user?.ad_soyad || '?')[0].toUpperCase()}
          </div>
          <div>
            <div style={{ fontWeight: 700, color: '#1e293b', fontSize: 15 }}>{user?.ad_soyad}</div>
            <div style={{ fontSize: 12, color: '#64748b' }}>{user?.email} · {user?.acente_adi || 'Acente belirtilmemiş'}</div>
          </div>
        </div>

        {/* Form */}
        <div className="kart" style={{ marginBottom: 16 }}>
          <div style={{ fontWeight: 700, color: '#1e293b', fontSize: 15, marginBottom: 16 }}>Bilgileri Güncelle</div>
          {mesaj && <div className="basarili" style={{ marginBottom: 12 }}>✅ {mesaj}</div>}
          {hata  && <div className="hata"     style={{ marginBottom: 12 }}>{hata}</div>}
          <form onSubmit={kaydet}>
            <div className="grid-2" style={{ marginBottom: 12 }}>
              <div><label className="etiket">Ad Soyad</label><input className="input" value={form.ad_soyad} onChange={e => setForm(p => ({ ...p, ad_soyad: e.target.value }))} /></div>
              <div><label className="etiket">Telefon (WhatsApp)</label><input className="input" value={form.telefon} onChange={e => setForm(p => ({ ...p, telefon: e.target.value }))} /></div>
            </div>
            <div className="grid-2" style={{ marginBottom: 16 }}>
              <div><label className="etiket">Acente / Şirket</label><input className="input" value={form.acente_adi} onChange={e => setForm(p => ({ ...p, acente_adi: e.target.value }))} /></div>
              <div><label className="etiket">Yetki Belgesi No</label><input className="input" value={form.yetki_no} onChange={e => setForm(p => ({ ...p, yetki_no: e.target.value }))} /></div>
            </div>
            <button className="btn-yesil" type="submit" disabled={yukleniyor}>
              {yukleniyor ? 'Kaydediliyor...' : 'Kaydet'}
            </button>
          </form>
        </div>

        {/* Çıkış */}
        <button onClick={cikisYap} className="btn-gri" style={{ width: '100%' }}>Çıkış Yap</button>
      </div>
    </Layout>
  );
}
