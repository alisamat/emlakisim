import React, { useState, useEffect, useCallback } from 'react';
import api from '../api';

const TIP_LABEL = { daire: 'Daire', villa: 'Villa', arsa: 'Arsa', dukkan: 'Dükkan', ofis: 'Ofis', depo: 'Depo', bina: 'Bina', ciftlik: 'Çiftlik' };

// Tip bazlı dinamik alan tanımları — yeni alan eklemek = buraya 1 satır
const DETAY_ALANLARI = {
  _ortak: [
    { key: 'brut_m2', label: 'Brüt m²', tip: 'number' },
    { key: 'net_m2', label: 'Net m²', tip: 'number' },
    { key: 'bina_yasi', label: 'Bina Yaşı', tip: 'number' },
    { key: 'kimden', label: 'Kimden', tip: 'select', secenekler: ['Sahibinden', 'Emlak Ofisinden', 'İnşaat Firmasından'] },
    { key: 'tapu_durumu', label: 'Tapu Durumu', tip: 'select', secenekler: ['Kat Mülkiyetli', 'Kat İrtifakı', 'Hisseli Tapu', 'Arsa Tapulu', 'Kooperatif'] },
    { key: 'krediye_uygun', label: 'Krediye Uygun', tip: 'select', secenekler: ['Evet', 'Hayır'] },
    { key: 'takas', label: 'Takas', tip: 'select', secenekler: ['Evet', 'Hayır'] },
    { key: 'kullanim_durumu', label: 'Kullanım Durumu', tip: 'select', secenekler: ['Boş', 'Kiracı Var', 'Mal Sahibi'] },
  ],
  daire: [
    { key: 'bulundugu_kat', label: 'Bulunduğu Kat', tip: 'text' },
    { key: 'kat_sayisi', label: 'Kat Sayısı', tip: 'number' },
    { key: 'isinma', label: 'Isınma', tip: 'select', secenekler: ['Kombi (Doğalgaz)', 'Merkezi', 'Soba', 'Klima', 'Yerden Isıtma', 'Isı Pompası'] },
    { key: 'banyo_sayisi', label: 'Banyo Sayısı', tip: 'number' },
    { key: 'mutfak', label: 'Mutfak', tip: 'select', secenekler: ['Açık (Amerikan)', 'Kapalı'] },
    { key: 'balkon', label: 'Balkon', tip: 'select', secenekler: ['Var', 'Yok'] },
    { key: 'asansor', label: 'Asansör', tip: 'select', secenekler: ['Var', 'Yok'] },
    { key: 'otopark', label: 'Otopark', tip: 'select', secenekler: ['Açık', 'Kapalı', 'Yok'] },
    { key: 'esyali', label: 'Eşyalı', tip: 'select', secenekler: ['Evet', 'Hayır'] },
    { key: 'site_icerisinde', label: 'Site İçerisinde', tip: 'select', secenekler: ['Evet', 'Hayır'] },
    { key: 'site_adi', label: 'Site Adı', tip: 'text' },
    { key: 'aidat', label: 'Aidat (TL)', tip: 'number' },
    { key: 'cephe', label: 'Cephe', tip: 'select', secenekler: ['Kuzey', 'Güney', 'Doğu', 'Batı', 'Güneydoğu', 'Güneybatı'] },
    { key: 'yapinin_durumu', label: 'Yapının Durumu', tip: 'select', secenekler: ['Sıfır', 'İkinci El', 'Tadilat Gerekli'] },
  ],
  villa: [
    { key: 'kat_sayisi', label: 'Kat Sayısı', tip: 'number' },
    { key: 'isinma', label: 'Isınma', tip: 'select', secenekler: ['Kombi (Doğalgaz)', 'Merkezi', 'Yerden Isıtma', 'Isı Pompası', 'Şömine'] },
    { key: 'banyo_sayisi', label: 'Banyo Sayısı', tip: 'number' },
    { key: 'havuz', label: 'Havuz', tip: 'select', secenekler: ['Var', 'Yok'] },
    { key: 'bahce', label: 'Bahçe', tip: 'select', secenekler: ['Var', 'Yok'] },
    { key: 'bahce_m2', label: 'Bahçe m²', tip: 'number' },
    { key: 'otopark', label: 'Otopark', tip: 'select', secenekler: ['Açık', 'Kapalı Garaj', 'Yok'] },
    { key: 'esyali', label: 'Eşyalı', tip: 'select', secenekler: ['Evet', 'Hayır'] },
    { key: 'guvenlik', label: 'Güvenlik', tip: 'select', secenekler: ['Var', 'Yok'] },
    { key: 'manzara', label: 'Manzara', tip: 'select', secenekler: ['Deniz', 'Göl', 'Dağ', 'Şehir', 'Doğa', 'Yok'] },
  ],
  arsa: [
    { key: 'imar_durumu', label: 'İmar Durumu', tip: 'select', secenekler: ['Konut İmarlı', 'Ticari İmarlı', 'Sanayi', 'Tarla', 'İmarsız', 'Karma'] },
    { key: 'gabari', label: 'Gabari', tip: 'text', placeholder: 'Örn: 5 kat' },
    { key: 'emsal', label: 'Emsal (KAKS)', tip: 'text', placeholder: 'Örn: 1.50' },
    { key: 'taks', label: 'TAKS', tip: 'text', placeholder: 'Örn: 0.30' },
    { key: 'cephe_uzunlugu', label: 'Cephe Uzunluğu (m)', tip: 'number' },
    { key: 'derinlik', label: 'Derinlik (m)', tip: 'number' },
    { key: 'yola_cephe', label: 'Yola Cephe', tip: 'select', secenekler: ['Evet', 'Hayır'] },
    { key: 'altyapi', label: 'Altyapı', tip: 'select', secenekler: ['Elektrik + Su + Doğalgaz', 'Elektrik + Su', 'Yok'] },
    { key: 'tapu_cinsi', label: 'Tapu Cinsi', tip: 'select', secenekler: ['Arsa', 'Tarla', 'Bağ', 'Bahçe'] },
  ],
  dukkan: [
    { key: 'bulundugu_kat', label: 'Bulunduğu Kat', tip: 'text' },
    { key: 'kat_sayisi', label: 'Kat Sayısı', tip: 'number' },
    { key: 'cephe_uzunlugu', label: 'Cephe Uzunluğu (m)', tip: 'number' },
    { key: 'yukseklik', label: 'Tavan Yüksekliği (m)', tip: 'number' },
    { key: 'wc', label: 'WC', tip: 'select', secenekler: ['Var', 'Yok'] },
    { key: 'vitrin', label: 'Vitrin', tip: 'select', secenekler: ['Var', 'Yok'] },
    { key: 'avm_icerisinde', label: 'AVM İçerisinde', tip: 'select', secenekler: ['Evet', 'Hayır'] },
    { key: 'aidat', label: 'Aidat (TL)', tip: 'number' },
  ],
  ofis: [
    { key: 'bulundugu_kat', label: 'Bulunduğu Kat', tip: 'text' },
    { key: 'kat_sayisi', label: 'Kat Sayısı', tip: 'number' },
    { key: 'oda_bolme', label: 'Oda/Bölme Sayısı', tip: 'number' },
    { key: 'isinma', label: 'Isınma', tip: 'select', secenekler: ['Merkezi', 'Kombi', 'Klima'] },
    { key: 'asansor', label: 'Asansör', tip: 'select', secenekler: ['Var', 'Yok'] },
    { key: 'otopark', label: 'Otopark', tip: 'select', secenekler: ['Açık', 'Kapalı', 'Yok'] },
    { key: 'aidat', label: 'Aidat (TL)', tip: 'number' },
    { key: 'plaza_icerisinde', label: 'Plaza İçerisinde', tip: 'select', secenekler: ['Evet', 'Hayır'] },
  ],
};

function alanlarGetir(tip) {
  return [...(DETAY_ALANLARI[tip] || []), ...DETAY_ALANLARI._ortak];
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

function MulkFormu({ onKaydet, onIptal, duzenle }) {
  const [form, setForm] = useState({
    baslik: '', adres: '', sehir: '', ilce: '', tip: 'daire', islem_turu: 'kira',
    fiyat: '', metrekare: '', oda_sayisi: '', ada: '', parsel: '', notlar: '',
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
      if (duzenle?.id) r = await api.put(`/api/panel/mulkler/${duzenle.id}`, payload);
      else r = await api.post('/api/panel/mulkler', payload);
      onKaydet(r.data.mulk, !!duzenle?.id);
    } catch {} finally { setYuk(false); }
  };

  const alanlar = alanlarGetir(form.tip);

  return (
    <div style={{ background: '#fff', borderRadius: 12, padding: 20, marginBottom: 16, border: '1px solid #e2e8f0' }}>
      <div style={{ fontWeight: 700, fontSize: 15, color: '#1e293b', marginBottom: 16 }}>
        {duzenle?.id ? 'Mülk Düzenle' : 'Yeni Mülk'}
      </div>
      <form onSubmit={kaydet}>
        <div style={{ marginBottom: 12 }}>
          <label className="etiket">Başlık</label>
          <input className="input" name="baslik" value={form.baslik} onChange={d} placeholder="Kadıköy 3+1 Kiralık Daire" />
        </div>
        <div style={{ marginBottom: 12 }}>
          <label className="etiket">Adres</label>
          <input className="input" name="adres" value={form.adres} onChange={d} />
        </div>
        <div className="grid-2" style={{ marginBottom: 12 }}>
          <div><label className="etiket">Şehir</label><input className="input" name="sehir" value={form.sehir || ''} onChange={d} /></div>
          <div><label className="etiket">İlçe</label><input className="input" name="ilce" value={form.ilce || ''} onChange={d} /></div>
        </div>
        <div className="grid-2" style={{ marginBottom: 12 }}>
          <div>
            <label className="etiket">Tip</label>
            <select className="input" name="tip" value={form.tip} onChange={d}>
              {Object.entries(TIP_LABEL).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
            </select>
          </div>
          <div>
            <label className="etiket">İşlem Türü</label>
            <select className="input" name="islem_turu" value={form.islem_turu} onChange={d}>
              <option value="kira">Kiralık</option><option value="satis">Satılık</option>
            </select>
          </div>
        </div>
        <div className="grid-2" style={{ marginBottom: 12 }}>
          <div><label className="etiket">Fiyat (TL)</label><input className="input" name="fiyat" type="number" value={form.fiyat || ''} onChange={d} /></div>
          <div><label className="etiket">Oda Sayısı</label><input className="input" name="oda_sayisi" value={form.oda_sayisi || ''} onChange={d} placeholder="3+1" /></div>
        </div>

        {/* Dinamik detay alanları */}
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

        <div className="grid-2" style={{ marginBottom: 12 }}>
          <div><label className="etiket">Ada</label><input className="input" name="ada" value={form.ada || ''} onChange={d} /></div>
          <div><label className="etiket">Parsel</label><input className="input" name="parsel" value={form.parsel || ''} onChange={d} /></div>
        </div>
        <div style={{ marginBottom: 16 }}>
          <label className="etiket">Notlar</label>
          <textarea className="input" name="notlar" value={form.notlar || ''} onChange={d} rows={2} style={{ resize: 'vertical' }} />
        </div>
        <div style={{ display: 'flex', gap: 10 }}>
          <button className="btn-yesil" type="submit" disabled={yukleniyor}>{yukleniyor ? 'Kaydediliyor...' : 'Kaydet'}</button>
          <button className="btn-gri" type="button" onClick={onIptal}>İptal</button>
        </div>
      </form>
    </div>
  );
}

function MulkKarti({ m, onDuzenle, onSil }) {
  const renk = m.islem_turu === 'kira' ? '#3b82f6' : '#f59e0b';
  const [menuAcik, setMenuAcik] = useState(false);
  const [detayAcik, setDetayAcik] = useState(false);
  const det = m.detaylar || {};

  const badges = Object.entries(det).filter(([, v]) => v).map(([k, v]) => {
    const alan = [...(DETAY_ALANLARI[m.tip] || []), ...DETAY_ALANLARI._ortak].find(a => a.key === k);
    return alan ? `${alan.label}: ${v}` : null;
  }).filter(Boolean);

  return (
    <div style={{ background: '#fff', borderRadius: 12, padding: '14px 16px', marginBottom: 10, border: '1px solid #e2e8f0', borderLeft: `3px solid ${renk}` }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div style={{ flex: 1 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 6, flexWrap: 'wrap' }}>
            <span style={{ fontWeight: 700, fontSize: 15, color: '#0f172a' }}>{m.baslik || m.adres || '—'}</span>
            <span style={{ background: m.islem_turu === 'kira' ? '#eff6ff' : '#fef3c7', color: renk, borderRadius: 6, padding: '2px 8px', fontSize: 11, fontWeight: 700 }}>
              {m.islem_turu === 'kira' ? 'Kiralık' : 'Satılık'}
            </span>
            {m.tip && <span style={{ background: '#f1f5f9', color: '#475569', borderRadius: 6, padding: '2px 8px', fontSize: 11, fontWeight: 600 }}>{TIP_LABEL[m.tip] || m.tip}</span>}
          </div>
          {m.adres && <div style={{ fontSize: 13, color: '#64748b' }}>📍 {m.adres}{m.sehir ? `, ${m.ilce || ''} ${m.sehir}` : ''}</div>}
          <div style={{ display: 'flex', gap: 12, marginTop: 6, flexWrap: 'wrap' }}>
            {m.fiyat && <span style={{ fontSize: 13, color: '#374151', fontWeight: 600 }}>💰 {Number(m.fiyat).toLocaleString('tr-TR')} TL</span>}
            {m.oda_sayisi && <span style={{ fontSize: 13, color: '#64748b' }}>🛏 {m.oda_sayisi}</span>}
            {det.brut_m2 && <span style={{ fontSize: 13, color: '#64748b' }}>{det.brut_m2} brüt m²</span>}
            {det.net_m2 && <span style={{ fontSize: 13, color: '#64748b' }}>{det.net_m2} net m²</span>}
          </div>

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
          {m.notlar && <div style={{ fontSize: 13, color: '#94a3b8', marginTop: 4 }}>{m.notlar}</div>}
        </div>
        <div style={{ position: 'relative' }}>
          <button onClick={() => setMenuAcik(p => !p)} style={{ background: 'none', border: 'none', cursor: 'pointer', fontSize: 18, color: '#94a3b8', padding: '2px 6px' }}>⋮</button>
          {menuAcik && (
            <div style={{ position: 'absolute', right: 0, top: 28, background: '#fff', border: '1px solid #e2e8f0', borderRadius: 8, boxShadow: '0 4px 12px rgba(0,0,0,0.1)', zIndex: 10, minWidth: 140 }}>
              <button onClick={() => { setMenuAcik(false); onDuzenle(m); }} style={{ display: 'block', width: '100%', padding: '8px 14px', border: 'none', background: 'none', textAlign: 'left', fontSize: 13, cursor: 'pointer', color: '#374151' }}>✏️ Düzenle</button>
              <button onClick={() => { setMenuAcik(false); onSil(m.id); }} style={{ display: 'block', width: '100%', padding: '8px 14px', border: 'none', background: 'none', textAlign: 'left', fontSize: 13, cursor: 'pointer', color: '#dc2626' }}>🗑 Sil</button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default function Mulkler() {
  const [mulkler, setMulkler]   = useState([]);
  const [formAcik, setFormAcik] = useState(false);
  const [duzenle, setDuzenle]   = useState(null);
  const [yukleniyor, setYuk]    = useState(false);
  const [arama, setArama]       = useState('');
  const [filtreTip, setFiltreTip]     = useState('');
  const [filtreIslem, setFiltreIslem] = useState('');

  const yukle = useCallback(async () => {
    setYuk(true);
    try { const r = await api.get('/api/panel/mulkler'); setMulkler(r.data.mulkler || []); }
    catch {} finally { setYuk(false); }
  }, []);

  useEffect(() => { yukle(); }, [yukle]);

  const onKaydet = (m, guncelleme) => {
    if (guncelleme) setMulkler(p => p.map(x => x.id === m.id ? m : x));
    else setMulkler(p => [m, ...p]);
    setFormAcik(false); setDuzenle(null);
  };

  const onSil = async (id) => {
    if (!window.confirm('Bu mülkü silmek istediğinize emin misiniz?')) return;
    try { await api.delete(`/api/panel/mulkler/${id}`); setMulkler(p => p.filter(x => x.id !== id)); } catch {}
  };

  let liste = mulkler;
  if (filtreIslem) liste = liste.filter(m => m.islem_turu === filtreIslem);
  if (filtreTip) liste = liste.filter(m => m.tip === filtreTip);
  if (arama.trim()) {
    const q = arama.toLowerCase();
    liste = liste.filter(m => (m.baslik || '').toLowerCase().includes(q) || (m.adres || '').toLowerCase().includes(q) || (m.sehir || '').toLowerCase().includes(q) || (m.ilce || '').toLowerCase().includes(q));
  }

  return (
    <>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
        <h1 style={{ fontSize: 20, fontWeight: 800, color: '#0f172a' }}>🏢 Portföy <span style={{ fontSize: 14, fontWeight: 400, color: '#94a3b8' }}>({mulkler.length})</span></h1>
        <button className="btn-yesil" onClick={() => { setDuzenle(null); setFormAcik(p => !p); }}>+ Ekle</button>
      </div>

      {formAcik && <MulkFormu onKaydet={onKaydet} onIptal={() => { setFormAcik(false); setDuzenle(null); }} duzenle={duzenle} />}

      <div style={{ marginBottom: 12 }}>
        <input className="input" placeholder="🔍 Mülk ara..." value={arama} onChange={e => setArama(e.target.value)} style={{ width: '100%' }} />
      </div>

      <div style={{ display: 'flex', gap: 8, marginBottom: 16, flexWrap: 'wrap' }}>
        {[['', 'Tümü'], ['kira', '🔵 Kiralık'], ['satis', '🟡 Satılık']].map(([v, l]) => (
          <button key={v} onClick={() => setFiltreIslem(v)} style={{
            padding: '6px 14px', borderRadius: 20, fontSize: 13, fontWeight: 600, cursor: 'pointer',
            background: filtreIslem === v ? '#16a34a' : '#fff', color: filtreIslem === v ? '#fff' : '#374151',
            border: `1px solid ${filtreIslem === v ? '#16a34a' : '#e2e8f0'}`,
          }}>{l}</button>
        ))}
        <span style={{ color: '#e2e8f0' }}>|</span>
        {[['', 'Hepsi'], ...Object.entries(TIP_LABEL)].map(([v, l]) => (
          <button key={v} onClick={() => setFiltreTip(v)} style={{
            padding: '6px 14px', borderRadius: 20, fontSize: 12, fontWeight: 600, cursor: 'pointer',
            background: filtreTip === v ? '#475569' : '#fff', color: filtreTip === v ? '#fff' : '#64748b',
            border: `1px solid ${filtreTip === v ? '#475569' : '#e2e8f0'}`,
          }}>{l}</button>
        ))}
      </div>

      {yukleniyor ? (
        <div style={{ textAlign: 'center', color: '#94a3b8', padding: 40 }}>Yükleniyor…</div>
      ) : liste.length === 0 ? (
        <div style={{ textAlign: 'center', color: '#94a3b8', padding: 40, background: '#fff', borderRadius: 12 }}>
          <div style={{ fontSize: 32, marginBottom: 8 }}>🏢</div>
          {arama || filtreIslem || filtreTip ? 'Filtreye uygun mülk yok' : 'Henüz mülk eklenmedi'}
        </div>
      ) : (
        liste.map(m => <MulkKarti key={m.id} m={m} onDuzenle={m => { setDuzenle(m); setFormAcik(true); }} onSil={onSil} />)
      )}
    </>
  );
}
