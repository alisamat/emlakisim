"""
AKILLI ÖNERİ MOTORU — Kimsenin düşünmediği proaktif öneriler
Emlakçının verilerini analiz edip stratejik öneriler sunar.
"""
import logging
from datetime import datetime, timedelta
from app.models import db, Musteri, Mulk
from app.models.muhasebe import GelirGider
from app.models.lead import Lead
from app.models.planlama import Gorev

logger = logging.getLogger(__name__)


def stratejik_oneriler(emlakci_id):
    """Emlakçıya özel stratejik öneriler üret."""
    oneriler = []

    # 1. Portföy-talep dengesizliği
    musteriler = Musteri.query.filter_by(emlakci_id=emlakci_id).all()
    mulkler = Mulk.query.filter_by(emlakci_id=emlakci_id, aktif=True).all()

    kira_musteri = sum(1 for m in musteriler if m.islem_turu == 'kira')
    satis_musteri = sum(1 for m in musteriler if m.islem_turu == 'satis')
    kira_mulk = sum(1 for m in mulkler if m.islem_turu == 'kira')
    satis_mulk = sum(1 for m in mulkler if m.islem_turu == 'satis')

    if kira_musteri > kira_mulk * 2 and kira_mulk > 0:
        oneriler.append({
            'tip': 'portfoy_dengesi',
            'oncelik': 'yuksek',
            'baslik': '🏢 Kiralık portföy yetersiz',
            'mesaj': f'{kira_musteri} kiralık arayan müşteri var ama sadece {kira_mulk} kiralık mülk. Portföyü genişletin.',
        })

    if satis_musteri > satis_mulk * 2 and satis_mulk > 0:
        oneriler.append({
            'tip': 'portfoy_dengesi',
            'oncelik': 'yuksek',
            'baslik': '🏢 Satılık portföy yetersiz',
            'mesaj': f'{satis_musteri} satılık arayan ama sadece {satis_mulk} satılık mülk.',
        })

    # 2. Fiyat uyumsuzluğu
    for m in musteriler[:20]:
        if m.butce_max:
            uygun = [p for p in mulkler if p.islem_turu == m.islem_turu and p.fiyat and p.fiyat <= m.butce_max]
            if not uygun and m.sicaklik == 'sicak':
                oneriler.append({
                    'tip': 'fiyat_uyumsuzluk',
                    'oncelik': 'orta',
                    'baslik': f'💰 {m.ad_soyad} için uygun fiyat yok',
                    'mesaj': f'Bütçe: max {int(m.butce_max):,} TL ama portföyde uygun mülk yok.'.replace(',', '.'),
                })

    # 3. Bölge boşluğu
    musteri_ilceler = set()
    for m in musteriler:
        det = m.detaylar or {}
        ilce = det.get('tercih_ilce', '')
        if ilce:
            musteri_ilceler.add(ilce.lower())

    mulk_ilceler = set(m.ilce.lower() for m in mulkler if m.ilce)
    eksik_bolgeler = musteri_ilceler - mulk_ilceler
    if eksik_bolgeler:
        oneriler.append({
            'tip': 'bolge_boslugu',
            'oncelik': 'orta',
            'baslik': f'📍 {len(eksik_bolgeler)} bölgede portföy yok',
            'mesaj': f'Müşteriler istiyor ama portföyde yok: {", ".join(list(eksik_bolgeler)[:3])}',
        })

    # 4. Gelir trendi
    bu_ay = datetime.utcnow().replace(day=1)
    gecen_ay = (bu_ay - timedelta(days=1)).replace(day=1)

    bu_ay_gelir = sum(k.tutar for k in GelirGider.query.filter(
        GelirGider.emlakci_id == emlakci_id, GelirGider.tip == 'gelir', GelirGider.tarih >= bu_ay).all())
    gecen_ay_gelir = sum(k.tutar for k in GelirGider.query.filter(
        GelirGider.emlakci_id == emlakci_id, GelirGider.tip == 'gelir',
        GelirGider.tarih >= gecen_ay, GelirGider.tarih < bu_ay).all())

    if gecen_ay_gelir > 0 and bu_ay_gelir < gecen_ay_gelir * 0.5:
        oneriler.append({
            'tip': 'gelir_dusus',
            'oncelik': 'yuksek',
            'baslik': '📉 Gelir düşüşü',
            'mesaj': f'Bu ay gelir geçen ayın %{int(bu_ay_gelir/gecen_ay_gelir*100)} seviyesinde. Aksiyon gerekli.',
        })

    # 5. Kaçırılan fırsatlar — lead dönüşüm
    toplam_lead = Lead.query.filter_by(emlakci_id=emlakci_id).count()
    musteri_olan = Lead.query.filter_by(emlakci_id=emlakci_id, durum='musteri_oldu').count()
    if toplam_lead > 5 and musteri_olan / toplam_lead < 0.2:
        oneriler.append({
            'tip': 'lead_donusum',
            'oncelik': 'orta',
            'baslik': f'🎯 Lead dönüşüm oranı düşük (%{int(musteri_olan/toplam_lead*100)})',
            'mesaj': f'{toplam_lead} lead\'den sadece {musteri_olan} müşteri oldu. İlk saat kuralına dikkat.',
        })

    # 6. Tamamlanmamış görevler
    gecmis_gorevler = Gorev.query.filter(
        Gorev.emlakci_id == emlakci_id, Gorev.durum == 'bekliyor',
        Gorev.baslangic < datetime.utcnow() - timedelta(days=2)
    ).count()
    if gecmis_gorevler > 3:
        oneriler.append({
            'tip': 'geciken_gorev',
            'oncelik': 'orta',
            'baslik': f'📌 {gecmis_gorevler} geciken görev var',
            'mesaj': 'Zamanı geçmiş görevleri tamamlayın veya iptal edin.',
        })

    return oneriler[:8]
