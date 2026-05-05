import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import api from '../api';

const TIP_LABEL = { daire: 'Daire', villa: 'Villa', arsa: 'Arsa', dukkan: 'Dükkan', ofis: 'Ofis', depo: 'Depo', bina: 'Bina' };

// Detay key → Türkçe label
const DETAY_LABEL = {
  bulundugu_kat: 'Bulunduğu Kat', kat_sayisi: 'Kat Sayısı', bina_yasi: 'Bina Yaşı',
  isinma: 'Isıtma', isitma: 'Isıtma', mutfak: 'Mutfak', banyo_sayisi: 'Banyo Sayısı',
  balkon: 'Balkon', asansor: 'Asansör', otopark: 'Otopark', esyali: 'Eşyalı',
  site_ici: 'Site İçi', site_icerisinde: 'Site İçi', aidat: 'Aidat (TL)',
  cephe: 'Cephe', brut_metrekare: 'Brüt m²', tapu_durumu: 'Tapu Durumu',
  kullanim_durumu: 'Kullanım Durumu', bina_tipi: 'Bina Tipi', yapinin_durumu: 'Yapının Durumu',
  kiracili: 'Kiracılı', krediye_uygun: 'Krediye Uygun', imar_durumu: 'İmar Durumu',
  m2_fiyati: 'm² Fiyatı', ada_no: 'Ada No', parsel_no: 'Parsel No', pafta_no: 'Pafta No',
  kaks: 'KAKS (Emsal)', gabari: 'Gabari', takas: 'Takas', zemin_etudu: 'Zemin Etüdü',
  manzara: 'Manzara', havuz: 'Havuz', bahce: 'Bahçe', guvenlik: 'Güvenlik',
  konut_tipi: 'Konut Tipi', kimden: 'Kimden',
};

// Boolean/değer formatlama
const formatDeger = (v) => {
  if (v === true) return 'Evet';
  if (v === false) return 'Hayır';
  if (v === 'acik') return 'Açık (Amerikan)';
  if (v === 'kapali') return 'Kapalı';
  return v;
};

// Gizlenecek key'ler (açıklama ayrı gösterilir, array'ler özellikler bölümünde)
const GIZLI_KEYLER = ['aciklama', 'ic_ozellikler', 'dis_ozellikler', 'muhit', 'ulasim', 'manzara_liste'];

function PublicMulkDetay({ m, emlakci, onGeri }) {
  const [aktifResim, setAktifResim] = useState(0);
  const resimler = m.resimler || [];
  const det = m.detaylar || {};
  const detaylar = Object.entries(det).filter(([k, v]) => v && !GIZLI_KEYLER.includes(k));
  const f = v => v ? Number(v).toLocaleString('tr-TR') : '—';

  return (
    <div style={{ maxWidth: 900, margin: '0 auto', padding: 20, fontFamily: '-apple-system, BlinkMacSystemFont, sans-serif' }}>
      <button onClick={onGeri} style={{ background: 'none', border: 'none', color: '#16a34a', fontSize: 14, cursor: 'pointer', marginBottom: 16 }}>← Portföye Dön</button>
      <h1 style={{ fontSize: 22, fontWeight: 800, color: '#0f172a', marginBottom: 8 }}>{m.baslik || m.adres || '—'}</h1>
      <div style={{ fontSize: 14, color: '#64748b', marginBottom: 16 }}>📍 {m.ilce || ''}{m.sehir ? `, ${m.sehir}` : ''}</div>
      {resimler.length > 0 ? (
        <div style={{ marginBottom: 16 }}>
          <div style={{ position: 'relative' }}>
            <img src={resimler[aktifResim]?.url} alt="" style={{ width: '100%', height: 400, objectFit: 'cover', borderRadius: 12, background: '#f1f5f9' }} />
            {resimler.length > 1 && (
              <>
                {aktifResim > 0 && (
                  <button onClick={() => setAktifResim(p => p - 1)} style={{
                    position: 'absolute', left: 8, top: '50%', transform: 'translateY(-50%)',
                    background: 'rgba(0,0,0,0.5)', color: '#fff', border: 'none', borderRadius: '50%',
                    width: 40, height: 40, fontSize: 20, cursor: 'pointer',
                  }}>◀</button>
                )}
                {aktifResim < resimler.length - 1 && (
                  <button onClick={() => setAktifResim(p => p + 1)} style={{
                    position: 'absolute', right: 8, top: '50%', transform: 'translateY(-50%)',
                    background: 'rgba(0,0,0,0.5)', color: '#fff', border: 'none', borderRadius: '50%',
                    width: 40, height: 40, fontSize: 20, cursor: 'pointer',
                  }}>▶</button>
                )}
                <div style={{
                  position: 'absolute', bottom: 8, left: '50%', transform: 'translateX(-50%)',
                  background: 'rgba(0,0,0,0.5)', color: '#fff', padding: '4px 12px', borderRadius: 12, fontSize: 12,
                }}>{aktifResim + 1} / {resimler.length}</div>
              </>
            )}
          </div>
          {resimler.length > 1 && (
            <div style={{ display: 'flex', gap: 6, marginTop: 8, overflowX: 'auto' }}>
              {resimler.map((r, i) => (
                <img key={i} src={r.url} alt="" onClick={() => setAktifResim(i)}
                  style={{ width: 72, height: 54, objectFit: 'cover', borderRadius: 8, cursor: 'pointer', border: aktifResim === i ? '3px solid #16a34a' : '2px solid #e2e8f0', flexShrink: 0 }} />
              ))}
            </div>
          )}
        </div>
      ) : (
        <div style={{ width: '100%', height: 200, background: '#f1f5f9', borderRadius: 12, display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: 16, color: '#94a3b8' }}>Fotoğraf yok</div>
      )}
      <div style={{ display: 'flex', gap: 20, flexWrap: 'wrap' }}>
        <div style={{ flex: '1 1 280px' }}>
          <div style={{ background: '#f0fdf4', borderRadius: 12, padding: 20, marginBottom: 16, border: '1px solid #bbf7d0' }}>
            <div style={{ fontSize: 28, fontWeight: 800, color: '#16a34a' }}>{f(m.fiyat)} TL</div>
            <div style={{ display: 'flex', gap: 8, marginTop: 8 }}>
              <span style={{ background: m.islem_turu === 'kira' ? '#eff6ff' : '#fef3c7', color: m.islem_turu === 'kira' ? '#2563eb' : '#d97706', borderRadius: 6, padding: '4px 12px', fontSize: 12, fontWeight: 700 }}>
                {m.islem_turu === 'kira' ? 'Kiralık' : 'Satılık'}
              </span>
              <span style={{ background: '#f1f5f9', borderRadius: 6, padding: '4px 12px', fontSize: 12 }}>{TIP_LABEL[m.tip] || m.tip}</span>
            </div>
          </div>
          <div style={{ background: '#fff', borderRadius: 12, padding: 16, border: '1px solid #e2e8f0' }}>
            <div style={{ fontWeight: 700, fontSize: 14, marginBottom: 8 }}>📞 İletişim</div>
            <div style={{ fontSize: 14, fontWeight: 600 }}>{emlakci.ad_soyad}</div>
            {emlakci.acente_adi && <div style={{ fontSize: 12, color: '#64748b' }}>{emlakci.acente_adi}</div>}
            {emlakci.telefon && (
              <a href={`https://wa.me/9${emlakci.telefon.replace(/\D/g, '').replace(/^0/, '')}`} target="_blank" rel="noopener noreferrer"
                style={{ display: 'block', marginTop: 12, padding: '10px 16px', background: '#25d366', color: '#fff', borderRadius: 8, textAlign: 'center', textDecoration: 'none', fontWeight: 700, fontSize: 14 }}>
                💬 WhatsApp ile İletişim
              </a>
            )}
            {emlakci.telefon && (
              <a href={`tel:${emlakci.telefon}`} style={{ display: 'block', marginTop: 8, padding: '10px 16px', background: '#3b82f6', color: '#fff', borderRadius: 8, textAlign: 'center', textDecoration: 'none', fontWeight: 700, fontSize: 14 }}>
                📞 Ara: {emlakci.telefon}
              </a>
            )}
          </div>
        </div>
        <div style={{ flex: '1 1 280px' }}>
          {/* İlan Detayları */}
          <div style={{ background: '#fff', borderRadius: 12, padding: 16, border: '1px solid #e2e8f0' }}>
            <div style={{ fontWeight: 700, fontSize: 14, marginBottom: 8 }}>📋 İlan Detayları</div>
            {m.oda_sayisi && <div style={{ display: 'flex', justifyContent: 'space-between', padding: '6px 0', borderBottom: '1px solid #f1f5f9', fontSize: 13 }}><span style={{ color: '#64748b' }}>Oda Sayısı</span><strong>{m.oda_sayisi}</strong></div>}
            {m.metrekare && <div style={{ display: 'flex', justifyContent: 'space-between', padding: '6px 0', borderBottom: '1px solid #f1f5f9', fontSize: 13 }}><span style={{ color: '#64748b' }}>m²</span><strong>{m.metrekare}</strong></div>}
            {detaylar.map(([k, v]) => (
              <div key={k} style={{ display: 'flex', justifyContent: 'space-between', padding: '6px 0', borderBottom: '1px solid #f1f5f9', fontSize: 13 }}>
                <span style={{ color: '#64748b' }}>{DETAY_LABEL[k] || k.replace(/_/g, ' ')}</span><strong>{formatDeger(v)}</strong>
              </div>
            ))}
            {m.adres && <div style={{ marginTop: 8, fontSize: 13, color: '#64748b' }}>📍 {m.adres}</div>}
          </div>

          {/* Açıklama */}
          {det.aciklama && (
            <div style={{ marginTop: 12, background: '#fff', borderRadius: 12, padding: 16, border: '1px solid #e2e8f0' }}>
              <div style={{ fontWeight: 700, fontSize: 14, marginBottom: 8 }}>📝 Açıklama</div>
              <div style={{ fontSize: 13, color: '#374151', lineHeight: 1.7, whiteSpace: 'pre-wrap' }}>{det.aciklama}</div>
            </div>
          )}

          {/* Özellikler — badge'ler */}
          {(() => {
            const ozellikler = [];
            if (det.mutfak) ozellikler.push(det.mutfak === 'acik' ? 'Açık Mutfak' : det.mutfak === 'kapali' ? 'Kapalı Mutfak' : det.mutfak);
            if (det.asansor === true || det.asansor === 'Var') ozellikler.push('Asansör');
            if (det.balkon === true || det.balkon === 'Var') ozellikler.push('Balkon');
            if (det.esyali === true || det.esyali === 'Evet') ozellikler.push('Eşyalı');
            if (det.site_ici === true || det.site_icerisinde === 'Evet') ozellikler.push('Site İçi');
            if (det.otopark && det.otopark !== 'Yok') ozellikler.push(`${det.otopark} Otopark`);
            if (det.havuz === 'Var') ozellikler.push('Havuz');
            if (det.bahce === 'Var') ozellikler.push('Bahçe');
            if (det.guvenlik === 'Var') ozellikler.push('7/24 Güvenlik');
            if (det.krediye_uygun === true) ozellikler.push('Krediye Uygun');
            if (det.zemin_etudu === true) ozellikler.push('Zemin Etüdü Var');
            if (det.takas === true) ozellikler.push('Takas Kabul');
            if (Array.isArray(det.ic_ozellikler)) ozellikler.push(...det.ic_ozellikler);
            if (Array.isArray(det.dis_ozellikler)) ozellikler.push(...det.dis_ozellikler);
            if (ozellikler.length === 0) return null;
            return (
              <div style={{ marginTop: 12, background: '#fff', borderRadius: 12, padding: 16, border: '1px solid #e2e8f0' }}>
                <div style={{ fontWeight: 700, fontSize: 14, marginBottom: 10 }}>✨ Özellikler</div>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
                  {ozellikler.map((o, i) => (
                    <span key={i} style={{ padding: '4px 10px', borderRadius: 6, fontSize: 12, background: '#f0fdf4', color: '#166534', border: '1px solid #bbf7d0' }}>{o}</span>
                  ))}
                </div>
              </div>
            );
          })()}

          {/* Konum bilgileri */}
          {(det.muhit || det.ulasim) && (
            <div style={{ marginTop: 12, background: '#fff', borderRadius: 12, padding: 16, border: '1px solid #e2e8f0' }}>
              {Array.isArray(det.muhit) && det.muhit.length > 0 && (
                <>
                  <div style={{ fontWeight: 700, fontSize: 14, marginBottom: 8 }}>📍 Muhit</div>
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6, marginBottom: det.ulasim ? 12 : 0 }}>
                    {det.muhit.map((o, i) => <span key={i} style={{ padding: '4px 10px', borderRadius: 6, fontSize: 12, background: '#eff6ff', color: '#1e40af', border: '1px solid #bfdbfe' }}>{o}</span>)}
                  </div>
                </>
              )}
              {Array.isArray(det.ulasim) && det.ulasim.length > 0 && (
                <>
                  <div style={{ fontWeight: 700, fontSize: 14, marginBottom: 8 }}>🚇 Ulaşım</div>
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
                    {det.ulasim.map((o, i) => <span key={i} style={{ padding: '4px 10px', borderRadius: 6, fontSize: 12, background: '#fefce8', color: '#854d0e', border: '1px solid #fde68a' }}>{o}</span>)}
                  </div>
                </>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default function PublicPortfoy() {
  const { emlakciId } = useParams();
  const [data, setData] = useState(null);
  const [secili, setSecili] = useState(null);
  const [filtreIslem, setFiltreIslem] = useState('');
  const [filtreTip, setFiltreTip] = useState('');
  const [yuk, setYuk] = useState(true);

  useEffect(() => {
    api.get(`/api/public/emlakci/${emlakciId}/portfoy`).then(r => setData(r.data)).catch(() => {}).finally(() => setYuk(false));
  }, [emlakciId]);

  if (yuk) return <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh', background: '#f8fafc' }}><div style={{ fontSize: 48 }}>🏠</div></div>;
  if (!data) return <div style={{ textAlign: 'center', padding: 60, color: '#94a3b8' }}>Emlakçı bulunamadı</div>;

  const { emlakci, mulkler } = data;
  const f = v => v ? Number(v).toLocaleString('tr-TR') : '—';

  let liste = mulkler;
  if (filtreIslem) liste = liste.filter(m => m.islem_turu === filtreIslem);
  if (filtreTip) liste = liste.filter(m => m.tip === filtreTip);

  // Mülk Detay
  if (secili) {
    return <PublicMulkDetay m={secili} emlakci={emlakci} onGeri={() => setSecili(null)} />;
  }

  // Portföy Listesi
  return (
    <div style={{ maxWidth: 900, margin: '0 auto', padding: 20, fontFamily: '-apple-system, BlinkMacSystemFont, sans-serif' }}>
      {/* Header */}
      <div style={{ textAlign: 'center', marginBottom: 24 }}>
        {emlakci.logo_url ? (
          <img src={emlakci.logo_url} alt="" style={{ width: 72, height: 72, borderRadius: 16, objectFit: 'cover', marginBottom: 8, border: '2px solid #e2e8f0' }} />
        ) : (
          <img src="/logo192.png" alt="Emlakisim" style={{ width: 48, height: 48, borderRadius: 12, marginBottom: 8 }} />
        )}
        <h1 style={{ fontSize: 22, fontWeight: 800, color: '#0f172a', margin: 0 }}>{emlakci.ad_soyad}</h1>
        {emlakci.unvan && <div style={{ fontSize: 13, color: '#16a34a', fontWeight: 600 }}>{emlakci.unvan}</div>}
        {emlakci.acente_adi && <div style={{ fontSize: 14, color: '#64748b' }}>{emlakci.acente_adi}</div>}
        {emlakci.slogan && <div style={{ fontSize: 13, color: '#94a3b8', fontStyle: 'italic', marginTop: 4 }}>"{emlakci.slogan}"</div>}
        <div style={{ display: 'flex', gap: 12, justifyContent: 'center', marginTop: 8, flexWrap: 'wrap', fontSize: 13 }}>
          {emlakci.telefon && <span style={{ color: '#16a34a' }}>📞 {emlakci.telefon}</span>}
          {emlakci.telefon2 && <span style={{ color: '#64748b' }}>📱 {emlakci.telefon2}</span>}
          {emlakci.email && <span style={{ color: '#64748b' }}>📧 {emlakci.email}</span>}
        </div>
        {emlakci.adres && <div style={{ fontSize: 12, color: '#94a3b8', marginTop: 4 }}>📍 {emlakci.adres}</div>}
        <div style={{ display: 'flex', gap: 8, justifyContent: 'center', marginTop: 8 }}>
          {emlakci.yetki_no && <span style={{ fontSize: 11, background: '#f0fdf4', color: '#16a34a', padding: '2px 8px', borderRadius: 4 }}>🏛 Yetki: {emlakci.yetki_no}</span>}
          {emlakci.ruhsat_no && <span style={{ fontSize: 11, background: '#eff6ff', color: '#2563eb', padding: '2px 8px', borderRadius: 4 }}>📋 Ruhsat: {emlakci.ruhsat_no}</span>}
        </div>
        {emlakci.sosyal_medya && (
          <div style={{ display: 'flex', gap: 12, justifyContent: 'center', marginTop: 8 }}>
            {emlakci.sosyal_medya.instagram && <a href={`https://instagram.com/${emlakci.sosyal_medya.instagram.replace('@','')}`} target="_blank" rel="noopener noreferrer" style={{ fontSize: 12, color: '#e4405f' }}>📸 Instagram</a>}
            {emlakci.sosyal_medya.facebook && <a href={emlakci.sosyal_medya.facebook.startsWith('http') ? emlakci.sosyal_medya.facebook : `https://facebook.com/${emlakci.sosyal_medya.facebook}`} target="_blank" rel="noopener noreferrer" style={{ fontSize: 12, color: '#1877f2' }}>👤 Facebook</a>}
          </div>
        )}
        {emlakci.website && <div style={{ marginTop: 4 }}><a href={emlakci.website} target="_blank" rel="noopener noreferrer" style={{ fontSize: 12, color: '#16a34a' }}>🌐 {emlakci.website}</a></div>}
        <div style={{ fontSize: 13, color: '#94a3b8', marginTop: 8 }}>{mulkler.length} aktif ilan</div>
      </div>

      {/* Filtreler */}
      <div style={{ display: 'flex', gap: 8, marginBottom: 16, flexWrap: 'wrap', justifyContent: 'center' }}>
        {[['', 'Tümü'], ['kira', '🔵 Kiralık'], ['satis', '🟡 Satılık']].map(([v, l]) => (
          <button key={v} onClick={() => setFiltreIslem(v)} style={{
            padding: '6px 16px', borderRadius: 20, fontSize: 13, fontWeight: 600, cursor: 'pointer',
            background: filtreIslem === v ? '#16a34a' : '#fff', color: filtreIslem === v ? '#fff' : '#374151',
            border: `1px solid ${filtreIslem === v ? '#16a34a' : '#e2e8f0'}`,
          }}>{l}</button>
        ))}
        <span style={{ color: '#e2e8f0' }}>|</span>
        {[['', 'Hepsi'], ...Object.entries(TIP_LABEL)].map(([v, l]) => (
          <button key={v} onClick={() => setFiltreTip(v)} style={{
            padding: '4px 12px', borderRadius: 16, fontSize: 12, cursor: 'pointer',
            background: filtreTip === v ? '#475569' : '#fff', color: filtreTip === v ? '#fff' : '#64748b',
            border: `1px solid ${filtreTip === v ? '#475569' : '#e2e8f0'}`,
          }}>{l}</button>
        ))}
      </div>

      {/* Mülk Kartları */}
      {liste.length === 0 ? (
        <div style={{ textAlign: 'center', padding: 40, color: '#94a3b8' }}>Filtreye uygun ilan yok</div>
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: 16 }}>
          {liste.map(m => {
            const kapak = m.resimler?.find(r => r.ana) || m.resimler?.[0];
            return (
              <div key={m.id} onClick={() => setSecili(m)} style={{
                background: '#fff', borderRadius: 12, overflow: 'hidden', cursor: 'pointer',
                border: '1px solid #e2e8f0', boxShadow: '0 2px 8px rgba(0,0,0,0.06)',
              }}>
                {kapak ? (
                  <img src={kapak.url} alt="" style={{ width: '100%', height: 180, objectFit: 'cover' }} />
                ) : (
                  <div style={{ width: '100%', height: 180, background: '#f1f5f9', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#94a3b8', fontSize: 32 }}>🏠</div>
                )}
                <div style={{ padding: 14 }}>
                  <div style={{ fontWeight: 700, fontSize: 15, color: '#0f172a', marginBottom: 4 }}>{m.baslik || m.adres || '—'}</div>
                  <div style={{ fontSize: 12, color: '#64748b', marginBottom: 6 }}>📍 {m.ilce || ''}{m.sehir ? `, ${m.sehir}` : ''}</div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <span style={{ fontSize: 16, fontWeight: 800, color: '#16a34a' }}>{f(m.fiyat)} TL</span>
                    <div style={{ display: 'flex', gap: 6 }}>
                      <span style={{ background: m.islem_turu === 'kira' ? '#eff6ff' : '#fef3c7', color: m.islem_turu === 'kira' ? '#2563eb' : '#d97706', borderRadius: 4, padding: '2px 8px', fontSize: 11, fontWeight: 700 }}>
                        {m.islem_turu === 'kira' ? 'Kiralık' : 'Satılık'}
                      </span>
                    </div>
                  </div>
                  <div style={{ display: 'flex', gap: 12, marginTop: 6, fontSize: 12, color: '#64748b' }}>
                    {m.oda_sayisi && <span>🛏 {m.oda_sayisi}</span>}
                    {m.metrekare && <span>📐 {m.metrekare}m²</span>}
                    {m.tip && <span>{TIP_LABEL[m.tip] || m.tip}</span>}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Footer */}
      <div style={{ textAlign: 'center', marginTop: 32, padding: 16, color: '#94a3b8', fontSize: 12 }}>
        <img src="/logo192.png" alt="" style={{ width: 24, height: 24, borderRadius: 6, verticalAlign: 'middle', marginRight: 4 }} />
        Emlakisim AI ile oluşturuldu · <a href="https://emlakisim.com" style={{ color: '#16a34a' }}>emlakisim.com</a>
      </div>
    </div>
  );
}
