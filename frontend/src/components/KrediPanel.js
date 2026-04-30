import React, { useState, useEffect } from 'react';
import api from '../api';

const PAKETLER = [
  { id: 'temel', ad: 'Temel Paket', kredi: 3000, usd: 8, aciklama: 'Küçük projeler için' },
  { id: 'standart', ad: 'Standart Paket', kredi: 12000, usd: 32, aciklama: 'Orta ölçekli projeler için', populer: true },
  { id: 'profesyonel', ad: 'Profesyonel Paket', kredi: 30000, usd: 80, aciklama: 'Yoğun kullanım için' },
  { id: 'kurumsal', ad: 'Kurumsal Paket', kredi: 120000, usd: 320, aciklama: 'Büyük ölçekli projeler için' },
];

const KURU = 37.65; // USD/TRY tahmini

export default function KrediPanel({ acik, onKapat, kredi }) {
  const [tab, setTab] = useState('genel');
  const [faturaForm, setFaturaForm] = useState({
    sirket_adi: '', vergi_no: '', vergi_dairesi: '', il: '', adres: '', email: '', telefon: '',
  });
  const [faturalar] = useState([]);
  const [maliyet, setMaliyet] = useState(null);

  useEffect(() => {
    if (acik) {
      api.get('/api/panel/egitim/maliyet-rapor').then(r => setMaliyet(r.data)).catch(() => {});
    }
  }, [acik]);

  if (!acik) return null;

  const f = v => Number(v || 0).toLocaleString('tr-TR');
  const tryFiyat = usd => (usd * KURU).toFixed(2);
  const kdvliFiyat = usd => (usd * KURU * 1.20).toFixed(2);

  const satirAl = (paket) => {
    alert(`${paket.ad} — ${paket.kredi} kredi\n\nÖdeme entegrasyonu yakında aktif olacaktır.\n\nFiyat: ${tryFiyat(paket.usd)} TL (KDV Dahil ${kdvliFiyat(paket.usd)} TL)`);
  };

  return (
    <div style={{ position: 'fixed', inset: 0, zIndex: 200, display: 'flex', justifyContent: 'center', alignItems: 'center' }}>
      <div style={{ position: 'absolute', inset: 0, background: 'rgba(0,0,0,0.5)' }} onClick={onKapat} />
      <div style={{
        position: 'relative', width: '95%', maxWidth: 600, maxHeight: '90vh', overflowY: 'auto',
        background: 'var(--bg-card, #fff)', borderRadius: 16, boxShadow: '0 20px 60px rgba(0,0,0,0.2)',
      }}>
        {/* Header */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '16px 20px', borderBottom: '1px solid var(--border, #e2e8f0)' }}>
          <span style={{ fontWeight: 800, fontSize: 16 }}>💳 Kredi Yönetimi</span>
          <button onClick={onKapat} style={{ background: 'none', border: 'none', fontSize: 20, cursor: 'pointer', color: '#94a3b8' }}>✕</button>
        </div>

        {/* Tabs */}
        <div style={{ display: 'flex', borderBottom: '1px solid var(--border, #e2e8f0)' }}>
          {[['genel', '📊 Genel Bakış'], ['satin', '🛒 Kredi Satın Al'], ['fatura_bilgi', '📝 Fatura Bilgileri'], ['faturalar', '🧾 Faturalarım']].map(([k, l]) => (
            <button key={k} onClick={() => setTab(k)} style={{
              flex: 1, padding: '10px', border: 'none', cursor: 'pointer', fontSize: 12, fontWeight: 600,
              background: tab === k ? 'var(--bg-card, #fff)' : '#f8fafc',
              color: tab === k ? '#16a34a' : '#64748b',
              borderBottom: tab === k ? '2px solid #16a34a' : 'none',
            }}>{l}</button>
          ))}
        </div>

        <div style={{ padding: 20 }}>
          {/* Genel Bakış */}
          {tab === 'genel' && (
            <>
              <div style={{ textAlign: 'center', marginBottom: 20 }}>
                <div style={{ fontSize: 12, color: '#64748b' }}>Kalan Kredi</div>
                <div style={{ fontSize: 36, fontWeight: 800, color: '#16a34a' }}>{f(kredi)}</div>
                <div style={{ fontSize: 13, color: '#94a3b8' }}>{f(kredi)} kredi</div>
              </div>
              <div className="grid-2" style={{ gap: 8, marginBottom: 16 }}>
                <div style={{ background: '#f8fafc', borderRadius: 8, padding: 12, textAlign: 'center' }}>
                  <div style={{ fontSize: 11, color: '#64748b' }}>Toplam Kullanılan</div>
                  <div style={{ fontSize: 18, fontWeight: 700, color: '#f59e0b' }}>{f(maliyet?.toplam_kredi || 0)}</div>
                </div>
                <div style={{ background: '#f8fafc', borderRadius: 8, padding: 12, textAlign: 'center' }}>
                  <div style={{ fontSize: 11, color: '#64748b' }}>İşlem Sayısı</div>
                  <div style={{ fontSize: 18, fontWeight: 700, color: '#3b82f6' }}>{maliyet?.islem_sayisi || 0}</div>
                </div>
              </div>
              <div style={{ textAlign: 'center' }}>
                <button onClick={() => setTab('satin')} className="btn-yesil" style={{ fontSize: 14 }}>🛒 Kredi Satın Al</button>
              </div>
            </>
          )}

          {/* Kredi Satın Al */}
          {tab === 'satin' && (
            <>
              <div style={{ background: '#eff6ff', borderRadius: 8, padding: 12, marginBottom: 16, fontSize: 11, color: '#1e40af', lineHeight: 1.6 }}>
                <strong>📋 Kullanım Şartları:</strong><br />
                ⏰ Her paket alımında kredilerinizin süresi 1 yıl uzar<br />
                🔄 Yeni paket alırsanız önceki krediler korunur<br />
                🚫 Satın alınan kredilerin iadesi yapılmaz<br />
                💳 Tüm ödemeler güvenli ödeme sistemi üzerinden gerçekleşir
              </div>
              {PAKETLER.map(p => (
                <div key={p.id} style={{
                  background: 'var(--bg-card)', borderRadius: 12, padding: 16, marginBottom: 10,
                  border: `2px solid ${p.populer ? '#16a34a' : 'var(--border, #e2e8f0)'}`,
                  position: 'relative',
                }}>
                  {p.populer && <div style={{ position: 'absolute', top: -10, right: 16, background: '#16a34a', color: '#fff', borderRadius: 12, padding: '2px 12px', fontSize: 11, fontWeight: 700 }}>En Popüler</div>}
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <div>
                      <div style={{ fontWeight: 700, fontSize: 15 }}>{p.ad}</div>
                      <div style={{ fontSize: 20, fontWeight: 800, color: '#16a34a' }}>{f(p.kredi)} <span style={{ fontSize: 12, fontWeight: 400 }}>kredi</span></div>
                      <div style={{ fontSize: 11, color: '#64748b' }}>⏰ 365 gün geçerli</div>
                      <div style={{ fontSize: 13, marginTop: 4 }}>
                        <strong>{f(parseFloat(tryFiyat(p.usd)))} TL</strong>
                        <span style={{ fontSize: 11, color: '#94a3b8', marginLeft: 4 }}>(KDV Dahil {f(parseFloat(kdvliFiyat(p.usd)))})</span>
                      </div>
                      <div style={{ fontSize: 11, color: '#94a3b8' }}>({`$${p.usd} USD`})</div>
                      <div style={{ fontSize: 11, color: '#64748b', marginTop: 2 }}>{p.aciklama}</div>
                    </div>
                    <button onClick={() => satirAl(p)} className="btn-yesil" style={{ fontSize: 13, whiteSpace: 'nowrap' }}>Satın Al</button>
                  </div>
                </div>
              ))}
            </>
          )}

          {/* Fatura Bilgileri */}
          {tab === 'fatura_bilgi' && (
            <>
              <div style={{ fontWeight: 700, fontSize: 14, marginBottom: 12 }}>Fatura Bilgileri</div>
              <div className="grid-2" style={{ marginBottom: 12 }}>
                <div><label className="etiket">Şirket/Kişi Adı *</label><input className="input" value={faturaForm.sirket_adi} onChange={e => setFaturaForm(p => ({ ...p, sirket_adi: e.target.value }))} /></div>
                <div><label className="etiket">Vergi No / TC *</label><input className="input" value={faturaForm.vergi_no} onChange={e => setFaturaForm(p => ({ ...p, vergi_no: e.target.value }))} /></div>
              </div>
              <div className="grid-2" style={{ marginBottom: 12 }}>
                <div><label className="etiket">Vergi Dairesi</label><input className="input" value={faturaForm.vergi_dairesi} onChange={e => setFaturaForm(p => ({ ...p, vergi_dairesi: e.target.value }))} /></div>
                <div><label className="etiket">İl *</label><input className="input" value={faturaForm.il} onChange={e => setFaturaForm(p => ({ ...p, il: e.target.value }))} /></div>
              </div>
              <div style={{ marginBottom: 12 }}>
                <label className="etiket">Adres *</label>
                <textarea className="input" value={faturaForm.adres} onChange={e => setFaturaForm(p => ({ ...p, adres: e.target.value }))} rows={2} style={{ resize: 'vertical' }} />
              </div>
              <div className="grid-2" style={{ marginBottom: 16 }}>
                <div><label className="etiket">E-posta</label><input className="input" value={faturaForm.email} onChange={e => setFaturaForm(p => ({ ...p, email: e.target.value }))} /></div>
                <div><label className="etiket">Telefon</label><input className="input" value={faturaForm.telefon} onChange={e => setFaturaForm(p => ({ ...p, telefon: e.target.value }))} /></div>
              </div>
              <button className="btn-yesil" onClick={() => alert('Fatura bilgileri kaydedildi')} style={{ fontSize: 13 }}>Güncelle</button>
            </>
          )}

          {/* Faturalarım */}
          {tab === 'faturalar' && (
            <>
              <div style={{ fontWeight: 700, fontSize: 14, marginBottom: 12 }}>Fatura Geçmişi</div>
              {faturalar.length === 0 ? (
                <div style={{ textAlign: 'center', color: '#94a3b8', padding: 30, fontSize: 13 }}>Henüz fatura yok</div>
              ) : (
                <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 12 }}>
                  <thead><tr style={{ borderBottom: '2px solid var(--border)' }}>
                    <th style={{ textAlign: 'left', padding: 6 }}>Fatura No</th>
                    <th style={{ padding: 6 }}>Tarih</th>
                    <th style={{ padding: 6 }}>Paket</th>
                    <th style={{ textAlign: 'right', padding: 6 }}>Tutar</th>
                    <th style={{ padding: 6 }}>Durum</th>
                  </tr></thead>
                  <tbody>{faturalar.map(f => (
                    <tr key={f.id} style={{ borderBottom: '1px solid var(--border-light)' }}>
                      <td style={{ padding: 6 }}>{f.fatura_no}</td>
                      <td style={{ padding: 6, textAlign: 'center' }}>{f.tarih}</td>
                      <td style={{ padding: 6, textAlign: 'center' }}>{f.paket}</td>
                      <td style={{ padding: 6, textAlign: 'right' }}>{f.tutar}</td>
                      <td style={{ padding: 6, textAlign: 'center' }}>{f.durum}</td>
                    </tr>
                  ))}</tbody>
                </table>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
}
