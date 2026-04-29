import React, { useState } from 'react';
import api from '../api';

const HESAP_TIPLERI = [
  { key: 'kira-vergisi', label: 'Kira Vergisi', ikon: '🧾', renk: '#dc2626' },
  { key: 'deger-artis', label: 'Değer Artış Kazancı', ikon: '📈', renk: '#f59e0b' },
  { key: 'kira-getirisi', label: 'Kira Getirisi (ROI)', ikon: '💰', renk: '#16a34a' },
  { key: 'aidat-analizi', label: 'Aidat Analizi', ikon: '🏢', renk: '#3b82f6' },
];

function HesapFormu({ tip, onSonuc }) {
  const [form, setForm] = useState({});
  const [yukleniyor, setYuk] = useState(false);
  const d = (key, val) => setForm(p => ({ ...p, [key]: val }));

  const hesapla = async () => {
    setYuk(true);
    try {
      const r = await api.post(`/api/panel/hesaplama/${tip}`, form);
      onSonuc(r.data);
    } catch {} finally { setYuk(false); }
  };

  if (tip === 'kira-vergisi') return (
    <div className="grid-2" style={{ marginBottom: 12, gap: 12 }}>
      <div><label className="etiket">Yıllık Kira Geliri (TL)</label><input className="input" type="number" value={form.yillik_kira || ''} onChange={e => d('yillik_kira', e.target.value)} placeholder="120000" /></div>
      <div><label className="etiket">İstisna Tutarı (TL)</label><input className="input" type="number" value={form.istisna || '33000'} onChange={e => d('istisna', e.target.value)} /></div>
      <div style={{ gridColumn: 'span 2' }}><button className="btn-yesil" onClick={hesapla} disabled={yukleniyor}>{yukleniyor ? 'Hesaplanıyor...' : '🧮 Hesapla'}</button></div>
    </div>
  );

  if (tip === 'deger-artis') return (
    <div className="grid-2" style={{ marginBottom: 12, gap: 12 }}>
      <div><label className="etiket">Alış Fiyatı (TL)</label><input className="input" type="number" value={form.alis_fiyati || ''} onChange={e => d('alis_fiyati', e.target.value)} /></div>
      <div><label className="etiket">Satış Fiyatı (TL)</label><input className="input" type="number" value={form.satis_fiyati || ''} onChange={e => d('satis_fiyati', e.target.value)} /></div>
      <div><label className="etiket">Alış Yılı</label><input className="input" type="number" value={form.alis_yili || '2024'} onChange={e => d('alis_yili', e.target.value)} /></div>
      <div><label className="etiket">Satış Yılı</label><input className="input" type="number" value={form.satis_yili || '2026'} onChange={e => d('satis_yili', e.target.value)} /></div>
      <div style={{ gridColumn: 'span 2' }}><button className="btn-yesil" onClick={hesapla} disabled={yukleniyor}>{yukleniyor ? 'Hesaplanıyor...' : '🧮 Hesapla'}</button></div>
    </div>
  );

  if (tip === 'kira-getirisi') return (
    <div className="grid-2" style={{ marginBottom: 12, gap: 12 }}>
      <div><label className="etiket">Mülk Fiyatı (TL)</label><input className="input" type="number" value={form.mulk_fiyati || ''} onChange={e => d('mulk_fiyati', e.target.value)} /></div>
      <div><label className="etiket">Aylık Kira (TL)</label><input className="input" type="number" value={form.aylik_kira || ''} onChange={e => d('aylik_kira', e.target.value)} /></div>
      <div><label className="etiket">Yıllık Gider (TL)</label><input className="input" type="number" value={form.yillik_gider || '0'} onChange={e => d('yillik_gider', e.target.value)} /></div>
      <div><button className="btn-yesil" onClick={hesapla} disabled={yukleniyor} style={{ marginTop: 20 }}>{yukleniyor ? '...' : '🧮 Hesapla'}</button></div>
    </div>
  );

  if (tip === 'aidat-analizi') return (
    <div className="grid-2" style={{ marginBottom: 12, gap: 12 }}>
      <div><label className="etiket">Aidat (TL)</label><input className="input" type="number" value={form.aidat || ''} onChange={e => d('aidat', e.target.value)} /></div>
      <div><label className="etiket">Aylık Kira (TL)</label><input className="input" type="number" value={form.kira || ''} onChange={e => d('kira', e.target.value)} /></div>
      <div><label className="etiket">Mülk Fiyatı (TL)</label><input className="input" type="number" value={form.mulk_fiyati || ''} onChange={e => d('mulk_fiyati', e.target.value)} /></div>
      <div><button className="btn-yesil" onClick={hesapla} disabled={yukleniyor} style={{ marginTop: 20 }}>{yukleniyor ? '...' : '🧮 Hesapla'}</button></div>
    </div>
  );

  return null;
}

function SonucGoster({ tip, sonuc }) {
  if (!sonuc) return null;

  const f = v => typeof v === 'number' ? Number(v).toLocaleString('tr-TR') : v;
  const Satir = ({ label, deger, renk }) => (
    <div style={{ display: 'flex', justifyContent: 'space-between', padding: '6px 0', borderBottom: '1px solid #f1f5f9' }}>
      <span style={{ fontSize: 13, color: '#64748b' }}>{label}</span>
      <span style={{ fontSize: 13, fontWeight: 600, color: renk || '#1e293b' }}>{deger}</span>
    </div>
  );

  return (
    <div style={{ background: '#fff', borderRadius: 12, padding: 16, border: '1px solid #e2e8f0', marginTop: 12 }}>
      <div style={{ fontWeight: 700, fontSize: 14, color: '#1e293b', marginBottom: 12 }}>📊 Sonuç</div>

      {tip === 'kira-vergisi' && <>
        <Satir label="Yıllık Kira" deger={f(sonuc.yillik_kira) + ' TL'} />
        <Satir label="İstisna" deger={f(sonuc.istisna) + ' TL'} />
        <Satir label="Matrah" deger={f(sonuc.matrah) + ' TL'} />
        <Satir label="Ödenecek Vergi" deger={f(sonuc.vergi) + ' TL'} renk="#dc2626" />
        <Satir label="Net Gelir" deger={f(sonuc.net_gelir) + ' TL'} renk="#16a34a" />
        <Satir label="Efektif Oran" deger={`%${sonuc.efektif_oran}`} />
        {sonuc.dilimler?.map((d, i) => (
          <Satir key={i} label={`  ${d.aralik} (${d.oran})`} deger={f(d.vergi) + ' TL'} />
        ))}
      </>}

      {tip === 'deger-artis' && <>
        <Satir label="Alış" deger={f(sonuc.alis_fiyati) + ' TL'} />
        <Satir label="Satış" deger={f(sonuc.satis_fiyati) + ' TL'} />
        <Satir label="Brüt Kazanç" deger={f(sonuc.brut_kazanc) + ' TL'} renk="#16a34a" />
        <Satir label="Elde Tutma" deger={`${sonuc.elde_tutma_yil} yıl`} />
        {sonuc.vergi_var_mi ? <>
          <Satir label="Matrah" deger={f(sonuc.matrah) + ' TL'} />
          <Satir label="Vergi" deger={f(sonuc.vergi) + ' TL'} renk="#dc2626" />
        </> : null}
        <div style={{ marginTop: 8, fontSize: 13, color: '#475569', background: '#f8fafc', padding: 10, borderRadius: 8 }}>{sonuc.aciklama}</div>
      </>}

      {tip === 'kira-getirisi' && <>
        <Satir label="Mülk Fiyatı" deger={f(sonuc.mulk_fiyati) + ' TL'} />
        <Satir label="Aylık Kira" deger={f(sonuc.aylik_kira) + ' TL'} />
        <Satir label="Yıllık Net" deger={f(sonuc.yillik_net) + ' TL'} />
        <Satir label="Brüt Getiri" deger={`%${sonuc.brut_getiri}`} />
        <Satir label="Net Getiri" deger={`%${sonuc.net_getiri}`} renk={sonuc.net_getiri >= 5 ? '#16a34a' : '#f59e0b'} />
        <Satir label="Geri Dönüş" deger={`${sonuc.geri_donus_yil} yıl`} />
        <div style={{ marginTop: 8, fontSize: 14, fontWeight: 600, color: '#475569' }}>{sonuc.degerlendirme}</div>
      </>}

      {tip === 'aidat-analizi' && <>
        <Satir label="Aidat" deger={f(sonuc.aidat) + ' TL'} />
        <Satir label="Aidat/Kira Oranı" deger={`%${sonuc.aidat_kira_orani}`} />
        <Satir label="Aidat/Fiyat Oranı" deger={`%${sonuc.aidat_fiyat_orani}`} />
        <div style={{ marginTop: 8, fontSize: 14, fontWeight: 600 }}>{sonuc.degerlendirme}</div>
      </>}
    </div>
  );
}

export default function Hesaplamalar() {
  const [aktifTip, setAktifTip] = useState('');
  const [sonuc, setSonuc] = useState(null);

  return (
    <>
      <h1 style={{ fontSize: 20, fontWeight: 800, color: '#0f172a', marginBottom: 16 }}>🧮 Hesaplamalar</h1>

      <div style={{ display: 'flex', gap: 10, marginBottom: 20, flexWrap: 'wrap' }}>
        {HESAP_TIPLERI.map(h => (
          <button key={h.key} onClick={() => { setAktifTip(h.key); setSonuc(null); }} style={{
            padding: '14px 20px', borderRadius: 12, fontSize: 14, fontWeight: 600, cursor: 'pointer',
            background: aktifTip === h.key ? '#f0fdf4' : '#fff', color: aktifTip === h.key ? '#16a34a' : '#374151',
            border: `2px solid ${aktifTip === h.key ? '#16a34a' : '#e2e8f0'}`, flex: '1 1 180px', textAlign: 'center',
          }}>
            <div style={{ fontSize: 24, marginBottom: 4 }}>{h.ikon}</div>
            {h.label}
          </button>
        ))}
      </div>

      {aktifTip && (
        <div style={{ background: '#fff', borderRadius: 12, padding: 20, border: '1px solid #e2e8f0' }}>
          <HesapFormu tip={aktifTip} onSonuc={setSonuc} />
          <SonucGoster tip={aktifTip} sonuc={sonuc} />
        </div>
      )}

      {!aktifTip && (
        <div style={{ textAlign: 'center', color: '#94a3b8', padding: 40, background: '#fff', borderRadius: 12 }}>
          <div style={{ fontSize: 32, marginBottom: 8 }}>🧮</div>
          Hesaplama tipini seçin
        </div>
      )}
    </>
  );
}
