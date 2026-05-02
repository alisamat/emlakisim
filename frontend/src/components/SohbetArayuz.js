import React, { useState, useCallback, useEffect } from 'react';
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
import Eslestirme from './Eslestirme';
import Takvim from './Takvim';
import Tanitim from './Tanitim';
import Faturalar from './Faturalar';
import Cagrilar from './Cagrilar';
import KarZarar from './KarZarar';
import Cariler from './Cariler';
import Ayarlar from './Ayarlar';
import MuhasebeRapor from './MuhasebeRapor';
import Butce from './Butce';
import SurecTakip from './SurecTakip';
import Talepler from './Talepler';
import Ekip from './Ekip';
import Performans from './Performans';
import IletisimGecmisi from './IletisimGecmisi';
import EnvanterYonetimi from './EnvanterYonetimi';
import AdminPanel from './AdminPanel';
import KrediPanel from './KrediPanel';
import AdminDashboard from './AdminDashboard';
import IlanOCR from './IlanOCR';
import ResimIsaretleme from './ResimIsaretleme';
import Emlakcilar from './Emlakcilar';
import Gruplar from './Gruplar';
import '../sohbet.css';

export default function SohbetArayuz() {
  const { user } = useAuth();
  const [activeTab, setActiveTab] = useState('chat');

  // Klavye kısayolları
  useEffect(() => {
    const handler = (e) => {
      if (e.ctrlKey || e.metaKey) {
        if (e.key === '1') { e.preventDefault(); setActiveTab('chat'); }
        if (e.key === '2') { e.preventDefault(); setActiveTab('musteriler'); }
        if (e.key === '3') { e.preventDefault(); setActiveTab('mulkler'); }
        if (e.key === 'k') { e.preventDefault(); document.querySelector('.sag-panel-ara')?.focus(); }
      }
      if (e.key === 'Escape') { setSolAcik(false); setSagAcik(false); setKrediPanelAcik(false); }
    };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, []); // eslint-disable-line

  // Sayfa title güncelleme
  useEffect(() => {
    const titles = { chat: 'Sohbet', musteriler: 'Müşteriler', mulkler: 'Portföy', muhasebe: 'Muhasebe', planlama: 'Planlama' };
    document.title = `${titles[activeTab] || activeTab} — Emlakisim AI`;
  }, [activeTab]);
  const [sohbetId, setSohbetId] = useState(null);
  const [mesajlar, setMesajlar] = useState([]);
  const [kredi, setKredi] = useState(user?.kredi ?? 10);
  const [solAcik, setSolAcik] = useState(false);
  const [sagAcik, setSagAcik] = useState(false);
  const [krediPanelAcik, setKrediPanelAcik] = useState(false);

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
        if (r.data.tab) setTimeout(() => openTab(r.data.tab), 600);
      })
      .catch(() => {
        setMesajlar(p => [...p, { rol: 'assistant', icerik: 'Bir hata oluştu.', olusturma: new Date().toISOString() }]);
      });
  }, [sohbetId, openTab]);

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
      case 'eslestirme':   return <div className="sayfa-icerik"><Eslestirme /></div>;
      case 'takvim':       return <div className="sayfa-icerik"><Takvim /></div>;
      case 'tanitim':      return <div className="sayfa-icerik"><Tanitim /></div>;
      case 'faturalar':    return <div className="sayfa-icerik"><Faturalar /></div>;
      case 'cagrilar':     return <div className="sayfa-icerik"><Cagrilar /></div>;
      case 'karzarar':     return <div className="sayfa-icerik"><KarZarar /></div>;
      case 'cariler':      return <div className="sayfa-icerik"><Cariler /></div>;
      case 'ayarlar':      return <div className="sayfa-icerik"><Ayarlar /></div>;
      case 'muhrapor':     return <div className="sayfa-icerik"><MuhasebeRapor /></div>;
      case 'butce':        return <div className="sayfa-icerik"><Butce /></div>;
      case 'surec':        return <div className="sayfa-icerik"><SurecTakip /></div>;
      case 'talepler':     return <div className="sayfa-icerik"><Talepler /></div>;
      case 'ekip':         return <div className="sayfa-icerik"><Ekip /></div>;
      case 'performans':   return <div className="sayfa-icerik"><Performans /></div>;
      case 'iletisim':     return <div className="sayfa-icerik"><IletisimGecmisi /></div>;
      case 'envanter':     return <div className="sayfa-icerik"><EnvanterYonetimi /></div>;
      case 'admin':        return <div className="sayfa-icerik"><AdminPanel /></div>;
      case 'admin_dash':   return <div className="sayfa-icerik"><AdminDashboard /></div>;
      case 'ilan_ocr':     return <div className="sayfa-icerik"><IlanOCR /></div>;
      case 'isaretleme':   return <div className="sayfa-icerik"><ResimIsaretleme /></div>;
      case 'emlakcilar':   return <div className="sayfa-icerik"><Emlakcilar /></div>;
      case 'gruplar':      return <div className="sayfa-icerik"><Gruplar /></div>;
      case 'profil':       return <div className="sayfa-icerik"><Profil /></div>;
      default:
        return (
          <SohbetAlani
            sohbetId={sohbetId}
            setSohbetId={setSohbetId}
            mesajlar={mesajlar}
            setMesajlar={setMesajlar}
            onKrediGuncelle={setKredi}
            onTabAc={openTab}
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
        onOpenTab={openTab}
        onKrediTikla={() => setKrediPanelAcik(true)}
      />

      <KrediPanel acik={krediPanelAcik} onKapat={() => setKrediPanelAcik(false)} kredi={kredi} />

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
