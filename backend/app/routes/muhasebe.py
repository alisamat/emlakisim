"""
MUHASEBE — Gelir/gider, cari hesap API'leri
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models.muhasebe import GelirGider, Cari, CariHareket
from datetime import datetime

bp = Blueprint('muhasebe', __name__, url_prefix='/api/panel/muhasebe')


def _eid():
    return int(get_jwt_identity())


# ── Gelir/Gider ──────────────────────────────────────────
@bp.route('/gelir-gider', methods=['GET'])
@jwt_required()
def gelir_gider_listesi():
    kayitlar = GelirGider.query.filter_by(emlakci_id=_eid()).order_by(GelirGider.tarih.desc()).limit(100).all()
    return jsonify({'kayitlar': [_gg(k) for k in kayitlar]})


@bp.route('/gelir-gider', methods=['POST'])
@jwt_required()
def gelir_gider_ekle():
    d = request.get_json() or {}
    k = GelirGider(
        emlakci_id=_eid(),
        tip=d.get('tip', 'gelir'),
        kategori=d.get('kategori'),
        tutar=float(d.get('tutar', 0)),
        aciklama=d.get('aciklama'),
        musteri_id=d.get('musteri_id'),
        mulk_id=d.get('mulk_id'),
        detaylar=d.get('detaylar', {}),
    )
    if d.get('tarih'):
        try: k.tarih = datetime.fromisoformat(d['tarih'])
        except: pass
    db.session.add(k); db.session.commit()
    return jsonify({'kayit': _gg(k)}), 201


@bp.route('/gelir-gider/<int:kid>', methods=['DELETE'])
@jwt_required()
def gelir_gider_sil(kid):
    k = GelirGider.query.filter_by(id=kid, emlakci_id=_eid()).first_or_404()
    db.session.delete(k); db.session.commit()
    return jsonify({'ok': True})


@bp.route('/ozet', methods=['GET'])
@jwt_required()
def ozet():
    kayitlar = GelirGider.query.filter_by(emlakci_id=_eid()).all()
    gelir = sum(k.tutar for k in kayitlar if k.tip == 'gelir')
    gider = sum(k.tutar for k in kayitlar if k.tip == 'gider')
    return jsonify({'gelir': gelir, 'gider': gider, 'net': gelir - gider, 'kayit_sayisi': len(kayitlar)})


# ── Cari ─────────────────────────────────────────────────
@bp.route('/cariler', methods=['GET'])
@jwt_required()
def cari_listesi():
    cariler = Cari.query.filter_by(emlakci_id=_eid()).order_by(Cari.olusturma.desc()).all()
    return jsonify({'cariler': [_cari(c) for c in cariler]})


@bp.route('/cariler', methods=['POST'])
@jwt_required()
def cari_ekle():
    d = request.get_json() or {}
    c = Cari(
        emlakci_id=_eid(),
        ad=d.get('ad', ''),
        tip=d.get('tip', 'musteri'),
        telefon=d.get('telefon'),
        detaylar=d.get('detaylar', {}),
    )
    db.session.add(c); db.session.commit()
    return jsonify({'cari': _cari(c)}), 201


@bp.route('/cariler/<int:cid>/hareket', methods=['POST'])
@jwt_required()
def cari_hareket_ekle(cid):
    c = Cari.query.filter_by(id=cid, emlakci_id=_eid()).first_or_404()
    d = request.get_json() or {}
    tutar = float(d.get('tutar', 0))
    tip = d.get('tip', 'borc')

    h = CariHareket(cari_id=cid, tip=tip, tutar=tutar, aciklama=d.get('aciklama'))
    if tip == 'alacak':
        c.bakiye += tutar
    else:
        c.bakiye -= tutar

    db.session.add(h); db.session.commit()
    return jsonify({'hareket': _ch(h), 'bakiye': c.bakiye}), 201


@bp.route('/cariler/<int:cid>', methods=['GET'])
@jwt_required()
def cari_detay(cid):
    c = Cari.query.filter_by(id=cid, emlakci_id=_eid()).first_or_404()
    hareketler = CariHareket.query.filter_by(cari_id=cid).order_by(CariHareket.tarih.desc()).all()
    return jsonify({'cari': _cari(c), 'hareketler': [_ch(h) for h in hareketler]})


# ── Serializers ──────────────────────────────────────────
def _gg(k):
    return {
        'id': k.id, 'tip': k.tip, 'kategori': k.kategori,
        'tutar': k.tutar, 'aciklama': k.aciklama,
        'tarih': k.tarih.isoformat() if k.tarih else None,
        'detaylar': k.detaylar or {},
    }

def _cari(c):
    return {
        'id': c.id, 'ad': c.ad, 'tip': c.tip,
        'telefon': c.telefon, 'bakiye': c.bakiye,
        'detaylar': c.detaylar or {},
    }

def _ch(h):
    return {
        'id': h.id, 'tip': h.tip, 'tutar': h.tutar,
        'aciklama': h.aciklama,
        'tarih': h.tarih.isoformat() if h.tarih else None,
    }
