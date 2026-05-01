"""
SÜREÇ BİLDİRİM — Müşteriye otomatik süreç güncellemesi
Adım tamamlandığında email/bildirim gönderir.
"""
import logging
from datetime import datetime
from app.models import db, Musteri, Emlakci
from app.models.islem_takip import SurecTakip
from app.services.iletisim import email_gonder
from app.routes.bildirim import bildirim_olustur

logger = logging.getLogger(__name__)

ADIM_MESAJLARI = {
    'Sözleşme imzalama': '📋 Satış sözleşmesi imzalandı. Sıradaki adım: kapora/kaparo.',
    'Kapora/kaparo alımı': '💰 Kapora alındı. Sıradaki: DASK poliçesi.',
    'DASK poliçesi': '🏗 DASK poliçesi hazırlandı. Sıradaki: ekspertiz raporu.',
    'Ekspertiz raporu': '📊 Ekspertiz tamamlandı. Sıradaki: kredi onayı.',
    'Kredi onayı': '🏦 Kredi onaylandı! Sıradaki: tapu randevusu.',
    'Tapu randevusu': '📅 Tapu randevusu alındı. Sıradaki: tapu devri.',
    'Tapu devri': '🎉 Tapu devri tamamlandı! Sıradaki: anahtar teslimi.',
    'Anahtar teslimi': '🔑 Anahtar teslimi yapıldı! Süreç başarıyla tamamlandı.',
    'Kredi başvurusu': '📝 Kredi başvurusu yapıldı. Sıradaki: gelir belgeleri.',
    'Gelir belgeleri': '📄 Gelir belgeleri teslim edildi. Sıradaki: ekspertiz.',
    'Ekspertiz': '📊 Ekspertiz tamamlandı. Sıradaki: kredi onayı.',
    'Sözleşme imzası': '✍️ Sözleşme imzalandı. Süreç tamamlanıyor.',
}


def adim_tamamlandi_bildir(surec_id, adim_index, emlakci_id):
    """Süreç adımı tamamlandığında müşteriye bildir."""
    surec = SurecTakip.query.filter_by(id=surec_id, emlakci_id=emlakci_id).first()
    if not surec or not surec.adimlar:
        return

    adimlar = surec.adimlar
    if adim_index >= len(adimlar):
        return

    adim = adimlar[adim_index]
    adim_adi = adim.get('ad', '')

    # Emlakçıya bildirim
    bildirim_olustur(emlakci_id, 'surec',
        f'✅ {surec.baslik}: {adim_adi} tamamlandı',
        link='surec')

    # Müşteriye email (varsa)
    if surec.musteri_id:
        musteri = Musteri.query.get(surec.musteri_id)
        emlakci = Emlakci.query.get(emlakci_id)
        if musteri and emlakci:
            det = musteri.detaylar or {}
            musteri_email = det.get('email', '')

            mesaj = ADIM_MESAJLARI.get(adim_adi, f'✅ {adim_adi} tamamlandı.')

            # Kalan adımlar
            tamamlanan = sum(1 for a in adimlar if a.get('durum') == 'tamamlandi')
            toplam = len(adimlar)
            ilerleme = f'{tamamlanan}/{toplam}'

            if musteri_email:
                html = f'''
                <div style="font-family:sans-serif;max-width:500px;margin:0 auto">
                    <div style="background:#16a34a;color:#fff;padding:16px 24px;border-radius:8px 8px 0 0">
                        <strong>📋 Süreç Güncelleme — {surec.baslik}</strong>
                    </div>
                    <div style="padding:24px;background:#fff;border:1px solid #e2e8f0;border-radius:0 0 8px 8px">
                        <p>Sayın {musteri.ad_soyad},</p>
                        <p style="font-size:16px;font-weight:700;color:#16a34a">{mesaj}</p>
                        <div style="background:#f0fdf4;border-radius:8px;padding:12px;margin:16px 0">
                            <div style="font-size:13px;color:#64748b">İlerleme: {ilerleme}</div>
                            <div style="height:8px;background:#e2e8f0;border-radius:4px;margin-top:6px;overflow:hidden">
                                <div style="height:100%;background:#16a34a;width:{int(tamamlanan/toplam*100)}%;border-radius:4px"></div>
                            </div>
                        </div>
                        <hr style="border:none;border-top:1px solid #e2e8f0;margin:16px 0">
                        <p style="font-size:12px;color:#94a3b8">{emlakci.ad_soyad} · {emlakci.acente_adi or ""} · {emlakci.telefon}</p>
                    </div>
                </div>'''
                try:
                    email_gonder(musteri_email, f'Süreç Güncelleme: {surec.baslik}', html, gonderen_ad=emlakci.ad_soyad)
                    logger.info(f'[Süreç] Email gönderildi: {musteri_email}')
                except Exception as e:
                    logger.error(f'[Süreç] Email hatası: {e}')


def surec_ozet_rapor(emlakci_id):
    """Aktif süreçlerin özet raporu."""
    surecler = SurecTakip.query.filter(
        SurecTakip.emlakci_id == emlakci_id,
        SurecTakip.durum != 'tamamlandi'
    ).all()

    rapor = []
    for s in surecler:
        adimlar = s.adimlar or []
        tamamlanan = sum(1 for a in adimlar if a.get('durum') == 'tamamlandi')
        toplam = len(adimlar)

        # Kaç gündür güncellenmedi
        gun = (datetime.utcnow() - s.guncelleme).days if s.guncelleme else 0

        rapor.append({
            'id': s.id,
            'baslik': s.baslik,
            'tip': s.tip,
            'ilerleme': f'{tamamlanan}/{toplam}',
            'yuzde': round(tamamlanan / toplam * 100) if toplam else 0,
            'gun_gecti': gun,
            'uyari': gun > 5,
        })

    return rapor
