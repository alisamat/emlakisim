import React, { useState, useEffect } from 'react';
import { useAuth } from '../App';
import api from '../api';

export default function Ayarlar() {
  const { user, setUser } = useAuth();
  const [profilForm, setProfilForm] = useState({
    ad_soyad: user?.ad_soyad || '', telefon: user?.telefon || '',
    acente_adi: user?.acente_adi || '', yetki_no: user?.yetki_no || '',
  });
  const [sifreForm, setSifreForm] = useState({ eski_sifre: '', yeni_sifre: '' });
  const [logo, setLogo] = useState(localStorage.getItem('emlakisim_logo') || '');
  const [tema, setTema] = useState(localStorage.getItem('emlakisim_tema') || 'acik');
  const [aiAyar, setAiAyar] = useState({});
  const [mesaj, setMesaj] = useState('');
  const [yuk, setYuk] = useState(false);

  useEffect(() => {
    document.documentElement.setAttribute('data-tema', tema);
    localStorage.setItem('emlakisim_tema', tema);
  }, [tema]);

  useEffect(() => {
    api.get('/api/panel/ayarlar').then(r => setAiAyar(r.data.ayarlar || {})).catch(() => {});
  }, []);

  const profilKaydet = async () => {
    setYuk(true); setMesaj('');
    try { const r = await api.put('/api/auth/profil', profilForm); setUser(r.data.user); setMesaj('Profil güncellendi'); }
    catch { setMesaj('Hata'); } finally { setYuk(false); }
  };

  const aiKaydet = async () => {
    try { await api.put('/api/panel/ayarlar', { ayarlar: aiAyar }); setMesaj('AI ayarları kaydedildi'); }
    catch { setMesaj('Hata'); }
  };

  const logoYukle = (e) => {
    const file = e.target.files?.[0]; if (!file) return;
    const reader = new FileReader();
    reader.onload = (ev) => { localStorage.setItem('emlakisim_logo', ev.target.result); setLogo(ev.target.result); };
    reader.readAsDataURL(file);
  };

  const dp = e => setProfilForm(p => ({ ...p, [e.target.name]: e.target.value }));
  const Toggle = ({ label, anahtar, aciklama }) => (
    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '8px 0', borderBottom: '1px solid var(--border-light, #f1f5f9)' }}>
      <div>
        <div style={{ fontSize: 13, fontWeight: 600 }}>{label}</div>
        {aciklama && <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>{aciklama}</div>}
      </div>
      <button onClick={() => setAiAyar(p => ({ ...p, [anahtar]: !p[anahtar] }))} style={{
        width: 44, height: 24, borderRadius: 12, border: 'none', cursor: 'pointer',
        background: aiAyar[anahtar] ? '#16a34a' : '#e2e8f0', position: 'relative', transition: 'background 0.2s',
      }}>
        <div style={{ width: 20, height: 20, borderRadius: 10, background: '#fff', position: 'absolute', top: 2, left: aiAyar[anahtar] ? 22 : 2, transition: 'left 0.2s', boxShadow: '0 1px 3px rgba(0,0,0,0.2)' }} />
      </button>
    </div>
  );

  return (
    <>
      <h1 style={{ fontSize: 20, fontWeight: 800, color: 'var(--text-primary)', marginBottom: 16 }}>⚙️ Ayarlar</h1>
      {mesaj && <div className="basarili" style={{ marginBottom: 12 }}>✅ {mesaj}</div>}

      {/* Profil */}
      <div style={{ background: 'var(--bg-card)', borderRadius: 12, padding: 20, marginBottom: 16, border: '1px solid var(--border)' }}>
        <div style={{ fontWeight: 700, fontSize: 15, marginBottom: 16 }}>👤 Profil</div>
        <div className="grid-2" style={{ marginBottom: 12 }}>
          <div><label className="etiket">Ad Soyad</label><input className="input" name="ad_soyad" value={profilForm.ad_soyad} onChange={dp} /></div>
          <div><label className="etiket">Telefon</label><input className="input" name="telefon" value={profilForm.telefon} onChange={dp} /></div>
        </div>
        <div className="grid-2" style={{ marginBottom: 16 }}>
          <div><label className="etiket">Acente</label><input className="input" name="acente_adi" value={profilForm.acente_adi} onChange={dp} /></div>
          <div><label className="etiket">Yetki No</label><input className="input" name="yetki_no" value={profilForm.yetki_no} onChange={dp} /></div>
        </div>
        <button className="btn-yesil" onClick={profilKaydet} disabled={yuk} style={{ fontSize: 13 }}>Kaydet</button>
      </div>

      {/* AI Davranış */}
      <div style={{ background: 'var(--bg-card)', borderRadius: 12, padding: 20, marginBottom: 16, border: '1px solid var(--border)' }}>
        <div style={{ fontWeight: 700, fontSize: 15, marginBottom: 12 }}>🤖 AI Davranış Ayarları</div>
        <Toggle label="İşlem Onayı" anahtar="islem_onay" aciklama="Her veritabanı işleminde onay iste" />
        <Toggle label="Otomatik Eşleştirme" anahtar="otomatik_eslestirme" aciklama="Müşteri/mülk ekleyince uygun eşleşmeleri göster" />
        <Toggle label="Proaktif Öneriler" anahtar="proaktif_oneriler" aciklama="Sorulmadan akıllı öneriler sun" />
        <div style={{ padding: '8px 0', borderBottom: '1px solid var(--border-light, #f1f5f9)' }}>
          <label className="etiket">Asistan İsmi</label>
          <input className="input" value={aiAyar.asistan_ismi || ''} onChange={e => setAiAyar(p => ({ ...p, asistan_ismi: e.target.value }))} placeholder="Emlakisim AI (varsayılan)" />
        </div>
        <div style={{ padding: '8px 0', borderBottom: '1px solid var(--border-light, #f1f5f9)' }}>
          <label className="etiket">AI Dil Tonu</label>
          <select className="input" value={aiAyar.ai_tonu || 'samimi'} onChange={e => setAiAyar(p => ({ ...p, ai_tonu: e.target.value }))}>
            <option value="resmi">Resmi</option><option value="samimi">Samimi</option><option value="kisa">Kısa & Öz</option>
          </select>
        </div>
        <div style={{ padding: '8px 0', borderBottom: '1px solid var(--border-light, #f1f5f9)' }}>
          <label className="etiket">Varsayılan İşlem Türü</label>
          <select className="input" value={aiAyar.varsayilan_islem || 'kira'} onChange={e => setAiAyar(p => ({ ...p, varsayilan_islem: e.target.value }))}>
            <option value="kira">Kiralık</option><option value="satis">Satılık</option>
          </select>
        </div>
        <div className="grid-2" style={{ padding: '8px 0' }}>
          <div><label className="etiket">Varsayılan Şehir</label><input className="input" value={aiAyar.varsayilan_sehir || ''} onChange={e => setAiAyar(p => ({ ...p, varsayilan_sehir: e.target.value }))} /></div>
          <div><label className="etiket">Varsayılan İlçe</label><input className="input" value={aiAyar.varsayilan_ilce || ''} onChange={e => setAiAyar(p => ({ ...p, varsayilan_ilce: e.target.value }))} /></div>
        </div>
        <div style={{ marginTop: 8 }}>
          <label className="etiket">Mesai Dışı WhatsApp Mesajı</label>
          <textarea className="input" value={aiAyar.mesai_disi_mesaj || ''} onChange={e => setAiAyar(p => ({ ...p, mesai_disi_mesaj: e.target.value }))} rows={2} style={{ resize: 'vertical' }} placeholder="Boş bırakırsanız varsayılan mesaj gönderilir" />
        </div>

        <div style={{ fontWeight: 700, fontSize: 13, marginTop: 16, marginBottom: 8 }}>🔔 Bildirim Tercihleri</div>
        <Toggle label="Lead Bildirimleri" anahtar="bildirim_lead" aciklama="Yeni lead geldiğinde bildir" />
        <Toggle label="Görev Hatırlatmaları" anahtar="bildirim_gorev" aciklama="Zamanı gelen görevleri hatırlat" />
        <Toggle label="Yedek Uyarıları" anahtar="bildirim_yedek" aciklama="Yedek alınmadığında uyar" />
        <Toggle label="Kredi Uyarısı" anahtar="bildirim_kredi" aciklama="Kredi düşük olduğunda uyar" />

        <div style={{ fontWeight: 700, fontSize: 13, marginTop: 16, marginBottom: 8 }}>👥 Grup Ayarları</div>
        <Toggle label="Grup Davetlerini Kapat" anahtar="grup_teklif_kapali" aciklama="Yeni grup davetlerini otomatik reddet" />

        <button className="btn-yesil" onClick={aiKaydet} style={{ marginTop: 12, fontSize: 13 }}>AI Ayarlarını Kaydet</button>
      </div>

      {/* Şifre */}
      <div style={{ background: 'var(--bg-card)', borderRadius: 12, padding: 20, marginBottom: 16, border: '1px solid var(--border)' }}>
        <div style={{ fontWeight: 700, fontSize: 15, marginBottom: 16 }}>🔒 Şifre Değiştir</div>
        <div className="grid-2" style={{ marginBottom: 12 }}>
          <div><label className="etiket">Eski Şifre</label><input className="input" type="password" value={sifreForm.eski_sifre} onChange={e => setSifreForm(p => ({ ...p, eski_sifre: e.target.value }))} /></div>
          <div><label className="etiket">Yeni Şifre</label><input className="input" type="password" value={sifreForm.yeni_sifre} onChange={e => setSifreForm(p => ({ ...p, yeni_sifre: e.target.value }))} /></div>
        </div>
        <button className="btn-yesil" onClick={async () => {
          try { await api.put('/api/auth/sifre-degistir', sifreForm); setMesaj('Şifre değiştirildi'); setSifreForm({ eski_sifre: '', yeni_sifre: '' }); }
          catch (e) { setMesaj(e.response?.data?.message || 'Hata'); }
        }} style={{ fontSize: 13 }}>Şifre Değiştir</button>
      </div>

      {/* Logo & Tema */}
      <div style={{ background: 'var(--bg-card)', borderRadius: 12, padding: 20, marginBottom: 16, border: '1px solid var(--border)' }}>
        <div style={{ fontWeight: 700, fontSize: 15, marginBottom: 12 }}>🎨 Görünüm</div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 16, marginBottom: 16 }}>
          {logo ? <img src={logo} alt="Logo" style={{ width: 48, height: 48, borderRadius: 8, objectFit: 'contain' }} /> : <div style={{ width: 48, height: 48, borderRadius: 8, background: '#16a34a', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 24, color: '#fff' }}>🏠</div>}
          <label style={{ background: '#eff6ff', color: '#1d4ed8', border: '1px solid #bfdbfe', borderRadius: 8, padding: '6px 14px', fontSize: 12, fontWeight: 600, cursor: 'pointer' }}>
            Logo Yükle <input type="file" accept="image/*" onChange={logoYukle} style={{ display: 'none' }} />
          </label>
          {logo && <button onClick={() => { localStorage.removeItem('emlakisim_logo'); setLogo(''); }} style={{ background: 'none', border: 'none', color: '#dc2626', fontSize: 12, cursor: 'pointer' }}>Kaldır</button>}
        </div>
        <div style={{ display: 'flex', gap: 12 }}>
          {[['acik', '☀️ Açık'], ['karanlik', '🌙 Karanlık']].map(([v, l]) => (
            <button key={v} onClick={() => setTema(v)} style={{
              flex: 1, padding: 12, borderRadius: 10, fontSize: 13, fontWeight: 600, cursor: 'pointer',
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
