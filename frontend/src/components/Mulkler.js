import React, { useState, useEffect, useCallback } from 'react';
import api from '../api';

const TIP_LABEL = { daire: 'Daire', villa: 'Villa', arsa: 'Arsa', dukkan: 'Dükkan', ofis: 'Ofis' };

function MulkFormu({ onKaydet, onIptal, duzenle }) {
  const [form, setForm] = useState(duzenle || {
    baslik: '', adres: '', sehir: '', ilce: '', tip: 'daire', islem_turu: 'kira',
    fiyat: '', metrekare: '', oda_sayisi: '', ada: '', parsel: '', notlar: '',
    brut_metrekare: '', net_metrekare: '', bina_yasi: '', bulundugu_kat: '', kat_sayisi: '',
    isinma: '', banyo_sayisi: '', mutfak: '', balkon: '', asansor: '', otopark: '',
    esyali: '', kullanim_durumu: '', site_icerisinde: '', site_adi: '', aidat: '',
    krediye_uygun: '', tapu_durumu: '', kimden: '', takas: '',
  });
  const [detayAcik, setDetayAcik] = useState(false);
  const [yukleniyor, setYuk] = useState(false);
  const d = e => setForm(p => ({ ...p, [e.target.name]: e.target.value }));

  const kaydet = async e => {
    e.preventDefault(); setYuk(true);
    try {
      let r;
      if (duzenle?.id) {
        r = await api.put(`/api/panel/mulkler/${duzenle.id}`, form);
      } else {
        r = await api.post('/api/panel/mulkler', form);
      }
      onKaydet(r.data.mulk, !!duzenle?.id);
    } catch {} finally { setYuk(false); }
  };

  return (
    <div style={{ background: '#fff', borderRadius: 12, padding: 20, marginBottom: 16, border: '1px solid #e2e8f0' }}>
      <div style={{ fontWeight: 700, fontSize: 15, color: '#1e293b', marginBottom: 16 }}>
        {duzenle?.id ? 'Mülk Düzenle' : 'Yeni Mülk'}
      </div>
      <form onSubmit={kaydet}>
        {/* Temel bilgiler */}
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
              <option value="daire">Daire</option><option value="villa">Villa</option>
              <option value="arsa">Arsa</option><option value="dukkan">Dükkan</option>
              <option value="ofis">Ofis</option>
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
        <div className="grid-2" style={{ marginBottom: 12 }}>
          <div><label className="etiket">m² (Brüt)</label><input className="input" name="brut_metrekare" type="number" value={form.brut_metrekare || ''} onChange={d} /></div>
          <div><label className="etiket">m² (Net)</label><input className="input" name="net_metrekare" type="number" value={form.net_metrekare || ''} onChange={d} /></div>
        </div>

        {/* Detay aç/kapa */}
        <button type="button" onClick={() => setDetayAcik(p => !p)} style={{
          background: 'none', border: 'none', color: '#16a34a', fontSize: 13, fontWeight: 600,
          cursor: 'pointer', marginBottom: 12, padding: 0,
        }}>
          {detayAcik ? '▼ Detayları gizle' : '▶ Detayları göster'}
        </button>

        {detayAcik && (
          <>
            <div className="grid-2" style={{ marginBottom: 12 }}>
              <div><label className="etiket">Bina Yaşı</label><input className="input" name="bina_yasi" type="number" value={form.bina_yasi || ''} onChange={d} /></div>
              <div><label className="etiket">Bulunduğu Kat</label><input className="input" name="bulundugu_kat" value={form.bulundugu_kat || ''} onChange={d} placeholder="3. Kat" /></div>
            </div>
            <div className="grid-2" style={{ marginBottom: 12 }}>
              <div><label className="etiket">Kat Sayısı</label><input className="input" name="kat_sayisi" type="number" value={form.kat_sayisi || ''} onChange={d} /></div>
              <div><label className="etiket">Banyo Sayısı</label><input className="input" name="banyo_sayisi" type="number" value={form.banyo_sayisi || ''} onChange={d} /></div>
            </div>
            <div className="grid-2" style={{ marginBottom: 12 }}>
              <div>
                <label className="etiket">Isınma</label>
                <select className="input" name="isinma" value={form.isinma || ''} onChange={d}>
                  <option value="">Seçiniz</option>
                  <option value="kombi">Kombi (Doğalgaz)</option>
                  <option value="merkezi">Merkezi</option>
                  <option value="soba">Soba</option>
                  <option value="klima">Klima</option>
                  <option value="yerden">Yerden Isıtma</option>
                </select>
              </div>
              <div>
                <label className="etiket">Mutfak</label>
                <select className="input" name="mutfak" value={form.mutfak || ''} onChange={d}>
                  <option value="">Seçiniz</option>
                  <option value="acik">Açık (Amerikan)</option>
                  <option value="kapali">Kapalı</option>
                </select>
              </div>
            </div>
            <div className="grid-2" style={{ marginBottom: 12 }}>
              <div>
                <label className="etiket">Balkon</label>
                <select className="input" name="balkon" value={form.balkon || ''} onChange={d}>
                  <option value="">Seçiniz</option><option value="var">Var</option><option value="yok">Yok</option>
                </select>
              </div>
              <div>
                <label className="etiket">Asansör</label>
                <select className="input" name="asansor" value={form.asansor || ''} onChange={d}>
                  <option value="">Seçiniz</option><option value="var">Var</option><option value="yok">Yok</option>
                </select>
              </div>
            </div>
            <div className="grid-2" style={{ marginBottom: 12 }}>
              <div>
                <label className="etiket">Otopark</label>
                <select className="input" name="otopark" value={form.otopark || ''} onChange={d}>
                  <option value="">Seçiniz</option><option value="acik">Açık</option><option value="kapali">Kapalı</option><option value="yok">Yok</option>
                </select>
              </div>
              <div>
                <label className="etiket">Eşyalı</label>
                <select className="input" name="esyali" value={form.esyali || ''} onChange={d}>
                  <option value="">Seçiniz</option><option value="evet">Evet</option><option value="hayir">Hayır</option>
                </select>
              </div>
            </div>
            <div className="grid-2" style={{ marginBottom: 12 }}>
              <div>
                <label className="etiket">Kullanım Durumu</label>
                <select className="input" name="kullanim_durumu" value={form.kullanim_durumu || ''} onChange={d}>
                  <option value="">Seçiniz</option><option value="bos">Boş</option><option value="kiraci">Kiracı Var</option><option value="mal_sahibi">Mal Sahibi</option>
                </select>
              </div>
              <div>
                <label className="etiket">Krediye Uygun</label>
                <select className="input" name="krediye_uygun" value={form.krediye_uygun || ''} onChange={d}>
                  <option value="">Seçiniz</option><option value="evet">Evet</option><option value="hayir">Hayır</option>
                </select>
              </div>
            </div>
            <div className="grid-2" style={{ marginBottom: 12 }}>
              <div>
                <label className="etiket">Tapu Durumu</label>
                <select className="input" name="tapu_durumu" value={form.tapu_durumu || ''} onChange={d}>
                  <option value="">Seçiniz</option><option value="kat_mulkiyeti">Kat Mülkiyetli</option>
                  <option value="kat_irtifaki">Kat İrtifakı</option><option value="hisseli">Hisseli Tapu</option>
                  <option value="arsa">Arsa Tapulu</option>
                </select>
              </div>
              <div>
                <label className="etiket">Kimden</label>
                <select className="input" name="kimden" value={form.kimden || ''} onChange={d}>
                  <option value="">Seçiniz</option><option value="sahibinden">Sahibinden</option><option value="emlak_ofisi">Emlak Ofisinden</option>
                </select>
              </div>
            </div>
            <div className="grid-2" style={{ marginBottom: 12 }}>
              <div>
                <label className="etiket">Site İçerisinde</label>
                <select className="input" name="site_icerisinde" value={form.site_icerisinde || ''} onChange={d}>
                  <option value="">Seçiniz</option><option value="evet">Evet</option><option value="hayir">Hayır</option>
                </select>
              </div>
              <div><label className="etiket">Site Adı</label><input className="input" name="site_adi" value={form.site_adi || ''} onChange={d} /></div>
            </div>
            <div className="grid-2" style={{ marginBottom: 12 }}>
              <div><label className="etiket">Aidat (TL)</label><input className="input" name="aidat" type="number" value={form.aidat || ''} onChange={d} /></div>
              <div>
                <label className="etiket">Takas</label>
                <select className="input" name="takas" value={form.takas || ''} onChange={d}>
                  <option value="">Seçiniz</option><option value="evet">Evet</option><option value="hayir">Hayır</option>
                </select>
              </div>
            </div>
            <div className="grid-2" style={{ marginBottom: 12 }}>
              <div><label className="etiket">Ada</label><input className="input" name="ada" value={form.ada || ''} onChange={d} /></div>
              <div><label className="etiket">Parsel</label><input className="input" name="parsel" value={form.parsel || ''} onChange={d} /></div>
            </div>
          </>
        )}

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

  const detaylar = [
    m.bulundugu_kat && `Kat: ${m.bulundugu_kat}`,
    m.kat_sayisi && `${m.kat_sayisi} katlı`,
    m.bina_yasi != null && `${m.bina_yasi} yaşında`,
    m.isinma && `🔥 ${m.isinma}`,
    m.banyo_sayisi && `🚿 ${m.banyo_sayisi} banyo`,
    m.balkon && (m.balkon === 'var' ? '🏠 Balkon' : '❌ Balkon yok'),
    m.asansor && (m.asansor === 'var' ? '🛗 Asansör' : '❌ Asansör yok'),
    m.esyali && (m.esyali === 'evet' ? '🪑 Eşyalı' : 'Eşyasız'),
    m.kullanim_durumu && `📋 ${m.kullanim_durumu === 'bos' ? 'Boş' : m.kullanim_durumu === 'kiraci' ? 'Kiracı var' : 'Mal sahibi'}`,
    m.krediye_uygun === 'evet' && '💳 Krediye uygun',
    m.tapu_durumu && `📄 ${m.tapu_durumu.replace('_', ' ')}`,
    m.aidat && `🏢 Aidat: ${Number(m.aidat).toLocaleString('tr-TR')} TL`,
    m.site_adi && `🏘 ${m.site_adi}`,
  ].filter(Boolean);

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
            {(m.brut_metrekare || m.net_metrekare || m.metrekare) && (
              <span style={{ fontSize: 13, color: '#64748b' }}>
                {m.brut_metrekare ? `${m.brut_metrekare} brüt` : ''}{m.net_metrekare ? ` / ${m.net_metrekare} net` : ''}{!m.brut_metrekare && !m.net_metrekare && m.metrekare ? `${m.metrekare} m²` : ' m²'}
              </span>
            )}
            {m.oda_sayisi && <span style={{ fontSize: 13, color: '#64748b' }}>🛏 {m.oda_sayisi}</span>}
          </div>

          {/* Detaylar */}
          {detaylar.length > 0 && (
            <>
              <button onClick={() => setDetayAcik(p => !p)} style={{
                background: 'none', border: 'none', color: '#16a34a', fontSize: 12, cursor: 'pointer', padding: 0, marginTop: 6,
              }}>
                {detayAcik ? '▼ Detayları gizle' : `▶ ${detaylar.length} detay`}
              </button>
              {detayAcik && (
                <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginTop: 6 }}>
                  {detaylar.map((d, i) => (
                    <span key={i} style={{ fontSize: 11, background: '#f8fafc', border: '1px solid #e2e8f0', borderRadius: 6, padding: '2px 8px', color: '#475569' }}>{d}</span>
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
        <input className="input" placeholder="🔍 Mülk ara (başlık, adres, şehir)..." value={arama} onChange={e => setArama(e.target.value)} style={{ width: '100%' }} />
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
        {[['', 'Hepsi'], ['daire', 'Daire'], ['villa', 'Villa'], ['arsa', 'Arsa'], ['dukkan', 'Dükkan'], ['ofis', 'Ofis']].map(([v, l]) => (
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
