import React, { useState, useEffect, useCallback } from 'react';
import api from '../api';

const SICAKLIK = {
  sicak: { label: '🔥 Sıcak', renk: '#dc2626', bg: '#fef2f2' },
  orta:  { label: '🌤 Orta',  renk: '#f59e0b', bg: '#fffbeb' },
  soguk: { label: '❄️ Soğuk', renk: '#3b82f6', bg: '#eff6ff' },
};

// İşlem türüne göre dinamik müşteri detay alanları
const MUSTERI_DETAY = {
  _ortak: [
    { key: 'email', label: 'E-posta', tip: 'text' },
    { key: 'meslek', label: 'Meslek', tip: 'text' },
    { key: 'dogum_tarihi', label: 'Doğum Tarihi', tip: 'date' },
    { key: 'adres', label: 'Adres', tip: 'text' },
    { key: 'kaynak', label: 'Nereden Geldi', tip: 'select', secenekler: ['WhatsApp', 'Web', 'Telefon', 'Referans', 'İlan', 'Diğer'] },
    { key: 'iletisim_tercihi', label: 'İletişim Tercihi', tip: 'select', secenekler: ['WhatsApp', 'Telefon', 'E-posta', 'Yüz yüze'] },
  ],
  kira: [
    { key: 'tercih_sehir', label: 'Tercih Şehir', tip: 'text' },
    { key: 'tercih_ilce', label: 'Tercih İlçe', tip: 'text' },
    { key: 'tercih_semt', label: 'Tercih Semt/Mahalle', tip: 'text' },
    { key: 'tercih_oda', label: 'Tercih Oda Sayısı', tip: 'text', placeholder: '2+1, 3+1' },
    { key: 'tercih_tip', label: 'Tercih Emlak Tipi', tip: 'select', secenekler: ['Daire', 'Villa', 'Ofis', 'Dükkan', 'Farketmez'] },
    { key: 'tercih_esyali', label: 'Eşyalı Tercih', tip: 'select', secenekler: ['Eşyalı', 'Boş', 'Farketmez'] },
    { key: 'tasinma_tarihi', label: 'Taşınma Tarihi', tip: 'date' },
    { key: 'kefil', label: 'Kefil Var mı', tip: 'select', secenekler: ['Evet', 'Hayır'] },
    { key: 'evcil_hayvan', label: 'Evcil Hayvan', tip: 'select', secenekler: ['Var', 'Yok'] },
    { key: 'sigara', label: 'Sigara', tip: 'select', secenekler: ['İçiyor', 'İçmiyor'] },
  ],
  satis: [
    { key: 'tercih_sehir', label: 'Tercih Şehir', tip: 'text' },
    { key: 'tercih_ilce', label: 'Tercih İlçe', tip: 'text' },
    { key: 'tercih_semt', label: 'Tercih Semt/Mahalle', tip: 'text' },
    { key: 'tercih_oda', label: 'Tercih Oda Sayısı', tip: 'text', placeholder: '2+1, 3+1' },
    { key: 'tercih_tip', label: 'Tercih Emlak Tipi', tip: 'select', secenekler: ['Daire', 'Villa', 'Arsa', 'Ofis', 'Farketmez'] },
    { key: 'kredi_kullanimi', label: 'Kredi Kullanacak mı', tip: 'select', secenekler: ['Evet', 'Hayır', 'Belki'] },
    { key: 'yatirim_amacli', label: 'Yatırım Amaçlı mı', tip: 'select', secenekler: ['Evet', 'Hayır'] },
    { key: 'tapu_tercihi', label: 'Tapu Tercihi', tip: 'select', secenekler: ['Kat Mülkiyeti', 'Kat İrtifakı', 'Farketmez'] },
    { key: 'acil_mi', label: 'Acil mi', tip: 'select', secenekler: ['Evet', 'Hayır'] },
  ],
};

function musteriAlanlari(islem_turu) {
  return [...(MUSTERI_DETAY[islem_turu] || []), ...MUSTERI_DETAY._ortak];
}

function DetayInput({ alan, value, onChange }) {
  if (alan.tip === 'select') {
    return (
      <div>
        <label className="etiket">{alan.label}</label>
        <select className="input" value={value || ''} onChange={e => onChange(alan.key, e.target.value)}>
          <option value="">Seçiniz</option>
          {alan.secenekler.map(s => <option key={s} value={s}>{s}</option>)}
        </select>
      </div>
    );
  }
  return (
    <div>
      <label className="etiket">{alan.label}</label>
      <input className="input" type={alan.tip || 'text'} value={value || ''} placeholder={alan.placeholder || ''}
        onChange={e => onChange(alan.key, e.target.value)} />
    </div>
  );
}

function MusteriFormu({ onKaydet, onIptal, duzenle }) {
  const [form, setForm] = useState({
    ad_soyad: '', telefon: '', tc_kimlik: '', islem_turu: 'kira',
    butce_min: '', butce_max: '', tercih_notlar: '', sicaklik: 'orta',
    ...(duzenle || {}),
  });
  const [detay, setDetay] = useState(duzenle?.detaylar || {});
  const [detayAcik, setDetayAcik] = useState(false);
  const [yukleniyor, setYuk] = useState(false);
  const d = e => setForm(p => ({ ...p, [e.target.name]: e.target.value }));
  const dd = (key, val) => setDetay(p => ({ ...p, [key]: val }));

  const kaydet = async e => {
    e.preventDefault(); setYuk(true);
    try {
      const payload = { ...form, detaylar: detay };
      let r;
      if (duzenle?.id) {
        r = await api.put(`/api/panel/musteriler/${duzenle.id}`, payload);
      } else {
        r = await api.post('/api/panel/musteriler', payload);
      }
      onKaydet(r.data.musteri, !!duzenle?.id);
    } catch {} finally { setYuk(false); }
  };

  const alanlar = musteriAlanlari(form.islem_turu);

  return (
    <div style={{ background: '#fff', borderRadius: 12, padding: 20, marginBottom: 16, border: '1px solid #e2e8f0' }}>
      <div style={{ fontWeight: 700, fontSize: 15, color: '#1e293b', marginBottom: 16 }}>
        {duzenle?.id ? 'Müşteri Düzenle' : 'Yeni Müşteri'}
      </div>
      <form onSubmit={kaydet}>
        <div className="grid-2" style={{ marginBottom: 12 }}>
          <div><label className="etiket">Ad Soyad *</label><input className="input" name="ad_soyad" value={form.ad_soyad} onChange={d} required /></div>
          <div><label className="etiket">Künye / Rumuz</label><input className="input" name="kunye" value={form.kunye || ''} onChange={d} placeholder="Eyyüpteki, mimar, Samilerin..." /></div>
        </div>
        <div className="grid-2" style={{ marginBottom: 12 }}>
          <div><label className="etiket">Telefon</label><input className="input" name="telefon" value={form.telefon} onChange={d} /></div>
        </div>
        <div className="grid-2" style={{ marginBottom: 12 }}>
          <div><label className="etiket">TC Kimlik</label><input className="input" name="tc_kimlik" value={form.tc_kimlik || ''} onChange={d} maxLength={11} /></div>
          <div>
            <label className="etiket">İşlem Türü</label>
            <select className="input" name="islem_turu" value={form.islem_turu} onChange={d}>
              <option value="kira">Kiralama</option>
              <option value="satis">Satış</option>
            </select>
          </div>
        </div>
        <div className="grid-2" style={{ marginBottom: 12 }}>
          <div><label className="etiket">Min Bütçe (TL)</label><input className="input" name="butce_min" type="number" value={form.butce_min || ''} onChange={d} /></div>
          <div><label className="etiket">Max Bütçe (TL)</label><input className="input" name="butce_max" type="number" value={form.butce_max || ''} onChange={d} /></div>
        </div>
        <div style={{ marginBottom: 12 }}>
          <label className="etiket">Tercihler / Notlar</label>
          <textarea className="input" name="tercih_notlar" value={form.tercih_notlar || ''} onChange={d} rows={2} style={{ resize: 'vertical' }} />
        </div>
        <div className="grid-2" style={{ marginBottom: 16 }}>
          <div>
            <label className="etiket">Sıcaklık</label>
            <select className="input" name="sicaklik" value={form.sicaklik} onChange={d}>
              <option value="sicak">🔥 Sıcak</option>
              <option value="orta">🌤 Orta</option>
              <option value="soguk">❄️ Soğuk</option>
            </select>
          </div>
          <div>
            <label className="etiket">Grup</label>
            <input className="input" name="grup" value={form.grup || ''} onChange={d} placeholder="VIP, Yatırımcı, Kadıköy..." />
          </div>
        </div>
        {/* Dinamik detaylar */}
        <button type="button" onClick={() => setDetayAcik(p => !p)} style={{
          background: 'none', border: 'none', color: '#16a34a', fontSize: 13, fontWeight: 600,
          cursor: 'pointer', marginBottom: 12, padding: 0,
        }}>
          {detayAcik ? `▼ Detayları gizle (${alanlar.length} alan)` : `▶ Detayları göster (${alanlar.length} alan)`}
        </button>

        {detayAcik && (
          <div className="grid-2" style={{ marginBottom: 12, gap: 12 }}>
            {alanlar.map(a => <DetayInput key={a.key} alan={a} value={detay[a.key]} onChange={dd} />)}
          </div>
        )}

        <div style={{ display: 'flex', gap: 10 }}>
          <button className="btn-yesil" type="submit" disabled={yukleniyor}>{yukleniyor ? 'Kaydediliyor...' : 'Kaydet'}</button>
          <button className="btn-gri" type="button" onClick={onIptal}>İptal</button>
        </div>
      </form>
    </div>
  );
}

function BagliListe({ musteriId, tip }) {
  const [data, setData] = useState(null);
  const [secili, setSecili] = useState(null);
  const [yuk, setYuk] = useState(true);

  useEffect(() => {
    const url = tip === 'talep' ? `/api/panel/talepler?musteri_id=${musteriId}&durum=hepsi` : `/api/panel/mulkler?musteri_id=${musteriId}`;
    api.get(url).then(r => setData(tip === 'talep' ? r.data.talepler : r.data.mulkler)).catch(() => setData([])).finally(() => setYuk(false));
  }, [musteriId, tip]);

  if (yuk) return <div style={{ fontSize: 12, color: '#94a3b8', padding: 8 }}>Yükleniyor...</div>;
  if (!data || data.length === 0) return <div style={{ fontSize: 12, color: '#94a3b8', padding: 8 }}>{tip === 'talep' ? 'Bağlı talep yok' : 'Bağlı mülk yok'}</div>;

  if (secili) {
    return (
      <div style={{ background: '#f8fafc', borderRadius: 8, padding: 12, marginTop: 6, border: '1px solid #e2e8f0' }}>
        <button onClick={() => setSecili(null)} style={{ background: 'none', border: 'none', color: '#16a34a', fontSize: 12, cursor: 'pointer', marginBottom: 8 }}>← Listeye dön</button>
        {tip === 'talep' ? (
          <div style={{ fontSize: 13 }}>
            <div style={{ fontWeight: 700, marginBottom: 4 }}>{secili.yonu === 'arayan' ? '🔍 Arıyor' : '🏠 Veriyor'} · {secili.islem_turu === 'kira' ? 'Kiralık' : 'Satılık'}</div>
            {(secili.butce_min || secili.butce_max) && <div>💰 {secili.butce_min ? Number(secili.butce_min).toLocaleString('tr-TR') : '—'} — {secili.butce_max ? Number(secili.butce_max).toLocaleString('tr-TR') : '—'} TL</div>}
            {secili.tercih_oda && <div>🛏 {secili.tercih_oda}</div>}
            {secili.tercih_ilce && <div>📍 {secili.tercih_ilce} {secili.tercih_sehir || ''}</div>}
            {secili.istenen?.length > 0 && <div>✅ {secili.istenen.join(', ')}</div>}
            {secili.istenmeyen?.length > 0 && <div>❌ {secili.istenmeyen.join(', ')}</div>}
            <div style={{ color: '#94a3b8', fontSize: 11, marginTop: 4 }}>📊 {secili.durum} · {secili.olusturma ? new Date(secili.olusturma).toLocaleDateString('tr-TR') : ''}</div>
          </div>
        ) : (
          <div style={{ fontSize: 13 }}>
            <div style={{ fontWeight: 700, marginBottom: 4 }}>{secili.baslik || secili.adres || '—'}</div>
            <div>🏷 {secili.islem_turu === 'kira' ? 'Kiralık' : 'Satılık'} · {secili.tip || '—'}</div>
            <div>💰 {secili.fiyat ? Number(secili.fiyat).toLocaleString('tr-TR') + ' TL' : '—'}</div>
            {secili.oda_sayisi && <div>🛏 {secili.oda_sayisi} · {secili.metrekare || '—'}m²</div>}
            {secili.ilce && <div>📍 {secili.ilce}{secili.sehir ? `, ${secili.sehir}` : ''}</div>}
          </div>
        )}
      </div>
    );
  }

  return (
    <div style={{ marginTop: 6 }}>
      {data.map(item => (
        <div key={item.id} onClick={() => setSecili(item)} style={{
          fontSize: 12, padding: '6px 10px', marginBottom: 4, background: '#f8fafc',
          borderRadius: 6, border: '1px solid #e2e8f0', cursor: 'pointer',
          display: 'flex', justifyContent: 'space-between', alignItems: 'center',
        }}>
          {tip === 'talep' ? (
            <>
              <span>{item.yonu === 'arayan' ? '🔍' : '🏠'} {item.islem_turu === 'kira' ? 'Kiralık' : 'Satılık'}{item.tercih_oda ? ` ${item.tercih_oda}` : ''}{item.tercih_ilce ? ` ${item.tercih_ilce}` : ''}</span>
              <span style={{ color: '#64748b' }}>{item.butce_max ? Number(item.butce_max).toLocaleString('tr-TR') + ' TL' : ''}</span>
            </>
          ) : (
            <>
              <span>🏢 {item.baslik || item.adres || '—'}</span>
              <span style={{ color: '#16a34a', fontWeight: 600 }}>{item.fiyat ? Number(item.fiyat).toLocaleString('tr-TR') + ' TL' : ''}</span>
            </>
          )}
        </div>
      ))}
    </div>
  );
}

function MusteriKarti({ m, onDuzenle, onSil }) {
  const s = SICAKLIK[m.sicaklik] || SICAKLIK.orta;
  const [menuAcik, setMenuAcik] = useState(false);
  const [detayAcik, setDetayAcik] = useState(false);
  const [talepAcik, setTalepAcik] = useState(false);
  const [mulkAcik, setMulkAcik] = useState(false);
  const det = m.detaylar || {};
  const badges = Object.entries(det).filter(([, v]) => v).map(([k, v]) => {
    const alan = [...(MUSTERI_DETAY[m.islem_turu] || []), ...MUSTERI_DETAY._ortak].find(a => a.key === k);
    return alan ? `${alan.label}: ${v}` : null;
  }).filter(Boolean);

  return (
    <div style={{ background: '#fff', borderRadius: 12, padding: '14px 16px', marginBottom: 10, border: '1px solid #e2e8f0', borderLeft: `3px solid ${s.renk}` }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div style={{ flex: 1 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4, flexWrap: 'wrap' }}>
            <span style={{ fontWeight: 700, fontSize: 15, color: '#0f172a' }}>{m.ad_soyad}</span>
            {m.kunye && <span style={{ fontSize: 11, color: '#64748b', fontStyle: 'italic', marginLeft: 4 }}>({m.kunye})</span>}
            <span style={{ background: s.bg, color: s.renk, borderRadius: 6, padding: '2px 8px', fontSize: 11, fontWeight: 700 }}>{s.label}</span>
            <span style={{ background: m.islem_turu === 'kira' ? '#eff6ff' : '#fef3c7', color: m.islem_turu === 'kira' ? '#1d4ed8' : '#92400e', borderRadius: 6, padding: '2px 8px', fontSize: 11, fontWeight: 600 }}>
              {m.islem_turu === 'kira' ? 'Kiralık' : 'Satılık'}
            </span>
          </div>
          {m.telefon && <div style={{ fontSize: 13, color: '#64748b' }}>📞 {m.telefon}</div>}
          {(m.butce_min || m.butce_max) && (
            <div style={{ fontSize: 13, color: '#64748b', marginTop: 2 }}>
              💰 {m.butce_min ? Number(m.butce_min).toLocaleString('tr-TR') : '—'} — {m.butce_max ? Number(m.butce_max).toLocaleString('tr-TR') : '—'} TL
            </div>
          )}
          {m.tercih_notlar && <div style={{ fontSize: 13, color: '#94a3b8', marginTop: 4 }}>{m.tercih_notlar}</div>}
          {badges.length > 0 && (
            <>
              <button onClick={() => setDetayAcik(p => !p)} style={{
                background: 'none', border: 'none', color: '#16a34a', fontSize: 12, cursor: 'pointer', padding: 0, marginTop: 6,
              }}>
                {detayAcik ? '▼ Gizle' : `▶ ${badges.length} detay`}
              </button>
              {detayAcik && (
                <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', marginTop: 6 }}>
                  {badges.map((b, i) => (
                    <span key={i} style={{ fontSize: 11, background: '#f8fafc', border: '1px solid #e2e8f0', borderRadius: 6, padding: '2px 8px', color: '#475569' }}>{b}</span>
                  ))}
                </div>
              )}
            </>
          )}
          {/* Bağlı Talepler + Mülkler */}
          <div style={{ display: 'flex', gap: 8, marginTop: 8 }}>
            <button onClick={() => { setTalepAcik(p => !p); setMulkAcik(false); }} style={{
              padding: '4px 10px', borderRadius: 6, fontSize: 11, cursor: 'pointer', fontWeight: 600,
              background: talepAcik ? '#eff6ff' : '#f8fafc', color: talepAcik ? '#1d4ed8' : '#64748b',
              border: `1px solid ${talepAcik ? '#bfdbfe' : '#e2e8f0'}`,
            }}>📋 Talepleri</button>
            <button onClick={() => { setMulkAcik(p => !p); setTalepAcik(false); }} style={{
              padding: '4px 10px', borderRadius: 6, fontSize: 11, cursor: 'pointer', fontWeight: 600,
              background: mulkAcik ? '#f0fdf4' : '#f8fafc', color: mulkAcik ? '#16a34a' : '#64748b',
              border: `1px solid ${mulkAcik ? '#bbf7d0' : '#e2e8f0'}`,
            }}>🏢 Mülkleri</button>
          </div>
          {talepAcik && <BagliListe musteriId={m.id} tip="talep" />}
          {mulkAcik && <BagliListe musteriId={m.id} tip="mulk" />}
        </div>
        <div style={{ position: 'relative' }}>
          <button onClick={() => setMenuAcik(p => !p)} style={{
            background: 'none', border: 'none', cursor: 'pointer', fontSize: 18, color: '#94a3b8', padding: '2px 6px',
          }}>⋮</button>
          {menuAcik && (
            <div style={{
              position: 'absolute', right: 0, top: 28, background: '#fff', border: '1px solid #e2e8f0',
              borderRadius: 8, boxShadow: '0 4px 12px rgba(0,0,0,0.1)', zIndex: 10, minWidth: 140,
            }}>
              <button onClick={() => { setMenuAcik(false); onDuzenle(m); }} style={{
                display: 'block', width: '100%', padding: '8px 14px', border: 'none', background: 'none',
                textAlign: 'left', fontSize: 13, cursor: 'pointer', color: '#374151',
              }}>✏️ Düzenle</button>
              <button onClick={() => {
                setMenuAcik(false);
                const email = window.prompt('Kartı gönderilecek email:');
                if (email) api.post(`/api/panel/musteriler/${m.id}/kart-gonder`, { email }).catch(() => {});
              }} style={{
                display: 'block', width: '100%', padding: '8px 14px', border: 'none', background: 'none',
                textAlign: 'left', fontSize: 13, cursor: 'pointer', color: '#1d4ed8',
              }}>📧 Kart Gönder</button>
              {m.telefon && <button onClick={() => {
                setMenuAcik(false);
                const mesaj = window.prompt('WhatsApp mesajı:', `Merhaba ${m.ad_soyad}, Emlakisim'den arıyoruz.`);
                if (mesaj) api.post('/api/webhook/gonder', { telefon: m.telefon, mesaj }).catch(() => {});
              }} style={{
                display: 'block', width: '100%', padding: '8px 14px', border: 'none', background: 'none',
                textAlign: 'left', fontSize: 13, cursor: 'pointer', color: '#16a34a',
              }}>💬 WhatsApp Gönder</button>}
              {m.telefon && <button onClick={() => {
                setMenuAcik(false);
                const mesaj = window.prompt('SMS mesajı:', `Merhaba ${m.ad_soyad}, Emlakisim.`);
                if (mesaj) api.post('/api/panel/sms/gonder', { telefon: m.telefon, mesaj }).catch(() => {});
              }} style={{
                display: 'block', width: '100%', padding: '8px 14px', border: 'none', background: 'none',
                textAlign: 'left', fontSize: 13, cursor: 'pointer', color: '#8b5cf6',
              }}>📱 SMS Gönder</button>}
              <button onClick={() => { setMenuAcik(false); onSil(m.id); }} style={{
                display: 'block', width: '100%', padding: '8px 14px', border: 'none', background: 'none',
                textAlign: 'left', fontSize: 13, cursor: 'pointer', color: '#dc2626',
              }}>🗑 Sil</button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default function Musteriler() {
  const [musteriler, setMusteriler] = useState([]);
  const [formAcik, setFormAcik]     = useState(false);
  const [duzenle, setDuzenle]       = useState(null);
  const [yukleniyor, setYuk]        = useState(false);
  const [filtre, setFiltre]         = useState('');
  const [filtreGrup, setFiltreGrup] = useState('');
  const [arama, setArama]           = useState('');

  const yukle = useCallback(async () => {
    setYuk(true);
    try {
      const r = await api.get('/api/panel/musteriler');
      setMusteriler(r.data.musteriler || []);
    } catch {} finally { setYuk(false); }
  }, []);

  useEffect(() => { yukle(); }, [yukle]);

  const onKaydet = (m, guncelleme) => {
    if (guncelleme) {
      setMusteriler(p => p.map(x => x.id === m.id ? m : x));
    } else {
      setMusteriler(p => [m, ...p]);
    }
    setFormAcik(false);
    setDuzenle(null);
  };

  const onSil = async (id) => {
    if (!window.confirm('Bu müşteriyi silmek istediğinize emin misiniz?')) return;
    try {
      await api.delete(`/api/panel/musteriler/${id}`);
      setMusteriler(p => p.filter(x => x.id !== id));
    } catch {}
  };

  const onDuzenle = (m) => {
    setDuzenle(m);
    setFormAcik(true);
  };

  // Grupları çıkar
  const gruplar = [...new Set(musteriler.map(m => m.grup).filter(Boolean))];

  // Filtreleme + arama
  let liste = musteriler;
  if (filtre) liste = liste.filter(m => m.sicaklik === filtre);
  if (filtreGrup) liste = liste.filter(m => m.grup === filtreGrup);
  if (arama.trim()) {
    const q = arama.toLowerCase();
    liste = liste.filter(m =>
      (m.ad_soyad || '').toLowerCase().includes(q) ||
      (m.telefon || '').includes(q) ||
      (m.tercih_notlar || '').toLowerCase().includes(q)
    );
  }

  return (
    <>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
        <h1 style={{ fontSize: 20, fontWeight: 800, color: '#0f172a' }}>👥 Müşteriler <span style={{ fontSize: 14, fontWeight: 400, color: '#94a3b8' }}>({musteriler.length})</span></h1>
        <button className="btn-yesil" onClick={() => { setDuzenle(null); setFormAcik(p => !p); }}>+ Ekle</button>
      </div>

      {formAcik && (
        <MusteriFormu
          onKaydet={onKaydet}
          onIptal={() => { setFormAcik(false); setDuzenle(null); }}
          duzenle={duzenle}
        />
      )}

      {/* Arama */}
      <div style={{ marginBottom: 12 }}>
        <input
          className="input"
          placeholder="🔍 Müşteri ara (isim, telefon, tercih)..."
          value={arama}
          onChange={e => setArama(e.target.value)}
          style={{ width: '100%' }}
        />
      </div>

      {/* Sıcaklık Filtre */}
      <div style={{ display: 'flex', gap: 8, marginBottom: 8, flexWrap: 'wrap' }}>
        {[['', 'Tümü'], ['sicak', '🔥 Sıcak'], ['orta', '🌤 Orta'], ['soguk', '❄️ Soğuk']].map(([v, l]) => (
          <button key={v} onClick={() => setFiltre(v)} style={{
            padding: '6px 14px', borderRadius: 20, fontSize: 13, fontWeight: 600, cursor: 'pointer',
            background: filtre === v ? '#16a34a' : '#fff', color: filtre === v ? '#fff' : '#374151',
            border: `1px solid ${filtre === v ? '#16a34a' : '#e2e8f0'}`,
          }}>{l}</button>
        ))}
      </div>

      {/* Grup Filtre */}
      {gruplar.length > 0 && (
        <div style={{ display: 'flex', gap: 8, marginBottom: 16, flexWrap: 'wrap' }}>
          <button onClick={() => setFiltreGrup('')} style={{
            padding: '4px 12px', borderRadius: 16, fontSize: 12, fontWeight: 600, cursor: 'pointer',
            background: !filtreGrup ? '#475569' : '#fff', color: !filtreGrup ? '#fff' : '#64748b',
            border: `1px solid ${!filtreGrup ? '#475569' : '#e2e8f0'}`,
          }}>Tüm Gruplar</button>
          {gruplar.map(g => (
            <button key={g} onClick={() => setFiltreGrup(filtreGrup === g ? '' : g)} style={{
              padding: '4px 12px', borderRadius: 16, fontSize: 12, fontWeight: 600, cursor: 'pointer',
              background: filtreGrup === g ? '#475569' : '#fff', color: filtreGrup === g ? '#fff' : '#64748b',
              border: `1px solid ${filtreGrup === g ? '#475569' : '#e2e8f0'}`,
            }}>🏷 {g}</button>
          ))}
        </div>
      )}

      {yukleniyor ? (
        <div style={{ textAlign: 'center', color: '#94a3b8', padding: 40 }}>Yükleniyor…</div>
      ) : liste.length === 0 ? (
        <div style={{ textAlign: 'center', color: '#94a3b8', padding: 40, background: '#fff', borderRadius: 12 }}>
          <div style={{ fontSize: 32, marginBottom: 8 }}>👥</div>
          {arama ? 'Arama sonucu bulunamadı' : filtre ? 'Bu filtrede müşteri yok' : 'Henüz müşteri eklenmedi'}
        </div>
      ) : (
        liste.map(m => <MusteriKarti key={m.id} m={m} onDuzenle={onDuzenle} onSil={onSil} />)
      )}
    </>
  );
}
