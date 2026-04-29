import React, { useState, useRef, useEffect } from 'react';
import { useAuth } from '../App';
import api from '../api';

export default function SohbetAlani({ sohbetId, setSohbetId, mesajlar, setMesajlar, onKrediGuncelle }) {
  const { user } = useAuth();
  const [girdi, setGirdi] = useState('');
  const [yukleniyor, setYuk] = useState(false);
  const mesajlarRef = useRef(null);
  const inputRef = useRef(null);

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
            <div className="sohbet-hosgeldin-ikon">🏠</div>
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
        <textarea
          ref={inputRef}
          className="sohbet-input"
          placeholder="Sorunuzu yazın... (Shift+Enter ile yeni satır)"
          value={girdi}
          onChange={inputAyar}
          onKeyDown={tusBasma}
          rows={1}
        />
        <button className="sohbet-gonder" onClick={gonder} disabled={!girdi.trim() || yukleniyor}>
          ➤
        </button>
      </div>
    </>
  );
}
