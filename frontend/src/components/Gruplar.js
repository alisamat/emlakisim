import React, { useState, useEffect, useCallback } from 'react';
import api from '../api';

export default function Gruplar() {
  const [gruplar, setGruplar] = useState([]);
  const [davetler, setDavetler] = useState([]);
  const [secili, setSecili] = useState(null);
  const [uyeler, setUyeler] = useState([]);
  const [eslestirme, setEslestirme] = useState(null);
  const [formAcik, setFormAcik] = useState(false);
  const [form, setForm] = useState({ ad: '', slogan: '' });
  const [yuk, setYuk] = useState(false);

  const yukle = useCallback(async () => {
    setYuk(true);
    try {
      const [g, d] = await Promise.all([api.get('/api/panel/gruplar'), api.get('/api/panel/gruplar/davetlerim')]);
      setGruplar(g.data.gruplar || []); setDavetler(d.data.davetler || []);
    } catch {} finally { setYuk(false); }
  }, []);

  useEffect(() => { yukle(); }, [yukle]);

  const grupKur = async () => {
    try { await api.post('/api/panel/gruplar', form); yukle(); setFormAcik(false); setForm({ ad: '', slogan: '' }); }
    catch (e) { alert(e.response?.data?.message || 'Hata'); }
  };

  const grupSec = async (g) => {
    setSecili(g);
    try { const r = await api.get(`/api/panel/gruplar/${g.id}/uyeler`); setUyeler(r.data.uyeler || []); }
    catch {}
  };

  const davetCevapla = async (uyelikId, kabul) => {
    try { await api.put(`/api/panel/gruplar/davet/${uyelikId}`, { kabul }); yukle(); }
    catch (e) { alert(e.response?.data?.message || 'Hata'); }
  };

  const grupCik = async (gid) => {
    if (!window.confirm('Gruptan çıkmak istediğinize emin misiniz?')) return;
    try { await api.post(`/api/panel/gruplar/${gid}/cik`); setSecili(null); yukle(); }
    catch (e) { alert(e.response?.data?.message || 'Hata'); }
  };

  const ayarGuncelle = async (gid, key, value) => {
    try { await api.put(`/api/panel/gruplar/${gid}/ayarlar`, { [key]: value }); yukle(); }
    catch {}
  };

  const eslesDir = async (gid) => {
    setYuk(true);
    try { const r = await api.get(`/api/panel/gruplar/${gid}/eslestirme`); setEslestirme(r.data); }
    catch {} finally { setYuk(false); }
  };

  if (secili) return (
    <>
      <button onClick={() => { setSecili(null); setEslestirme(null); }} className="btn-gri" style={{ marginBottom: 12, fontSize: 13 }}>← Gruplarıma Dön</button>

      <div style={{ background: 'var(--bg-card)', borderRadius: 12, padding: 16, marginBottom: 16, border: '1px solid var(--border)' }}>
        <div style={{ fontWeight: 800, fontSize: 18 }}>{secili.ad}</div>
        {secili.slogan && <div style={{ fontSize: 13, color: 'var(--text-secondary)', marginTop: 2 }}>{secili.slogan}</div>}
        <div style={{ fontSize: 12, color: 'var(--text-muted)', marginTop: 4 }}>
          {secili.uye_sayisi} üye · Rol: {secili.rol === 'yonetici' ? '👑 Yönetici' : '👤 Üye'}
        </div>
        <div style={{ display: 'flex', gap: 8, marginTop: 10 }}>
          <button onClick={() => eslesDir(secili.id)} className="btn-yesil" style={{ fontSize: 12 }}>🔗 Eşleştir</button>
          <button onClick={() => grupCik(secili.id)} style={{ background: '#fef2f2', border: '1px solid #fecaca', borderRadius: 8, padding: '6px 12px', fontSize: 12, color: '#dc2626', cursor: 'pointer' }}>Çık</button>
        </div>
      </div>

      {/* Ayarlar */}
      <div style={{ background: 'var(--bg-card)', borderRadius: 12, padding: 16, marginBottom: 16, border: '1px solid var(--border)' }}>
        <div style={{ fontWeight: 700, fontSize: 14, marginBottom: 8 }}>⚙️ Paylaşım Ayarları</div>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '6px 0' }}>
          <span style={{ fontSize: 13 }}>Portföyümü gruba aç</span>
          <button onClick={() => ayarGuncelle(secili.id, 'portfoy_acik', !secili.portfoy_acik)} style={{
            width: 44, height: 24, borderRadius: 12, border: 'none', cursor: 'pointer',
            background: secili.portfoy_acik ? '#16a34a' : '#e2e8f0', position: 'relative',
          }}><div style={{ width: 20, height: 20, borderRadius: 10, background: '#fff', position: 'absolute', top: 2, left: secili.portfoy_acik ? 22 : 2, boxShadow: '0 1px 3px rgba(0,0,0,0.2)' }} /></button>
        </div>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '6px 0' }}>
          <span style={{ fontSize: 13 }}>Taleplerimizi gruba aç</span>
          <button onClick={() => ayarGuncelle(secili.id, 'talep_acik', !secili.talep_acik)} style={{
            width: 44, height: 24, borderRadius: 12, border: 'none', cursor: 'pointer',
            background: secili.talep_acik ? '#16a34a' : '#e2e8f0', position: 'relative',
          }}><div style={{ width: 20, height: 20, borderRadius: 10, background: '#fff', position: 'absolute', top: 2, left: secili.talep_acik ? 22 : 2, boxShadow: '0 1px 3px rgba(0,0,0,0.2)' }} /></button>
        </div>
      </div>

      {/* Üyeler */}
      <div style={{ background: 'var(--bg-card)', borderRadius: 12, padding: 16, marginBottom: 16, border: '1px solid var(--border)' }}>
        <div style={{ fontWeight: 700, fontSize: 14, marginBottom: 8 }}>👥 Üyeler ({uyeler.length})</div>
        {uyeler.map(u => (
          <div key={u.id} style={{ display: 'flex', justifyContent: 'space-between', padding: '4px 0', borderBottom: '1px solid var(--border-light, #f1f5f9)', fontSize: 13 }}>
            <span>{u.rol === 'yonetici' ? '👑 ' : ''}{u.ad_soyad}</span>
            <span style={{ color: 'var(--text-muted)', fontSize: 11 }}>
              {u.portfoy_acik ? '🏢' : ''} {u.talep_acik ? '👥' : ''}
            </span>
          </div>
        ))}
      </div>

      {/* Eşleştirme */}
      {eslestirme && (
        <div style={{ background: '#f0fdf4', borderRadius: 12, padding: 16, border: '1px solid #bbf7d0' }}>
          <div style={{ fontWeight: 700, fontSize: 14, color: '#16a34a', marginBottom: 8 }}>
            🔗 Eşleştirme ({eslestirme.eslesim_sayisi} eşleşme)
          </div>
          <div style={{ fontSize: 12, color: '#64748b', marginBottom: 8 }}>
            {eslestirme.portfoy_sayisi} portföy · {eslestirme.talep_sayisi} talep
          </div>
          {eslestirme.eslesimler?.slice(0, 10).map((e, i) => (
            <div key={i} style={{ padding: '4px 0', borderBottom: '1px solid #dcfce7', fontSize: 12 }}>
              {e.portfoy_tip} · {e.portfoy_ilce || '?'} · {e.portfoy_oda || '?'} · {Number(e.portfoy_fiyat).toLocaleString('tr-TR')} TL
              <span style={{ color: '#94a3b8' }}> ← bütçe: {Number(e.talep_butce).toLocaleString('tr-TR')} TL</span>
            </div>
          ))}
        </div>
      )}
    </>
  );

  return (
    <>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
        <h1 style={{ fontSize: 20, fontWeight: 800, color: 'var(--text-primary)' }}>👥 Gruplar</h1>
        <button className="btn-yesil" onClick={() => setFormAcik(p => !p)}>+ Grup Kur</button>
      </div>

      {/* Davetler */}
      {davetler.length > 0 && (
        <div style={{ background: '#fffbeb', borderRadius: 12, padding: 14, marginBottom: 16, border: '1px solid #fde68a' }}>
          <div style={{ fontWeight: 700, fontSize: 13, color: '#92400e', marginBottom: 6 }}>📩 Grup Davetleri</div>
          {davetler.map(d => (
            <div key={d.uyelik_id} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '4px 0' }}>
              <span style={{ fontSize: 13 }}>{d.grup_ad}</span>
              <div style={{ display: 'flex', gap: 6 }}>
                <button onClick={() => davetCevapla(d.uyelik_id, true)} style={{ background: '#16a34a', color: '#fff', border: 'none', borderRadius: 6, padding: '4px 12px', fontSize: 11, cursor: 'pointer' }}>Kabul</button>
                <button onClick={() => davetCevapla(d.uyelik_id, false)} style={{ background: '#fef2f2', color: '#dc2626', border: '1px solid #fecaca', borderRadius: 6, padding: '4px 12px', fontSize: 11, cursor: 'pointer' }}>Red</button>
              </div>
            </div>
          ))}
        </div>
      )}

      {formAcik && (
        <div style={{ background: 'var(--bg-card)', borderRadius: 12, padding: 20, marginBottom: 16, border: '1px solid var(--border)' }}>
          <div className="grid-2" style={{ marginBottom: 12 }}>
            <div><label className="etiket">Grup Adı *</label><input className="input" value={form.ad} onChange={e => setForm(p => ({ ...p, ad: e.target.value }))} required /></div>
            <div><label className="etiket">Slogan</label><input className="input" value={form.slogan} onChange={e => setForm(p => ({ ...p, slogan: e.target.value }))} /></div>
          </div>
          <div style={{ display: 'flex', gap: 10 }}>
            <button className="btn-yesil" onClick={grupKur}>Kur</button>
            <button className="btn-gri" onClick={() => setFormAcik(false)}>İptal</button>
          </div>
        </div>
      )}

      {yuk ? <div style={{ textAlign: 'center', color: '#94a3b8', padding: 40 }}>Yükleniyor…</div> :
        gruplar.length === 0 ? <div style={{ textAlign: 'center', color: '#94a3b8', padding: 40, background: 'var(--bg-card)', borderRadius: 12 }}>Henüz grubunuz yok</div> :
        gruplar.map(g => (
          <div key={g.id} onClick={() => grupSec(g)} style={{
            background: 'var(--bg-card)', borderRadius: 12, padding: '14px 16px', marginBottom: 8,
            border: '1px solid var(--border)', cursor: 'pointer', borderLeft: `3px solid ${g.rol === 'yonetici' ? '#f59e0b' : '#3b82f6'}`,
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div>
                <span style={{ fontWeight: 700, fontSize: 15 }}>{g.ad}</span>
                <span style={{ marginLeft: 8, fontSize: 11, color: 'var(--text-muted)' }}>{g.rol === 'yonetici' ? '👑 Yönetici' : '👤 Üye'}</span>
              </div>
              <span style={{ fontSize: 12, color: 'var(--text-muted)' }}>{g.uye_sayisi} üye</span>
            </div>
            {g.slogan && <div style={{ fontSize: 12, color: 'var(--text-secondary)', marginTop: 2 }}>{g.slogan}</div>}
          </div>
        ))
      }
    </>
  );
}
