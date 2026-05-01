"""
AYARLAR — Kullanıcı AI ayarları + Admin sistem parametreleri
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models.ayarlar import KullaniciAyar, SistemParametre

bp = Blueprint('ayarlar_api', __name__, url_prefix='/api/panel')

# Varsayılan kullanıcı ayarları
VARSAYILAN_AYARLAR = {
    'islem_onay': False,           # Her DB işleminde onay iste
    'ai_tonu': 'samimi',           # resmi / samimi / kisa
    'otomatik_eslestirme': True,   # Müşteri/mülk ekleyince otomatik eşleştir
    'proaktif_oneriler': True,     # Proaktif öneriler göster
    'bildirim_lead': True,         # Lead bildirimleri
    'bildirim_gorev': True,        # Görev hatırlatmaları
    'bildirim_yedek': True,        # Yedek uyarıları
    'bildirim_kredi': True,        # Kredi düşük uyarısı
    'varsayilan_islem': 'kira',    # kiralık / satılık
    'varsayilan_sehir': '',        # Varsayılan şehir
    'varsayilan_ilce': '',         # Varsayılan ilçe
    'mesai_disi_mesaj': '',        # Özel mesai dışı mesajı
    'tema': 'acik',                # acik / karanlik
}


@bp.route('/ayarlar', methods=['GET'])
@jwt_required()
def ayar_getir():
    eid = int(get_jwt_identity())
    kayit = KullaniciAyar.query.filter_by(emlakci_id=eid).first()
    ayarlar = {**VARSAYILAN_AYARLAR, **(kayit.ayarlar if kayit else {})}
    return jsonify({'ayarlar': ayarlar})


@bp.route('/ayarlar', methods=['PUT'])
@jwt_required()
def ayar_guncelle():
    eid = int(get_jwt_identity())
    d = request.get_json() or {}
    kayit = KullaniciAyar.query.filter_by(emlakci_id=eid).first()
    if not kayit:
        kayit = KullaniciAyar(emlakci_id=eid, ayarlar={})
        db.session.add(kayit)
    mevcut = kayit.ayarlar or {}
    mevcut.update(d.get('ayarlar', {}))
    kayit.ayarlar = mevcut
    db.session.commit()
    return jsonify({'ok': True, 'ayarlar': {**VARSAYILAN_AYARLAR, **mevcut}})


# ── Admin Sistem Parametreleri ───────────────────────────
VARSAYILAN_PARAMETRELER = [
    {'anahtar': 'vergi_istisna_2026', 'deger': '33000', 'aciklama': 'Kira geliri vergi istisnası (TL)', 'kategori': 'vergi'},
    {'anahtar': 'vergi_dilim_1', 'deger': '110000:0.15', 'aciklama': 'Gelir vergisi 1. dilim (sınır:oran)', 'kategori': 'vergi'},
    {'anahtar': 'vergi_dilim_2', 'deger': '230000:0.20', 'aciklama': 'Gelir vergisi 2. dilim', 'kategori': 'vergi'},
    {'anahtar': 'vergi_dilim_3', 'deger': '580000:0.27', 'aciklama': 'Gelir vergisi 3. dilim', 'kategori': 'vergi'},
    {'anahtar': 'vergi_dilim_4', 'deger': '3000000:0.35', 'aciklama': 'Gelir vergisi 4. dilim', 'kategori': 'vergi'},
    {'anahtar': 'tapu_harci_oran', 'deger': '0.04', 'aciklama': 'Tapu harcı oranı (toplam %4)', 'kategori': 'vergi'},
    {'anahtar': 'kdv_oran', 'deger': '20', 'aciklama': 'KDV oranı (%)', 'kategori': 'vergi'},
    {'anahtar': 'deger_artis_istisna', 'deger': '87000', 'aciklama': 'Değer artış kazancı istisnası (TL)', 'kategori': 'hesaplama'},
    {'anahtar': 'komisyon_oran_satis', 'deger': '0.02', 'aciklama': 'Satış komisyon oranı', 'kategori': 'hesaplama'},
    {'anahtar': 'komisyon_oran_kira', 'deger': '1', 'aciklama': 'Kira komisyonu (aylık kira)', 'kategori': 'hesaplama'},
    {'anahtar': 'usd_try_kur', 'deger': '37.65', 'aciklama': 'USD/TRY kuru', 'kategori': 'sistem'},
    {'anahtar': 'kredi_kar_marji', 'deger': '3.0', 'aciklama': 'AI maliyeti × kar marjı = kredi', 'kategori': 'sistem'},
]


@bp.route('/admin/parametreler', methods=['GET'])
@jwt_required()
def parametreler_getir():
    kayitlar = SistemParametre.query.order_by(SistemParametre.kategori, SistemParametre.anahtar).all()
    if not kayitlar:
        # İlk çalışmada varsayılanları ekle
        for p in VARSAYILAN_PARAMETRELER:
            db.session.add(SistemParametre(**p))
        db.session.commit()
        kayitlar = SistemParametre.query.order_by(SistemParametre.kategori, SistemParametre.anahtar).all()

    return jsonify({'parametreler': [{
        'id': p.id, 'anahtar': p.anahtar, 'deger': p.deger,
        'aciklama': p.aciklama, 'kategori': p.kategori,
    } for p in kayitlar]})


@bp.route('/admin/parametreler/<int:pid>', methods=['PUT'])
@jwt_required()
def parametre_guncelle(pid):
    p = SistemParametre.query.get_or_404(pid)
    d = request.get_json() or {}
    if 'deger' in d:
        p.deger = str(d['deger'])
    db.session.commit()
    return jsonify({'ok': True})


def parametre_al(anahtar, varsayilan=None):
    """Sistem parametresini oku (servislerden çağrılır)."""
    p = SistemParametre.query.filter_by(anahtar=anahtar).first()
    return p.deger if p else varsayilan
