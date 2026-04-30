"""
HAFIZA KATMANI — Kısa / Orta / Uzun dönem hafıza
Gerçek asistan gibi: unutmaz, bağlam korur, öğrenir.

Kısa dönem: Aktif sohbet (son 20 mesaj) — zaten var
Orta dönem: Günlük özet, son işlemler, aktif görevler
Uzun dönem: Müşteri bazlı tercihler, kararlar, önemli notlar, alışkanlıklar
"""
import logging
from datetime import datetime, timedelta
from app.models import db, Musteri, Mulk, Not, YerGosterme
from app.models.muhasebe import GelirGider
from app.models.planlama import Gorev
from app.models.lead import Lead

logger = logging.getLogger(__name__)


class HafizaMotoru:
    """Her mesajda AI'ya verilecek bağlam bilgisini oluşturur."""

    def __init__(self, emlakci):
        self.emlakci = emlakci
        self.id = emlakci.id

    def baglamOlustur(self, metin=''):
        """Mesaj bağlamına göre ilgili veriyi topla → sistem prompt'a ekle."""
        parcalar = []

        # 1. Emlakçı profili
        parcalar.append(self._profil())

        # 2. Güncel durum özeti
        parcalar.append(self._guncel_durum())

        # 3. Bugünkü görevler
        parcalar.append(self._bugunun_gorevleri())

        # 4. Bekleyen hatırlatmalar
        parcalar.append(self._hatirlatmalar())

        # 5. Son işlemler (neyi yaptı en son)
        parcalar.append(self._son_islemler())

        # 6. Mesajda geçen müşteri/mülk varsa detayını getir
        if metin:
            parcalar.append(self._ilgili_veri(metin))

        # 7. Uzun dönem alışkanlıklar
        parcalar.append(self._aliskanliklar())

        return '\n'.join([p for p in parcalar if p])

    def _profil(self):
        e = self.emlakci
        return (f'[PROFIL] {e.ad_soyad}, {e.acente_adi or "Bağımsız"}, '
                f'Tel: {e.telefon}, Kredi: {e.kredi}')

    def _guncel_durum(self):
        m = Musteri.query.filter_by(emlakci_id=self.id).count()
        p = Mulk.query.filter_by(emlakci_id=self.id, aktif=True).count()
        l = Lead.query.filter_by(emlakci_id=self.id, durum='yeni').count()
        return f'[DURUM] {m} müşteri, {p} mülk, {l} yeni lead'

    def _bugunun_gorevleri(self):
        bugun = datetime.utcnow().replace(hour=0, minute=0, second=0)
        yarin = bugun + timedelta(days=1)
        gorevler = Gorev.query.filter(
            Gorev.emlakci_id == self.id,
            Gorev.baslangic >= bugun, Gorev.baslangic < yarin,
            Gorev.durum != 'iptal'
        ).all()
        if not gorevler:
            return ''
        satirlar = [f'  - {g.baslik} ({g.baslangic.strftime("%H:%M") if g.baslangic else ""})' for g in gorevler]
        return f'[BUGÜN] {len(gorevler)} görev:\n' + '\n'.join(satirlar)

    def _hatirlatmalar(self):
        notlar = Not.query.filter_by(
            emlakci_id=self.id, etiket='hatirlatici', tamamlandi=False
        ).order_by(Not.olusturma.desc()).limit(5).all()
        if not notlar:
            return ''
        satirlar = [f'  - {n.icerik[:60]}' for n in notlar]
        return f'[HATIRLATMALAR] {len(notlar)} aktif:\n' + '\n'.join(satirlar)

    def _son_islemler(self):
        """Son 24 saatteki önemli işlemler."""
        from app.models import IslemLog
        son24 = datetime.utcnow() - timedelta(hours=24)
        islemler = IslemLog.query.filter(
            IslemLog.emlakci_id == self.id,
            IslemLog.olusturma >= son24
        ).order_by(IslemLog.olusturma.desc()).limit(5).all()
        if not islemler:
            return ''
        satirlar = [f'  - {i.islem_tipi}: {i.aciklama or ""}' for i in islemler]
        return f'[SON İŞLEMLER]\n' + '\n'.join(satirlar)

    def _ilgili_veri(self, metin):
        """Mesajda geçen müşteri veya mülk adı varsa detay getir."""
        metin_lower = metin.lower()
        parcalar = []

        # Müşteri adı ara
        musteriler = Musteri.query.filter_by(emlakci_id=self.id).all()
        for m in musteriler:
            if m.ad_soyad and m.ad_soyad.lower() in metin_lower:
                det = m.detaylar or {}
                parcalar.append(
                    f'[MÜŞTERİ: {m.ad_soyad}] Tel: {m.telefon or "-"}, '
                    f'İşlem: {m.islem_turu or "-"}, Sıcaklık: {m.sicaklik or "-"}, '
                    f'Bütçe: {m.butce_min or "?"}-{m.butce_max or "?"} TL, '
                    f'Tercih: {m.tercih_notlar or "-"}, '
                    f'Detay: {", ".join(f"{k}={v}" for k,v in det.items() if v) or "-"}'
                )
                break  # İlk eşleşme yeter

        # Mülk başlığı/adresi ara
        mulkler = Mulk.query.filter_by(emlakci_id=self.id, aktif=True).all()
        for p in mulkler:
            baslik = (p.baslik or '').lower()
            adres = (p.adres or '').lower()
            if (baslik and baslik in metin_lower) or (adres and len(adres) > 5 and adres in metin_lower):
                det = p.detaylar or {}
                fiyat = f'{int(p.fiyat):,}'.replace(',', '.') if p.fiyat else '?'
                parcalar.append(
                    f'[MÜLK: {p.baslik or p.adres}] {p.sehir or ""} {p.ilce or ""}, '
                    f'{p.tip or ""}, {"Kiralık" if p.islem_turu == "kira" else "Satılık"}, '
                    f'Fiyat: {fiyat} TL, Oda: {p.oda_sayisi or "-"}, '
                    f'Detay: {", ".join(f"{k}={v}" for k,v in det.items() if v)[:100] or "-"}'
                )
                break

        return '\n'.join(parcalar)

    def _aliskanliklar(self):
        """Uzun dönem: emlakçının çalışma alışkanlıkları."""
        from app.models.egitim import DiyalogKayit
        # En çok kullanılan komutlar
        try:
            from sqlalchemy import func
            en_cok = db.session.query(
                DiyalogKayit.islem, func.count(DiyalogKayit.id)
            ).filter_by(emlakci_id=self.id).group_by(DiyalogKayit.islem)\
             .order_by(func.count(DiyalogKayit.id).desc()).limit(3).all()
            if en_cok:
                satirlar = ', '.join([f'{islem}({sayi})' for islem, sayi in en_cok])
                return f'[ALIŞKANLIKLAR] En çok: {satirlar}'
        except:
            pass
        return ''


def baglam_olustur(emlakci, metin=''):
    """Kısayol: hafıza motorundan bağlam al."""
    motor = HafizaMotoru(emlakci)
    return motor.baglamOlustur(metin)
