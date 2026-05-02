"""
OTONOM AGENT — WhatsApp proaktif davranışlar
Otomatik hatırlatma, yeni ilan bildirimi, takip mesajları.
"""
import logging
from datetime import datetime, timedelta
from app import db
from app.models import Emlakci, Musteri, Mulk
from app.services import whatsapp as wa

logger = logging.getLogger(__name__)


def takip_hatirlatma():
    """2+ gün dönüş yapılmayan müşterileri emlakçıya hatırlat."""
    import os
    pid = os.environ.get('WA_PHONE_NUMBER_ID', '')
    tok = os.environ.get('WA_ACCESS_TOKEN', '')
    if not pid or not tok:
        return

    sinir = datetime.utcnow() - timedelta(days=2)
    emlakcilar = Emlakci.query.filter_by(aktif=True).all()

    for emlakci in emlakcilar:
        try:
            from app.models.iletisim_gecmisi import IletisimKayit
            # Son 2 günde iletişim kurulmayan sıcak müşteriler
            sicak = Musteri.query.filter_by(emlakci_id=emlakci.id, sicaklik='sicak').all()
            hatirlatilacak = []
            for m in sicak:
                son_iletisim = IletisimKayit.query.filter_by(
                    emlakci_id=emlakci.id, musteri_id=m.id
                ).order_by(IletisimKayit.olusturma.desc()).first()
                if not son_iletisim or son_iletisim.olusturma < sinir:
                    hatirlatilacak.append(m)

            if hatirlatilacak and emlakci.telefon:
                isimler = ', '.join([m.ad_soyad for m in hatirlatilacak[:5]])
                mesaj = (f'⏰ *Takip Hatırlatması*\n\n'
                         f'{len(hatirlatilacak)} sıcak müşterinize 2+ gündür dönüş yapılmadı:\n'
                         f'{isimler}\n\n'
                         f'_Emlakisim AI Asistanı_')
                telefon = emlakci.telefon.replace('+', '').replace(' ', '')
                if telefon.startswith('0'):
                    telefon = '90' + telefon[1:]
                wa.mesaj_gonder(pid, tok, telefon, mesaj)

                # Bildirim de oluştur
                from app.routes.bildirim import bildirim_olustur
                bildirim_olustur(emlakci.id, 'hatirlatma',
                    f'⏰ {len(hatirlatilacak)} müşteriye dönüş yapılmadı',
                    isimler, link='musteriler')
        except Exception as e:
            logger.error(f'[OtonomAgent] Takip hatırlatma hatası: {e}')


def yeni_eslesme_bildirimi():
    """Yeni eklenen mülkler için uygun müşterilere bildirim."""
    sinir = datetime.utcnow() - timedelta(hours=24)
    yeni_mulkler = Mulk.query.filter(
        Mulk.aktif == True,
        Mulk.olusturma >= sinir,
    ).all()

    if not yeni_mulkler:
        return

    for mulk in yeni_mulkler:
        try:
            # Bu mülke uygun müşterileri bul
            uygun = Musteri.query.filter_by(
                emlakci_id=mulk.emlakci_id,
                islem_turu=mulk.islem_turu,
            ).all()
            for musteri in uygun:
                if musteri.butce_max and mulk.fiyat and mulk.fiyat <= musteri.butce_max:
                    # Bildirim oluştur
                    from app.routes.bildirim import bildirim_olustur
                    bildirim_olustur(mulk.emlakci_id, 'eslesme',
                        f'🔗 {musteri.ad_soyad} için uygun mülk: {mulk.baslik or mulk.adres}',
                        f'Fiyat: {int(mulk.fiyat):,} TL'.replace(',', '.'),
                        link='eslestirme')
        except Exception as e:
            logger.error(f'[OtonomAgent] Eşleşme bildirimi hatası: {e}')


def gunluk_ozet():
    """Her gün saat 09:00'da emlakçıya günlük özet gönder."""
    import os
    pid = os.environ.get('WA_PHONE_NUMBER_ID', '')
    tok = os.environ.get('WA_ACCESS_TOKEN', '')

    emlakcilar = Emlakci.query.filter_by(aktif=True).all()
    for emlakci in emlakcilar:
        try:
            if not emlakci.telefon:
                continue

            m_sayi = Musteri.query.filter_by(emlakci_id=emlakci.id).count()
            p_sayi = Mulk.query.filter_by(emlakci_id=emlakci.id, aktif=True).count()

            # Bugünkü görevler
            from app.models.planlama import Gorev
            bugun = datetime.utcnow().replace(hour=0, minute=0, second=0)
            yarin = bugun + timedelta(days=1)
            gorevler = Gorev.query.filter(
                Gorev.emlakci_id == emlakci.id,
                Gorev.baslangic >= bugun,
                Gorev.baslangic < yarin,
                Gorev.durum != 'iptal'
            ).all()

            # Yeni leadler
            from app.models.lead import Lead
            yeni_lead = Lead.query.filter_by(emlakci_id=emlakci.id, durum='yeni').count()

            mesaj = (f'☀️ *Günaydın {emlakci.ad_soyad.split(" ")[0]}!*\n\n'
                     f'👥 {m_sayi} müşteri · 🏢 {p_sayi} mülk\n'
                     f'📅 Bugün {len(gorevler)} görev\n')

            if yeni_lead:
                mesaj += f'🎯 {yeni_lead} yeni lead — dönüş yapılmadı!\n'

            if gorevler:
                mesaj += '\n*Görevler:*\n'
                for g in gorevler[:5]:
                    saat = g.baslangic.strftime('%H:%M') if g.baslangic else ''
                    mesaj += f'  • {g.baslik} {saat}\n'

            mesaj += '\n_Emlakisim AI Asistanı_'

            if pid and tok:
                telefon = emlakci.telefon.replace('+', '').replace(' ', '')
                if telefon.startswith('0'):
                    telefon = '90' + telefon[1:]
                wa.mesaj_gonder(pid, tok, telefon, mesaj)
        except Exception as e:
            logger.error(f'[OtonomAgent] Günlük özet hatası: {e}')
