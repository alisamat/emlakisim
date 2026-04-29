import React, { useState } from 'react';
import api from '../api';

const ISLEMLER = [
  { key: 'musteri-excel', label: 'Excel\'den Müşteri Ekle', ikon: '👥', aciklama: 'Excel dosyasından toplu müşteri ekleyin (Sütunlar: Ad Soyad, Telefon, İşlem Türü)', accept: '.xlsx,.xls' },
  { key: 'portfoy-excel', label: 'Excel\'den Portföy Ekle', ikon: '🏢', aciklama: 'Excel dosyasından toplu mülk ekleyin (Sütunlar: Başlık, Adres, Tip, İşlem, Fiyat)', accept: '.xlsx,.xls' },
  { key: 'portfoy-ocr', label: 'Fotoğraftan Portföy Ekle', ikon: '📸', aciklama: 'Sahibinden.com ekran görüntüsü çekin, AI ilanları otomatik okuyup portföye eklesin', accept: 'image/*' },
  { key: 'rehber', label: 'Rehberden Müşteri Ekle', ikon: '📱', aciklama: 'Telefon rehberinizden kişileri müşteri olarak ekleyin', accept: null },
];

export default function TopluIslem() {
  const [aktif, setAktif] = useState('');
  const [yukleniyor, setYuk] = useState(false);
  const [sonuc, setSonuc] = useState(null);

  const dosyaYukle = async (e, tip) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setYuk(true); setSonuc(null);

    const formData = new FormData();
    if (tip === 'portfoy-ocr') formData.append('image', file);
    else formData.append('file', file);

    try {
      const r = await api.post(`/api/panel/toplu/${tip}`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      setSonuc(r.data);
    } catch (err) {
      setSonuc({ hata: err.response?.data?.message || 'Hata oluştu' });
    } finally { setYuk(false); }
  };

  return (
    <>
      <h1 style={{ fontSize: 20, fontWeight: 800, color: '#0f172a', marginBottom: 8 }}>📦 Toplu İşlem</h1>
      <p style={{ fontSize: 13, color: '#64748b', marginBottom: 16 }}>Excel, fotoğraf veya rehberden toplu veri ekleyin</p>

      <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap', marginBottom: 20 }}>
        {ISLEMLER.map(i => (
          <button key={i.key} onClick={() => { setAktif(i.key); setSonuc(null); }} style={{
            flex: '1 1 200px', padding: '16px', borderRadius: 12, border: `2px solid ${aktif === i.key ? '#16a34a' : '#e2e8f0'}`,
            background: aktif === i.key ? '#f0fdf4' : '#fff', cursor: 'pointer', textAlign: 'left',
          }}>
            <div style={{ fontSize: 28, marginBottom: 6 }}>{i.ikon}</div>
            <div style={{ fontWeight: 700, fontSize: 14, color: '#1e293b' }}>{i.label}</div>
            <div style={{ fontSize: 12, color: '#64748b', marginTop: 4 }}>{i.aciklama}</div>
          </button>
        ))}
      </div>

      {aktif && aktif !== 'rehber' && (
        <div style={{ background: '#fff', borderRadius: 12, padding: 20, border: '1px solid #e2e8f0' }}>
          <label style={{
            display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 30,
            border: '2px dashed #e2e8f0', borderRadius: 12, cursor: 'pointer',
            background: '#f8fafc', color: '#64748b', fontSize: 14,
          }}>
            {yukleniyor ? '⏳ İşleniyor...' : `📁 ${aktif.includes('ocr') ? 'Fotoğraf' : 'Excel dosyası'} seçin veya sürükleyin`}
            <input type="file" accept={ISLEMLER.find(i => i.key === aktif)?.accept}
              onChange={e => dosyaYukle(e, aktif)} style={{ display: 'none' }} disabled={yukleniyor}
              capture={aktif === 'portfoy-ocr' ? 'environment' : undefined} />
          </label>
        </div>
      )}

      {sonuc && (
        <div style={{
          marginTop: 16, borderRadius: 12, padding: 16,
          background: sonuc.hata ? '#fef2f2' : '#f0fdf4',
          border: `1px solid ${sonuc.hata ? '#fecaca' : '#bbf7d0'}`,
        }}>
          {sonuc.hata ? (
            <div style={{ color: '#dc2626', fontWeight: 600 }}>❌ {sonuc.hata}</div>
          ) : (
            <>
              <div style={{ color: '#16a34a', fontWeight: 700, fontSize: 15, marginBottom: 8 }}>
                ✅ {sonuc.eklenen} kayıt eklendi!
              </div>
              {sonuc.toplam_satir && <div style={{ fontSize: 13, color: '#64748b' }}>Toplam satır: {sonuc.toplam_satir}</div>}
              {sonuc.toplam_ilan && <div style={{ fontSize: 13, color: '#64748b' }}>Toplam ilan: {sonuc.toplam_ilan}</div>}
              {sonuc.ilanlar && (
                <div style={{ marginTop: 8 }}>
                  {sonuc.ilanlar.slice(0, 5).map((il, i) => (
                    <div key={i} style={{ fontSize: 12, color: '#475569', padding: '2px 0' }}>
                      • {il.baslik} — {il.fiyat ? `${Number(il.fiyat).toLocaleString('tr-TR')} TL` : '?'}
                    </div>
                  ))}
                </div>
              )}
            </>
          )}
        </div>
      )}
    </>
  );
}
