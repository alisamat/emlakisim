"""
PUBLIC — Herkese açık emlakçı portföy sayfası API
Giriş gerektirmez. /api/public/... endpoint'leri.
"""
from flask import Blueprint, request, jsonify
from app.models import Emlakci, Mulk

bp = Blueprint('public', __name__, url_prefix='/api/public')


def _public_profil(e):
    """Görünürlük ayarlarına göre filtrelenmiş profil bilgileri."""
    g = e.profil_gorunum or {}
    # Varsayılan: ad, acente, telefon her zaman gösterilir
    profil = {
        'id': e.id,
        'ad_soyad': e.ad_soyad,
        'acente_adi': e.acente_adi,
        'telefon': e.telefon,
        'slug': e.slug,
    }
    # Opsiyonel alanlar — varsayılan göster, kullanıcı kapatabilir
    if g.get('unvan', True) and e.unvan:
        profil['unvan'] = e.unvan
    if g.get('slogan', True) and e.slogan:
        profil['slogan'] = e.slogan
    if g.get('logo', True) and e.logo_url:
        profil['logo_url'] = e.logo_url
    if g.get('email', False) and e.email:  # email varsayılan gizli
        profil['email'] = e.email
    if g.get('telefon2', True) and e.telefon2:
        profil['telefon2'] = e.telefon2
    if g.get('adres', True) and e.adres:
        profil['adres'] = e.adres
    if g.get('website', True) and e.website:
        profil['website'] = e.website
    if g.get('sosyal_medya', True) and e.sosyal_medya:
        profil['sosyal_medya'] = e.sosyal_medya
    if g.get('yetki_no', True) and e.yetki_no:
        profil['yetki_no'] = e.yetki_no
    if g.get('ruhsat_no', True) and e.ruhsat_no:
        profil['ruhsat_no'] = e.ruhsat_no
    if g.get('vergi_no', False) and e.vergi_no:  # vergi no varsayılan gizli
        profil['vergi_no'] = e.vergi_no
    return profil


def _emlakci_bul(eid):
    """ID veya slug ile emlakçı bul."""
    try:
        return Emlakci.query.filter_by(id=int(eid), aktif=True).first()
    except (ValueError, TypeError):
        return Emlakci.query.filter_by(slug=eid, aktif=True).first()


@bp.route('/emlakci/<eid>', methods=['GET'])
def emlakci_profil(eid):
    """Emlakçının herkese açık profil bilgileri."""
    e = _emlakci_bul(eid)
    if not e:
        return jsonify({'message': 'Emlakçı bulunamadı'}), 404

    return jsonify({'emlakci': _public_profil(e)})


@bp.route('/emlakci/<eid>/portfoy', methods=['GET'])
def emlakci_portfoy(eid):
    """Emlakçının herkese açık portföyü — sadece aktif mülkler."""
    e = _emlakci_bul(eid)
    if not e:
        return jsonify({'message': 'Emlakçı bulunamadı'}), 404

    # Filtreler
    islem = request.args.get('islem')  # kira / satis
    tip = request.args.get('tip')      # daire / villa / ...
    fiyat_min = request.args.get('fiyat_min', type=float)
    fiyat_max = request.args.get('fiyat_max', type=float)
    oda = request.args.get('oda')

    sorgu = Mulk.query.filter_by(emlakci_id=e.id, aktif=True)
    if islem:
        sorgu = sorgu.filter(Mulk.islem_turu == islem)
    if tip:
        sorgu = sorgu.filter(Mulk.tip == tip)
    if fiyat_min:
        sorgu = sorgu.filter(Mulk.fiyat >= fiyat_min)
    if fiyat_max:
        sorgu = sorgu.filter(Mulk.fiyat <= fiyat_max)
    if oda:
        sorgu = sorgu.filter(Mulk.oda_sayisi == oda)

    mulkler = sorgu.order_by(Mulk.olusturma.desc()).all()

    return jsonify({
        'emlakci': _public_profil(e),
        'mulkler': [{
            'id': m.id,
            'baslik': m.baslik,
            'adres': m.adres,
            'sehir': m.sehir,
            'ilce': m.ilce,
            'tip': m.tip,
            'islem_turu': m.islem_turu,
            'fiyat': m.fiyat,
            'metrekare': m.metrekare,
            'oda_sayisi': m.oda_sayisi,
            'detaylar': m.detaylar or {},
            'resimler': m.resimler or [],
            'olusturma': m.olusturma.isoformat() if m.olusturma else None,
        } for m in mulkler],
        'toplam': len(mulkler),
    })


@bp.route('/mulk/<int:mid>', methods=['GET'])
def mulk_detay(mid):
    """Tek mülkün herkese açık detayı."""
    m = Mulk.query.filter_by(id=mid, aktif=True).first()
    if not m:
        return jsonify({'message': 'Mülk bulunamadı'}), 404

    e = Emlakci.query.get(m.emlakci_id)
    det = m.detaylar or {}

    return jsonify({
        'mulk': {
            'id': m.id, 'baslik': m.baslik, 'adres': m.adres,
            'sehir': m.sehir, 'ilce': m.ilce, 'tip': m.tip,
            'islem_turu': m.islem_turu, 'fiyat': m.fiyat,
            'metrekare': m.metrekare, 'oda_sayisi': m.oda_sayisi,
            'detaylar': det, 'resimler': m.resimler or [],
            'olusturma': m.olusturma.isoformat() if m.olusturma else None,
        },
        'emlakci': {
            'ad_soyad': e.ad_soyad if e else '',
            'telefon': e.telefon if e else '',
            'acente_adi': e.acente_adi if e else '',
        },
    })
