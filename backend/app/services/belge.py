"""
BELGE SERVİSİ — PDF oluşturma (yer gösterme, kontrat, fatura)
Dinamik JSON config ile şablonlar — yeni belge tipi = config'e satır
"""
import io
import os
from datetime import datetime


from fpdf import FPDF

# Türkçe → ASCII dönüşüm tablosu (Helvetica uyumlu)
_TR_MAP = str.maketrans({
    'ç': 'c', 'Ç': 'C', 'ğ': 'g', 'Ğ': 'G',
    'ı': 'i', 'İ': 'I', 'ö': 'o', 'Ö': 'O',
    'ş': 's', 'Ş': 'S', 'ü': 'u', 'Ü': 'U',
})

def _ascii(text):
    """Türkçe karakterleri ASCII karşılıklarına çevir."""
    if not text:
        return text or ''
    return str(text).translate(_TR_MAP)


class TurkPDF(FPDF):
    """Türkçe karakter destekli PDF."""
    def __init__(self):
        super().__init__()
        self.add_page()
        self.set_auto_page_break(auto=True, margin=20)

    def cell(self, w, h=0, text='', *args, **kwargs):
        return super().cell(w, h, _ascii(text), *args, **kwargs)

    def multi_cell(self, w, h, text='', *args, **kwargs):
        return super().multi_cell(w, h, _ascii(text), *args, **kwargs)

    def baslik(self, metin):
        self.set_font('Helvetica', 'B', 16)
        self.cell(0, 12, metin, ln=True, align='C')
        self.ln(4)

    def alt_baslik(self, metin):
        self.set_font('Helvetica', 'B', 11)
        self.set_fill_color(240, 253, 244)
        self.cell(0, 8, metin, ln=True, fill=True)
        self.ln(2)

    def satir(self, etiket, deger):
        self.set_font('Helvetica', 'B', 10)
        self.cell(60, 7, etiket + ':', align='R')
        self.set_font('Helvetica', '', 10)
        self.cell(0, 7, str(deger or '-'), ln=True)

    def bos_satir(self):
        self.ln(4)

    def imza_alani(self, sol_baslik, sag_baslik):
        y = self.get_y() + 10
        self.set_font('Helvetica', '', 9)
        self.set_y(y)
        self.cell(90, 6, sol_baslik, align='C')
        self.cell(90, 6, sag_baslik, align='C')
        self.ln(20)
        self.cell(90, 6, '_' * 30, align='C')
        self.cell(90, 6, '_' * 30, align='C')
        self.ln(6)
        self.cell(90, 6, 'Ad Soyad / Imza', align='C')
        self.cell(90, 6, 'Ad Soyad / Imza', align='C')


# ── Yer Gösterme Belgesi ──────────────────────────────────
def yer_gosterme_pdf(emlakci, musteri, mulk, tarih=None):
    """Yer gösterme tutanağı PDF oluştur → bytes döndür."""
    pdf = TurkPDF()
    tarih = tarih or datetime.now()

    # Başlık
    pdf.baslik('YER GOSTERME TUTANAGI')
    pdf.set_font('Helvetica', '', 9)
    pdf.cell(0, 6, f'Tarih: {tarih.strftime("%d.%m.%Y")} - Saat: {tarih.strftime("%H:%M")}', ln=True, align='C')
    pdf.cell(0, 6, f'Belge No: YG-{tarih.strftime("%Y%m%d%H%M")}', ln=True, align='C')
    pdf.ln(8)

    # Emlakçı bilgileri
    pdf.alt_baslik('EMLAK DANISMANI BILGILERI')
    pdf.satir('Ad Soyad', emlakci.ad_soyad)
    pdf.satir('Acente', emlakci.acente_adi or '-')
    pdf.satir('Yetki No', emlakci.yetki_no or '-')
    pdf.satir('Telefon', emlakci.telefon)
    pdf.bos_satir()

    # Müşteri bilgileri
    pdf.alt_baslik('MUSTERI BILGILERI')
    if musteri:
        pdf.satir('Ad Soyad', musteri.ad_soyad)
        pdf.satir('Telefon', musteri.telefon or '-')
        pdf.satir('TC Kimlik', musteri.tc_kimlik or '-')
        det = musteri.detaylar or {}
        if det.get('adres'):
            pdf.satir('Adres', det['adres'])
    else:
        pdf.satir('Ad Soyad', '-')
    pdf.bos_satir()

    # Mülk bilgileri
    pdf.alt_baslik('GOSTERILEN MULK BILGILERI')
    if mulk:
        pdf.satir('Baslik', mulk.baslik or '-')
        pdf.satir('Adres', mulk.adres or '-')
        pdf.satir('Sehir / Ilce', f'{mulk.sehir or "-"} / {mulk.ilce or "-"}')
        pdf.satir('Tip', mulk.tip or '-')
        pdf.satir('Islem Turu', 'Kiralik' if mulk.islem_turu == 'kira' else 'Satilik')
        if mulk.fiyat:
            pdf.satir('Fiyat', f'{int(mulk.fiyat):,} TL'.replace(',', '.'))
        pdf.satir('Oda Sayisi', mulk.oda_sayisi or '-')
        pdf.satir('Ada / Parsel', f'{mulk.ada or "-"} / {mulk.parsel or "-"}')
        det = mulk.detaylar or {}
        if det.get('brut_m2'):
            pdf.satir('Brut m2', det['brut_m2'])
        if det.get('net_m2'):
            pdf.satir('Net m2', det['net_m2'])
        if det.get('bulundugu_kat'):
            pdf.satir('Kat', det['bulundugu_kat'])
    pdf.bos_satir()

    # Yasal uyarı
    pdf.alt_baslik('YASAL UYARI')
    pdf.set_font('Helvetica', '', 8)
    pdf.multi_cell(0, 5,
        'Yukaridaki mulk, emlak danismani tarafindan musteriye gosterilmistir. '
        'Musteri, bu mulku baska bir emlak danismani araciligiyla veya dogrudan '
        'mulk sahibinden satin almasi/kiralaması durumunda, yukaridaki emlak '
        'danismaninin hizmet bedelini odemeyi kabul ve taahhut eder. '
        'Bu belge 6098 sayili Turk Borclar Kanunu ve ilgili mevzuat '
        'cercevesinde duzenlenmistir.'
    )
    pdf.bos_satir()

    # İmza alanları
    pdf.imza_alani('Emlak Danismani', 'Musteri')

    # Alt bilgi
    pdf.set_font('Helvetica', 'I', 7)
    pdf.set_y(-15)
    pdf.cell(0, 5, f'Emlakisim AI - {tarih.strftime("%d.%m.%Y %H:%M")}', align='C')

    return pdf.output()


# ── Yönlendirme Belgesi ───────────────────────────────────
def yonlendirme_belgesi_pdf(emlakci, musteri, mulk, taraf='alici'):
    """Alıcı veya satıcı yönlendirme belgesi PDF."""
    pdf = TurkPDF()
    tarih = datetime.now()

    taraf_baslik = 'ALICI YONLENDIRME BELGESI' if taraf == 'alici' else 'SATICI YONLENDIRME BELGESI'
    pdf.baslik(taraf_baslik)
    pdf.set_font('Helvetica', '', 9)
    pdf.cell(0, 6, f'Tarih: {tarih.strftime("%d.%m.%Y")}', ln=True, align='C')
    pdf.ln(8)

    pdf.alt_baslik('EMLAK DANISMANI')
    pdf.satir('Ad Soyad', emlakci.ad_soyad)
    pdf.satir('Acente', emlakci.acente_adi or '-')
    pdf.satir('Telefon', emlakci.telefon)
    pdf.bos_satir()

    taraf_label = 'ALICI' if taraf == 'alici' else 'SATICI'
    pdf.alt_baslik(f'{taraf_label} BILGILERI')
    if musteri:
        pdf.satir('Ad Soyad', musteri.ad_soyad)
        pdf.satir('TC Kimlik', musteri.tc_kimlik or '-')
    pdf.bos_satir()

    if mulk:
        pdf.alt_baslik('TASINMAZ')
        pdf.satir('Baslik', mulk.baslik or '-')
        pdf.satir('Adres', mulk.adres or '-')
        if mulk.fiyat:
            pdf.satir('Fiyat', f'{int(mulk.fiyat):,} TL'.replace(',', '.'))
        pdf.bos_satir()

    pdf.alt_baslik('SARTLAR')
    pdf.set_font('Helvetica', '', 8)
    pdf.multi_cell(0, 5,
        f'{taraf_label}, belirtilen tasinmaz icin emlak danismani {emlakci.ad_soyad} '
        f'tarafindan yonlendirilmistir. Islemin baska bir aracı ile gerceklesmesi '
        f'durumunda komisyon bedeli odenecektir.')
    pdf.bos_satir()

    pdf.imza_alani('Emlak Danismani', taraf_label)
    return pdf.output()


# ── Kira Kontratı ─────────────────────────────────────────
def kira_kontrati_pdf(emlakci, kiraci, mulk, detaylar=None):
    """Basit kira sözleşmesi PDF → bytes."""
    pdf = TurkPDF()
    det = detaylar or {}
    tarih = datetime.now()

    pdf.baslik('KIRA SOZLESMESI')
    pdf.set_font('Helvetica', '', 9)
    pdf.cell(0, 6, f'Sozlesme Tarihi: {tarih.strftime("%d.%m.%Y")}', ln=True, align='C')
    pdf.ln(8)

    # Taraflar
    pdf.alt_baslik('TARAFLAR')
    pdf.satir('Kiraya Veren (Mal Sahibi)', det.get('mal_sahibi', '-'))
    pdf.satir('Kiraci', kiraci.ad_soyad if kiraci else '-')
    pdf.satir('TC Kimlik', kiraci.tc_kimlik if kiraci else '-')
    pdf.satir('Emlak Danismani', emlakci.ad_soyad)
    pdf.bos_satir()

    # Kiralanan
    pdf.alt_baslik('KIRALANAN TASINMAZ')
    if mulk:
        pdf.satir('Adres', mulk.adres or '-')
        pdf.satir('Tip', mulk.tip or '-')
        pdf.satir('Oda Sayisi', mulk.oda_sayisi or '-')
        pdf.satir('Ada / Parsel', f'{mulk.ada or "-"} / {mulk.parsel or "-"}')
    pdf.bos_satir()

    # Kira şartları
    pdf.alt_baslik('KIRA SARTLARI')
    pdf.satir('Aylik Kira', det.get('aylik_kira', '-'))
    pdf.satir('Depozito', det.get('depozito', '-'))
    pdf.satir('Odeme Gunu', det.get('odeme_gunu', '-'))
    pdf.satir('Baslangic Tarihi', det.get('baslangic', '-'))
    pdf.satir('Bitis Tarihi', det.get('bitis', '-'))
    pdf.satir('Artis Orani', det.get('artis_orani', 'TUFE'))
    pdf.bos_satir()

    # İmzalar
    pdf.imza_alani('Kiraya Veren', 'Kiraci')

    pdf.set_font('Helvetica', 'I', 7)
    pdf.set_y(-15)
    pdf.cell(0, 5, f'Emlakisim AI - {tarih.strftime("%d.%m.%Y %H:%M")}', align='C')

    return pdf.output()
