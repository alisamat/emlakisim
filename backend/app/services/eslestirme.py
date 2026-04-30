"""
AKILLI EŞLEŞTİRME — Çok boyutlu puanlama
Tip(%15) + Fiyat(%25) + Lokasyon(%25) + Oda(%15) + Detay(%20)
"""
from app.models import Musteri, Mulk


def eslesdir(emlakci_id, musteri_id=None, mulk_id=None, limit=10):
    """Müşteri→mülk veya mülk→müşteri eşleştirme."""
    if musteri_id:
        musteri = Musteri.query.get(musteri_id)
        if not musteri:
            return []
        mulkler = Mulk.query.filter_by(emlakci_id=emlakci_id, aktif=True).all()
        return _musteri_icin_mulk(musteri, mulkler, limit)

    if mulk_id:
        mulk = Mulk.query.get(mulk_id)
        if not mulk:
            return []
        musteriler = Musteri.query.filter_by(emlakci_id=emlakci_id).all()
        return _mulk_icin_musteri(mulk, musteriler, limit)

    return []


def _musteri_icin_mulk(musteri, mulkler, limit):
    """Müşteriye uygun mülkleri puanla."""
    sonuclar = []
    for mulk in mulkler:
        puan, nedenler = _puan_hesapla(musteri, mulk)
        if puan > 0:
            fiyat = f'{int(mulk.fiyat):,}'.replace(',', '.') if mulk.fiyat else '?'
            sonuclar.append({
                'mulk_id': mulk.id,
                'baslik': mulk.baslik or mulk.adres or '—',
                'fiyat': mulk.fiyat,
                'fiyat_str': fiyat + ' TL',
                'tip': mulk.tip,
                'islem': mulk.islem_turu,
                'oda': mulk.oda_sayisi,
                'puan': puan,
                'nedenler': nedenler,
            })
    sonuclar.sort(key=lambda x: x['puan'], reverse=True)
    return sonuclar[:limit]


def _mulk_icin_musteri(mulk, musteriler, limit):
    """Mülke uygun müşterileri puanla."""
    sonuclar = []
    for musteri in musteriler:
        puan, nedenler = _puan_hesapla(musteri, mulk)
        if puan > 0:
            sonuclar.append({
                'musteri_id': musteri.id,
                'ad_soyad': musteri.ad_soyad,
                'telefon': musteri.telefon,
                'sicaklik': musteri.sicaklik,
                'puan': puan,
                'nedenler': nedenler,
            })
    sonuclar.sort(key=lambda x: x['puan'], reverse=True)
    return sonuclar[:limit]


def _puan_hesapla(musteri, mulk):
    """Çok boyutlu eşleştirme puanı."""
    puan = 0
    nedenler = []

    # 1. İşlem türü (%15)
    if musteri.islem_turu and mulk.islem_turu:
        if musteri.islem_turu == mulk.islem_turu:
            puan += 15
            nedenler.append('İşlem türü uyumlu')
        else:
            return 0, []  # Kira arayan satılık istemez

    # 2. Fiyat (%25)
    if mulk.fiyat:
        if musteri.butce_max and musteri.butce_min:
            if musteri.butce_min <= mulk.fiyat <= musteri.butce_max:
                puan += 25
                nedenler.append('Bütçeye tam uygun')
            elif mulk.fiyat <= musteri.butce_max * 1.1:
                puan += 15
                nedenler.append('Bütçeye yakın (+%10)')
            elif mulk.fiyat <= musteri.butce_max * 1.2:
                puan += 8
                nedenler.append('Bütçe üstü (+%20)')
        elif musteri.butce_max:
            if mulk.fiyat <= musteri.butce_max:
                puan += 20
                nedenler.append('Max bütçe altında')

    # 3. Lokasyon (%25)
    musteri_det = musteri.detaylar or {}
    tercih_sehir = (musteri_det.get('tercih_sehir') or '').lower()
    tercih_ilce = (musteri_det.get('tercih_ilce') or '').lower()
    tercih_semt = (musteri_det.get('tercih_semt') or '').lower()
    mulk_sehir = (mulk.sehir or '').lower()
    mulk_ilce = (mulk.ilce or '').lower()
    mulk_adres = (mulk.adres or '').lower()

    if tercih_sehir and tercih_sehir in mulk_sehir:
        puan += 10
        nedenler.append(f'Şehir uyumlu ({mulk.sehir})')
    if tercih_ilce and tercih_ilce in mulk_ilce:
        puan += 10
        nedenler.append(f'İlçe uyumlu ({mulk.ilce})')
    if tercih_semt and tercih_semt in mulk_adres:
        puan += 5
        nedenler.append('Semt/mahalle uyumlu')

    # Tercih notlarından lokasyon
    if musteri.tercih_notlar:
        tercihler = musteri.tercih_notlar.lower().split()
        for t in tercihler:
            if len(t) > 3 and (t in mulk_ilce or t in mulk_adres or t in (mulk.baslik or '').lower()):
                puan += 5
                nedenler.append(f'Tercih: "{t}"')
                break

    # 4. Oda sayısı (%15)
    tercih_oda = musteri_det.get('tercih_oda', '').lower()
    mulk_oda = (mulk.oda_sayisi or '').lower()
    if tercih_oda and mulk_oda:
        if tercih_oda in mulk_oda or mulk_oda in tercih_oda:
            puan += 15
            nedenler.append(f'Oda uyumlu ({mulk_oda})')
        elif tercih_oda.split('+')[0] == mulk_oda.split('+')[0]:
            puan += 8
            nedenler.append('Oda yakın')

    # 5. Detay (%20)
    mulk_det = mulk.detaylar or {}

    # Eşya tercihi
    tercih_esya = musteri_det.get('tercih_esyali', '').lower()
    mulk_esya = (mulk_det.get('esyali') or '').lower()
    if tercih_esya and mulk_esya:
        if ('eşyalı' in tercih_esya and mulk_esya == 'Evet') or ('boş' in tercih_esya and mulk_esya == 'Hayır'):
            puan += 5
            nedenler.append('Eşya tercihi uyumlu')

    # Kredi uygunluğu
    if musteri_det.get('kredi_kullanimi') == 'Evet' and mulk_det.get('krediye_uygun') == 'Evet':
        puan += 5
        nedenler.append('Krediye uygun')

    # Tip eşleşmesi
    tercih_tip = musteri_det.get('tercih_tip', '').lower()
    if tercih_tip and mulk.tip:
        if tercih_tip == mulk.tip.lower() or 'farketmez' in tercih_tip:
            puan += 5
            nedenler.append(f'Tip uyumlu ({mulk.tip})')

    # Sıcak müşteri bonusu
    if musteri.sicaklik == 'sicak':
        puan += 5
        nedenler.append('Sıcak müşteri')

    return puan, nedenler
