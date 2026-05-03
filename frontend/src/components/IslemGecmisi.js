import React, { useState, useEffect } from 'react';
import api from '../api';

const ISLEM_IKON = {
  musteri_ekle: '👤+', musteri_guncelle: '👤✏️', musteri_sil: '👤🗑',
  mulk_ekle: '🏢+', mulk_guncelle: '🏢✏️', mulk_sil: '🏢🗑',
  gorev_ekle: '📌+', gorev_guncelle: '📌✏️', gorev_sil: '📌🗑',
  not_ekle: '📝+', not_guncelle: '📝✏️', not_sil: '📝🗑',
  fatura_olustur: '🧾+', fatura_guncelle: '🧾✏️', fatura_sil: '🧾🗑',
  teklif_kaydet: '💰+', teklif_guncelle: '💰✏️', teklif_sil: '💰🗑',
  satis_kapandi: '🎉', dogum_gunu_kaydet: '🎂', not_goreve_donustur: '📝→📌',
  gosterim_geri_bildirim: '🏠📝', whatsapp_mesaj_gonder: '💬', toplu_mesaj_gonder: '📨',
  asistan_ismi_degistir: '🤖',
};

export default function IslemGecmisiSayfa() {
  const [islemler, setIslemler] = useState([]);
  const [yuk, setYuk] = useState(true);

  const yukle = () => {
    setYuk(true);
    api.get('/api/panel/islem-gecmisi').then(r => setIslemler(r.data.islemler || [])).catch(() => {}).finally(() => setYuk(false));
  };

  useEffect(() => { yukle(); }, []);

  const geriAl = async (id) => {
    if (!window.confirm('Bu işlemi geri almak istediğinize emin misiniz?')) return;
    try {
      const r = await api.post(`/api/panel/islem-gecmisi/${id}/geri-al`);
      alert(r.data.mesaj || 'Geri alındı');
      yukle();
    } catch (e) { alert(e.response?.data?.message || 'Hata'); }
  };

  return (
    <>
      <h1 style={{ fontSize: 20, fontWeight: 800, color: 'var(--text-primary)', marginBottom: 16 }}>📋 İşlem Geçmişi</h1>

      {yuk ? (
        <div style={{ textAlign: 'center', padding: 40, color: '#94a3b8' }}>Yükleniyor...</div>
      ) : islemler.length === 0 ? (
        <div style={{ textAlign: 'center', padding: 40, color: '#94a3b8', background: 'var(--bg-card)', borderRadius: 12 }}>Henüz işlem kaydı yok</div>
      ) : (
        islemler.map(i => (
          <div key={i.id} style={{
            background: 'var(--bg-card)', borderRadius: 10, padding: '10px 14px', marginBottom: 6,
            border: '1px solid var(--border)', opacity: i.geri_alindi ? 0.4 : 1,
            display: 'flex', justifyContent: 'space-between', alignItems: 'center',
          }}>
            <div style={{ flex: 1 }}>
              <div style={{ fontSize: 13, display: 'flex', alignItems: 'center', gap: 6 }}>
                <span style={{ fontSize: 16 }}>{ISLEM_IKON[i.islem] || '📋'}</span>
                <span style={{ fontWeight: 600, textDecoration: i.geri_alindi ? 'line-through' : 'none' }}>{i.ozet}</span>
              </div>
              <div style={{ fontSize: 11, color: '#94a3b8', marginTop: 2 }}>
                {i.islem} · {i.tablo} · {new Date(i.olusturma).toLocaleString('tr-TR', { day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit' })}
                {i.geri_alindi && ' · ↩️ geri alındı'}
              </div>
            </div>
            {!i.geri_alindi && (
              <button onClick={() => geriAl(i.id)} style={{
                background: '#fef2f2', border: '1px solid #fecaca', borderRadius: 6,
                padding: '4px 10px', fontSize: 11, color: '#dc2626', cursor: 'pointer',
              }}>↩️ Geri Al</button>
            )}
          </div>
        ))
      )}
    </>
  );
}
