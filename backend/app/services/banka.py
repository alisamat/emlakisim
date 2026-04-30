"""
BANKA — Excel hesap özetinden masraf çıkarma
"""
import io
import logging
from datetime import datetime
from app.models import db
from app.models.muhasebe import GelirGider

logger = logging.getLogger(__name__)

# Kategori tahmin: açıklamadaki anahtar kelimelere göre
_KATEGORI_MAP = {
    'kira': 'Ofis Kirası', 'elektrik': 'Fatura', 'su': 'Fatura', 'dogalgaz': 'Fatura',
    'doğalgaz': 'Fatura', 'internet': 'Fatura', 'telefon': 'Fatura',
    'benzin': 'Ulaşım', 'akaryakit': 'Ulaşım', 'otopark': 'Ulaşım', 'taksi': 'Ulaşım',
    'yemek': 'Yemek', 'restoran': 'Yemek', 'kafe': 'Yemek', 'market': 'Yemek',
    'reklam': 'Reklam', 'ilan': 'Reklam', 'google': 'Reklam', 'facebook': 'Reklam',
    'maas': 'Personel', 'maaş': 'Personel', 'sgk': 'Personel',
    'vergi': 'Vergi', 'kdv': 'Vergi', 'stopaj': 'Vergi',
    'noter': 'Diğer Gider', 'tapu': 'Diğer Gider',
}


def _kategori_tahmin(aciklama):
    if not aciklama:
        return 'Diğer Gider'
    aciklama_lower = aciklama.lower()
    for anahtar, kategori in _KATEGORI_MAP.items():
        if anahtar in aciklama_lower:
            return kategori
    return 'Diğer Gider'


def banka_excel_import(emlakci_id, dosya_bytes):
    """Banka hesap özeti Excel'den masrafları çıkar ve gider olarak kaydet."""
    try:
        import openpyxl
        wb = openpyxl.load_workbook(io.BytesIO(dosya_bytes))
        ws = wb.active
    except Exception as e:
        return {'hata': f'Excel okunamadı: {e}', 'eklenen': 0}

    rows = list(ws.iter_rows(min_row=2, values_only=True))
    eklenen = 0
    atlanan = 0
    kayitlar = []

    for row in rows:
        if not row or len(row) < 3:
            continue

        # Tipik banka Excel: Tarih | Açıklama | Tutar (veya Borç/Alacak)
        tarih_raw = row[0]
        aciklama = str(row[1]).strip() if row[1] else ''
        tutar = None

        # Tutar bul (negatif = gider, pozitif = gelir)
        for col_idx in range(2, min(len(row), 6)):
            val = row[col_idx]
            if val and isinstance(val, (int, float)) and val != 0:
                tutar = float(val)
                break
            if val and isinstance(val, str):
                try:
                    tutar = float(val.replace('.', '').replace(',', '.').replace('TL', '').strip())
                    break
                except:
                    continue

        if tutar is None or tutar == 0:
            atlanan += 1
            continue

        # Tarih parse
        tarih = None
        if isinstance(tarih_raw, datetime):
            tarih = tarih_raw
        elif tarih_raw:
            for fmt in ['%d.%m.%Y', '%Y-%m-%d', '%d/%m/%Y']:
                try:
                    tarih = datetime.strptime(str(tarih_raw).strip(), fmt)
                    break
                except:
                    continue

        tip = 'gider' if tutar < 0 else 'gelir'
        abs_tutar = abs(tutar)
        kategori = _kategori_tahmin(aciklama)

        k = GelirGider(
            emlakci_id=emlakci_id,
            tip=tip,
            kategori=kategori,
            tutar=abs_tutar,
            aciklama=aciklama[:200],
            tarih=tarih,
            detaylar={'kaynak': 'banka_excel'},
        )
        db.session.add(k)
        eklenen += 1
        kayitlar.append({
            'aciklama': aciklama[:50],
            'tutar': abs_tutar,
            'tip': tip,
            'kategori': kategori,
        })

    db.session.commit()
    return {'eklenen': eklenen, 'atlanan': atlanan, 'toplam_satir': len(rows), 'kayitlar': kayitlar[:20]}
