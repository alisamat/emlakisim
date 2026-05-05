"""
OFİS — Envanter + Geri bildirim + Broşür API
"""
from flask import Blueprint, request, jsonify, send_file
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models import Emlakci, Mulk
from app.models.ofis import Envanter, GeriBildirim
import io

bp = Blueprint('ofis', __name__, url_prefix='/api/panel/ofis')


def _eid():
    return int(get_jwt_identity())


# ── Envanter ─────────────────────────────────────────────
def _envanter_tablo_kontrol():
    """Envanter tablosu yoksa oluştur."""
    try:
        from sqlalchemy import inspect
        inspector = inspect(db.engine)
        if 'envanter' not in inspector.get_table_names():
            Envanter.__table__.create(db.engine)
    except Exception:
        pass

@bp.route('/envanter', methods=['GET'])
@jwt_required()
def envanter_listesi():
    try:
        kayitlar = Envanter.query.filter_by(emlakci_id=_eid()).order_by(Envanter.kategori, Envanter.ad).all()
    except Exception:
        _envanter_tablo_kontrol()
        kayitlar = Envanter.query.filter_by(emlakci_id=_eid()).order_by(Envanter.kategori, Envanter.ad).all()
    eksikler = [e for e in kayitlar if e.min_miktar and e.miktar <= e.min_miktar]
    return jsonify({
        'envanter': [{
            'id': e.id, 'ad': e.ad, 'kategori': e.kategori,
            'miktar': e.miktar, 'min_miktar': e.min_miktar,
            'birim': e.birim, 'notlar': e.notlar,
        } for e in kayitlar],
        'eksik_sayisi': len(eksikler),
    })


@bp.route('/envanter', methods=['POST'])
@jwt_required()
def envanter_ekle():
    _envanter_tablo_kontrol()
    d = request.get_json() or {}
    e = Envanter(
        emlakci_id=_eid(), ad=d.get('ad', ''), kategori=d.get('kategori'),
        miktar=int(d.get('miktar', 0)), min_miktar=int(d.get('min_miktar', 0)),
        birim=d.get('birim', 'adet'), notlar=d.get('notlar'),
    )
    db.session.add(e); db.session.commit()
    return jsonify({'ok': True}), 201


@bp.route('/envanter/<int:eid_p>', methods=['PUT'])
@jwt_required()
def envanter_guncelle(eid_p):
    e = Envanter.query.filter_by(id=eid_p, emlakci_id=_eid()).first_or_404()
    d = request.get_json() or {}
    for f in ['ad', 'kategori', 'miktar', 'min_miktar', 'birim', 'notlar']:
        if f in d: setattr(e, f, d[f])
    db.session.commit()
    return jsonify({'ok': True})


@bp.route('/envanter/<int:eid_p>', methods=['DELETE'])
@jwt_required()
def envanter_sil(eid_p):
    e = Envanter.query.filter_by(id=eid_p, emlakci_id=_eid()).first_or_404()
    db.session.delete(e); db.session.commit()
    return jsonify({'ok': True})


# ── Geri Bildirim ────────────────────────────────────────
@bp.route('/geri-bildirim', methods=['GET'])
@jwt_required()
def gb_listesi():
    kayitlar = GeriBildirim.query.filter_by(emlakci_id=_eid()).order_by(GeriBildirim.olusturma.desc()).limit(50).all()
    return jsonify({'geri_bildirimler': [{
        'id': g.id, 'puan': g.puan, 'yorum': g.yorum,
        'ilgi_durumu': g.ilgi_durumu, 'sonraki_adim': g.sonraki_adim,
        'musteri_id': g.musteri_id, 'mulk_id': g.mulk_id,
        'olusturma': g.olusturma.isoformat() if g.olusturma else None,
    } for g in kayitlar]})


@bp.route('/geri-bildirim', methods=['POST'])
@jwt_required()
def gb_ekle():
    d = request.get_json() or {}
    g = GeriBildirim(
        emlakci_id=_eid(), musteri_id=d.get('musteri_id'), mulk_id=d.get('mulk_id'),
        yer_gosterme_id=d.get('yer_gosterme_id'), puan=d.get('puan'),
        yorum=d.get('yorum'), ilgi_durumu=d.get('ilgi_durumu'),
        sonraki_adim=d.get('sonraki_adim'),
    )
    db.session.add(g); db.session.commit()
    return jsonify({'ok': True}), 201


# ── Broşür ───────────────────────────────────────────────
@bp.route('/brosur/<int:mulk_id>', methods=['GET'])
@jwt_required()
def brosur(mulk_id):
    mulk = Mulk.query.filter_by(id=mulk_id, emlakci_id=_eid()).first_or_404()
    emlakci = Emlakci.query.get(_eid())
    from app.services.brosur import brosur_pdf
    pdf_bytes = brosur_pdf(emlakci, mulk)
    return send_file(io.BytesIO(pdf_bytes), mimetype='application/pdf', as_attachment=True,
                     download_name=f'brosur_{mulk_id}.pdf')
