import React, { useState, useEffect } from 'react';
import api from '../api';

export default function IlanOCR() {
  const [hafiza, setHafiza] = useState([]);
  const [sonuc, setSonuc] = useState(null);
  const [karsilastirma, setKarsilastirma] = useState('');
  const [yuk, setYuk] = useState(false);

  const yukle = () => { api.get('/api/panel/gelismis/ilan-hafiza').then(r => setHafiza(r.data.ilanlar || [])).catch(() => {}); };
  useEffect(() => { yukle(); }, []);

  const fotoOku = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setYuk(true); setSonuc(null);
    const formData = new FormData();
    formData.append('image', file);
    try {
      const r = await api.post('/api/panel/gelismis/ilan-ocr', formData, { headers: { 'Content-Type': 'multipart/form-data' } });
      setSonuc(r.data.ilan);
      yukle();
    } catch {} finally { setYuk(false); }
  };

  const karsilastir = async () => {
    if (hafiza.length < 2) { alert('En az 2 ilan gerekli'); return; }
    setYuk(true);
    try {
      const r = await api.post('/api/panel/gelismis/ilan-karsilastir', {});
      setKarsilastirma(r.data.analiz || '');
    } catch {} finally { setYuk(false); }
  };

  const temizle = async () => {
    await api.delete('/api/panel/gelismis/ilan-hafiza').catch(() => {});
    setHafiza([]); setSonuc(null); setKarsilastirma('');
  };

  const portfoyeEkle = async (ilan) => {
    try {
      await api.post('/api/panel/mulkler', {
        baslik: ilan.baslik, adres: ilan.adres, sehir: ilan.sehir, ilce: ilan.ilce,
        tip: ilan.tip || 'daire', islem_turu: ilan.islem_turu || 'satis',
        fiyat: ilan.fiyat, oda_sayisi: ilan.oda_sayisi,
        detaylar: { brut_m2: ilan.brut_m2, net_m2: ilan.net_m2, bina_yasi: ilan.bina_yasi,
                    bulundugu_kat: ilan.kat, isinma: ilan.isinma, esyali: ilan.esyali },
      });
      alert('Portföye eklendi!');
    } catch {}
  };

  const f = v => v ? Number(v).toLocaleString('tr-TR') : '—';

  return (
    <>
      <h1 style={{ fontSize: 20, fontWeight: 800, color: 'var(--text-primary)', marginBottom: 8 }}>📸 İlan OCR & Karşılaştırma</h1>
      <p style={{ fontSize: 13, color: 'var(--text-secondary)', marginBottom: 16 }}>İlan sitesinden fotoğraf çekin, AI bilgileri okusun</p>

      {/* Fotoğraf çek */}
      <div style={{ display: 'flex', gap: 10, marginBottom: 16, flexWrap: 'wrap' }}>
        <label style={{ flex: '1 1 200px', padding: 20, borderRadius: 12, border: '2px dashed var(--border)', textAlign: 'center', cursor: 'pointer', background: 'var(--bg-card)' }}>
          {yuk ? '⏳ Okunuyor...' : '📸 İlan Fotoğrafı Çek / Seç'}
          <input type="file" accept="image/*" capture="environment" onChange={fotoOku} style={{ display: 'none' }} disabled={yuk} />
        </label>
        {hafiza.length >= 2 && (
          <button onClick={karsilastir} disabled={yuk} style={{
            flex: '1 1 200px', padding: 20, borderRadius: 12, border: '2px solid #16a34a',
            background: '#f0fdf4', color: '#16a34a', fontWeight: 700, fontSize: 14, cursor: 'pointer',
          }}>🔗 {hafiza.length} İlanı Karşılaştır</button>
        )}
      </div>

      {/* Son okunan */}
      {sonuc && (
        <div style={{ background: '#f0fdf4', borderRadius: 12, padding: 16, marginBottom: 16, border: '1px solid #bbf7d0' }}>
          <div style={{ fontWeight: 700, fontSize: 14, color: '#16a34a', marginBottom: 8 }}>✅ İlan Okundu!</div>
          <div style={{ fontSize: 14, fontWeight: 700 }}>{sonuc.baslik || '—'}</div>
          <div style={{ fontSize: 13, color: '#374151' }}>📍 {sonuc.adres || ''} {sonuc.ilce || ''} {sonuc.sehir || ''}</div>
          <div style={{ fontSize: 15, fontWeight: 700, color: '#16a34a', marginTop: 4 }}>💰 {f(sonuc.fiyat)} TL</div>
          <div style={{ fontSize: 12, color: '#64748b', marginTop: 2 }}>
            {sonuc.oda_sayisi && `🛏 ${sonuc.oda_sayisi}`} {sonuc.brut_m2 && `· ${sonuc.brut_m2} m²`} {sonuc.bina_yasi != null && `· ${sonuc.bina_yasi} yaş`}
          </div>
          {sonuc.emlakci_telefon && (
            <div style={{ marginTop: 8, display: 'flex', gap: 8, alignItems: 'center' }}>
              <span style={{ fontSize: 13, fontWeight: 600 }}>📞 {sonuc.emlakci_adi || 'İlan Sahibi'}: {sonuc.emlakci_telefon}</span>
              <a href={`tel:${sonuc.emlakci_telefon}`} style={{
                background: '#16a34a', color: '#fff', borderRadius: 6, padding: '4px 12px', fontSize: 12, fontWeight: 600, textDecoration: 'none',
              }}>Ara</a>
            </div>
          )}
          <div style={{ display: 'flex', gap: 8, marginTop: 10, flexWrap: 'wrap' }}>
            <button onClick={() => portfoyeEkle(sonuc)} className="btn-yesil" style={{ fontSize: 12 }}>🏢 Portföye Ekle</button>
            <button onClick={() => {
              const metin = `📌 ${sonuc.baslik || '—'}\n📍 ${sonuc.adres || ''} ${sonuc.sehir || ''}\n💰 ${f(sonuc.fiyat)} TL\n🛏 ${sonuc.oda_sayisi || ''} · ${sonuc.brut_m2 || ''} m²\n📞 ${sonuc.emlakci_telefon || '—'}`;
              if (navigator.share) navigator.share({ text: metin });
              else navigator.clipboard.writeText(metin);
            }} style={{ background: '#eff6ff', border: '1px solid #bfdbfe', borderRadius: 8, padding: '4px 12px', fontSize: 12, cursor: 'pointer', color: '#1d4ed8', fontWeight: 600 }}>📤 Paylaş</button>
            <button onClick={() => navigator.clipboard.writeText(JSON.stringify(sonuc, null, 2))} className="btn-gri" style={{ fontSize: 12 }}>📋 JSON Kopyala</button>
          </div>
        </div>
      )}

      {/* Karşılaştırma sonucu */}
      {karsilastirma && (
        <div style={{ background: '#eff6ff', borderRadius: 12, padding: 16, marginBottom: 16, border: '1px solid #bfdbfe' }}>
          <div style={{ fontWeight: 700, fontSize: 14, color: '#1d4ed8', marginBottom: 8 }}>🔗 Karşılaştırma Analizi</div>
          <div style={{ fontSize: 13, color: '#1e40af', lineHeight: 1.7, whiteSpace: 'pre-wrap' }}>{karsilastirma}</div>
        </div>
      )}

      {/* Hafıza */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
        <div style={{ fontWeight: 700, fontSize: 14 }}>📂 Hafızadaki İlanlar ({hafiza.length}/20)</div>
        {hafiza.length > 0 && <button onClick={temizle} style={{ background: 'none', border: 'none', color: '#dc2626', fontSize: 12, cursor: 'pointer' }}>Tümünü Temizle</button>}
      </div>

      {hafiza.length === 0 ? (
        <div style={{ textAlign: 'center', padding: 30, color: '#94a3b8', background: 'var(--bg-card)', borderRadius: 12, fontSize: 13 }}>
          Fotoğraf çekerek ilan ekleyin
        </div>
      ) : hafiza.map((ilan, i) => (
        <div key={i} style={{
          background: 'var(--bg-card)', borderRadius: 10, padding: '10px 14px', marginBottom: 6,
          border: '1px solid var(--border)', borderLeft: '3px solid #3b82f6',
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div>
              <span style={{ fontWeight: 600, fontSize: 13 }}>{ilan.baslik || '—'}</span>
              <span style={{ marginLeft: 8, fontSize: 12, color: '#64748b' }}>{f(ilan.fiyat)} TL</span>
            </div>
            <div style={{ display: 'flex', gap: 4 }}>
              <button onClick={() => portfoyeEkle(ilan)} style={{ background: '#f0fdf4', border: 'none', borderRadius: 4, padding: '2px 8px', fontSize: 10, cursor: 'pointer', color: '#16a34a' }}>+Portföy</button>
              {ilan.emlakci_telefon && <a href={`tel:${ilan.emlakci_telefon}`} style={{ background: '#eff6ff', borderRadius: 4, padding: '2px 8px', fontSize: 10, color: '#1d4ed8', textDecoration: 'none' }}>📞 Ara</a>}
            </div>
          </div>
        </div>
      ))}
    </>
  );
}
