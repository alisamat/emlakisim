"""
YASAL DURUM YÖNETİMİ — Mülk yasal kontrol, risk skoru, piyasa değeri analizi
"""
import os
import logging
import requests
from datetime import datetime
from app.models import db, Mulk

logger = logging.getLogger(__name__)

# Yasal kontrol checklist'i
YASAL_KONTROL = {
    'iskan': {'label': 'İskan (Yapı Kullanma İzni)', 'onem': 'kritik', 'aciklama': 'İskansız mülkte kredi çıkmaz, sigorta yapılmaz'},
    'tapu_durumu': {'label': 'Tapu Durumu', 'onem': 'kritik', 'aciklama': 'Kat mülkiyeti en güvenli, kat irtifakı riskli'},
    'ipotek': {'label': 'İpotek/Haciz', 'onem': 'kritik', 'aciklama': 'İpotekli/hacizli mülk satılamaz veya ek işlem gerekir'},
    'dask': {'label': 'DASK Poliçesi', 'onem': 'zorunlu', 'aciklama': 'Tapu işlemi için zorunlu, yıllık yenilenmeli'},
    'imar': {'label': 'İmar Durumu', 'onem': 'onemli', 'aciklama': 'Yapılaşma izni ve plan uygunluğu'},
    'deprem_riski': {'label': 'Deprem Risk Bölgesi', 'onem': 'bilgi', 'aciklama': 'Binanın deprem risk değerlendirmesi'},
    'asbest': {'label': 'Yapı Denetim', 'onem': 'bilgi', 'aciklama': 'Yapı denetim raporu ve bina güvenliği'},
    'aidat_borcu': {'label': 'Aidat Borcu', 'onem': 'onemli', 'aciklama': 'Eski aidat borçları yeni sahibine geçebilir'},
    'kira_sozlesmesi': {'label': 'Mevcut Kira Sözleşmesi', 'onem': 'onemli', 'aciklama': 'Kiracı varsa haklarına dikkat'},
    'vekaletname': {'label': 'Vekaletname Kontrolü', 'onem': 'kritik', 'aciklama': 'Vekaletle satışta doğrulama şart'},
}


def yasal_durum_getir(mulk_id, emlakci_id):
    """Mülkün yasal durum checklist'ini getir."""
    mulk = Mulk.query.filter_by(id=mulk_id, emlakci_id=emlakci_id).first()
    if not mulk:
        return None

    mevcut = mulk.yasal_durum or {}

    checklist = []
    eksik = 0
    risk_puan = 0

    for key, bilgi in YASAL_KONTROL.items():
        durum = mevcut.get(key, 'belirsiz')  # tamam / sorunlu / belirsiz
        item = {
            'anahtar': key,
            'label': bilgi['label'],
            'onem': bilgi['onem'],
            'aciklama': bilgi['aciklama'],
            'durum': durum,
            'not': mevcut.get(f'{key}_not', ''),
        }
        checklist.append(item)

        if durum == 'belirsiz':
            eksik += 1
            if bilgi['onem'] == 'kritik':
                risk_puan += 3
            elif bilgi['onem'] == 'zorunlu':
                risk_puan += 2
            else:
                risk_puan += 1
        elif durum == 'sorunlu':
            risk_puan += 5 if bilgi['onem'] == 'kritik' else 3

    # DASK son kullanma kontrolü
    dask_tarih = mevcut.get('dask_bitis')
    if dask_tarih:
        try:
            bitis = datetime.fromisoformat(dask_tarih)
            if bitis < datetime.utcnow():
                risk_puan += 3
                for item in checklist:
                    if item['anahtar'] == 'dask':
                        item['durum'] = 'sorunlu'
                        item['not'] = f'SÜRESİ DOLMUŞ! ({bitis.strftime("%d.%m.%Y")})'
        except:
            pass

    risk_seviye = 'dusuk' if risk_puan < 5 else 'orta' if risk_puan < 15 else 'yuksek'

    return {
        'mulk_id': mulk_id,
        'checklist': checklist,
        'eksik_sayisi': eksik,
        'risk_puan': risk_puan,
        'risk_seviye': risk_seviye,
        'toplam_kontrol': len(YASAL_KONTROL),
        'tamamlanan': len(YASAL_KONTROL) - eksik,
    }


def yasal_durum_guncelle(mulk_id, emlakci_id, guncellemeler):
    """Yasal durum checklist'ini güncelle."""
    mulk = Mulk.query.filter_by(id=mulk_id, emlakci_id=emlakci_id).first()
    if not mulk:
        return False

    mevcut = mulk.yasal_durum or {}
    mevcut.update(guncellemeler)
    mulk.yasal_durum = mevcut
    db.session.commit()
    return True


def piyasa_degeri_analiz(mulk, emlakci_id):
    """Mülkün piyasa değeri karşılaştırması — portföy + AI analiz."""
    if not mulk.fiyat:
        return {'hata': 'Mülk fiyatı belirtilmemiş'}

    # Portföydeki benzer mülkler
    benzerler = Mulk.query.filter(
        Mulk.emlakci_id == emlakci_id,
        Mulk.aktif == True,
        Mulk.islem_turu == mulk.islem_turu,
        Mulk.tip == mulk.tip,
        Mulk.id != mulk.id,
        Mulk.fiyat.isnot(None),
    ).all()

    # Aynı ilçedekiler
    ayni_ilce = [m for m in benzerler if m.ilce and mulk.ilce and m.ilce.lower() == mulk.ilce.lower()]

    # m² fiyatı
    det = mulk.detaylar or {}
    m2 = det.get('brut_m2') or det.get('net_m2') or mulk.metrekare
    mulk_m2_fiyat = round(mulk.fiyat / float(m2)) if m2 and float(m2) > 0 else None

    benzer_fiyatlar = [m.fiyat for m in benzerler if m.fiyat]
    ilce_fiyatlar = [m.fiyat for m in ayni_ilce if m.fiyat]

    # m² fiyatları
    benzer_m2 = []
    for m in benzerler:
        d = m.detaylar or {}
        mm = d.get('brut_m2') or d.get('net_m2') or m.metrekare
        if mm and m.fiyat and float(mm) > 0:
            benzer_m2.append(round(m.fiyat / float(mm)))

    ort_fiyat = round(sum(benzer_fiyatlar) / len(benzer_fiyatlar)) if benzer_fiyatlar else 0
    ort_m2 = round(sum(benzer_m2) / len(benzer_m2)) if benzer_m2 else 0

    # Karşılaştırma
    if ort_fiyat > 0:
        fark_yuzde = round((mulk.fiyat - ort_fiyat) / ort_fiyat * 100, 1)
    else:
        fark_yuzde = 0

    degerlendirme = ''
    if fark_yuzde > 20:
        degerlendirme = '🔴 Piyasanın çok üstünde — fiyat indirimi önerilir'
    elif fark_yuzde > 10:
        degerlendirme = '🟡 Piyasanın üstünde — pazarlık payı var'
    elif fark_yuzde > -10:
        degerlendirme = '🟢 Piyasa fiyatında — uygun'
    elif fark_yuzde > -20:
        degerlendirme = '🟢 Piyasanın altında — fırsat'
    else:
        degerlendirme = '💰 Çok uygun fiyat — hızlı satış potansiyeli'

    return {
        'mulk_fiyat': mulk.fiyat,
        'mulk_m2_fiyat': mulk_m2_fiyat,
        'portfoy_ortalama': ort_fiyat,
        'portfoy_m2_ortalama': ort_m2,
        'ilce_ortalama': round(sum(ilce_fiyatlar) / len(ilce_fiyatlar)) if ilce_fiyatlar else 0,
        'benzer_sayisi': len(benzerler),
        'ilce_sayisi': len(ayni_ilce),
        'fark_yuzde': fark_yuzde,
        'degerlendirme': degerlendirme,
        'fiyat_min': min(benzer_fiyatlar) if benzer_fiyatlar else 0,
        'fiyat_max': max(benzer_fiyatlar) if benzer_fiyatlar else 0,
    }


def piyasa_rapor_pdf(emlakci, mulk, analiz):
    """Piyasa değeri analiz raporu PDF."""
    from app.services.belge import TurkPDF
    pdf = TurkPDF()
    f = lambda v: f'{int(v):,}'.replace(',', '.') if v else '—'

    pdf.baslik('PIYASA DEGERI ANALIZ RAPORU')
    pdf.set_font('Helvetica', '', 9)
    pdf.cell(0, 6, f'Tarih: {datetime.now().strftime("%d.%m.%Y")}', ln=True, align='C')
    pdf.ln(8)

    pdf.alt_baslik('MULK BILGILERI')
    pdf.satir('Baslik', mulk.baslik or '—')
    pdf.satir('Adres', f'{mulk.adres or ""} {mulk.ilce or ""} {mulk.sehir or ""}')
    pdf.satir('Tip', mulk.tip or '—')
    pdf.satir('Islem', 'Kiralik' if mulk.islem_turu == 'kira' else 'Satilik')
    pdf.satir('Fiyat', f'{f(mulk.fiyat)} TL')
    pdf.bos_satir()

    pdf.alt_baslik('PIYASA KARSILASTIRMASI')
    pdf.satir('Portfoy Ortalama', f'{f(analiz["portfoy_ortalama"])} TL')
    pdf.satir('Ilce Ortalama', f'{f(analiz["ilce_ortalama"])} TL')
    pdf.satir('Fiyat Araliği', f'{f(analiz["fiyat_min"])} - {f(analiz["fiyat_max"])} TL')
    pdf.satir('Fark', f'%{analiz["fark_yuzde"]}')
    if analiz.get('mulk_m2_fiyat'):
        pdf.satir('m2 Fiyat', f'{f(analiz["mulk_m2_fiyat"])} TL/m2')
    if analiz.get('portfoy_m2_ortalama'):
        pdf.satir('Ort. m2 Fiyat', f'{f(analiz["portfoy_m2_ortalama"])} TL/m2')
    pdf.bos_satir()

    pdf.alt_baslik('DEGERLENDIRME')
    pdf.set_font('Helvetica', '', 10)
    pdf.multi_cell(0, 6, analiz['degerlendirme'])
    pdf.bos_satir()

    pdf.satir('Benzer Mulk Sayisi', str(analiz['benzer_sayisi']))
    pdf.satir('Ayni Ilce', str(analiz['ilce_sayisi']))

    pdf.set_font('Helvetica', 'I', 7)
    pdf.set_y(-15)
    pdf.cell(0, 5, f'Emlakisim AI - {emlakci.ad_soyad} - {datetime.now().strftime("%d.%m.%Y")}', align='C')

    return pdf.output()
