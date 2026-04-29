import React, { useState, useEffect } from 'react';
import api from '../api';

export default function Yedekleme() {
  const [ozet, setOzet] = useState(null);
  const [yukleniyor, setYuk] = useState(false);
  const [mesaj, setMesaj] = useState('');

  useEffect(() => {
    api.get('/api/panel/yedek/ozet').then(r => setOzet(r.data)).catch(() => {});
  }, []);

  const indir = async () => {
    setYuk(true); setMesaj('');
    try {
      const r = await api.get('/api/panel/yedek/indir', { responseType: 'blob' });
      const contentType = r.headers['content-type'] || '';
      const ext = contentType.includes('spreadsheet') ? 'xlsx' : 'json';
      const url = URL.createObjectURL(new Blob([r.data]));
      const a = document.createElement('a');
      a.href = url;
      a.download = `emlakisim_yedek_${Date.now()}.${ext}`;
      a.click();
      URL.revokeObjectURL(url);
      setMesaj('Yedek indirildi!');
    } catch { setMesaj('İndirme hatası'); } finally { setYuk(false); }
  };

  const emailGonder = async () => {
    const email = window.prompt('Yedek gönderilecek email adresi:');
    if (!email) return;
    setYuk(true); setMesaj('');
    try {
      const r = await api.post('/api/panel/yedek/email', { email });
      setMesaj(r.data.mesaj || 'Gönderildi');
    } catch { setMesaj('Gönderim hatası'); } finally { setYuk(false); }
  };

  return (
    <>
      <h1 style={{ fontSize: 20, fontWeight: 800, color: '#0f172a', marginBottom: 16 }}>💾 Yedekleme</h1>

      <div style={{ background: '#fffbeb', borderRadius: 12, padding: 16, marginBottom: 16, border: '1px solid #fde68a' }}>
        <div style={{ fontWeight: 700, fontSize: 13, color: '#92400e', marginBottom: 6 }}>⚠️ Veri Sorumluluğu</div>
        <div style={{ fontSize: 13, color: '#78350f', lineHeight: 1.6 }}>
          Emlakisim verilerinizin düzenli yedeklenmesini önerir. Verilerinizi Excel veya JSON formatında indirebilir,
          email ile kendinize gönderebilirsiniz. 3 ay inaktif hesaplarda veriler silinebilir.
        </div>
      </div>

      {/* Veri özeti */}
      {ozet && (
        <div style={{ background: '#fff', borderRadius: 12, padding: 16, marginBottom: 16, border: '1px solid #e2e8f0' }}>
          <div style={{ fontWeight: 700, fontSize: 14, color: '#1e293b', marginBottom: 12 }}>📊 Veri Özeti</div>
          <div className="grid-2" style={{ gap: 8 }}>
            <div style={{ background: '#f8fafc', borderRadius: 8, padding: 10, textAlign: 'center' }}>
              <div style={{ fontSize: 20, fontWeight: 800, color: '#3b82f6' }}>{ozet.musteriler}</div>
              <div style={{ fontSize: 11, color: '#64748b' }}>Müşteri</div>
            </div>
            <div style={{ background: '#f8fafc', borderRadius: 8, padding: 10, textAlign: 'center' }}>
              <div style={{ fontSize: 20, fontWeight: 800, color: '#f59e0b' }}>{ozet.mulkler}</div>
              <div style={{ fontSize: 11, color: '#64748b' }}>Mülk</div>
            </div>
            <div style={{ background: '#f8fafc', borderRadius: 8, padding: 10, textAlign: 'center' }}>
              <div style={{ fontSize: 20, fontWeight: 800, color: '#16a34a' }}>{ozet.gelir_gider}</div>
              <div style={{ fontSize: 11, color: '#64748b' }}>Muhasebe</div>
            </div>
            <div style={{ background: '#f8fafc', borderRadius: 8, padding: 10, textAlign: 'center' }}>
              <div style={{ fontSize: 20, fontWeight: 800, color: '#8b5cf6' }}>{ozet.gorevler}</div>
              <div style={{ fontSize: 11, color: '#64748b' }}>Görev</div>
            </div>
          </div>
        </div>
      )}

      {/* İşlemler */}
      <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap', marginBottom: 16 }}>
        <button onClick={indir} disabled={yukleniyor} style={{
          flex: '1 1 200px', padding: '16px 20px', borderRadius: 12, border: '2px solid #16a34a',
          background: '#f0fdf4', color: '#16a34a', fontWeight: 700, fontSize: 14, cursor: 'pointer',
        }}>
          📥 Excel İndir
        </button>
        <button onClick={emailGonder} disabled={yukleniyor} style={{
          flex: '1 1 200px', padding: '16px 20px', borderRadius: 12, border: '2px solid #3b82f6',
          background: '#eff6ff', color: '#1d4ed8', fontWeight: 700, fontSize: 14, cursor: 'pointer',
        }}>
          📧 Email ile Gönder
        </button>
      </div>

      {mesaj && (
        <div style={{ background: '#f0fdf4', borderRadius: 8, padding: 12, fontSize: 13, color: '#16a34a', fontWeight: 600 }}>
          ✅ {mesaj}
        </div>
      )}
    </>
  );
}
