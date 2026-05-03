"""
AKILLI EŞLEŞTİRME v3 — Talep ↔ Mülk çapraz puanlama
Talep modeli varsa onu kullan, yoksa Musteri alanlarına fallback.
"""
from app.models import Musteri, Mulk


def eslesdir(emlakci_id, musteri_id=None, mulk_id=None, talep_id=None, limit=10):
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

    # Tüm eşleştirme tablosu
    return tum_eslesme(emlakci_id, limit)


def tum_eslesme(emlakci_id, limit=20):
    """Talep ↔ Mülk çapraz eşleştirme. Talep varsa onu kullan, yoksa Musteri fallback."""
    mulkler = Mulk.query.filter_by(emlakci_id=emlakci_id, aktif=True).all()
    if not mulkler:
        return []

    sonuclar = []

    # 1. Talep modeli ile eşleştir (yeni sistem)
    try:
        from app.models.talep import Talep
        talepler = Talep.query.filter_by(emlakci_id=emlakci_id, durum='aktif', yonu='arayan').all()
        for talep in talepler:
            for mulk in mulkler:
                puan, nedenler = _talep_puan_hesapla(talep, mulk)
                if puan >= 15:
                    fiyat = f'{int(mulk.fiyat):,}'.replace(',', '.') if mulk.fiyat else '?'
                    musteri_ad = ''
                    if talep.musteri_id:
                        m = Musteri.query.get(talep.musteri_id)
                        if m: musteri_ad = m.ad_soyad + (f' ({m.kunye})' if m.kunye else '')
                    sonuclar.append({
                        'talep_id': talep.id,
                        'musteri_id': talep.musteri_id,
                        'musteri_ad': musteri_ad or '(isimsiz)',
                        'musteri_sicaklik': Musteri.query.get(talep.musteri_id).sicaklik if talep.musteri_id and Musteri.query.get(talep.musteri_id) else 'orta',
                        'mulk_id': mulk.id,
                        'mulk_baslik': mulk.baslik or mulk.adres or '—',
                        'mulk_fiyat': fiyat,
                        'mulk_islem': mulk.islem_turu,
                        'puan': puan,
                        'nedenler': nedenler,
                    })
    except Exception:
        pass

    # 2. Fallback: Eski Musteri alanlarıyla eşleştir (geriye uyumluluk)
    if not sonuclar:
        musteriler = Musteri.query.filter_by(emlakci_id=emlakci_id).all()
        for musteri in musteriler:
            for mulk in mulkler:
                puan, nedenler = _puan_hesapla(musteri, mulk)
                if puan >= 15:
                    fiyat = f'{int(mulk.fiyat):,}'.replace(',', '.') if mulk.fiyat else '?'
                    sonuclar.append({
                        'musteri_id': musteri.id,
                        'musteri_ad': musteri.ad_soyad,
                        'musteri_sicaklik': musteri.sicaklik,
                        'mulk_id': mulk.id,
                        'mulk_baslik': mulk.baslik or mulk.adres or '—',
                        'mulk_fiyat': fiyat,
                        'mulk_islem': mulk.islem_turu,
                        'puan': puan,
                        'nedenler': nedenler,
                    })

    sonuclar.sort(key=lambda x: x['puan'], reverse=True)
    return sonuclar[:limit]


def _talep_puan_hesapla(talep, mulk):
    """Talep modeli ile mülk puanlama."""
    puan = 0
    nedenler = []
    mulk_det = mulk.detaylar or {}

    # 1. İşlem türü (15) — zorunlu
    if talep.islem_turu and mulk.islem_turu:
        if talep.islem_turu == mulk.islem_turu:
            puan += 15
            nedenler.append('İşlem uyumlu')
        else:
            return 0, []

    # 2. Fiyat (25)
    if mulk.fiyat and talep.butce_max:
        if talep.butce_min and talep.butce_min <= mulk.fiyat <= talep.butce_max:
            puan += 25
            nedenler.append('Bütçeye tam uygun')
        elif mulk.fiyat <= talep.butce_max:
            puan += 20
            nedenler.append('Bütçe altında')
        elif mulk.fiyat <= talep.butce_max * 1.1:
            puan += 12
            nedenler.append('Bütçeye yakın (+%10)')

    # 3. Lokasyon (20)
    if talep.tercih_ilce and mulk.ilce:
        if talep.tercih_ilce.lower() in mulk.ilce.lower():
            puan += 12
            nedenler.append(f'İlçe: {mulk.ilce}')
    if talep.tercih_sehir and mulk.sehir:
        if talep.tercih_sehir.lower() in mulk.sehir.lower():
            puan += 8
            nedenler.append(f'Şehir: {mulk.sehir}')

    # 4. Oda (15)
    if talep.tercih_oda and mulk.oda_sayisi:
        if talep.tercih_oda == mulk.oda_sayisi:
            puan += 15
            nedenler.append(f'Oda: {mulk.oda_sayisi}')
        elif talep.tercih_oda.split('+')[0] == mulk.oda_sayisi.split('+')[0]:
            puan += 8
            nedenler.append('Oda yakın')

    # 5. İstenen (15)
    if talep.istenen and isinstance(talep.istenen, list):
        eslesen = sum(1 for o in talep.istenen if _ozellik_kontrol(o.lower(), mulk_det, mulk))
        if talep.istenen:
            puan += int(15 * eslesen / len(talep.istenen))
            for o in talep.istenen:
                if _ozellik_kontrol(o.lower(), mulk_det, mulk):
                    nedenler.append(f'✅ {o}')

    # 6. İstenmeyen (-20 ceza)
    if talep.istenmeyen and isinstance(talep.istenmeyen, list):
        for o in talep.istenmeyen:
            if _ozellik_kontrol(o.lower(), mulk_det, mulk):
                puan -= 20
                nedenler.append(f'❌ {o} (istenmiyor!)')

    # 7. Tip
    if talep.tercih_tip and mulk.tip:
        if talep.tercih_tip.lower() == mulk.tip.lower():
            puan += 5
            nedenler.append(f'Tip: {mulk.tip}')

    return max(0, puan), nedenler


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
    """
    Eşleştirme v2 — yapısal tercihler + istenmeyen özellik kontrolü.

    Puanlama:
    - İşlem türü: 15 (zorunlu eşleşme)
    - Fiyat: 25 (bütçe aralığı)
    - Lokasyon: 20 (şehir/ilçe/semt)
    - Oda: 15 (tercih_oda ↔ mulk.oda_sayisi)
    - İstenen özellikler: 15 (asansör, balkon → mulk detayları)
    - İstenmeyen özellikler: -20 (açık mutfak → mulk kapalıysa +0, açıksa -20)
    - Sıcaklık bonusu: 5
    - Toplam max: 100
    """
    puan = 0
    nedenler = []
    musteri_det = musteri.detaylar or {}
    mulk_det = mulk.detaylar or {}

    # 1. İşlem türü (15) — zorunlu
    if musteri.islem_turu and mulk.islem_turu:
        if musteri.islem_turu == mulk.islem_turu:
            puan += 15
            nedenler.append('İşlem uyumlu')
        else:
            return 0, []

    # 2. Fiyat (25)
    if mulk.fiyat:
        if musteri.butce_max:
            if musteri.butce_min and musteri.butce_min <= mulk.fiyat <= musteri.butce_max:
                puan += 25
                nedenler.append('Bütçeye tam uygun')
            elif mulk.fiyat <= musteri.butce_max:
                puan += 20
                nedenler.append('Bütçe altında')
            elif mulk.fiyat <= musteri.butce_max * 1.1:
                puan += 12
                nedenler.append('Bütçeye yakın (+%10)')
            elif mulk.fiyat <= musteri.butce_max * 1.2:
                puan += 5
                nedenler.append('Bütçe üstü (+%20)')

    # 3. Lokasyon (20)
    tercih_sehir = (musteri_det.get('tercih_sehir') or '').lower()
    tercih_ilce = (musteri_det.get('tercih_ilce') or '').lower()
    mulk_sehir = (mulk.sehir or '').lower()
    mulk_ilce = (mulk.ilce or '').lower()

    if tercih_sehir and tercih_sehir in mulk_sehir:
        puan += 8
        nedenler.append(f'Şehir: {mulk.sehir}')
    if tercih_ilce and tercih_ilce in mulk_ilce:
        puan += 12
        nedenler.append(f'İlçe: {mulk.ilce}')

    # Tercih notlarından lokasyon
    if musteri.tercih_notlar:
        for t in musteri.tercih_notlar.lower().split():
            if len(t) > 3 and (t in mulk_ilce or t in (mulk.adres or '').lower()):
                puan += 5
                nedenler.append(f'Lokasyon: "{t}"')
                break

    # 4. Oda sayısı (15)
    tercih_oda = (musteri_det.get('tercih_oda') or '').lower()
    mulk_oda = (mulk.oda_sayisi or '').lower()
    if tercih_oda and mulk_oda:
        if tercih_oda == mulk_oda:
            puan += 15
            nedenler.append(f'Oda: {mulk_oda}')
        elif tercih_oda in mulk_oda or mulk_oda in tercih_oda:
            puan += 10
            nedenler.append(f'Oda yakın: {mulk_oda}')
        elif tercih_oda.split('+')[0] == mulk_oda.split('+')[0]:
            puan += 6
            nedenler.append('Oda benzer')

    # 5. İstenen özellikler (15)
    istenen = musteri_det.get('istenen_ozellikler', [])
    if isinstance(istenen, list) and istenen:
        eslesen = 0
        for ozellik in istenen:
            oz_lower = ozellik.lower()
            # Mülk detaylarında bu özellik var mı?
            if _ozellik_kontrol(oz_lower, mulk_det, mulk):
                eslesen += 1
                nedenler.append(f'✅ {ozellik}')
        if istenen:
            puan += int(15 * eslesen / len(istenen))

    # 6. İstenmeyen özellikler (-20 ceza)
    istenmeyen = musteri_det.get('istenmeyen_ozellikler', [])
    if isinstance(istenmeyen, list) and istenmeyen:
        for ozellik in istenmeyen:
            oz_lower = ozellik.lower()
            if _ozellik_kontrol(oz_lower, mulk_det, mulk):
                puan -= 20
                nedenler.append(f'❌ {ozellik} (istenmiyor!)')

    # 7. Tip eşleşmesi
    tercih_tip = musteri_det.get('tercih_tip', '').lower()
    if tercih_tip and mulk.tip:
        if tercih_tip == mulk.tip.lower():
            puan += 5
            nedenler.append(f'Tip: {mulk.tip}')

    # 8. Sıcak müşteri bonusu
    if musteri.sicaklik == 'sicak':
        puan += 5
        nedenler.append('🔥 Sıcak')

    return max(0, puan), nedenler


def _ozellik_kontrol(ozellik, mulk_det, mulk):
    """Mülkte bu özellik var mı kontrol et."""
    # Özellik → mülk detay alanı eşleştirmesi
    eslesme = {
        'asansör': ('asansor', ['Var']),
        'asansor': ('asansor', ['Var']),
        'balkon': ('balkon', ['Var']),
        'otopark': ('otopark', ['Açık', 'Kapalı']),
        'eşyalı': ('esyali', ['Evet']),
        'esyali': ('esyali', ['Evet']),
        'site içi': ('site_icerisinde', ['Evet']),
        'site ici': ('site_icerisinde', ['Evet']),
        'açık mutfak': ('mutfak', ['Açık (Amerikan)', 'Açık']),
        'acik mutfak': ('mutfak', ['Açık (Amerikan)', 'Açık']),
        'kapalı mutfak': ('mutfak', ['Kapalı']),
        'kapali mutfak': ('mutfak', ['Kapalı']),
        'doğalgaz': ('isinma', ['Kombi (Doğalgaz)']),
        'dogalgaz': ('isinma', ['Kombi (Doğalgaz)']),
        'merkezi ısıtma': ('isinma', ['Merkezi']),
        'zemin kat': ('bulundugu_kat', ['Zemin', '0', 'Bodrum']),
        'bodrum': ('bulundugu_kat', ['Bodrum', 'Bodrum Kat']),
        'krediye uygun': ('krediye_uygun', ['Evet']),
    }

    if ozellik in eslesme:
        alan, degerler = eslesme[ozellik]
        mulk_deger = str(mulk_det.get(alan, '')).strip()
        return any(d.lower() in mulk_deger.lower() for d in degerler)

    # Serbest metin araması (başlık, adres, detaylar)
    tum_metin = f'{mulk.baslik or ""} {mulk.adres or ""} {str(mulk_det)}'.lower()
    return ozellik in tum_metin
