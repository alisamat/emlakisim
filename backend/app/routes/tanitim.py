"""
TANITIM — Emlakçı public tanıtım sayfası + portföy paylaşım linkleri
"""
from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models import Emlakci, Mulk

bp = Blueprint('tanitim', __name__, url_prefix='/api')


# ── Public (auth gerekmez) ────────────────────────────────
@bp.route('/e/<int:eid>', methods=['GET'])
def emlakci_tanitim(eid):
    """Public emlakçı tanıtım sayfası verisi."""
    e = Emlakci.query.filter_by(id=eid, aktif=True).first()
    if not e:
        return jsonify({'message': 'Bulunamadı'}), 404
    mulkler = Mulk.query.filter_by(emlakci_id=eid, aktif=True).order_by(Mulk.olusturma.desc()).limit(20).all()
    return jsonify({
        'emlakci': {
            'ad_soyad': e.ad_soyad,
            'acente_adi': e.acente_adi,
            'telefon': e.telefon,
            'yetki_no': e.yetki_no,
        },
        'mulkler': [{
            'id': m.id, 'baslik': m.baslik, 'adres': m.adres,
            'sehir': m.sehir, 'ilce': m.ilce, 'tip': m.tip,
            'islem_turu': m.islem_turu, 'fiyat': m.fiyat,
            'oda_sayisi': m.oda_sayisi, 'detaylar': m.detaylar or {},
        } for m in mulkler],
    })


@bp.route('/e/<int:eid>/mulk/<int:mid>', methods=['GET'])
def mulk_detay_public(eid, mid):
    """Public tek mülk detayı."""
    m = Mulk.query.filter_by(id=mid, emlakci_id=eid, aktif=True).first()
    if not m:
        return jsonify({'message': 'Bulunamadı'}), 404
    e = Emlakci.query.get(eid)
    return jsonify({
        'mulk': {
            'id': m.id, 'baslik': m.baslik, 'adres': m.adres,
            'sehir': m.sehir, 'ilce': m.ilce, 'tip': m.tip,
            'islem_turu': m.islem_turu, 'fiyat': m.fiyat,
            'metrekare': m.metrekare, 'oda_sayisi': m.oda_sayisi,
            'ada': m.ada, 'parsel': m.parsel, 'notlar': m.notlar,
            'detaylar': m.detaylar or {},
        },
        'emlakci': {
            'ad_soyad': e.ad_soyad if e else '',
            'acente_adi': e.acente_adi if e else '',
            'telefon': e.telefon if e else '',
        },
    })


# ── Paylaşım linki oluşturma (auth gerekli) ──────────────
@bp.route('/panel/paylasim/portfoy', methods=['GET'])
@jwt_required()
def paylasim_link():
    """Emlakçının portföy paylaşım linkini döndür."""
    eid = int(get_jwt_identity())
    return jsonify({
        'tanitim_url': f'/e/{eid}',
        'portfoy_url': f'/e/{eid}',
    })
