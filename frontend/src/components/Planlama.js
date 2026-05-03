import React, { useState, useEffect, useCallback } from 'react';
import api from '../api';

function tarihGoster(tarihStr) {
  if (!tarihStr) return '';
  const tarih = new Date(tarihStr);
  const bugun = new Date();
  bugun.setHours(0,0,0,0);
  const yarin = new Date(bugun); yarin.setDate(yarin.getDate() + 1);
  const haftaya = new Date(bugun); haftaya.setDate(haftaya.getDate() + 7);

  const t = new Date(tarih); t.setHours(0,0,0,0);
  const saat = tarih.toLocaleTimeString('tr-TR', { hour: '2-digit', minute: '2-digit' });
  const gunler = ['Pazar', 'Pazartesi', 'Salı', 'Çarşamba', 'Perşembe', 'Cuma', 'Cumartesi'];
  const gun = gunler[tarih.getDay()];

  if (t.getTime() === bugun.getTime()) return `Bugün ${saat}`;
  if (t.getTime() === yarin.getTime()) return `Yarın ${saat}`;
  if (t < haftaya) return `${gun} ${saat}`;
  return `${tarih.toLocaleDateString('tr-TR', { day: 'numeric', month: 'long' })} ${gun} ${saat}`;
}

const ONCELIK = {
  acil:   { label: '🔴 Acil', renk: '#dc2626' },
  yuksek: { label: '🟠 Yüksek', renk: '#f59e0b' },
  orta:   { label: '🟡 Orta', renk: '#eab308' },
  dusuk:  { label: '🟢 Düşük', renk: '#16a34a' },
};

const TIP_LABEL = { gorev: '📌 Görev', hatirlatma: '🔔 Hatırlatma', yer_gosterme: '🏠 Yer Gösterme', toplanti: '🤝 Toplantı' };

function GorevFormu({ onKaydet, onIptal }) {
  const [form, setForm] = useState({ baslik: '', aciklama: '', tip: 'gorev', oncelik: 'orta', baslangic: '', bitis: '' });
  const [yukleniyor, setYuk] = useState(false);
  const d = e => setForm(p => ({ ...p, [e.target.name]: e.target.value }));

  const kaydet = async e => {
    e.preventDefault(); setYuk(true);
    try {
      const r = await api.post('/api/panel/planlama/gorevler', form);
      onKaydet(r.data.gorev);
    } catch {} finally { setYuk(false); }
  };

  return (
    <div style={{ background: '#fff', borderRadius: 12, padding: 20, marginBottom: 16, border: '1px solid #e2e8f0' }}>
      <div style={{ fontWeight: 700, fontSize: 15, color: '#1e293b', marginBottom: 16 }}>Yeni Görev</div>
      <form onSubmit={kaydet}>
        <div style={{ marginBottom: 12 }}>
          <label className="etiket">Başlık *</label>
          <input className="input" name="baslik" value={form.baslik} onChange={d} required placeholder="Ahmet bey'e dönüş yap" />
        </div>
        <div className="grid-2" style={{ marginBottom: 12 }}>
          <div>
            <label className="etiket">Tip</label>
            <select className="input" name="tip" value={form.tip} onChange={d}>
              {Object.entries(TIP_LABEL).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
            </select>
          </div>
          <div>
            <label className="etiket">Öncelik</label>
            <select className="input" name="oncelik" value={form.oncelik} onChange={d}>
              {Object.entries(ONCELIK).map(([k, v]) => <option key={k} value={k}>{v.label}</option>)}
            </select>
          </div>
        </div>
        <div className="grid-2" style={{ marginBottom: 12 }}>
          <div><label className="etiket">Başlangıç</label><input className="input" name="baslangic" type="datetime-local" value={form.baslangic} onChange={d} /></div>
          <div><label className="etiket">Bitiş</label><input className="input" name="bitis" type="datetime-local" value={form.bitis} onChange={d} /></div>
        </div>
        <div style={{ marginBottom: 16 }}>
          <label className="etiket">Açıklama</label>
          <textarea className="input" name="aciklama" value={form.aciklama} onChange={d} rows={2} style={{ resize: 'vertical' }} />
        </div>
        <div style={{ display: 'flex', gap: 10 }}>
          <button className="btn-yesil" type="submit" disabled={yukleniyor}>{yukleniyor ? 'Kaydediliyor...' : 'Kaydet'}</button>
          <button className="btn-gri" type="button" onClick={onIptal}>İptal</button>
        </div>
      </form>
    </div>
  );
}

function GorevKarti({ g, onDurumDegistir, onSil }) {
  const o = ONCELIK[g.oncelik] || ONCELIK.orta;
  const tamamlandi = g.durum === 'tamamlandi';

  return (
    <div style={{
      background: '#fff', borderRadius: 12, padding: '12px 16px', marginBottom: 8,
      border: '1px solid #e2e8f0', borderLeft: `3px solid ${o.renk}`,
      opacity: tamamlandi ? 0.6 : 1,
    }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div style={{ flex: 1 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
            <button onClick={() => onDurumDegistir(g.id, tamamlandi ? 'bekliyor' : 'tamamlandi')} style={{
              width: 20, height: 20, borderRadius: 4, border: `2px solid ${o.renk}`,
              background: tamamlandi ? o.renk : 'transparent', cursor: 'pointer',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              color: '#fff', fontSize: 12,
            }}>{tamamlandi ? '✓' : ''}</button>
            <span style={{ fontWeight: 600, fontSize: 14, color: '#1e293b', textDecoration: tamamlandi ? 'line-through' : 'none' }}>{g.baslik}</span>
            <span style={{ fontSize: 11, color: '#94a3b8' }}>{TIP_LABEL[g.tip] || g.tip}</span>
          </div>
          {g.aciklama && <div style={{ fontSize: 12, color: '#94a3b8', marginLeft: 28 }}>{g.aciklama}</div>}
          <div style={{ fontSize: 11, color: '#64748b', marginLeft: 28, marginTop: 2 }}>
            📅 {g.baslangic ? tarihGoster(g.baslangic) : 'Tarih belirtilmedi'}
          </div>
        </div>
        <button onClick={() => onSil(g.id)} style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#94a3b8', fontSize: 14 }}>🗑</button>
      </div>
    </div>
  );
}

export default function Planlama() {
  const [gorevler, setGorevler] = useState([]);
  const [bugun, setBugun] = useState({ bugun: [], yaklasan: [] });
  const [formAcik, setFormAcik] = useState(false);
  const [yukleniyor, setYuk] = useState(false);
  const [filtre, setFiltre] = useState('aktif'); // aktif, tamamlandi, hepsi

  const yukle = useCallback(async () => {
    setYuk(true);
    try {
      const [g, b] = await Promise.all([
        api.get('/api/panel/planlama/gorevler'),
        api.get('/api/panel/planlama/bugun'),
      ]);
      setGorevler(g.data.gorevler || []);
      setBugun(b.data);
    } catch {} finally { setYuk(false); }
  }, []);

  useEffect(() => { yukle(); }, [yukle]);

  const onKaydet = g => { setGorevler(p => [g, ...p]); setFormAcik(false); };

  const durumDegistir = async (id, durum) => {
    try {
      await api.put(`/api/panel/planlama/gorevler/${id}`, { durum });
      setGorevler(p => p.map(g => g.id === id ? { ...g, durum } : g));
    } catch {}
  };

  const sil = async id => {
    if (!window.confirm('Bu görevi silmek istediğinize emin misiniz?')) return;
    try { await api.delete(`/api/panel/planlama/gorevler/${id}`); setGorevler(p => p.filter(g => g.id !== id)); } catch {}
  };

  let liste = gorevler;
  if (filtre === 'aktif') liste = liste.filter(g => g.durum !== 'tamamlandi' && g.durum !== 'iptal');
  else if (filtre === 'tamamlandi') liste = liste.filter(g => g.durum === 'tamamlandi');

  const aktifSayi = gorevler.filter(g => g.durum !== 'tamamlandi' && g.durum !== 'iptal').length;
  const tamamSayi = gorevler.filter(g => g.durum === 'tamamlandi').length;

  return (
    <>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
        <h1 style={{ fontSize: 20, fontWeight: 800, color: '#0f172a' }}>📅 Planlama</h1>
        <button className="btn-yesil" onClick={() => setFormAcik(p => !p)}>+ Görev Ekle</button>
      </div>

      {/* Bugün özet */}
      {bugun.bugun.length > 0 && (
        <div style={{ background: '#fffbeb', borderRadius: 12, padding: 14, marginBottom: 16, border: '1px solid #fde68a' }}>
          <div style={{ fontWeight: 700, fontSize: 13, color: '#92400e', marginBottom: 6 }}>📌 Bugün ({bugun.bugun.length})</div>
          {bugun.bugun.map(g => (
            <div key={g.id} style={{ fontSize: 13, color: '#78350f', padding: '2px 0' }}>
              • {g.baslik} {g.baslangic ? `— ${tarihGoster(g.baslangic)}` : ''}
            </div>
          ))}
        </div>
      )}

      {bugun.yaklasan.length > 0 && (
        <div style={{ background: '#eff6ff', borderRadius: 12, padding: 14, marginBottom: 16, border: '1px solid #bfdbfe' }}>
          <div style={{ fontWeight: 700, fontSize: 13, color: '#1d4ed8', marginBottom: 6 }}>🔜 Yaklaşan ({bugun.yaklasan.length})</div>
          {bugun.yaklasan.slice(0, 3).map(g => (
            <div key={g.id} style={{ fontSize: 13, color: '#1e40af', padding: '2px 0' }}>
              • {g.baslik} — {g.baslangic ? tarihGoster(g.baslangic) : ''}
            </div>
          ))}
        </div>
      )}

      {formAcik && <GorevFormu onKaydet={onKaydet} onIptal={() => setFormAcik(false)} />}

      {/* Filtre */}
      <div style={{ display: 'flex', gap: 8, marginBottom: 16 }}>
        {[['aktif', `📌 Aktif (${aktifSayi})`], ['tamamlandi', `✅ Tamamlandı (${tamamSayi})`], ['hepsi', 'Hepsi']].map(([v, l]) => (
          <button key={v} onClick={() => setFiltre(v)} style={{
            padding: '6px 14px', borderRadius: 20, fontSize: 13, fontWeight: 600, cursor: 'pointer',
            background: filtre === v ? '#16a34a' : '#fff', color: filtre === v ? '#fff' : '#374151',
            border: `1px solid ${filtre === v ? '#16a34a' : '#e2e8f0'}`,
          }}>{l}</button>
        ))}
      </div>

      {yukleniyor ? (
        <div style={{ textAlign: 'center', color: '#94a3b8', padding: 40 }}>Yükleniyor…</div>
      ) : liste.length === 0 ? (
        <div style={{ textAlign: 'center', color: '#94a3b8', padding: 40, background: '#fff', borderRadius: 12 }}>
          <div style={{ fontSize: 32, marginBottom: 8 }}>📅</div>
          {filtre === 'tamamlandi' ? 'Tamamlanmış görev yok' : 'Henüz görev eklenmedi'}
        </div>
      ) : (
        liste.map(g => <GorevKarti key={g.id} g={g} onDurumDegistir={durumDegistir} onSil={sil} />)
      )}
    </>
  );
}
