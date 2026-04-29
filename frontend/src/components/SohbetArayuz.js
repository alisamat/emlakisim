import React, { useState, useCallback } from 'react';
import { useAuth } from '../App';
import api from '../api';
import UstBaslik from './UstBaslik';
import SolPanel from './SolPanel';
import SagPanel from './SagPanel';
import SohbetAlani from './SohbetAlani';
import Musteriler from './Musteriler';
import Mulkler from './Mulkler';
import YerGostermeler from './YerGostermeler';
import Profil from './Profil';
import Belgeler from './Belgeler';
import Muhasebe from './Muhasebe';
import Hesaplamalar from './Hesaplamalar';
import Planlama from './Planlama';
import Yedekleme from './Yedekleme';
import TopluIslem from './TopluIslem';
import Leadler from './Leadler';
import '../sohbet.css';

export default function SohbetArayuz() {
  const { user } = useAuth();
  const [activeTab, setActiveTab] = useState('chat');
  const [sohbetId, setSohbetId] = useState(null);
  const [mesajlar, setMesajlar] = useState([]);
  const [kredi, setKredi] = useState(user?.kredi ?? 10);
  const [solAcik, setSolAcik] = useState(false);
  const [sagAcik, setSagAcik] = useState(false);

  const sohbetGit = useCallback(() => {
    setActiveTab('chat');
    setSolAcik(false);
    setSagAcik(false);
  }, []);

  const yeniSohbet = useCallback(() => {
    setSohbetId(null);
    setMesajlar([]);
    setActiveTab('chat');
    setSolAcik(false);
  }, []);

  const sohbetSec = useCallback(async (id) => {
    try {
      const r = await api.get(`/api/panel/sohbetler/${id}`);
      setSohbetId(id);
      setMesajlar(r.data.mesajlar || []);
      setActiveTab('chat');
      setSolAcik(false);
    } catch {}
  }, []);

  const openTab = useCallback((tab) => {
    setActiveTab(tab);
    setSagAcik(false);
  }, []);

  const mesajGonder = useCallback((metin) => {
    setActiveTab('chat');
    setSagAcik(false);
    // Mesajı otomatik gönder
    setMesajlar(p => [...p, { rol: 'user', icerik: metin, olusturma: new Date().toISOString() }]);
    api.post('/api/panel/sohbet', { mesaj: metin, sohbet_id: sohbetId || undefined })
      .then(r => {
        setMesajlar(p => [...p, { rol: 'assistant', icerik: r.data.cevap, olusturma: new Date().toISOString() }]);
        if (!sohbetId) setSohbetId(r.data.sohbet_id);
        if (r.data.kredi_kalan !== undefined) setKredi(r.data.kredi_kalan);
      })
      .catch(() => {
        setMesajlar(p => [...p, { rol: 'assistant', icerik: 'Bir hata oluştu.', olusturma: new Date().toISOString() }]);
      });
  }, [sohbetId]);

  const renderCenter = () => {
    switch (activeTab) {
      case 'musteriler': return <div className="sayfa-icerik"><Musteriler /></div>;
      case 'mulkler':    return <div className="sayfa-icerik"><Mulkler /></div>;
      case 'kayitlar':   return <div className="sayfa-icerik"><YerGostermeler /></div>;
      case 'belgeler':   return <div className="sayfa-icerik"><Belgeler /></div>;
      case 'muhasebe':      return <div className="sayfa-icerik"><Muhasebe /></div>;
      case 'hesaplamalar': return <div className="sayfa-icerik"><Hesaplamalar /></div>;
      case 'planlama':     return <div className="sayfa-icerik"><Planlama /></div>;
      case 'yedekleme':    return <div className="sayfa-icerik"><Yedekleme /></div>;
      case 'toplu':        return <div className="sayfa-icerik"><TopluIslem /></div>;
      case 'leadler':      return <div className="sayfa-icerik"><Leadler /></div>;
      case 'profil':       return <div className="sayfa-icerik"><Profil /></div>;
      default:
        return (
          <SohbetAlani
            sohbetId={sohbetId}
            setSohbetId={setSohbetId}
            mesajlar={mesajlar}
            setMesajlar={setMesajlar}
            onKrediGuncelle={setKredi}
          />
        );
    }
  };

  return (
    <div className="sohbet-arayuz">
      <UstBaslik
        kredi={kredi}
        onSolToggle={() => { setSolAcik(p => !p); setSagAcik(false); }}
        onSagToggle={() => { setSagAcik(p => !p); setSolAcik(false); }}
        onSohbetGit={sohbetGit}
      />

      {/* Mobil backdrop */}
      {(solAcik || sagAcik) && (
        <div className="mobil-arka-plan acik" onClick={() => { setSolAcik(false); setSagAcik(false); }} />
      )}

      <SolPanel
        kredi={kredi}
        sohbetId={sohbetId}
        onYeniSohbet={yeniSohbet}
        onSohbetSec={sohbetSec}
        acik={solAcik}
      />

      <div className="ana-icerik">
        {renderCenter()}
      </div>

      <SagPanel
        onOpenTab={openTab}
        onMesajGonder={mesajGonder}
        acik={sagAcik}
      />
    </div>
  );
}
