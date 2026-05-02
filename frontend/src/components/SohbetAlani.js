import React, { useState, useRef, useEffect, useCallback } from 'react';
import { useAuth } from '../App';
import api from '../api';

// Proaktif zeka önerileri
function ZekaOnerileri() {
  const [oneriler, setOneriler] = useState([]);
  useEffect(() => {
    api.get('/api/panel/gelismis/zeka/oneriler').then(r => setOneriler(r.data.oneriler || [])).catch(() => {});
  }, []);
  if (oneriler.length === 0) return null;
  return (
    <div style={{ marginTop: 16, width: '100%', maxWidth: 400 }}>
      <div style={{ fontSize: 12, fontWeight: 700, color: '#f59e0b', marginBottom: 6 }}>💡 Akıllı Öneriler</div>
      {oneriler.slice(0, 3).map((o, i) => (
        <div key={i} style={{ fontSize: 12, color: '#64748b', padding: '4px 0', borderBottom: '1px solid #f1f5f9' }}>
          {o.mesaj}
        </div>
      ))}
    </div>
  );
}

// Web Speech API — sesli asistan (STT + TTS)
function useSesliYazma(onSonuc, otomatikGonder) {
  const [dinliyor, setDinliyor] = useState(false);
  const [sesliMod, setSesliMod] = useState(false); // sürekli dinleme modu
  const recognition = useRef(null);

  useEffect(() => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (SpeechRecognition) {
      recognition.current = new SpeechRecognition();
      recognition.current.lang = 'tr-TR';
      recognition.current.continuous = false;
      recognition.current.interimResults = false;
      recognition.current.onresult = (e) => {
        const text = e.results[0][0].transcript;
        if (sesliMod && otomatikGonder) {
          otomatikGonder(text); // sesli modda direkt gönder
        } else {
          onSonuc(text);
        }
        setDinliyor(false);
      };
      recognition.current.onerror = () => setDinliyor(false);
      recognition.current.onend = () => {
        setDinliyor(false);
        // Sesli modda tekrar dinlemeye başla
        if (sesliMod && recognition.current) {
          setTimeout(() => {
            try { recognition.current.start(); setDinliyor(true); } catch {}
          }, 500);
        }
      };
    }
  }, [onSonuc, otomatikGonder, sesliMod]);

  const baslat = () => {
    if (recognition.current && !dinliyor) {
      recognition.current.start();
      setDinliyor(true);
    }
  };

  const durdur = () => {
    setSesliMod(false);
    if (recognition.current) { try { recognition.current.stop(); } catch {} }
    setDinliyor(false);
  };

  const sesliModToggle = () => {
    if (sesliMod) {
      durdur();
    } else {
      setSesliMod(true);
      baslat();
    }
  };

  return { dinliyor, baslat, durdur, sesliMod, sesliModToggle, destekleniyor: !!recognition.current };
}

// Text-to-Speech — cevabı sesli oku
function sesliOku(metin) {
  if (!window.speechSynthesis) return;
  // Markdown/emoji temizle
  const temiz = metin.replace(/[*_#`]/g, '').replace(/[^\w\sğüşıöçĞÜŞİÖÇ.,!?:;()\-\n]/g, '').trim();
  if (!temiz) return;
  const utterance = new SpeechSynthesisUtterance(temiz.slice(0, 500));
  utterance.lang = 'tr-TR';
  utterance.rate = 1.1;
  utterance.pitch = 1.0;
  // Türkçe ses tercih et
  const sesler = window.speechSynthesis.getVoices();
  const turkce = sesler.find(s => s.lang.startsWith('tr'));
  if (turkce) utterance.voice = turkce;
  window.speechSynthesis.speak(utterance);
}

// Mesaj içindeki markdown linkleri tıklanabilir yap + bold
function mesajRender(text) {
  if (!text) return text;
  // [label](url) → tıklanabilir indirme butonu
  const parts = text.split(/(\[.*?\]\(.*?\))/g);
  return parts.map((part, i) => {
    const linkMatch = part.match(/\[(.*?)\]\((.*?)\)/);
    if (linkMatch) {
      const [, label, url] = linkMatch;
      const indir = async (e) => {
        e.preventDefault();
        try {
          const token = localStorage.getItem('emlakisim_token');
          const r = await fetch(`${api.defaults.baseURL || ''}${url}`, {
            headers: { 'Authorization': `Bearer ${token}` },
          });
          const blob = await r.blob();
          const a = document.createElement('a');
          a.href = URL.createObjectURL(blob);
          const cd = r.headers.get('content-disposition');
          a.download = cd ? cd.split('filename=')[1]?.replace(/"/g, '') : 'dosya.xlsx';
          a.click();
          URL.revokeObjectURL(a.href);
        } catch { alert('İndirme hatası'); }
      };
      return (
        <button key={i} onClick={indir}
          style={{ display: 'inline-block', margin: '6px 0', padding: '8px 16px', background: '#16a34a', color: '#fff', borderRadius: 8, border: 'none', fontSize: 13, fontWeight: 600, cursor: 'pointer' }}
        >{label}</button>
      );
    }
    // *bold* → <strong>
    return <span key={i}>{part.split(/(\*[^*]+\*)/).map((p, j) => {
      if (p.startsWith('*') && p.endsWith('*')) return <strong key={j}>{p.slice(1, -1)}</strong>;
      return p;
    })}</span>;
  });
}

export default function SohbetAlani({ sohbetId, setSohbetId, mesajlar, setMesajlar, onKrediGuncelle, onTabAc }) {
  const { user } = useAuth();
  const [girdi, setGirdi] = useState('');
  const [yukleniyor, setYuk] = useState(false);
  const mesajlarRef = useRef(null);
  const inputRef = useRef(null);
  const sesliCallback = useCallback((text) => setGirdi(p => p ? p + ' ' + text : text), []);
  const sesliOtomatikGonder = useCallback((text) => {
    // Sesli modda direkt mesaj gönder
    setMesajlar(p => [...p, { rol: 'user', icerik: text, olusturma: new Date().toISOString() }]);
    setYuk(true);
    api.post('/api/panel/sohbet', { mesaj: text, sohbet_id: sohbetId || undefined })
      .then(r => {
        setMesajlar(p => [...p, { rol: 'assistant', icerik: r.data.cevap, olusturma: new Date().toISOString() }]);
        if (!sohbetId) setSohbetId(r.data.sohbet_id);
        if (r.data.kredi_kalan !== undefined) onKrediGuncelle(r.data.kredi_kalan);
        if (r.data.tab && onTabAc) setTimeout(() => onTabAc(r.data.tab), 600);
        // Sesli modda cevabı sesli oku
        sesliOku(r.data.cevap);
      })
      .catch(() => {
        setMesajlar(p => [...p, { rol: 'assistant', icerik: 'Bir hata oluştu.', olusturma: new Date().toISOString() }]);
      })
      .finally(() => setYuk(false));
  }, [sohbetId, setSohbetId, setMesajlar, onKrediGuncelle, onTabAc]);
  const sesli = useSesliYazma(sesliCallback, sesliOtomatikGonder);

  // Otomatik scroll
  useEffect(() => {
    if (mesajlarRef.current) {
      mesajlarRef.current.scrollTop = mesajlarRef.current.scrollHeight;
    }
  }, [mesajlar, yukleniyor]);

  const gonder = async () => {
    const metin = girdi.trim();
    if (!metin || yukleniyor) return;

    setGirdi('');
    setMesajlar(p => [...p, { rol: 'user', icerik: metin, olusturma: new Date().toISOString() }]);
    setYuk(true);

    try {
      const r = await api.post('/api/panel/sohbet', { mesaj: metin, sohbet_id: sohbetId || undefined });
      setMesajlar(p => [...p, { rol: 'assistant', icerik: r.data.cevap, olusturma: new Date().toISOString() }]);
      if (!sohbetId) setSohbetId(r.data.sohbet_id);
      if (r.data.kredi_kalan !== undefined) onKrediGuncelle(r.data.kredi_kalan);
      if (r.data.tab && onTabAc) setTimeout(() => onTabAc(r.data.tab), 600);
    } catch {
      setMesajlar(p => [...p, { rol: 'assistant', icerik: 'Bir hata oluştu, lütfen tekrar deneyin.', olusturma: new Date().toISOString() }]);
    } finally {
      setYuk(false);
    }
  };

  const tusBasma = e => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      gonder();
    }
  };

  // Textarea yükseklik ayarı
  const inputAyar = e => {
    setGirdi(e.target.value);
    e.target.style.height = 'auto';
    e.target.style.height = Math.min(e.target.scrollHeight, 120) + 'px';
  };

  return (
    <>
      {/* Mesajlar */}
      <div className="sohbet-mesajlar" ref={mesajlarRef}>
        {mesajlar.length === 0 ? (
          <div className="sohbet-hosgeldin">
            {localStorage.getItem('emlakisim_logo') ? (
              <img src={localStorage.getItem('emlakisim_logo')} alt="Logo" style={{ width: 64, height: 64, borderRadius: 12, objectFit: 'contain' }} />
            ) : (
              <div className="sohbet-hosgeldin-ikon">🏠</div>
            )}
            <div className="sohbet-hosgeldin-baslik">Merhaba, {user?.ad_soyad?.split(' ')[0]}!</div>
            <div className="sohbet-hosgeldin-aciklama">
              Emlakisim AI Asistanınız hazır. Müşteri ekle, portföy yönet, belge oluştur — her şeyi buradan yapabilirsiniz.
            </div>
            <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginTop: 12 }}>
              {['müşteri ekle', 'portföy listele', 'bugün özet', 'rapor', 'yardım'].map(cmd => (
                <button key={cmd} onClick={() => { setGirdi(cmd); }}
                  style={{ background: '#f0fdf4', border: '1px solid #bbf7d0', borderRadius: 20, padding: '6px 14px', fontSize: 12, color: '#16a34a', cursor: 'pointer', fontWeight: 600 }}>
                  {cmd}
                </button>
              ))}
            </div>
            <ZekaOnerileri />
          </div>
        ) : (
          mesajlar.map((m, i) => (
            <div key={i} className={`sohbet-mesaj ${m.rol}`}>
              <div style={{ whiteSpace: 'pre-wrap' }}>{mesajRender(m.icerik)}</div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: 4 }}>
                <span className="sohbet-mesaj-zaman">
                  {new Date(m.olusturma).toLocaleTimeString('tr-TR', { hour: '2-digit', minute: '2-digit' })}
                </span>
                <span style={{ display: 'flex', gap: 4 }}>
                  <button onClick={() => navigator.clipboard.writeText(m.icerik)} style={{
                    background: 'none', border: 'none', cursor: 'pointer', fontSize: 11, color: '#94a3b8', padding: '0 2px',
                  }} title="Kopyala">📋</button>
                  <button onClick={() => {
                    if (navigator.share) navigator.share({ text: m.icerik });
                    else navigator.clipboard.writeText(m.icerik);
                  }} style={{
                    background: 'none', border: 'none', cursor: 'pointer', fontSize: 11, color: '#94a3b8', padding: '0 2px',
                  }} title="Paylaş">📤</button>
                </span>
              </div>
            </div>
          ))
        )}
        {yukleniyor && <div className="sohbet-yazıyor">Yazıyor...</div>}
      </div>

      {/* Input */}
      <div className="sohbet-input-alan">
        {/* Dosya ekleme */}
        <label style={{ cursor: 'pointer', fontSize: 20, color: '#94a3b8', padding: '0 4px', flexShrink: 0 }} title="Dosya ekle">
          📎
          <input type="file" accept="image/*,.pdf,.xlsx,.xls" style={{ display: 'none' }}
            onChange={e => {
              const f = e.target.files?.[0];
              if (f) setGirdi(p => p + `\n[Dosya: ${f.name}]`);
            }} />
        </label>
        {/* Kamera */}
        <label style={{ cursor: 'pointer', fontSize: 20, color: '#94a3b8', padding: '0 4px', flexShrink: 0 }} title="Fotoğraf çek">
          📷
          <input type="file" accept="image/*" capture="environment" style={{ display: 'none' }}
            onChange={e => {
              const f = e.target.files?.[0];
              if (f) setGirdi(p => p + `\n[Fotoğraf: ${f.name}]`);
            }} />
        </label>
        <textarea
          ref={inputRef}
          className="sohbet-input"
          placeholder="Sorunuzu yazın... (Shift+Enter ile yeni satır)"
          value={girdi}
          onChange={inputAyar}
          onKeyDown={tusBasma}
          rows={1}
        />
        {/* Sesli yazma */}
        {sesli.destekleniyor && (
          <>
            <button onClick={sesli.baslat} style={{
              background: sesli.dinliyor ? '#dc2626' : 'none', border: 'none',
              fontSize: 20, cursor: 'pointer', padding: '0 4px', flexShrink: 0,
              color: sesli.dinliyor ? '#fff' : '#94a3b8', borderRadius: 8,
            }} title="Sesli yaz">
              🎤
            </button>
            <button onClick={sesli.sesliModToggle} style={{
              background: sesli.sesliMod ? '#16a34a' : 'none', border: 'none',
              fontSize: 14, cursor: 'pointer', padding: '2px 6px', flexShrink: 0,
              color: sesli.sesliMod ? '#fff' : '#94a3b8', borderRadius: 6,
            }} title={sesli.sesliMod ? 'Sesli asistan kapatma' : 'Sesli asistan — konuş, otomatik gönder, cevabı dinle'}>
              {sesli.sesliMod ? '🔊' : '🔇'}
            </button>
          </>
        )}
        <button className="sohbet-gonder" onClick={gonder} disabled={!girdi.trim() || yukleniyor}>
          ➤
        </button>
      </div>
    </>
  );
}
