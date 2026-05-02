import React, { useState, useEffect } from 'react';
import api from '../api';

const PAKETLER = [
  { id: 'temel', ad: 'Temel Paket', kredi: 3000, fiyat: 250, aciklama: 'Başlangıç için' },
  { id: 'standart', ad: 'Standart Paket', kredi: 12000, fiyat: 800, aciklama: 'Aktif kullanım için', populer: true },
  { id: 'profesyonel', ad: 'Profesyonel Paket', kredi: 30000, fiyat: 1800, aciklama: 'Yoğun kullanım için' },
  { id: 'kurumsal', ad: 'Kurumsal Paket', kredi: 120000, fiyat: 6000, aciklama: 'Büyük ofisler için' },
];

export default function KrediPanel({ acik, onKapat, kredi }) {
  const [tab, setTab] = useState('genel');
  const [faturaForm, setFaturaForm] = useState({
    sirket_adi: '', vergi_no: '', vergi_dairesi: '', il: '', adres: '', email: '', telefon: '',
  });
  const [faturalar] = useState([]);
  const [maliyet, setMaliyet] = useState(null);
  const [secilenPaket, setSecilenPaket] = useState(null);
  const [kartForm, setKartForm] = useState({ kart_sahibi: '', kart_no: '', kart_ay: '', kart_yil: '', kart_cvv: '' });
  const [odemeYuk, setOdemeYuk] = useState(false);

  useEffect(() => {
    if (acik) {
      api.get('/api/panel/egitim/maliyet-rapor').then(r => setMaliyet(r.data)).catch(() => {});
    }
  }, [acik]);

  if (!acik) return null;

  const f = v => Number(v || 0).toLocaleString('tr-TR');

  const odemeBaslat = async () => {
    if (!secilenPaket) return;
    if (!kartForm.kart_sahibi || !kartForm.kart_no || !kartForm.kart_ay || !kartForm.kart_yil || !kartForm.kart_cvv) {
      alert('Tüm kart bilgilerini doldurun'); return;
    }
    setOdemeYuk(true);
    try {
      const r = await api.post('/api/odeme/kuveytturk/init', {
        paket_id: secilenPaket.id, ...kartForm,
      });
      // 3D Secure HTML'i yeni pencerede aç
      const w = window.open('', '_blank', 'width=500,height=600');
      if (w) {
        w.document.write(r.data.html);
        w.document.close();
      } else {
        alert('Pop-up engellendi. Lütfen pop-up engelleyiciyi kapatın.');
      }
    } catch (e) {
      alert(e.response?.data?.message || 'Ödeme başlatılamadı');
    } finally { setOdemeYuk(false); }
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
                <div key={p.id} onClick={() => setSecilenPaket(p)} style={{
                  background: 'var(--bg-card)', borderRadius: 12, padding: 16, marginBottom: 10, cursor: 'pointer',
                  border: `2px solid ${secilenPaket?.id === p.id ? '#16a34a' : p.populer ? '#bbf7d0' : 'var(--border, #e2e8f0)'}`,
                  position: 'relative',
                }}>
                  {p.populer && <div style={{ position: 'absolute', top: -10, right: 16, background: '#16a34a', color: '#fff', borderRadius: 12, padding: '2px 12px', fontSize: 11, fontWeight: 700 }}>En Popüler</div>}
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <div>
                      <div style={{ fontWeight: 700, fontSize: 15 }}>{p.ad}</div>
                      <div style={{ fontSize: 20, fontWeight: 800, color: '#16a34a' }}>{f(p.kredi)} <span style={{ fontSize: 12, fontWeight: 400 }}>kredi</span></div>
                      <div style={{ fontSize: 13, marginTop: 4 }}><strong>{f(p.fiyat)} TL</strong></div>
                      <div style={{ fontSize: 11, color: '#64748b' }}>{p.aciklama} · ⏰ 365 gün geçerli</div>
                    </div>
                    <div style={{ width: 24, height: 24, borderRadius: 12, border: `2px solid ${secilenPaket?.id === p.id ? '#16a34a' : '#cbd5e1'}`, background: secilenPaket?.id === p.id ? '#16a34a' : 'transparent', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                      {secilenPaket?.id === p.id && <span style={{ color: '#fff', fontSize: 14 }}>✓</span>}
                    </div>
                  </div>
                </div>
              ))}

              {/* Kart Formu */}
              {secilenPaket && (
                <div style={{ background: '#f8fafc', borderRadius: 12, padding: 16, marginTop: 12, border: '1px solid #e2e8f0' }}>
                  <div style={{ fontWeight: 700, fontSize: 14, marginBottom: 12 }}>💳 Kart Bilgileri — {secilenPaket.ad} ({f(secilenPaket.fiyat)} TL)</div>
                  <div style={{ marginBottom: 10 }}>
                    <label className="etiket">Kart Üzerindeki İsim</label>
                    <input className="input" value={kartForm.kart_sahibi} onChange={e => setKartForm(p => ({ ...p, kart_sahibi: e.target.value }))} placeholder="AD SOYAD" />
                  </div>
                  <div style={{ marginBottom: 10 }}>
                    <label className="etiket">Kart Numarası</label>
                    <input className="input" value={kartForm.kart_no} onChange={e => setKartForm(p => ({ ...p, kart_no: e.target.value.replace(/\D/g, '').slice(0, 16) }))} placeholder="1234 5678 9012 3456" maxLength={16} />
                  </div>
                  <div className="grid-2" style={{ marginBottom: 10, gap: 8 }}>
                    <div style={{ display: 'flex', gap: 8 }}>
                      <div style={{ flex: 1 }}><label className="etiket">Ay</label><input className="input" value={kartForm.kart_ay} onChange={e => setKartForm(p => ({ ...p, kart_ay: e.target.value.replace(/\D/g, '').slice(0, 2) }))} placeholder="MM" maxLength={2} /></div>
                      <div style={{ flex: 1 }}><label className="etiket">Yıl</label><input className="input" value={kartForm.kart_yil} onChange={e => setKartForm(p => ({ ...p, kart_yil: e.target.value.replace(/\D/g, '').slice(0, 2) }))} placeholder="YY" maxLength={2} /></div>
                    </div>
                    <div><label className="etiket">CVV</label><input className="input" type="password" value={kartForm.kart_cvv} onChange={e => setKartForm(p => ({ ...p, kart_cvv: e.target.value.replace(/\D/g, '').slice(0, 3) }))} placeholder="***" maxLength={3} /></div>
                  </div>
                  <button className="btn-yesil" onClick={odemeBaslat} disabled={odemeYuk} style={{ width: '100%', fontSize: 14, padding: 12 }}>
                    {odemeYuk ? '⏳ İşleniyor...' : `💳 ${f(secilenPaket.fiyat)} TL Öde — ${f(secilenPaket.kredi)} Kredi`}
                  </button>
                  <div style={{ fontSize: 10, color: '#94a3b8', marginTop: 8, textAlign: 'center' }}>🔒 256-bit SSL ile güvenli ödeme · Kuveyt Türk 3D Secure</div>
                </div>
              )}
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
