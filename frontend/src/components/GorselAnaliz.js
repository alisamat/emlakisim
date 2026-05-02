import React, { useState } from 'react';
import api from '../api';

export default function GorselAnaliz() {
  const [resimler, setResimler] = useState([]);
  const [sonuc, setSonuc] = useState(null);
  const [yuk, setYuk] = useState(false);

  const resimEkle = (e) => {
    const files = Array.from(e.target.files || []);
    files.forEach(file => {
      const reader = new FileReader();
      reader.onload = (ev) => {
        const base64 = ev.target.result.split(',')[1];
        setResimler(p => [...p.slice(0, 4), { src: ev.target.result, base64 }]);
      };
      reader.readAsDataURL(file);
    });
  };

  const analiz = async () => {
    if (resimler.length === 0) return;
    setYuk(true); setSonuc(null);
    try {
      const r = await api.post('/api/panel/gorsel-analiz', { images: resimler.map(r => r.base64) });
      setSonuc(r.data.analiz);
    } catch (e) { alert(e.response?.data?.message || 'Hata'); }
    finally { setYuk(false); }
  };

  const PuanBar = ({ puan }) => (
    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
      <div style={{ flex: 1, height: 8, background: '#e2e8f0', borderRadius: 4 }}>
        <div style={{ width: `${puan}%`, height: '100%', borderRadius: 4, background: puan >= 70 ? '#16a34a' : puan >= 40 ? '#f59e0b' : '#dc2626' }} />
      </div>
      <span style={{ fontSize: 13, fontWeight: 700 }}>{puan}/100</span>
    </div>
  );

  return (
    <>
      <h1 style={{ fontSize: 20, fontWeight: 800, color: 'var(--text-primary)', marginBottom: 16 }}>📸 AI Görsel Analiz & Değerleme</h1>

      <div style={{ background: 'var(--bg-card)', borderRadius: 12, padding: 20, marginBottom: 16, border: '1px solid var(--border)' }}>
        <label style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 30, border: '2px dashed var(--border)', borderRadius: 12, cursor: 'pointer', fontSize: 14 }}>
          📸 Fotoğraf Ekle (max 5)
          <input type="file" accept="image/*" multiple onChange={resimEkle} style={{ display: 'none' }} />
        </label>
        {resimler.length > 0 && (
          <div style={{ display: 'flex', gap: 8, marginTop: 12, flexWrap: 'wrap' }}>
            {resimler.map((r, i) => (
              <div key={i} style={{ position: 'relative' }}>
                <img src={r.src} alt="" style={{ width: 100, height: 75, objectFit: 'cover', borderRadius: 8 }} />
                <button onClick={() => setResimler(p => p.filter((_, j) => j !== i))} style={{ position: 'absolute', top: -6, right: -6, width: 20, height: 20, borderRadius: 10, border: 'none', background: '#dc2626', color: '#fff', fontSize: 11, cursor: 'pointer' }}>×</button>
              </div>
            ))}
          </div>
        )}
        <button className="btn-yesil" onClick={analiz} disabled={yuk || resimler.length === 0} style={{ marginTop: 12, width: '100%' }}>
          {yuk ? '🔄 Analiz ediliyor...' : `🔍 ${resimler.length} Fotoğrafı Analiz Et`}
        </button>
      </div>

      {sonuc && !sonuc.hata && (
        <>
          {/* Tekli analiz */}
          {sonuc.durum_puani && (
            <div style={{ background: 'var(--bg-card)', borderRadius: 12, padding: 20, marginBottom: 16, border: '1px solid var(--border)' }}>
              <div style={{ fontWeight: 700, fontSize: 15, marginBottom: 12 }}>🏠 Oda Analizi: {sonuc.oda_tipi}</div>
              <PuanBar puan={sonuc.durum_puani} />
              <div style={{ fontSize: 13, color: 'var(--text-secondary)', marginTop: 8 }}>{sonuc.durum_aciklama}</div>
              <div style={{ fontSize: 13, marginTop: 8 }}>💡 Aydınlatma: {sonuc.aydinlatma} · Ferahlık: {sonuc.ferahlik}</div>
              {sonuc.pozitif_ozellikler?.length > 0 && (
                <div style={{ marginTop: 12 }}>
                  <div style={{ fontSize: 12, fontWeight: 700, color: '#16a34a' }}>✅ Güçlü Yanlar</div>
                  {sonuc.pozitif_ozellikler.map((o, i) => <div key={i} style={{ fontSize: 12, padding: '2px 0' }}>• {o}</div>)}
                </div>
              )}
              {sonuc.negatif_ozellikler?.length > 0 && (
                <div style={{ marginTop: 8 }}>
                  <div style={{ fontSize: 12, fontWeight: 700, color: '#dc2626' }}>⚠️ Zayıf Yanlar</div>
                  {sonuc.negatif_ozellikler.map((o, i) => <div key={i} style={{ fontSize: 12, padding: '2px 0' }}>• {o}</div>)}
                </div>
              )}
              {sonuc.renovasyon_onerileri?.length > 0 && (
                <div style={{ marginTop: 8 }}>
                  <div style={{ fontSize: 12, fontWeight: 700, color: '#f59e0b' }}>🔧 Renovasyon Önerileri</div>
                  {sonuc.renovasyon_onerileri.map((o, i) => <div key={i} style={{ fontSize: 12, padding: '2px 0' }}>• {o}</div>)}
                  <div style={{ fontSize: 12, marginTop: 4, color: 'var(--text-muted)' }}>
                    Tahmini maliyet: {sonuc.tahmini_renovasyon_maliyeti} (~{Number(sonuc.renovasyon_maliyet_tl || 0).toLocaleString('tr-TR')} TL)
                  </div>
                </div>
              )}
              <div style={{ marginTop: 12, padding: 12, background: '#f0fdf4', borderRadius: 8, fontSize: 13 }}>
                📊 <strong>Değer etkisi:</strong> {sonuc.deger_etkisi}
              </div>
            </div>
          )}

          {/* Çoklu analiz */}
          {sonuc.genel_durum_puani && (
            <div style={{ background: 'var(--bg-card)', borderRadius: 12, padding: 20, marginBottom: 16, border: '1px solid var(--border)' }}>
              <div style={{ fontWeight: 700, fontSize: 15, marginBottom: 12 }}>🏠 Genel Değerleme</div>
              <PuanBar puan={sonuc.genel_durum_puani} />
              <div style={{ display: 'flex', gap: 12, marginTop: 12, flexWrap: 'wrap' }}>
                <div style={{ padding: '8px 16px', background: '#eff6ff', borderRadius: 8, fontSize: 13 }}>🏷 Sınıf: <strong>{sonuc.deger_sinifi}</strong></div>
                <div style={{ padding: '8px 16px', background: '#f0fdf4', borderRadius: 8, fontSize: 13 }}>📈 Satış: <strong>{sonuc.satis_potansiyeli}</strong></div>
                <div style={{ padding: '8px 16px', background: '#fefce8', borderRadius: 8, fontSize: 13 }}>👤 Hedef: <strong>{sonuc.hedef_kitle}</strong></div>
              </div>
              {sonuc.tahmini_m2_fiyat_araligi && (
                <div style={{ marginTop: 12, padding: 12, background: '#f0fdf4', borderRadius: 8, fontSize: 13 }}>
                  💰 Tahmini m² fiyatı: <strong>{Number(sonuc.tahmini_m2_fiyat_araligi.min || 0).toLocaleString('tr-TR')} - {Number(sonuc.tahmini_m2_fiyat_araligi.max || 0).toLocaleString('tr-TR')} TL</strong>
                </div>
              )}
              {sonuc.odalar?.map((o, i) => (
                <div key={i} style={{ display: 'flex', justifyContent: 'space-between', padding: '6px 0', borderBottom: '1px solid var(--border-light, #f1f5f9)', fontSize: 13 }}>
                  <span>{o.tip}</span>
                  <span style={{ fontWeight: 700, color: o.puan >= 70 ? '#16a34a' : o.puan >= 40 ? '#f59e0b' : '#dc2626' }}>{o.puan}/100</span>
                </div>
              ))}
              <div style={{ marginTop: 12, fontSize: 13, color: 'var(--text-secondary)' }}>{sonuc.genel_degerlendirme}</div>
            </div>
          )}
        </>
      )}
    </>
  );
}
