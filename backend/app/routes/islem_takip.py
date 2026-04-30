"""
İŞLEM TAKİP — Tapu/kredi süreç takibi + Evrak arşivi API
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models.islem_takip import SurecTakip, Evrak
from datetime import datetime

bp = Blueprint('islem_takip', __name__, url_prefix='/api/panel')


def _eid():
    return int(get_jwt_identity())


# ── Süreç Takip ──────────────────────────────────────────
@bp.route('/surec', methods=['GET'])
@jwt_required()
def surec_listesi():
    kayitlar = SurecTakip.query.filter_by(emlakci_id=_eid()).order_by(SurecTakip.guncelleme.desc()).all()
    return jsonify({'surecler': [_s(s) for s in kayitlar]})


@bp.route('/surec', methods=['POST'])
@jwt_required()
def surec_ekle():
    d = request.get_json() or {}
    # Tapu devri için hazır adım şablonu
    adimlar = d.get('adimlar', [])
    if not adimlar and d.get('tip') == 'tapu_devri':
        adimlar = [
            {'ad': 'Sözleşme imzalama', 'durum': 'bekliyor'},
            {'ad': 'Kapora/kaparo alımı', 'durum': 'bekliyor'},
            {'ad': 'DASK poliçesi', 'durum': 'bekliyor'},
            {'ad': 'Ekspertiz raporu', 'durum': 'bekliyor'},
            {'ad': 'Kredi onayı', 'durum': 'bekliyor'},
            {'ad': 'Tapu randevusu', 'durum': 'bekliyor'},
            {'ad': 'Tapu devri', 'durum': 'bekliyor'},
            {'ad': 'Anahtar teslimi', 'durum': 'bekliyor'},
        ]
    elif not adimlar and d.get('tip') == 'kredi':
        adimlar = [
            {'ad': 'Kredi başvurusu', 'durum': 'bekliyor'},
            {'ad': 'Gelir belgeleri', 'durum': 'bekliyor'},
            {'ad': 'Ekspertiz', 'durum': 'bekliyor'},
            {'ad': 'Kredi onayı', 'durum': 'bekliyor'},
            {'ad': 'Sözleşme imzası', 'durum': 'bekliyor'},
        ]

    s = SurecTakip(
        emlakci_id=_eid(), tip=d.get('tip', 'tapu_devri'),
        baslik=d.get('baslik', ''), musteri_id=d.get('musteri_id'),
        mulk_id=d.get('mulk_id'), adimlar=adimlar, detaylar=d.get('detaylar', {}),
    )
    db.session.add(s); db.session.commit()
    return jsonify({'surec': _s(s)}), 201


@bp.route('/surec/<int:sid>', methods=['PUT'])
@jwt_required()
def surec_guncelle(sid):
    s = SurecTakip.query.filter_by(id=sid, emlakci_id=_eid()).first_or_404()
    d = request.get_json() or {}
    if 'durum' in d: s.durum = d['durum']
    if 'adimlar' in d: s.adimlar = d['adimlar']
    if 'baslik' in d: s.baslik = d['baslik']
    db.session.commit()
    return jsonify({'surec': _s(s)})


# ── Evrak Arşivi ─────────────────────────────────────────
@bp.route('/evrak', methods=['GET'])
@jwt_required()
def evrak_listesi():
    tip = request.args.get('tip')
    q = Evrak.query.filter_by(emlakci_id=_eid())
    if tip: q = q.filter_by(tip=tip)
    kayitlar = q.order_by(Evrak.olusturma.desc()).all()
    return jsonify({'evraklar': [_e(e) for e in kayitlar]})


@bp.route('/evrak', methods=['POST'])
@jwt_required()
def evrak_ekle():
    d = request.get_json() or {}
    e = Evrak(
        emlakci_id=_eid(), baslik=d.get('baslik', ''),
        tip=d.get('tip', 'diger'), etiketler=d.get('etiketler', ''),
        notlar=d.get('notlar', ''), musteri_id=d.get('musteri_id'),
        mulk_id=d.get('mulk_id'), detaylar=d.get('detaylar', {}),
    )
    db.session.add(e); db.session.commit()
    return jsonify({'evrak': _e(e)}), 201


@bp.route('/evrak/<int:eid_param>', methods=['DELETE'])
@jwt_required()
def evrak_sil(eid_param):
    e = Evrak.query.filter_by(id=eid_param, emlakci_id=_eid()).first_or_404()
    db.session.delete(e); db.session.commit()
    return jsonify({'ok': True})


def _s(s):
    return {
        'id': s.id, 'tip': s.tip, 'baslik': s.baslik, 'durum': s.durum,
        'adimlar': s.adimlar or [], 'detaylar': s.detaylar or {},
        'musteri_id': s.musteri_id, 'mulk_id': s.mulk_id,
        'olusturma': s.olusturma.isoformat() if s.olusturma else None,
    }

def _e(e):
    return {
        'id': e.id, 'baslik': e.baslik, 'tip': e.tip,
        'etiketler': e.etiketler, 'notlar': e.notlar,
        'musteri_id': e.musteri_id, 'mulk_id': e.mulk_id,
        'olusturma': e.olusturma.isoformat() if e.olusturma else None,
    }
