"""
ZAMANLAYICI — Otomatik görevler (hatırlatma, günlük özet, yedek uyarısı, lead takip)
APScheduler ile — cron gerekmez.
"""
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)
_scheduler = None


def zamanlayici_baslat(app):
    """Flask app context'inde scheduler başlat."""
    global _scheduler
    try:
        from apscheduler.schedulers.background import BackgroundScheduler
        _scheduler = BackgroundScheduler()

        # Her saat — hatırlatma kontrolü
        _scheduler.add_job(lambda: _with_app(app, _hatirlatma_kontrol), 'interval', hours=1, id='hatirlatma')

        # Her gün 08:00 — günlük özet bildirimi
        _scheduler.add_job(lambda: _with_app(app, _gunluk_ozet), 'cron', hour=8, minute=0, id='gunluk_ozet')

        # Her hafta Pazartesi 09:00 — yedek hatırlatması
        _scheduler.add_job(lambda: _with_app(app, _yedek_hatirlat), 'cron', day_of_week='mon', hour=9, id='yedek')

        # Her 6 saat — soğuyan lead kontrolü
        _scheduler.add_job(lambda: _with_app(app, _lead_soguma_kontrol), 'interval', hours=6, id='lead_soguma')

        # Her gün 18:00 — kredi düşük uyarısı
        _scheduler.add_job(lambda: _with_app(app, _kredi_kontrol), 'cron', hour=18, id='kredi_uyari')

        # Her gün 03:00 — otomatik pattern öğrenme
        _scheduler.add_job(lambda: _with_app(app, _otomatik_ogren), 'cron', hour=3, id='ogren')

        _scheduler.start()
        logger.info('[Zamanlayıcı] Başlatıldı — 6 görev aktif')
    except ImportError:
        logger.warning('[Zamanlayıcı] apscheduler yüklü değil, atlanıyor')
    except Exception as e:
        logger.error(f'[Zamanlayıcı] Hata: {e}')


def _with_app(app, func):
    """Flask app context ile çalıştır."""
    with app.app_context():
        try:
            func()
        except Exception as e:
            logger.error(f'[Zamanlayıcı] Görev hatası: {e}')


def _hatirlatma_kontrol():
    """Zamanı gelen hatırlatmaları bildirime dönüştür."""
    from app.models import Emlakci, Not
    from app.models.planlama import Gorev
    from app.routes.bildirim import bildirim_olustur

    simdi = datetime.utcnow()

    # Görev hatırlatmaları — başlangıç zamanı geçmiş ama tamamlanmamış
    gorevler = Gorev.query.filter(
        Gorev.baslangic <= simdi,
        Gorev.baslangic >= simdi - timedelta(hours=1),
        Gorev.durum == 'bekliyor'
    ).all()

    for g in gorevler:
        bildirim_olustur(g.emlakci_id, 'hatirlatma', f'📌 Görev: {g.baslik}',
                        g.aciklama or '', link='planlama')
        g.durum = 'devam'

    from app.models import db
    db.session.commit()
    if gorevler:
        logger.info(f'[Zamanlayıcı] {len(gorevler)} görev hatırlatması gönderildi')


def _gunluk_ozet():
    """Her emlakçıya günlük özet bildirimi."""
    from app.models import Emlakci, Musteri, Mulk
    from app.models.lead import Lead
    from app.models.planlama import Gorev
    from app.routes.bildirim import bildirim_olustur

    bugun = datetime.utcnow().replace(hour=0, minute=0, second=0)
    yarin = bugun + timedelta(days=1)

    for e in Emlakci.query.filter_by(aktif=True).all():
        gorevler = Gorev.query.filter(
            Gorev.emlakci_id == e.id, Gorev.baslangic >= bugun,
            Gorev.baslangic < yarin, Gorev.durum != 'iptal'
        ).count()

        yeni_lead = Lead.query.filter(
            Lead.emlakci_id == e.id, Lead.durum == 'yeni'
        ).count()

        if gorevler > 0 or yeni_lead > 0:
            bildirim_olustur(e.id, 'sistem',
                f'☀️ Günaydın! Bugün {gorevler} görev, {yeni_lead} yeni lead',
                link='planlama')

    logger.info('[Zamanlayıcı] Günlük özetler gönderildi')


def _yedek_hatirlat():
    """Haftalık yedek hatırlatması."""
    from app.models import Emlakci
    from app.services.yedekleme import yedek_durumu
    from app.routes.bildirim import bildirim_olustur

    for e in Emlakci.query.filter_by(aktif=True).all():
        durum = yedek_durumu(e)
        if durum['uyari']:
            bildirim_olustur(e.id, 'yedek',
                f'💾 {durum["mesaj"]}',
                'Verilerinizi yedeklemenizi öneririz.', link='yedekleme')

    logger.info('[Zamanlayıcı] Yedek hatırlatmaları kontrol edildi')


def _lead_soguma_kontrol():
    """3+ gündür dönüş yapılmamış lead'lere uyarı."""
    from app.models.lead import Lead
    from app.routes.bildirim import bildirim_olustur

    sinir = datetime.utcnow() - timedelta(days=3)
    soguk_leadler = Lead.query.filter(
        Lead.durum == 'yeni',
        Lead.olusturma <= sinir
    ).all()

    for l in soguk_leadler:
        bildirim_olustur(l.emlakci_id, 'lead',
            f'⚠️ {l.ad_soyad} — {((datetime.utcnow() - l.olusturma).days)} gündür dönüş yok!',
            link='leadler')

    if soguk_leadler:
        logger.info(f'[Zamanlayıcı] {len(soguk_leadler)} soğuyan lead uyarısı')


def _kredi_kontrol():
    """Kredi düşük olan kullanıcılara uyarı."""
    from app.models import Emlakci
    from app.routes.bildirim import bildirim_olustur

    for e in Emlakci.query.filter(Emlakci.aktif == True, Emlakci.kredi < 3).all():
        bildirim_olustur(e.id, 'kredi',
            f'💎 Krediniz düşük: {e.kredi}',
            'AI asistan kullanmaya devam etmek için kredi ekleyin.')

    logger.info('[Zamanlayıcı] Kredi kontrolleri yapıldı')


def _otomatik_ogren():
    """Otomatik pattern öğrenme — 3+ kez tekrarlanan mesajlar."""
    from app.services.egitim import otomatik_ogren
    eklenen = otomatik_ogren()
    if eklenen:
        logger.info(f'[Zamanlayıcı] {eklenen} pattern otomatik öğrenildi')
