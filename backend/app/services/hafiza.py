"""
HAFIZA KATMANI v2 — Gerçek kalıcı hafıza + konuşma sürekliliği
Müşteri bazlı: tercihler, kararlar, geçmiş günler arası korunur.
Konuşma state: "daha ucuz göster" deyince önceki aramayı hatırlar.
"""
import logging
import re
from datetime import datetime, timedelta
from app.models import db, Musteri, Mulk, Not, YerGosterme
from app.models.muhasebe import GelirGider
from app.models.planlama import Gorev
from app.models.lead import Lead
from app.models.hafiza_model import MusteriHafiza, KonusmaState

logger = logging.getLogger(__name__)


def baglam_olustur(emlakci, metin=''):
    """Her mesajda AI'ya verilecek tam bağlam."""
    parcalar = []

    # 1. Profil
    parcalar.append(f'[SEN] {emlakci.ad_soyad}, {emlakci.acente_adi or "Bağımsız"}, Kredi: {emlakci.kredi}')

    # 2. Güncel istatistik
    m_sayi = Musteri.query.filter_by(emlakci_id=emlakci.id).count()
    p_sayi = Mulk.query.filter_by(emlakci_id=emlakci.id, aktif=True).count()
    l_yeni = Lead.query.filter_by(emlakci_id=emlakci.id, durum='yeni').count()
    parcalar.append(f'[DURUM] {m_sayi} müşteri, {p_sayi} mülk, {l_yeni} yeni lead')

    # 3. Bugünkü görevler
    bugun = datetime.utcnow().replace(hour=0, minute=0, second=0)
    yarin = bugun + timedelta(days=1)
    gorevler = Gorev.query.filter(Gorev.emlakci_id == emlakci.id, Gorev.baslangic >= bugun,
                                   Gorev.baslangic < yarin, Gorev.durum != 'iptal').all()
    if gorevler:
        parcalar.append(f'[BUGÜN] {len(gorevler)} görev: ' + ', '.join([g.baslik for g in gorevler[:5]]))

    # 4. Hatırlatmalar
    notlar = Not.query.filter_by(emlakci_id=emlakci.id, etiket='hatirlatici', tamamlandi=False)\
        .order_by(Not.olusturma.desc()).limit(3).all()
    if notlar:
        parcalar.append(f'[HATIRLA] ' + ' | '.join([n.icerik[:40] for n in notlar]))

    # 5. Konuşma state (multi-turn)
    state = _state_getir(emlakci.id)
    if state:
        if state.son_musteri_id:
            sm = Musteri.query.get(state.son_musteri_id)
            if sm:
                parcalar.append(f'[SON MÜŞTERİ] {sm.ad_soyad} (ID:{sm.id}), '
                               f'{sm.islem_turu or "?"}, Bütçe: {sm.butce_min or "?"}-{sm.butce_max or "?"}, '
                               f'Tercih: {sm.tercih_notlar or "-"}')
        if state.son_mulk_id:
            sp = Mulk.query.get(state.son_mulk_id)
            if sp:
                fiyat = f'{int(sp.fiyat):,}'.replace(',', '.') if sp.fiyat else '?'
                parcalar.append(f'[SON MÜLK] {sp.baslik or sp.adres} — {fiyat} TL')
        if state.son_islem:
            parcalar.append(f'[SON İŞLEM] {state.son_islem}')
        if state.son_arama:
            parcalar.append(f'[SON ARAMA] {state.son_arama}')

    # 6. Mesajda geçen müşteri/mülk → detaylı bağlam + kalıcı hafıza
    if metin:
        musteri = _musteri_bul(emlakci.id, metin)
        if musteri:
            parcalar.append(_musteri_tam_baglam(emlakci.id, musteri))
            _state_guncelle(emlakci.id, son_musteri_id=musteri.id)

        mulk = _mulk_bul(emlakci.id, metin)
        if mulk:
            fiyat = f'{int(mulk.fiyat):,}'.replace(',', '.') if mulk.fiyat else '?'
            det = mulk.detaylar or {}
            parcalar.append(f'[MÜLK: {mulk.baslik or mulk.adres}] {mulk.sehir or ""} {mulk.ilce or ""}, '
                           f'{mulk.tip or ""}, {"Kiralık" if mulk.islem_turu == "kira" else "Satılık"}, '
                           f'Fiyat: {fiyat} TL, Oda: {mulk.oda_sayisi or "-"}, '
                           f'Detay: {", ".join(f"{k}={v}" for k, v in det.items() if v)[:150]}')
            _state_guncelle(emlakci.id, son_mulk_id=mulk.id)

    # 7. Zamir çözme — "onu", "ona", "bunu"
    if metin and re.search(r'\b(onu|ona|onun|bunu|buna|bunun|onu\s*ara)\b', metin.lower()):
        if state and state.son_musteri_id:
            sm = Musteri.query.get(state.son_musteri_id)
            if sm:
                parcalar.append(f'[ZAMIR→MÜŞTERİ] "onu/ona/bunu" → {sm.ad_soyad} (Tel: {sm.telefon or "-"})')
        if state and state.son_mulk_id:
            sp = Mulk.query.get(state.son_mulk_id)
            if sp:
                parcalar.append(f'[ZAMIR→MÜLK] "bunu/buna" → {sp.baslik or sp.adres}')

    return '\n'.join([p for p in parcalar if p])


def _musteri_bul(emlakci_id, metin):
    """Mesajda müşteri adı ara — kısmi eşleşme destekli."""
    metin_lower = metin.lower()
    musteriler = Musteri.query.filter_by(emlakci_id=emlakci_id).all()

    # Tam ad eşleşmesi
    for m in musteriler:
        if m.ad_soyad and m.ad_soyad.lower() in metin_lower:
            return m

    # Kısmi eşleşme (sadece ad veya soyad)
    for m in musteriler:
        if m.ad_soyad:
            parcalar = m.ad_soyad.lower().split()
            for parca in parcalar:
                if len(parca) > 2 and parca in metin_lower:
                    return m
    return None


def _mulk_bul(emlakci_id, metin):
    """Mesajda mülk başlığı/adresi ara."""
    metin_lower = metin.lower()
    mulkler = Mulk.query.filter_by(emlakci_id=emlakci_id, aktif=True).all()
    for p in mulkler:
        baslik = (p.baslik or '').lower()
        adres = (p.adres or '').lower()
        if (baslik and len(baslik) > 3 and baslik in metin_lower):
            return p
        if (adres and len(adres) > 5 and adres in metin_lower):
            return p
    return None


def _musteri_tam_baglam(emlakci_id, musteri):
    """Müşterinin tüm bilgisi + kalıcı hafıza → AI bağlamı."""
    det = musteri.detaylar or {}
    baglam = (f'[MÜŞTERİ: {musteri.ad_soyad}] Tel: {musteri.telefon or "-"}, '
              f'İşlem: {musteri.islem_turu or "-"}, Sıcaklık: {musteri.sicaklik or "-"}, '
              f'Bütçe: {musteri.butce_min or "?"}-{musteri.butce_max or "?"} TL, '
              f'Tercih: {musteri.tercih_notlar or "-"}, Grup: {musteri.grup or "-"}, '
              f'Detay: {", ".join(f"{k}={v}" for k, v in det.items() if v)[:100]}')

    # Kalıcı hafıza
    hafizalar = MusteriHafiza.query.filter_by(
        emlakci_id=emlakci_id, musteri_id=musteri.id
    ).order_by(MusteriHafiza.olusturma.desc()).limit(5).all()

    if hafizalar:
        baglam += '\n[HAFIZA] ' + ' | '.join([f'{h.tip}: {h.icerik[:50]}' for h in hafizalar])

    return baglam


def musteri_hafiza_ekle(emlakci_id, musteri_id, tip, icerik):
    """Müşteri hakkında kalıcı bilgi kaydet."""
    h = MusteriHafiza(emlakci_id=emlakci_id, musteri_id=musteri_id, tip=tip, icerik=icerik[:300])
    db.session.add(h)
    db.session.commit()


def _state_getir(emlakci_id):
    """Konuşma state'i getir."""
    return KonusmaState.query.filter_by(emlakci_id=emlakci_id).first()


def _state_guncelle(emlakci_id, **kwargs):
    """Konuşma state'i güncelle."""
    state = KonusmaState.query.filter_by(emlakci_id=emlakci_id).first()
    if not state:
        state = KonusmaState(emlakci_id=emlakci_id)
        db.session.add(state)
    for k, v in kwargs.items():
        if hasattr(state, k):
            setattr(state, k, v)
    db.session.commit()


def state_guncelle_islem(emlakci_id, islem, musteri_id=None, mulk_id=None, arama=None):
    """İşlem sonrası state güncelle (asistan'dan çağrılır)."""
    kwargs = {'son_islem': islem}
    if musteri_id: kwargs['son_musteri_id'] = musteri_id
    if mulk_id: kwargs['son_mulk_id'] = mulk_id
    if arama: kwargs['son_arama'] = arama
    _state_guncelle(emlakci_id, **kwargs)
