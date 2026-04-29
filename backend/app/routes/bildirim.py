"""
BİLDİRİM — Uygulama içi bildirim API
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models.bildirim import Bildirim

bp = Blueprint('bildirim', __name__, url_prefix='/api/panel/bildirim')


@bp.route('/listele', methods=['GET'])
@jwt_required()
def listele():
    eid = int(get_jwt_identity())
    bildirimler = Bildirim.query.filter_by(emlakci_id=eid).order_by(Bildirim.olusturma.desc()).limit(50).all()
    okunmamis = Bildirim.query.filter_by(emlakci_id=eid, okundu=False).count()
    return jsonify({
        'bildirimler': [{
            'id': b.id, 'tip': b.tip, 'baslik': b.baslik,
            'icerik': b.icerik, 'okundu': b.okundu, 'link': b.link,
            'olusturma': b.olusturma.isoformat(),
        } for b in bildirimler],
        'okunmamis': okunmamis,
    })


@bp.route('/oku/<int:bid>', methods=['PUT'])
@jwt_required()
def oku(bid):
    b = Bildirim.query.filter_by(id=bid, emlakci_id=int(get_jwt_identity())).first_or_404()
    b.okundu = True
    db.session.commit()
    return jsonify({'ok': True})


@bp.route('/tumunu-oku', methods=['PUT'])
@jwt_required()
def tumunu_oku():
    Bildirim.query.filter_by(emlakci_id=int(get_jwt_identity()), okundu=False).update({'okundu': True})
    db.session.commit()
    return jsonify({'ok': True})


def bildirim_olustur(emlakci_id, tip, baslik, icerik='', link=None):
    """Helper: bildirim oluştur."""
    b = Bildirim(emlakci_id=emlakci_id, tip=tip, baslik=baslik, icerik=icerik, link=link)
    db.session.add(b)
    db.session.commit()
    return b
