import React, { useState, useRef } from 'react';

export default function ResimIsaretleme({ onKapat }) {
  const canvasRef = useRef(null);
  const [resim, setResim] = useState(null);
  const [cizimModu, setCizimModu] = useState('serbest'); // serbest, daire, dikdortgen
  const [renk, setRenk] = useState('#dc2626');
  const [kalinlik, setKalinlik] = useState(3);
  const [ciziliyor, setCiziliyor] = useState(false);
  const [baslangic, setBaslangic] = useState(null);

  const resimYukle = (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const img = new Image();
    img.onload = () => {
      setResim(img);
      const canvas = canvasRef.current;
      if (canvas) {
        canvas.width = Math.min(img.width, 800);
        canvas.height = img.height * (canvas.width / img.width);
        const ctx = canvas.getContext('2d');
        ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
      }
    };
    img.src = URL.createObjectURL(file);
  };

  const getPos = (e) => {
    const rect = canvasRef.current.getBoundingClientRect();
    const touch = e.touches ? e.touches[0] : e;
    return { x: touch.clientX - rect.left, y: touch.clientY - rect.top };
  };

  const basla = (e) => {
    e.preventDefault();
    setCiziliyor(true);
    const pos = getPos(e);
    setBaslangic(pos);
    if (cizimModu === 'serbest') {
      const ctx = canvasRef.current.getContext('2d');
      ctx.beginPath();
      ctx.moveTo(pos.x, pos.y);
    }
  };

  const hareket = (e) => {
    if (!ciziliyor) return;
    e.preventDefault();
    const pos = getPos(e);
    if (cizimModu === 'serbest') {
      const ctx = canvasRef.current.getContext('2d');
      ctx.strokeStyle = renk;
      ctx.lineWidth = kalinlik;
      ctx.lineCap = 'round';
      ctx.lineTo(pos.x, pos.y);
      ctx.stroke();
    }
  };

  const bitir = (e) => {
    if (!ciziliyor) return;
    e.preventDefault();
    setCiziliyor(false);
    const pos = getPos(e.changedTouches ? e.changedTouches[0] : e);
    const ctx = canvasRef.current.getContext('2d');

    if (cizimModu === 'daire' && baslangic) {
      const r = Math.sqrt((pos.x - baslangic.x) ** 2 + (pos.y - baslangic.y) ** 2);
      ctx.strokeStyle = renk;
      ctx.lineWidth = kalinlik;
      ctx.beginPath();
      ctx.arc(baslangic.x, baslangic.y, r, 0, Math.PI * 2);
      ctx.stroke();
    } else if (cizimModu === 'dikdortgen' && baslangic) {
      ctx.strokeStyle = renk;
      ctx.lineWidth = kalinlik;
      ctx.strokeRect(baslangic.x, baslangic.y, pos.x - baslangic.x, pos.y - baslangic.y);
    }
  };

  const temizle = () => {
    if (!resim) return;
    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.drawImage(resim, 0, 0, canvas.width, canvas.height);
  };

  const kaydet = () => {
    const canvas = canvasRef.current;
    const link = document.createElement('a');
    link.download = `isaretlenmis_${Date.now()}.png`;
    link.href = canvas.toDataURL();
    link.click();
  };

  const paylas = () => {
    const canvas = canvasRef.current;
    canvas.toBlob(blob => {
      if (navigator.share) {
        navigator.share({ files: [new File([blob], 'isaretli.png', { type: 'image/png' })] });
      } else {
        kaydet();
      }
    });
  };

  return (
    <>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
        <h1 style={{ fontSize: 20, fontWeight: 800, color: 'var(--text-primary)' }}>🖊 Resim İşaretleme</h1>
      </div>

      {/* Resim yükle */}
      {!resim && (
        <label style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 40, border: '2px dashed var(--border)', borderRadius: 12, cursor: 'pointer', background: 'var(--bg-card)', fontSize: 14 }}>
          📸 Fotoğraf seç veya çek
          <input type="file" accept="image/*" capture="environment" onChange={resimYukle} style={{ display: 'none' }} />
        </label>
      )}

      {resim && (
        <>
          {/* Araç çubuğu */}
          <div style={{ display: 'flex', gap: 6, marginBottom: 8, flexWrap: 'wrap', alignItems: 'center' }}>
            {[['serbest', '✏️'], ['daire', '⭕'], ['dikdortgen', '⬜']].map(([mod, ikon]) => (
              <button key={mod} onClick={() => setCizimModu(mod)} style={{
                padding: '6px 12px', borderRadius: 6, fontSize: 13, cursor: 'pointer',
                background: cizimModu === mod ? '#16a34a' : 'var(--bg-card)',
                color: cizimModu === mod ? '#fff' : 'var(--text-primary)',
                border: `1px solid ${cizimModu === mod ? '#16a34a' : 'var(--border)'}`,
              }}>{ikon} {mod}</button>
            ))}
            <input type="color" value={renk} onChange={e => setRenk(e.target.value)} style={{ width: 30, height: 30, border: 'none', cursor: 'pointer' }} />
            <select value={kalinlik} onChange={e => setKalinlik(parseInt(e.target.value))} style={{ padding: '4px 8px', borderRadius: 4, border: '1px solid var(--border)', fontSize: 12 }}>
              <option value="2">İnce</option><option value="3">Normal</option><option value="5">Kalın</option><option value="8">Çok Kalın</option>
            </select>
            <button onClick={temizle} style={{ padding: '6px 12px', borderRadius: 6, fontSize: 12, background: '#fef2f2', color: '#dc2626', border: '1px solid #fecaca', cursor: 'pointer' }}>🗑 Temizle</button>
            <button onClick={kaydet} style={{ padding: '6px 12px', borderRadius: 6, fontSize: 12, background: '#f0fdf4', color: '#16a34a', border: '1px solid #bbf7d0', cursor: 'pointer' }}>💾 Kaydet</button>
            <button onClick={paylas} style={{ padding: '6px 12px', borderRadius: 6, fontSize: 12, background: '#eff6ff', color: '#1d4ed8', border: '1px solid #bfdbfe', cursor: 'pointer' }}>📤 Paylaş</button>
          </div>

          {/* Canvas */}
          <canvas ref={canvasRef} style={{ border: '1px solid var(--border)', borderRadius: 8, cursor: 'crosshair', maxWidth: '100%', touchAction: 'none' }}
            onMouseDown={basla} onMouseMove={hareket} onMouseUp={bitir} onMouseLeave={bitir}
            onTouchStart={basla} onTouchMove={hareket} onTouchEnd={bitir}
          />

          <div style={{ marginTop: 8 }}>
            <label style={{ fontSize: 12, color: '#64748b', cursor: 'pointer' }}>
              📸 Farklı fotoğraf seç
              <input type="file" accept="image/*" capture="environment" onChange={resimYukle} style={{ display: 'none' }} />
            </label>
          </div>
        </>
      )}
    </>
  );
}
