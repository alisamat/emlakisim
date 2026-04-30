import React, { useState, useRef, useEffect, useCallback } from 'react';
import { useAuth } from '../App';
import api from '../api';

// Web Speech API — sesli yazma
function useSesliYazma(onSonuc) {
  const [dinliyor, setDinliyor] = useState(false);
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
        onSonuc(text);
        setDinliyor(false);
      };
      recognition.current.onerror = () => setDinliyor(false);
      recognition.current.onend = () => setDinliyor(false);
    }
  }, [onSonuc]);

  const baslat = () => {
    if (recognition.current && !dinliyor) {
      recognition.current.start();
      setDinliyor(true);
    }
  };

  return { dinliyor, baslat, destekleniyor: !!recognition.current };
}

export default function SohbetAlani({ sohbetId, setSohbetId, mesajlar, setMesajlar, onKrediGuncelle }) {
  const { user } = useAuth();
  const [girdi, setGirdi] = useState('');
  const [yukleniyor, setYuk] = useState(false);
  const mesajlarRef = useRef(null);
  const inputRef = useRef(null);
  const sesliCallback = useCallback((text) => setGirdi(p => p ? p + ' ' + text : text), []);
  const sesli = useSesliYazma(sesliCallback);

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
          </div>
        ) : (
          mesajlar.map((m, i) => (
            <div key={i} className={`sohbet-mesaj ${m.rol}`}>
              <div style={{ whiteSpace: 'pre-wrap' }}>{m.icerik}</div>
              <div className="sohbet-mesaj-zaman">
                {new Date(m.olusturma).toLocaleTimeString('tr-TR', { hour: '2-digit', minute: '2-digit' })}
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
          <button onClick={sesli.baslat} style={{
            background: sesli.dinliyor ? '#dc2626' : 'none', border: 'none',
            fontSize: 20, cursor: 'pointer', padding: '0 4px', flexShrink: 0,
            color: sesli.dinliyor ? '#fff' : '#94a3b8', borderRadius: 8,
          }} title="Sesli yaz">
            🎤
          </button>
        )}
        <button className="sohbet-gonder" onClick={gonder} disabled={!girdi.trim() || yukleniyor}>
          ➤
        </button>
      </div>
    </>
  );
}
