import React, { useState, useEffect } from 'react';
import api from '../api';

const AY_ISIMLERI = ['Ocak', 'Şubat', 'Mart', 'Nisan', 'Mayıs', 'Haziran', 'Temmuz', 'Ağustos', 'Eylül', 'Ekim', 'Kasım', 'Aralık'];
const GUN_ISIMLERI = ['Pzt', 'Sal', 'Çar', 'Per', 'Cum', 'Cmt', 'Paz'];

export default function Takvim() {
  const simdi = new Date();
  const [yil, setYil] = useState(simdi.getFullYear());
  const [ay, setAy] = useState(simdi.getMonth() + 1);
  const [gorevler, setGorevler] = useState([]);
  const [seciliGun, setSeciliGun] = useState(null);

  useEffect(() => {
    api.get(`/api/panel/planlama/takvim?yil=${yil}&ay=${ay}`)
      .then(r => setGorevler(r.data.gorevler || []))
      .catch(() => {});
  }, [yil, ay]);

  const oncekiAy = () => { if (ay === 1) { setAy(12); setYil(y => y - 1); } else setAy(a => a - 1); };
  const sonrakiAy = () => { if (ay === 12) { setAy(1); setYil(y => y + 1); } else setAy(a => a + 1); };

  // Takvim grid hesapla
  const ilkGun = new Date(yil, ay - 1, 1).getDay(); // 0=Paz
  const baslangicOffset = ilkGun === 0 ? 6 : ilkGun - 1; // Pzt=0
  const gunSayisi = new Date(yil, ay, 0).getDate();
  const gunler = [];
  for (let i = 0; i < baslangicOffset; i++) gunler.push(null);
  for (let i = 1; i <= gunSayisi; i++) gunler.push(i);

  const gunGorevleri = (gun) => {
    if (!gun) return [];
    const tarih = `${yil}-${String(ay).padStart(2, '0')}-${String(gun).padStart(2, '0')}`;
    return gorevler.filter(g => g.baslangic && g.baslangic.startsWith(tarih));
  };

  const bugun = simdi.getDate();
  const bugunMu = (gun) => gun === bugun && ay === simdi.getMonth() + 1 && yil === simdi.getFullYear();

  return (
    <>
      <h1 style={{ fontSize: 20, fontWeight: 800, color: '#0f172a', marginBottom: 16 }}>📅 Takvim</h1>

      {/* Ay navigasyonu */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
        <button onClick={oncekiAy} style={{ background: 'none', border: '1px solid #e2e8f0', borderRadius: 8, padding: '6px 14px', cursor: 'pointer', fontSize: 14 }}>←</button>
        <span style={{ fontWeight: 700, fontSize: 16, color: '#1e293b' }}>{AY_ISIMLERI[ay - 1]} {yil}</span>
        <button onClick={sonrakiAy} style={{ background: 'none', border: '1px solid #e2e8f0', borderRadius: 8, padding: '6px 14px', cursor: 'pointer', fontSize: 14 }}>→</button>
      </div>

      {/* Gün başlıkları */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(7, 1fr)', gap: 2, marginBottom: 4 }}>
        {GUN_ISIMLERI.map(g => (
          <div key={g} style={{ textAlign: 'center', fontSize: 11, fontWeight: 700, color: '#94a3b8', padding: 4 }}>{g}</div>
        ))}
      </div>

      {/* Takvim grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(7, 1fr)', gap: 2 }}>
        {gunler.map((gun, i) => {
          const gg = gunGorevleri(gun);
          return (
            <div key={i} onClick={() => gun && setSeciliGun(seciliGun === gun ? null : gun)} style={{
              minHeight: 60, padding: 4, background: gun ? (bugunMu(gun) ? '#f0fdf4' : '#fff') : 'transparent',
              border: gun ? `1px solid ${seciliGun === gun ? '#16a34a' : '#e2e8f0'}` : 'none',
              borderRadius: 6, cursor: gun ? 'pointer' : 'default',
            }}>
              {gun && (
                <>
                  <div style={{ fontSize: 12, fontWeight: bugunMu(gun) ? 800 : 400, color: bugunMu(gun) ? '#16a34a' : '#374151' }}>{gun}</div>
                  {gg.length > 0 && (
                    <div style={{ marginTop: 2 }}>
                      {gg.slice(0, 2).map((g, j) => (
                        <div key={j} style={{ fontSize: 9, background: '#16a34a', color: '#fff', borderRadius: 3, padding: '1px 3px', marginTop: 1, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                          {g.baslik}
                        </div>
                      ))}
                      {gg.length > 2 && <div style={{ fontSize: 9, color: '#94a3b8' }}>+{gg.length - 2}</div>}
                    </div>
                  )}
                </>
              )}
            </div>
          );
        })}
      </div>

      {/* Seçili gün detayı */}
      {seciliGun && (
        <div style={{ marginTop: 16, background: '#fff', borderRadius: 12, padding: 16, border: '1px solid #e2e8f0' }}>
          <div style={{ fontWeight: 700, fontSize: 14, marginBottom: 8 }}>
            📅 {seciliGun} {AY_ISIMLERI[ay - 1]} {yil}
          </div>
          {gunGorevleri(seciliGun).length === 0 ? (
            <div style={{ fontSize: 13, color: '#94a3b8' }}>Bu günde görev yok</div>
          ) : (
            gunGorevleri(seciliGun).map(g => (
              <div key={g.id} style={{ padding: '8px 0', borderBottom: '1px solid #f1f5f9', fontSize: 13 }}>
                <span style={{ fontWeight: 600 }}>{g.baslik}</span>
                {g.baslangic && <span style={{ color: '#64748b', marginLeft: 8 }}>{new Date(g.baslangic).toLocaleTimeString('tr-TR', { hour: '2-digit', minute: '2-digit' })}</span>}
                {g.aciklama && <div style={{ fontSize: 12, color: '#94a3b8', marginTop: 2 }}>{g.aciklama}</div>}
              </div>
            ))
          )}
        </div>
      )}
    </>
  );
}
