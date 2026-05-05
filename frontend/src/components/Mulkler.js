import React, { useState, useEffect, useCallback } from 'react';
import api from '../api';

const TIP_LABEL = { daire: 'Daire', villa: 'Villa', arsa: 'Arsa', dukkan: 'Dükkan', ofis: 'Ofis', depo: 'Depo', bina: 'Bina', ciftlik: 'Çiftlik', yazlik: 'Yazlık', isyeri: 'İş Yeri', arazi: 'Arazi' };
const ISLEM_LABEL = { kira: 'Kiralık', satis: 'Satılık', devren_kira: 'Devren Kiralık', devren_satis: 'Devren Satılık' };

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
    musteri_id: '',
    ...(duzenle || {}),
  });
  const [detay, setDetay] = useState(duzenle?.detaylar || {});
  const [detayAcik, setDetayAcik] = useState(false);
  const [musteriler, setMusteriler] = useState([]);

  // Müşteri listesini yükle (sahip seçimi için)
  React.useEffect(() => {
    api.get('/api/panel/musteriler').then(r => setMusteriler(r.data.musteriler || [])).catch(() => {});
  }, []);
  const [yukleniyor, setYuk] = useState(false);
  const d = e => setForm(p => ({ ...p, [e.target.name]: e.target.value }));
  const dd = (key, val) => setDetay(p => ({ ...p, [key]: val }));

  const kaydet = async e => {
    e.preventDefault(); setYuk(true);
    try {
      const payload = { ...form, detaylar: detay, musteri_id: form.musteri_id ? parseInt(form.musteri_id) : null };
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
              {Object.entries(ISLEM_LABEL).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
            </select>
          </div>
        </div>
        <div className="grid-2" style={{ marginBottom: 12 }}>
          <div><label className="etiket">Fiyat (TL)</label><input className="input" name="fiyat" type="number" value={form.fiyat || ''} onChange={d} /></div>
          <div><label className="etiket">Oda Sayısı</label><input className="input" name="oda_sayisi" value={form.oda_sayisi || ''} onChange={d} placeholder="3+1" /></div>
        </div>
        <div className="grid-2" style={{ marginBottom: 12 }}>
          <div>
            <label className="etiket">Mülk Sahibi 🔒</label>
            <select className="input" name="musteri_id" value={form.musteri_id || ''} onChange={d}>
              <option value="">— Seçilmedi —</option>
              {musteriler.map(m => (
                <option key={m.id} value={m.id}>{m.ad_soyad}{m.kunye ? ` (${m.kunye})` : ''} — {m.telefon || 'tel yok'}</option>
              ))}
            </select>
            <div style={{ fontSize: 10, color: '#f59e0b', marginTop: 2 }}>🔒 Sahip bilgisi asla paylaşılmaz</div>
          </div>
          <div>
            <label className="etiket">Grup</label>
            <input className="input" name="grup" value={form.grup || ''} onChange={d} placeholder="Premium, Acil Satılık, Yatırımlık..." />
          </div>
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

// ═══════ MÜLK DETAY SAYFASI (sahibinden kalitesinde) ═══════
// Sahibinden tarzı özellikler bölümü
const OZELLIK_KATEGORILERI = [
  {
    baslik: 'Cephe',
    ikon: '🧭',
    alanlar: ['cephe'],
    etiketler: { cephe: v => v?.split?.(',')?.map(s => s.trim()) || [v] },
  },
  {
    baslik: 'İç Özellikler',
    ikon: '🏠',
    kontrol: (det) => {
      const ozellikler = [];
      if (det.mutfak === 'acik' || det.mutfak === 'Açık (Amerikan)') ozellikler.push('Amerikan Mutfak');
      if (det.mutfak === 'kapali' || det.mutfak === 'Kapalı') ozellikler.push('Kapalı Mutfak');
      if (det.esyali === true || det.esyali === 'Evet') ozellikler.push('Eşyalı');
      if (det.asansor === true || det.asansor === 'Var') ozellikler.push('Asansör');
      if (det.balkon === true || det.balkon === 'Var') ozellikler.push('Balkon');
      if (det.isinma) ozellikler.push(`${det.isinma}`);
      if (det.banyo_sayisi) ozellikler.push(`${det.banyo_sayisi} Banyo`);
      if (det.aidat) ozellikler.push(`Aidat: ${Number(det.aidat).toLocaleString('tr-TR')} TL`);
      if (Array.isArray(det.ic_ozellikler)) ozellikler.push(...det.ic_ozellikler);
      return ozellikler;
    },
  },
  {
    baslik: 'Dış Özellikler',
    ikon: '🏗',
    kontrol: (det) => {
      const ozellikler = [];
      if (det.site_ici === true || det.site_icerisinde === 'Evet') ozellikler.push('Site İçerisinde');
      if (det.otopark && det.otopark !== 'Yok') ozellikler.push(`${det.otopark} Otopark`);
      if (det.havuz === 'Var') ozellikler.push('Yüzme Havuzu');
      if (det.bahce === 'Var') ozellikler.push('Bahçe');
      if (det.guvenlik === 'Var') ozellikler.push('24 Saat Güvenlik');
      if (det.zemin_etudu === true) ozellikler.push('Zemin Etüdü Var');
      if (Array.isArray(det.dis_ozellikler)) ozellikler.push(...det.dis_ozellikler);
      return ozellikler;
    },
  },
  {
    baslik: 'Muhit',
    ikon: '📍',
    kontrol: (det) => Array.isArray(det.muhit) ? det.muhit : [],
  },
  {
    baslik: 'Ulaşım',
    ikon: '🚇',
    kontrol: (det) => Array.isArray(det.ulasim) ? det.ulasim : [],
  },
  {
    baslik: 'Manzara',
    ikon: '🌅',
    kontrol: (det) => {
      const ozellikler = [];
      if (det.manzara && det.manzara !== 'Yok') ozellikler.push(det.manzara);
      if (Array.isArray(det.manzara_liste)) ozellikler.push(...det.manzara_liste);
      return ozellikler;
    },
  },
  {
    baslik: 'Konut Tipi',
    ikon: '🏢',
    kontrol: (det) => {
      const ozellikler = [];
      if (det.bina_tipi) ozellikler.push(det.bina_tipi);
      if (det.yapinin_durumu) ozellikler.push(det.yapinin_durumu);
      if (det.konut_tipi) ozellikler.push(det.konut_tipi);
      return ozellikler;
    },
  },
];

function OzelliklerBolumu({ det, tip }) {
  if (!det || Object.keys(det).length === 0) return null;

  const kategoriler = OZELLIK_KATEGORILERI.map(kat => {
    let items = [];
    if (kat.kontrol) {
      items = kat.kontrol(det);
    } else if (kat.alanlar) {
      for (const alan of kat.alanlar) {
        if (det[alan]) {
          if (kat.etiketler?.[alan]) {
            items.push(...kat.etiketler[alan](det[alan]));
          } else {
            items.push(det[alan]);
          }
        }
      }
    }
    return { ...kat, items };
  }).filter(k => k.items.length > 0);

  if (kategoriler.length === 0) return null;

  return (
    <div style={{ marginTop: 12 }}>
      <div style={{ fontWeight: 700, fontSize: 14, color: '#0f172a', marginBottom: 10 }}>📋 Özellikler</div>
      {kategoriler.map((kat, ki) => (
        <div key={ki} style={{ marginBottom: 10, background: '#fff', borderRadius: 10, border: '1px solid #e2e8f0', overflow: 'hidden' }}>
          <div style={{ padding: '8px 14px', background: '#f8fafc', borderBottom: '1px solid #e2e8f0', fontWeight: 600, fontSize: 13, color: '#374151' }}>
            {kat.ikon} {kat.baslik}
          </div>
          <div style={{ padding: '10px 14px', display: 'flex', flexWrap: 'wrap', gap: 6 }}>
            {kat.items.map((item, i) => (
              <span key={i} style={{
                padding: '4px 10px', borderRadius: 6, fontSize: 12,
                background: '#f0fdf4', color: '#166534', border: '1px solid #bbf7d0',
              }}>{item}</span>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}

function MulkDetay({ m, onGeri, onDuzenle, onResimGuncelle }) {
  const [aktifResim, setAktifResim] = useState(0);
  const det = m.detaylar || {};
  const resimler = m.resimler || [];

  const alanlar = alanlarGetir(m.tip);
  const doluAlanlar = alanlar.filter(a => det[a.key]);

  const f = (v) => v ? Number(v).toLocaleString('tr-TR') : '—';

  return (
    <>
      <button onClick={onGeri} className="btn-gri" style={{ marginBottom: 12, fontSize: 13 }}>← Portföye Dön</button>

      <div style={{ fontWeight: 800, fontSize: 20, color: '#0f172a', marginBottom: 12 }}>
        {m.baslik || m.adres || 'Mülk Detay'}
      </div>

      <div style={{ display: 'flex', gap: 20, flexWrap: 'wrap' }}>
        {/* SOL — Fotoğraf Galerisi */}
        <div style={{ flex: '1 1 400px', minWidth: 300 }}>
          {/* Ana fotoğraf */}
          {resimler.length > 0 ? (
            <div style={{ position: 'relative', marginBottom: 8 }}>
              <img src={resimler[aktifResim]?.url} alt="" style={{ width: '100%', height: 360, objectFit: 'cover', borderRadius: 12, background: '#f1f5f9' }} />
              {resimler.length > 1 && (
                <>
                  {aktifResim > 0 && <button onClick={() => setAktifResim(p => p - 1)} style={{ position: 'absolute', left: 8, top: '50%', transform: 'translateY(-50%)', background: 'rgba(0,0,0,0.5)', color: '#fff', border: 'none', borderRadius: '50%', width: 36, height: 36, fontSize: 18, cursor: 'pointer' }}>◀</button>}
                  {aktifResim < resimler.length - 1 && <button onClick={() => setAktifResim(p => p + 1)} style={{ position: 'absolute', right: 8, top: '50%', transform: 'translateY(-50%)', background: 'rgba(0,0,0,0.5)', color: '#fff', border: 'none', borderRadius: '50%', width: 36, height: 36, fontSize: 18, cursor: 'pointer' }}>▶</button>}
                  <div style={{ position: 'absolute', bottom: 8, left: '50%', transform: 'translateX(-50%)', background: 'rgba(0,0,0,0.5)', color: '#fff', padding: '4px 12px', borderRadius: 12, fontSize: 12 }}>{aktifResim + 1} / {resimler.length} Fotoğraf</div>
                </>
              )}
            </div>
          ) : (
            <div style={{ width: '100%', height: 200, background: '#f1f5f9', borderRadius: 12, display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#94a3b8', fontSize: 14, marginBottom: 8 }}>📸 Fotoğraf eklenmemiş</div>
          )}

          {/* Küçük resimler */}
          {resimler.length > 1 && (
            <div style={{ display: 'flex', gap: 6, overflowX: 'auto', paddingBottom: 4 }}>
              {resimler.map((r, i) => (
                <img key={i} src={r.url} alt="" onClick={() => setAktifResim(i)}
                  style={{ width: 72, height: 54, objectFit: 'cover', borderRadius: 8, cursor: 'pointer', border: aktifResim === i ? '3px solid #16a34a' : '2px solid #e2e8f0', flexShrink: 0 }} />
              ))}
            </div>
          )}

          {/* Fotoğraf ekle */}
          <FotoGaleriEkle mulkId={m.id} resimSayisi={resimler.length} onGuncelle={(r) => onResimGuncelle(m.id, r)} />

          {/* Notlar */}
          {m.notlar && (
            <div style={{ marginTop: 16, padding: 14, background: '#fffbeb', borderRadius: 10, border: '1px solid #fde68a', fontSize: 13 }}>
              📝 <strong>Notlar:</strong> {m.notlar}
            </div>
          )}

          {/* Mülk Sahibi (gizli — sadece emlakçı görür) */}
          {m.sahip_ad && (
            <div style={{ marginTop: 12, padding: 12, background: '#fef3c7', borderRadius: 8, border: '1px solid #fde68a' }}>
              <div style={{ fontSize: 12, fontWeight: 700, color: '#92400e', marginBottom: 4 }}>🔒 Mülk Sahibi (gizli)</div>
              <div style={{ fontSize: 13 }}>👤 {m.sahip_ad}</div>
              {m.sahip_tel && <div style={{ fontSize: 13 }}>📞 {m.sahip_tel}</div>}
              <div style={{ fontSize: 10, color: '#b45309', marginTop: 4 }}>Bu bilgi sadece size görünür — paylaşımlarda gizlenir</div>
            </div>
          )}

          {/* Aksiyon butonları */}
          <div style={{ display: 'flex', gap: 8, marginTop: 16, flexWrap: 'wrap' }}>
            <button onClick={() => onDuzenle(m)} className="btn-yesil" style={{ fontSize: 12 }}>✏️ Düzenle</button>
            <button onClick={async () => { try { const r = await api.get(`/api/panel/ofis/brosur/${m.id}`, {responseType:'blob'}); const url=URL.createObjectURL(new Blob([r.data])); const a=document.createElement('a'); a.href=url; a.download=`brosur_${m.id}.pdf`; a.click(); } catch{ alert('Broşür oluşturulurken hata oluştu'); } }} className="btn-gri" style={{ fontSize: 12 }}>📄 Broşür PDF</button>
            <button onClick={async () => { try { const r = await api.post('/api/panel/gelismis/ilan-metni', {mulk_id:m.id}); navigator.clipboard.writeText(r.data.ilan); alert('İlan metni kopyalandı!'); } catch{} }} className="btn-gri" style={{ fontSize: 12 }}>📝 İlan Metni</button>
          </div>
        </div>

        {/* SAĞ — Detay Tablosu */}
        <div style={{ flex: '1 1 320px', minWidth: 280 }}>
          {/* Fiyat */}
          <div style={{ background: '#f0fdf4', borderRadius: 12, padding: 16, marginBottom: 12, border: '1px solid #bbf7d0' }}>
            <div style={{ fontSize: 28, fontWeight: 800, color: '#16a34a' }}>{f(m.fiyat)} TL</div>
            <div style={{ fontSize: 13, color: '#64748b', marginTop: 4 }}>
              {m.sehir && `${m.ilce || ''} / ${m.sehir}`}
              {m.ada && ` · Ada: ${m.ada}`}
              {m.parsel && ` · Parsel: ${m.parsel}`}
            </div>
          </div>

          {/* Temel bilgiler */}
          <div style={{ background: '#fff', borderRadius: 12, padding: 16, border: '1px solid #e2e8f0' }}>
            <DetaySatir label="Emlak Tipi" value={`${ISLEM_LABEL[m.islem_turu] || 'Satılık'} ${TIP_LABEL[m.tip] || m.tip || '—'}`} />
            {m.metrekare && <DetaySatir label="m² (Brüt)" value={m.metrekare} />}
            {det.brut_m2 && <DetaySatir label="m² (Brüt)" value={det.brut_m2} />}
            {det.net_m2 && <DetaySatir label="m² (Net)" value={det.net_m2} />}
            {m.oda_sayisi && <DetaySatir label="Oda Sayısı" value={m.oda_sayisi} />}

            {/* Dinamik detaylar — dolu olanlar */}
            {doluAlanlar.map(a => (
              <DetaySatir key={a.key} label={a.label} value={det[a.key]} />
            ))}

            {m.adres && <DetaySatir label="Adres" value={m.adres} />}
            {m.grup && <DetaySatir label="Grup" value={m.grup} />}
          </div>

          {/* Açıklama */}
          {det.aciklama && (
            <div style={{ marginTop: 12, padding: 14, background: '#fff', borderRadius: 12, border: '1px solid #e2e8f0' }}>
              <div style={{ fontWeight: 700, fontSize: 14, color: '#0f172a', marginBottom: 8 }}>📝 Açıklama</div>
              <div style={{ fontSize: 13, color: '#374151', lineHeight: 1.6, whiteSpace: 'pre-wrap' }}>{det.aciklama}</div>
            </div>
          )}

          {/* Özellikler — sahibinden gibi kategorize */}
          <OzelliklerBolumu det={det} tip={m.tip} />
        </div>
      </div>
    </>
  );
}

function DetaySatir({ label, value }) {
  if (!value) return null;
  return (
    <div style={{ display: 'flex', justifyContent: 'space-between', padding: '8px 0', borderBottom: '1px solid #f1f5f9', fontSize: 13 }}>
      <span style={{ fontWeight: 600, color: '#374151' }}>{label}</span>
      <span style={{ color: '#0f172a' }}>{value}</span>
    </div>
  );
}

// Fotoğraf ekleme butonu (detay sayfası için)
function FotoGaleriEkle({ mulkId, resimSayisi, onGuncelle }) {
  const [yukleniyor, setYuk] = useState(false);
  const resimEkle = async (e) => {
    const files = Array.from(e.target.files || []);
    for (const file of files) {
      if (file.size > 5 * 1024 * 1024) { alert('Fotoğraf 5MB\'dan küçük olmalı'); continue; }
      setYuk(true);
      try {
        const formData = new FormData();
        formData.append('image', file);
        const r = await api.post(`/api/panel/mulkler/${mulkId}/resim`, formData);
        if (onGuncelle) onGuncelle(r.data.resimler);
      } catch (err) { alert(err.response?.data?.message || 'Yükleme hatası'); }
      finally { setYuk(false); }
    }
  };
  return (
    <label style={{ display: 'inline-flex', alignItems: 'center', gap: 4, fontSize: 12, color: '#16a34a', cursor: 'pointer', marginTop: 8 }}>
      {yukleniyor ? '⏳ Yükleniyor...' : `📸 Fotoğraf Ekle (${resimSayisi || 0})`}
      <input type="file" accept="image/*" multiple onChange={resimEkle} style={{ display: 'none' }} disabled={yukleniyor} />
    </label>
  );
}

function MulkKarti({ m, onTikla, onDuzenle, onSil, onToggle, onResimGuncelle }) {
  const renk = m.aktif === false ? '#94a3b8' : m.islem_turu === 'kira' ? '#3b82f6' : '#f59e0b';
  const [menuAcik, setMenuAcik] = useState(false);
  const [detayAcik, setDetayAcik] = useState(false);
  const det = m.detaylar || {};

  const badges = Object.entries(det).filter(([, v]) => v).map(([k, v]) => {
    const alan = [...(DETAY_ALANLARI[m.tip] || []), ...DETAY_ALANLARI._ortak].find(a => a.key === k);
    return alan ? `${alan.label}: ${v}` : null;
  }).filter(Boolean);

  return (
    <div onClick={onTikla} style={{ background: '#fff', borderRadius: 12, padding: '14px 16px', marginBottom: 10, border: '1px solid #e2e8f0', borderLeft: `3px solid ${renk}`, cursor: 'pointer', opacity: m.aktif === false ? 0.5 : 1 }}>
      {m.aktif === false && <div style={{ background: '#fef2f2', color: '#dc2626', borderRadius: 6, padding: '2px 10px', fontSize: 11, fontWeight: 700, marginBottom: 6, display: 'inline-block' }}>PASİF</div>}
      {/* Kapak fotoğraf (varsa) */}
      {m.resimler?.[0] && (
        <img src={(m.resimler.find(r => r.ana) || m.resimler[0]).url} alt="" style={{ width: '100%', height: 140, objectFit: 'cover', borderRadius: 8, marginBottom: 8 }} />
      )}
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
          <button onClick={(e) => { e.stopPropagation(); setMenuAcik(p => !p); }} style={{ background: 'none', border: 'none', cursor: 'pointer', fontSize: 18, color: '#94a3b8', padding: '2px 6px' }}>⋮</button>
          {menuAcik && (
            <div style={{ position: 'absolute', right: 0, top: 28, background: '#fff', border: '1px solid #e2e8f0', borderRadius: 8, boxShadow: '0 4px 12px rgba(0,0,0,0.1)', zIndex: 10, minWidth: 140 }}>
              <button onClick={() => { setMenuAcik(false); onDuzenle(m); }} style={{ display: 'block', width: '100%', padding: '8px 14px', border: 'none', background: 'none', textAlign: 'left', fontSize: 13, cursor: 'pointer', color: '#374151' }}>✏️ Düzenle</button>
              <button onClick={() => { setMenuAcik(false); navigator.clipboard.writeText(`${window.location.origin}/sayfa/${m.emlakci_id || ''}`); alert('Link kopyalandı!'); }} style={{ display: 'block', width: '100%', padding: '8px 14px', border: 'none', background: 'none', textAlign: 'left', fontSize: 13, cursor: 'pointer', color: '#1d4ed8' }}>🔗 Link Kopyala</button>
              <button onClick={async () => { setMenuAcik(false); try { const r = await api.get(`/api/panel/ofis/brosur/${m.id}`, {responseType:'blob'}); const url=URL.createObjectURL(new Blob([r.data])); const a=document.createElement('a'); a.href=url; a.download=`brosur_${m.id}.pdf`; a.click(); } catch{} }} style={{ display: 'block', width: '100%', padding: '8px 14px', border: 'none', background: 'none', textAlign: 'left', fontSize: 13, cursor: 'pointer', color: '#16a34a' }}>📄 Broşür PDF</button>
              <button onClick={async () => { setMenuAcik(false); try { const r = await api.post('/api/panel/gelismis/ilan-metni', {mulk_id:m.id}); navigator.clipboard.writeText(r.data.ilan); alert('İlan metni kopyalandı!'); } catch{} }} style={{ display: 'block', width: '100%', padding: '8px 14px', border: 'none', background: 'none', textAlign: 'left', fontSize: 13, cursor: 'pointer', color: '#8b5cf6' }}>📝 İlan Metni</button>
              <button onClick={async () => { setMenuAcik(false); try { const r = await api.get(`/api/panel/gelismis/piyasa-degeri/${m.id}`); alert(`Piyasa Analizi:\n\nFiyat: ${Number(m.fiyat).toLocaleString('tr-TR')} TL\nPortföy Ort: ${Number(r.data.portfoy_ortalama).toLocaleString('tr-TR')} TL\nFark: %${r.data.fark_yuzde}\n\n${r.data.degerlendirme}`); } catch{} }} style={{ display: 'block', width: '100%', padding: '8px 14px', border: 'none', background: 'none', textAlign: 'left', fontSize: 13, cursor: 'pointer', color: '#f59e0b' }}>📊 Piyasa Değeri</button>
              <button onClick={async () => { setMenuAcik(false); try { const r = await api.get(`/api/panel/gelismis/yasal/${m.id}`); alert(`Yasal Durum:\n\nRisk: ${r.data.risk_seviye}\nKontrol: ${r.data.tamamlanan}/${r.data.toplam_kontrol}\nEksik: ${r.data.eksik_sayisi}`); } catch{} }} style={{ display: 'block', width: '100%', padding: '8px 14px', border: 'none', background: 'none', textAlign: 'left', fontSize: 13, cursor: 'pointer', color: '#dc2626' }}>⚖️ Yasal Durum</button>
              {m.fiyat && <button onClick={async () => { setMenuAcik(false); try { const r = await api.post('/api/panel/hesaplama/fiyat-donustur', {tutar: m.fiyat}); alert(`💱 ${Number(m.fiyat).toLocaleString('tr-TR')} TL =\n\n$ ${r.data.USD?.toLocaleString('tr-TR')}\n€ ${r.data.EUR?.toLocaleString('tr-TR')}\n£ ${r.data.GBP?.toLocaleString('tr-TR')}\n🥇 ${r.data.ALTIN_GRAM?.toLocaleString('tr-TR')} gram altın`); } catch{} }} style={{ display: 'block', width: '100%', padding: '8px 14px', border: 'none', background: 'none', textAlign: 'left', fontSize: 13, cursor: 'pointer', color: '#06b6d4' }}>💱 Döviz Karşılığı</button>}
              <button onClick={(e) => { e.stopPropagation(); setMenuAcik(false); onToggle(m.id); }} style={{ display: 'block', width: '100%', padding: '8px 14px', border: 'none', background: 'none', textAlign: 'left', fontSize: 13, cursor: 'pointer', color: m.aktif === false ? '#16a34a' : '#f59e0b' }}>
                {m.aktif === false ? '✅ Aktif Yap' : '⏸ Pasife Al'}
              </button>
              <button onClick={(e) => { e.stopPropagation(); setMenuAcik(false); onSil(m.id); }} style={{ display: 'block', width: '100%', padding: '8px 14px', border: 'none', background: 'none', textAlign: 'left', fontSize: 13, cursor: 'pointer', color: '#dc2626' }}>🗑 Sil</button>
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
  const [secili, setSecili]     = useState(null); // detay sayfası
  const [yukleniyor, setYuk]    = useState(false);
  const [arama, setArama]       = useState('');
  const [filtreTip, setFiltreTip]     = useState('');
  const [filtreIslem, setFiltreIslem] = useState('');
  const [filtreGrup, setFiltreGrup]   = useState('');
  const [pasifGoster, setPasifGoster] = useState(false);

  const yukle = useCallback(async () => {
    setYuk(true);
    try {
      const url = pasifGoster ? '/api/panel/mulkler?pasif=true' : '/api/panel/mulkler';
      const r = await api.get(url);
      setMulkler(r.data.mulkler || []);
    } catch {} finally { setYuk(false); }
  }, [pasifGoster]);

  useEffect(() => { yukle(); }, [yukle]);

  const onKaydet = (m, guncelleme) => {
    if (guncelleme) setMulkler(p => p.map(x => x.id === m.id ? m : x));
    else setMulkler(p => [m, ...p]);
    setFormAcik(false); setDuzenle(null);
  };

  const onSil = async (id) => {
    if (!window.confirm('Bu mülkü silmek istediğinize emin misiniz?')) return;
    try { await api.delete(`/api/panel/mulkler/${id}`); yukle(); } catch {}
  };

  const onToggle = async (id) => {
    try {
      const r = await api.put(`/api/panel/mulkler/${id}/toggle`);
      setMulkler(p => p.map(x => x.id === id ? { ...x, aktif: r.data.aktif } : x));
    } catch {}
  };

  const gruplar = [...new Set(mulkler.map(m => m.grup).filter(Boolean))];

  let liste = mulkler;
  if (!pasifGoster) liste = liste.filter(m => m.aktif !== false);
  if (filtreIslem) liste = liste.filter(m => m.islem_turu === filtreIslem);
  if (filtreTip) liste = liste.filter(m => m.tip === filtreTip);
  if (filtreGrup) liste = liste.filter(m => m.grup === filtreGrup);
  if (arama.trim()) {
    const q = arama.toLowerCase();
    liste = liste.filter(m => (m.baslik || '').toLowerCase().includes(q) || (m.adres || '').toLowerCase().includes(q) || (m.sehir || '').toLowerCase().includes(q) || (m.ilce || '').toLowerCase().includes(q));
  }

  const onResimGuncelle = (id, resimler) => setMulkler(p => p.map(x => x.id === id ? { ...x, resimler } : x));

  // Detay sayfası
  if (secili) {
    const guncelMulk = mulkler.find(x => x.id === secili.id) || secili;
    return (
      <MulkDetay
        m={guncelMulk}
        onGeri={() => setSecili(null)}
        onDuzenle={m => { setSecili(null); setDuzenle(m); setFormAcik(true); }}
        onResimGuncelle={onResimGuncelle}
      />
    );
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

      <div style={{ display: 'flex', gap: 8, marginBottom: 16, flexWrap: 'wrap', alignItems: 'center' }}>
        <button onClick={() => setPasifGoster(p => !p)} style={{
          padding: '6px 14px', borderRadius: 20, fontSize: 12, cursor: 'pointer',
          background: pasifGoster ? '#fef2f2' : '#fff', color: pasifGoster ? '#dc2626' : '#94a3b8',
          border: `1px solid ${pasifGoster ? '#fecaca' : '#e2e8f0'}`,
        }}>{pasifGoster ? '👁 Pasifler gösteriliyor' : '👁‍🗨 Pasifler gizli'}</button>
        <span style={{ color: '#e2e8f0' }}>|</span>
        {[['', 'Tümü'], ['kira', '🔵 Kiralık'], ['satis', '🟡 Satılık'], ['devren_kira', 'Devren Kiralık'], ['devren_satis', 'Devren Satılık']].map(([v, l]) => (
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
          <div style={{ fontSize: 32, marginBottom: 8 }}>🏢</div>
          {arama || filtreIslem || filtreTip ? 'Filtreye uygun mülk yok' : 'Henüz mülk eklenmedi'}
        </div>
      ) : (
        liste.map(m => <MulkKarti key={m.id} m={m} onTikla={() => setSecili(m)} onDuzenle={m => { setDuzenle(m); setFormAcik(true); }} onSil={onSil} onToggle={onToggle} onResimGuncelle={onResimGuncelle} />)
      )}
    </>
  );
}
