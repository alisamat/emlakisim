"""
BROŞÜR — Mülk tanıtım broşürü PDF
"""
from datetime import datetime
from app.services.belge import TurkPDF


def brosur_pdf(emlakci, mulk):
    """Tek mülk için tanıtım broşürü PDF."""
    pdf = TurkPDF()
    det = mulk.detaylar or {}
    fiyat = f'{int(mulk.fiyat):,}'.replace(',', '.') + ' TL' if mulk.fiyat else ''

    # Başlık
    pdf.set_font('Helvetica', 'B', 20)
    pdf.cell(0, 14, mulk.baslik or mulk.adres or 'Emlak Ilani', ln=True, align='C')
    pdf.set_font('Helvetica', '', 12)
    pdf.cell(0, 8, 'Kiralik' if mulk.islem_turu == 'kira' else 'Satilik', ln=True, align='C')
    if fiyat:
        pdf.set_font('Helvetica', 'B', 18)
        pdf.set_text_color(22, 163, 74)
        pdf.cell(0, 12, fiyat, ln=True, align='C')
        pdf.set_text_color(0, 0, 0)
    pdf.ln(8)

    # Konum
    if mulk.adres:
        pdf.alt_baslik('KONUM')
        pdf.set_font('Helvetica', '', 11)
        pdf.cell(0, 7, f'{mulk.adres}', ln=True)
        if mulk.sehir or mulk.ilce:
            pdf.cell(0, 7, f'{mulk.ilce or ""}, {mulk.sehir or ""}', ln=True)
        pdf.bos_satir()

    # Temel bilgiler
    pdf.alt_baslik('OZELLIKLER')
    if mulk.tip: pdf.satir('Tip', mulk.tip.capitalize())
    if mulk.oda_sayisi: pdf.satir('Oda Sayisi', mulk.oda_sayisi)
    if det.get('brut_m2'): pdf.satir('Brut m2', det['brut_m2'])
    if det.get('net_m2'): pdf.satir('Net m2', det['net_m2'])
    if mulk.metrekare: pdf.satir('m2', str(mulk.metrekare))
    if det.get('bina_yasi'): pdf.satir('Bina Yasi', det['bina_yasi'])
    if det.get('bulundugu_kat'): pdf.satir('Kat', det['bulundugu_kat'])
    if det.get('kat_sayisi'): pdf.satir('Kat Sayisi', det['kat_sayisi'])
    if det.get('isinma'): pdf.satir('Isinma', det['isinma'])
    if det.get('banyo_sayisi'): pdf.satir('Banyo', det['banyo_sayisi'])
    pdf.bos_satir()

    # Ek özellikler
    ozellikler = []
    if det.get('balkon') == 'Var': ozellikler.append('Balkon')
    if det.get('asansor') == 'Var': ozellikler.append('Asansor')
    if det.get('otopark') and det['otopark'] != 'Yok': ozellikler.append(f'Otopark ({det["otopark"]})')
    if det.get('esyali') == 'Evet': ozellikler.append('Esyali')
    if det.get('site_icerisinde') == 'Evet': ozellikler.append('Site Ici')
    if det.get('havuz') == 'Var': ozellikler.append('Havuz')
    if det.get('bahce') == 'Var': ozellikler.append('Bahce')
    if det.get('krediye_uygun') == 'Evet': ozellikler.append('Krediye Uygun')

    if ozellikler:
        pdf.alt_baslik('EK OZELLIKLER')
        pdf.set_font('Helvetica', '', 10)
        pdf.multi_cell(0, 6, ' • '.join(ozellikler))
        pdf.bos_satir()

    # Notlar
    if mulk.notlar:
        pdf.alt_baslik('ACIKLAMA')
        pdf.set_font('Helvetica', '', 10)
        pdf.multi_cell(0, 6, mulk.notlar[:500])
        pdf.bos_satir()

    # İletişim
    pdf.alt_baslik('ILETISIM')
    pdf.satir('Danisnan', emlakci.ad_soyad)
    pdf.satir('Acente', emlakci.acente_adi or '-')
    pdf.satir('Telefon', emlakci.telefon)
    if emlakci.yetki_no:
        pdf.satir('Yetki No', emlakci.yetki_no)

    pdf.set_font('Helvetica', 'I', 7)
    pdf.set_y(-15)
    pdf.cell(0, 5, f'Emlakisim AI - {datetime.now().strftime("%d.%m.%Y")}', align='C')

    return pdf.output()
