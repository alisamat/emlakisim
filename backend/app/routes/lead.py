"""
LEAD & ÇAĞRI — Lead takibi ve çağrı yönetimi API
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models.lead import Lead, CagriKayit
from datetime import datetime

bp = Blueprint('lead', __name__, url_prefix='/api/panel/lead')


def _eid():
    return int(get_jwt_identity())


# ── Lead ─────────────────────────────────────────────────
@bp.route('/listele', methods=['GET'])
@jwt_required()
def lead_listesi():
    durum = request.args.get('durum')
    q = Lead.query.filter_by(emlakci_id=_eid())
    if durum:
        q = q.filter_by(durum=durum)
    kayitlar = q.order_by(Lead.olusturma.desc()).limit(100).all()
    return jsonify({'leadler': [_l(l) for l in kayitlar]})


@bp.route('/ekle', methods=['POST'])
@jwt_required()
def lead_ekle():
    d = request.get_json() or {}
    l = Lead(
        emlakci_id=_eid(),
        ad_soyad=d.get('ad_soyad', ''),
        telefon=d.get('telefon'),
        email=d.get('email'),
        kaynak=d.get('kaynak', 'web'),
        ilk_mesaj=d.get('ilk_mesaj'),
        detaylar=d.get('detaylar', {}),
    )
    db.session.add(l); db.session.commit()
    return jsonify({'lead': _l(l)}), 201


@bp.route('/<int:lid>', methods=['PUT'])
@jwt_required()
def lead_guncelle(lid):
    l = Lead.query.filter_by(id=lid, emlakci_id=_eid()).first_or_404()
    d = request.get_json() or {}
    for f in ['ad_soyad', 'telefon', 'email', 'kaynak', 'sicaklik', 'durum']:
        if f in d:
            setattr(l, f, d[f])
    if 'detaylar' in d:
        l.detaylar = d['detaylar']
    l.son_iletisim = datetime.utcnow()
    db.session.commit()
    return jsonify({'lead': _l(l)})


@bp.route('/<int:lid>', methods=['DELETE'])
@jwt_required()
def lead_sil(lid):
    l = Lead.query.filter_by(id=lid, emlakci_id=_eid()).first_or_404()
    db.session.delete(l); db.session.commit()
    return jsonify({'ok': True})


@bp.route('/istatistik', methods=['GET'])
@jwt_required()
def lead_istatistik():
    eid = _eid()
    toplam = Lead.query.filter_by(emlakci_id=eid).count()
    yeni = Lead.query.filter_by(emlakci_id=eid, durum='yeni').count()
    iletisimde = Lead.query.filter_by(emlakci_id=eid, durum='iletisimde').count()
    musteri = Lead.query.filter_by(emlakci_id=eid, durum='musteri_oldu').count()
    return jsonify({'toplam': toplam, 'yeni': yeni, 'iletisimde': iletisimde, 'musteri_oldu': musteri})


# ── Çağrı ────────────────────────────────────────────────
@bp.route('/cagri', methods=['GET'])
@jwt_required()
def cagri_listesi():
    kayitlar = CagriKayit.query.filter_by(emlakci_id=_eid()).order_by(CagriKayit.olusturma.desc()).limit(50).all()
    return jsonify({'cagrilar': [_c(c) for c in kayitlar]})


@bp.route('/cagri', methods=['POST'])
@jwt_required()
def cagri_ekle():
    d = request.get_json() or {}
    c = CagriKayit(
        emlakci_id=_eid(),
        telefon=d.get('telefon'),
        yon=d.get('yon', 'gelen'),
        sure_sn=d.get('sure_sn'),
        notlar=d.get('notlar'),
        musteri_id=d.get('musteri_id'),
        lead_id=d.get('lead_id'),
    )
    db.session.add(c); db.session.commit()
    return jsonify({'cagri': _c(c)}), 201


def _l(l):
    return {
        'id': l.id, 'ad_soyad': l.ad_soyad, 'telefon': l.telefon,
        'email': l.email, 'kaynak': l.kaynak, 'sicaklik': l.sicaklik,
        'durum': l.durum, 'ilk_mesaj': l.ilk_mesaj,
        'son_iletisim': l.son_iletisim.isoformat() if l.son_iletisim else None,
        'detaylar': l.detaylar or {},
        'olusturma': l.olusturma.isoformat() if l.olusturma else None,
    }

def _c(c):
    return {
        'id': c.id, 'telefon': c.telefon, 'yon': c.yon,
        'sure_sn': c.sure_sn, 'notlar': c.notlar,
        'olusturma': c.olusturma.isoformat() if c.olusturma else None,
    }
