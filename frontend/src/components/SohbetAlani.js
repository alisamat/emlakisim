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

  // Satır satır işle
  const satirlar = text.split('\n');
  const sonuc = [];
  let listeAcik = false;
  let listeItems = [];

  const listeKapat = () => {
    if (listeItems.length > 0) {
      sonuc.push(<ul key={`ul-${sonuc.length}`} style={{ margin: '4px 0', paddingLeft: 20 }}>{listeItems}</ul>);
      listeItems = [];
      listeAcik = false;
    }
  };

  satirlar.forEach((satir, si) => {
    // Numaralı liste: "1. ", "2. " vb.
    const numaraMatch = satir.match(/^(\d+)\.\s+(.+)/);
    // Madde işareti: "• ", "- ", "  • " vb.
    const maddeMatch = satir.match(/^\s*[•\u002D]\s+(.+)/);

    if (numaraMatch) {
      if (!listeAcik) listeAcik = true;
      listeItems.push(<li key={`li-${si}`} style={{ fontSize: 13, padding: '1px 0' }}>{satirIciBicimle(numaraMatch[2])}</li>);
      return;
    }
    if (maddeMatch) {
      if (!listeAcik) listeAcik = true;
      listeItems.push(<li key={`li-${si}`} style={{ listStyleType: 'disc', fontSize: 13, padding: '1px 0' }}>{satirIciBicimle(maddeMatch[1])}</li>);
      return;
    }

    listeKapat();

    // Başlık: "### ", "## "
    if (satir.startsWith('### ')) {
      sonuc.push(<div key={si} style={{ fontWeight: 700, fontSize: 14, color: '#0f172a', margin: '8px 0 4px' }}>{satirIciBicimle(satir.slice(4))}</div>);
      return;
    }
    if (satir.startsWith('## ')) {
      sonuc.push(<div key={si} style={{ fontWeight: 800, fontSize: 15, color: '#0f172a', margin: '10px 0 4px' }}>{satirIciBicimle(satir.slice(3))}</div>);
      return;
    }

    // Ayırıcı çizgi
    if (satir.match(/^[═─\u002D]{3,}$/)) {
      sonuc.push(<hr key={si} style={{ border: 'none', borderTop: '1px solid #e2e8f0', margin: '8px 0' }} />);
      return;
    }

    // Boş satır
    if (!satir.trim()) {
      sonuc.push(<div key={si} style={{ height: 6 }} />);
      return;
    }

    // Normal satır
    sonuc.push(<div key={si} style={{ lineHeight: 1.5 }}>{satirIciBicimle(satir)}</div>);
  });

  listeKapat();
  return sonuc;
}

// Satır içi biçimlendirme: *bold*, _italic_, `code`, [link](url)
function satirIciBicimle(text) {
  if (!text) return text;
  // Önce [link](url) → buton
  const parts = text.split(/(\[.*?\]\(.*?\))/g);
  return parts.map((part, i) => {
    const linkMatch = part.match(/\[(.*?)\]\((.*?)\)/);
    if (linkMatch) {
      const [, label, url] = linkMatch;
      const indir = async (e) => {
        e.preventDefault();
        try {
          const r = await api.get(url, { responseType: 'blob' });
          const blob = new Blob([r.data]);
          const a = document.createElement('a');
          a.href = URL.createObjectURL(blob);
          const cd = r.headers['content-disposition'];
          a.download = cd ? cd.split('filename=')[1]?.replace(/"/g, '') : url.includes('zip') ? 'emlakisim.zip' : 'emlakisim.xlsx';
          document.body.appendChild(a);
          a.click();
          document.body.removeChild(a);
          URL.revokeObjectURL(a.href);
        } catch { alert('İndirme hatası'); }
      };
      return (
        <button key={i} onClick={indir}
          style={{ display: 'inline-block', margin: '4px 0', padding: '8px 16px', background: '#16a34a', color: '#fff', borderRadius: 8, border: 'none', fontSize: 13, fontWeight: 600, cursor: 'pointer' }}
        >{label}</button>
      );
    }
    // *bold* + _italic_ + `code` + URL link
    return <span key={i}>{part.split(/(\*[^*]+\*|_[^_]+_|`[^`]+`|https?:\/\/[^\s]+)/).map((p, j) => {
      if (p.startsWith('*') && p.endsWith('*')) return <strong key={j} style={{ color: '#0f172a' }}>{p.slice(1, -1)}</strong>;
      if (p.startsWith('_') && p.endsWith('_')) return <em key={j} style={{ color: '#64748b' }}>{p.slice(1, -1)}</em>;
      if (p.startsWith('`') && p.endsWith('`')) return <code key={j} style={{ background: '#f1f5f9', padding: '1px 4px', borderRadius: 4, fontSize: 12, color: '#dc2626' }}>{p.slice(1, -1)}</code>;
      if (p.match(/^https?:\/\//)) return <a key={j} href={p} target="_blank" rel="noopener noreferrer" style={{ color: '#2563eb', textDecoration: 'underline', wordBreak: 'break-all' }}>{p}</a>;
      return p;
    })}</span>;
  });
}

export default function SohbetAlani({ sohbetId, setSohbetId, mesajlar, setMesajlar, onKrediGuncelle, onTabAc }) {
  const { user } = useAuth();
  const [girdi, setGirdi] = useState('');
  const [asistanIsmi, setAsistanIsmi] = useState('');

  useEffect(() => {
    api.get('/api/panel/ayarlar').then(r => {
      const ayar = r.data.ayarlar || {};
      setAsistanIsmi(ayar.asistan_ismi || '');
    }).catch(() => {});
  }, []);
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
              <img src="/logo192.png" alt="Emlakisim" style={{ width: 64, height: 64, borderRadius: 12 }} />
            )}
            <div className="sohbet-hosgeldin-baslik">Merhaba, {user?.ad_soyad?.split(' ')[0]}!</div>
            <div className="sohbet-hosgeldin-aciklama">
              {asistanIsmi
                ? `Ben Emlakisim AI Asistanınız ${asistanIsmi}. Bana Müşteri ekle, portföy yönet, belge oluştur gibi talimatlar verebilir, her şeyi buradan yapabilirsiniz.`
                : 'Emlakisim AI Asistanınız hazır. Müşteri ekle, portföy yönet, belge oluştur — her şeyi buradan yapabilirsiniz.'}
            </div>
            {/* Hızlı Sohbet Komutları */}
            <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', marginTop: 12 }}>
              {[
                { ikon: '👥', cmd: 'müşteri ekle' },
                { ikon: '🏢', cmd: 'mülk ekle' },
                { ikon: '📋', cmd: 'talep ekle' },
                { ikon: '☀️', cmd: 'bugün özet' },
                { ikon: '📊', cmd: 'rapor' },
                { ikon: '🔗', cmd: 'eşleştirme tablosu' },
                { ikon: '🌤', cmd: 'hava durumu' },
                { ikon: '❓', cmd: 'ne yapabilirsin' },
              ].map(b => (
                <button key={b.cmd} onClick={() => { setGirdi(b.cmd); }}
                  style={{ background: '#f0fdf4', border: '1px solid #bbf7d0', borderRadius: 20, padding: '5px 12px', fontSize: 11, color: '#16a34a', cursor: 'pointer', fontWeight: 600 }}>
                  {b.ikon} {b.cmd}
                </button>
              ))}
            </div>
            {/* Hızlı Sayfa Butonları */}
            <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', marginTop: 8 }}>
              {[
                { ikon: '👥', ad: 'Müşteriler', tab: 'musteriler' },
                { ikon: '🏢', ad: 'Portföy', tab: 'mulkler' },
                { ikon: '📋', ad: 'Talepler', tab: 'talepler' },
                { ikon: '📝', ad: 'Notlar', tab: 'notlar' },
                { ikon: '📅', ad: 'Görevler', tab: 'planlama' },
                { ikon: '📰', ad: 'Haberler', tab: 'haberler' },
                { ikon: '🗺', ad: 'Isı Haritası', tab: 'isi_haritasi' },
                { ikon: '⚙️', ad: 'Ayarlar', tab: 'ayarlar' },
              ].map(b => (
                <button key={b.tab} onClick={() => onTabAc && onTabAc(b.tab)}
                  style={{ background: '#eff6ff', border: '1px solid #bfdbfe', borderRadius: 20, padding: '5px 12px', fontSize: 11, color: '#2563eb', cursor: 'pointer', fontWeight: 600 }}>
                  {b.ikon} {b.ad}
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
