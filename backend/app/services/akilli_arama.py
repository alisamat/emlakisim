"""
AKILLI ARAMA — Tüm verilerde arama (müşteri + mülk + not + görev + fatura)
Tek bir sorgu ile her yerde arar.
"""
from app.models import db, Musteri, Mulk, Not
from app.models.planlama import Gorev
from app.models.fatura import Fatura
from app.models.lead import Lead


def genel_arama(emlakci_id, sorgu, limit=20):
    """Tüm verilerde arama — tek sorgu, tüm sonuçlar."""
    if not sorgu or len(sorgu) < 2:
        return {'sonuclar': []}

    q = f'%{sorgu}%'
    sonuclar = []

    # Müşteriler
    musteriler = Musteri.query.filter(
        Musteri.emlakci_id == emlakci_id,
        db.or_(Musteri.ad_soyad.ilike(q), Musteri.telefon.ilike(q), Musteri.tercih_notlar.ilike(q))
    ).limit(5).all()
    for m in musteriler:
        sonuclar.append({
            'tip': 'musteri', 'ikon': '👥', 'baslik': m.ad_soyad,
            'detay': f'{m.telefon or ""} · {m.islem_turu or ""}',
            'id': m.id, 'tab': 'musteriler',
        })

    # Mülkler
    mulkler = Mulk.query.filter(
        Mulk.emlakci_id == emlakci_id, Mulk.aktif == True,
        db.or_(Mulk.baslik.ilike(q), Mulk.adres.ilike(q), Mulk.sehir.ilike(q), Mulk.ilce.ilike(q))
    ).limit(5).all()
    for m in mulkler:
        fiyat = f'{int(m.fiyat):,}'.replace(',', '.') + ' TL' if m.fiyat else ''
        sonuclar.append({
            'tip': 'mulk', 'ikon': '🏢', 'baslik': m.baslik or m.adres or '—',
            'detay': f'{fiyat} · {m.tip or ""}',
            'id': m.id, 'tab': 'mulkler',
        })

    # Görevler
    gorevler = Gorev.query.filter(
        Gorev.emlakci_id == emlakci_id,
        db.or_(Gorev.baslik.ilike(q), Gorev.aciklama.ilike(q))
    ).limit(3).all()
    for g in gorevler:
        sonuclar.append({
            'tip': 'gorev', 'ikon': '📌', 'baslik': g.baslik,
            'detay': g.durum, 'id': g.id, 'tab': 'planlama',
        })

    # Lead'ler
    leadler = Lead.query.filter(
        Lead.emlakci_id == emlakci_id,
        db.or_(Lead.ad_soyad.ilike(q), Lead.telefon.ilike(q))
    ).limit(3).all()
    for l in leadler:
        sonuclar.append({
            'tip': 'lead', 'ikon': '🎯', 'baslik': l.ad_soyad or '—',
            'detay': f'{l.kaynak or ""} · {l.durum}',
            'id': l.id, 'tab': 'leadler',
        })

    # Faturalar
    faturalar = Fatura.query.filter(
        Fatura.emlakci_id == emlakci_id,
        db.or_(Fatura.fatura_no.ilike(q), Fatura.alici_ad.ilike(q))
    ).limit(3).all()
    for f in faturalar:
        sonuclar.append({
            'tip': 'fatura', 'ikon': '🧾', 'baslik': f.fatura_no or '—',
            'detay': f'{f.alici_ad or ""} · {f.toplam} TL',
            'id': f.id, 'tab': 'faturalar',
        })

    return {'sonuclar': sonuclar[:limit], 'toplam': len(sonuclar)}
