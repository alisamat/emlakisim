import React, { useState, useEffect, useCallback } from 'react';
import api from '../api';

const BELGE_TIPLERI = {
  'yer-gosterme': { label: 'Yer Gösterme Tutanağı', ikon: '📋', endpoint: '/api/panel/belge/yer-gosterme' },
  'kira-kontrati': { label: 'Kira Sözleşmesi', ikon: '📄', endpoint: '/api/panel/belge/kira-kontrati' },
  'yonlendirme-alici': { label: 'Alıcı Yönlendirme', ikon: '📝', endpoint: '/api/panel/belge/yonlendirme', extra: { taraf: 'alici' } },
  'yonlendirme-satici': { label: 'Satıcı Yönlendirme', ikon: '📝', endpoint: '/api/panel/belge/yonlendirme', extra: { taraf: 'satici' } },
};

// Kira kontratı detay alanları
const KIRA_DETAY = [
  { key: 'mal_sahibi', label: 'Mal Sahibi Ad Soyad', tip: 'text' },
  { key: 'aylik_kira', label: 'Aylık Kira (TL)', tip: 'text' },
  { key: 'depozito', label: 'Depozito (TL)', tip: 'text' },
  { key: 'odeme_gunu', label: 'Ödeme Günü', tip: 'text', placeholder: 'Her ayın 1\'i' },
  { key: 'baslangic', label: 'Başlangıç Tarihi', tip: 'date' },
  { key: 'bitis', label: 'Bitiş Tarihi', tip: 'date' },
  { key: 'artis_orani', label: 'Artış Oranı', tip: 'text', placeholder: 'TÜFE' },
];

export default function Belgeler() {
  const [belgeTip, setBelgeTip] = useState('');
  const [musteriler, setMusteriler] = useState([]);
  const [mulkler, setMulkler] = useState([]);
  const [form, setForm] = useState({ musteri_id: '', mulk_id: '', detaylar: {} });
  const [yukleniyor, setYuk] = useState(false);

  const yukle = useCallback(async () => {
    try {
      const [m, p] = await Promise.all([
        api.get('/api/panel/musteriler'),
        api.get('/api/panel/mulkler'),
      ]);
      setMusteriler(m.data.musteriler || []);
      setMulkler(p.data.mulkler || []);
    } catch {}
  }, []);

  useEffect(() => { yukle(); }, [yukle]);

  const olustur = async () => {
    if (!belgeTip) return;
    setYuk(true);
    try {
      const payload = { ...form, ...(BELGE_TIPLERI[belgeTip].extra || {}) };
      const r = await api.post(BELGE_TIPLERI[belgeTip].endpoint, payload, { responseType: 'blob' });
      const url = URL.createObjectURL(new Blob([r.data], { type: 'application/pdf' }));
      const a = document.createElement('a');
      a.href = url;
      a.download = `${belgeTip}_${Date.now()}.pdf`;
      a.click();
      URL.revokeObjectURL(url);
    } catch {} finally { setYuk(false); }
  };

  const dd = (key, val) => setForm(p => ({ ...p, detaylar: { ...p.detaylar, [key]: val } }));

  return (
    <>
      <h1 style={{ fontSize: 20, fontWeight: 800, color: '#0f172a', marginBottom: 16 }}>📄 Belge Oluştur</h1>

      {/* Belge tipi seçimi */}
      <div style={{ display: 'flex', gap: 10, marginBottom: 20, flexWrap: 'wrap' }}>
        {Object.entries(BELGE_TIPLERI).map(([k, v]) => (
          <button key={k} onClick={() => setBelgeTip(k)} style={{
            padding: '14px 20px', borderRadius: 12, fontSize: 14, fontWeight: 600, cursor: 'pointer',
            background: belgeTip === k ? '#f0fdf4' : '#fff', color: belgeTip === k ? '#16a34a' : '#374151',
            border: `2px solid ${belgeTip === k ? '#16a34a' : '#e2e8f0'}`, flex: '1 1 200px',
          }}>
            <div style={{ fontSize: 24, marginBottom: 4 }}>{v.ikon}</div>
            {v.label}
          </button>
        ))}
      </div>

      {belgeTip && (
        <div style={{ background: '#fff', borderRadius: 12, padding: 20, border: '1px solid #e2e8f0' }}>
          <div style={{ fontWeight: 700, fontSize: 15, color: '#1e293b', marginBottom: 16 }}>
            {BELGE_TIPLERI[belgeTip].ikon} {BELGE_TIPLERI[belgeTip].label}
          </div>

          {/* Müşteri seçimi */}
          <div style={{ marginBottom: 12 }}>
            <label className="etiket">Müşteri</label>
            <select className="input" value={form.musteri_id} onChange={e => setForm(p => ({ ...p, musteri_id: e.target.value }))}>
              <option value="">Müşteri seçin</option>
              {musteriler.map(m => <option key={m.id} value={m.id}>{m.ad_soyad} — {m.telefon || ''}</option>)}
            </select>
          </div>

          {/* Mülk seçimi */}
          <div style={{ marginBottom: 12 }}>
            <label className="etiket">Mülk</label>
            <select className="input" value={form.mulk_id} onChange={e => setForm(p => ({ ...p, mulk_id: e.target.value }))}>
              <option value="">Mülk seçin</option>
              {mulkler.map(m => <option key={m.id} value={m.id}>{m.baslik || m.adres || '—'} — {m.islem_turu === 'kira' ? 'Kiralık' : 'Satılık'}</option>)}
            </select>
          </div>

          {/* Kira kontratı detayları */}
          {belgeTip === 'kira-kontrati' && (
            <div className="grid-2" style={{ marginBottom: 12, gap: 12 }}>
              {KIRA_DETAY.map(a => (
                <div key={a.key}>
                  <label className="etiket">{a.label}</label>
                  <input className="input" type={a.tip || 'text'} value={form.detaylar[a.key] || ''}
                    placeholder={a.placeholder || ''} onChange={e => dd(a.key, e.target.value)} />
                </div>
              ))}
            </div>
          )}

          <button className="btn-yesil" onClick={olustur} disabled={yukleniyor} style={{ marginTop: 8 }}>
            {yukleniyor ? 'Oluşturuluyor...' : '📥 PDF Oluştur ve İndir'}
          </button>
        </div>
      )}

      {!belgeTip && (
        <div style={{ textAlign: 'center', color: '#94a3b8', padding: 40, background: '#fff', borderRadius: 12 }}>
          <div style={{ fontSize: 32, marginBottom: 8 }}>📄</div>
          Oluşturmak istediğiniz belge tipini seçin
        </div>
      )}
    </>
  );
}
