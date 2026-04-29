"""
PANEL — Emlakçı dashboard API'leri
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models import Emlakci, Musteri, Mulk, YerGosterme, Not

bp = Blueprint('panel', __name__, url_prefix='/api/panel')


def _eid():
    return int(get_jwt_identity())


# ── Müşteriler ─────────────────────────────────────────────────────────────────
@bp.route('/musteriler', methods=['GET'])
@jwt_required()
def musteriler():
    q = Musteri.query.filter_by(emlakci_id=_eid())
    sicaklik = request.args.get('sicaklik')
    if sicaklik:
        q = q.filter_by(sicaklik=sicaklik)
    kayitlar = q.order_by(Musteri.guncelleme.desc()).all()
    return jsonify({'musteriler': [_m(m) for m in kayitlar]})


@bp.route('/musteriler', methods=['POST'])
@jwt_required()
def musteri_ekle():
    d = request.get_json() or {}
    _temel = ['ad_soyad', 'telefon', 'tc_kimlik', 'email', 'islem_turu', 'butce_min', 'butce_max', 'tercih_notlar', 'sicaklik']
    m = Musteri(emlakci_id=_eid(), **{k: d.get(k) for k in _temel if d.get(k) is not None})
    if d.get('detaylar'):
        m.detaylar = d['detaylar']
    db.session.add(m); db.session.commit()
    return jsonify({'musteri': _m(m)}), 201


@bp.route('/musteriler/<int:mid>', methods=['PUT'])
@jwt_required()
def musteri_guncelle(mid):
    m = Musteri.query.filter_by(id=mid, emlakci_id=_eid()).first_or_404()
    d = request.get_json() or {}
    for f in ['ad_soyad', 'telefon', 'islem_turu', 'butce_min', 'butce_max', 'tercih_notlar', 'sicaklik']:
        if f in d:
            setattr(m, f, d[f])
    if 'detaylar' in d:
        m.detaylar = d['detaylar']
    db.session.commit()
    return jsonify({'musteri': _m(m)})


@bp.route('/musteriler/<int:mid>', methods=['DELETE'])
@jwt_required()
def musteri_sil(mid):
    m = Musteri.query.filter_by(id=mid, emlakci_id=_eid()).first_or_404()
    db.session.delete(m); db.session.commit()
    return jsonify({'ok': True})


@bp.route('/musteriler/ara', methods=['GET'])
@jwt_required()
def musteri_ara():
    q = request.args.get('q', '').strip()
    if not q:
        return jsonify({'musteriler': []})
    kayitlar = Musteri.query.filter_by(emlakci_id=_eid()).filter(
        db.or_(
            Musteri.ad_soyad.ilike(f'%{q}%'),
            Musteri.telefon.ilike(f'%{q}%'),
            Musteri.tercih_notlar.ilike(f'%{q}%'),
        )
    ).order_by(Musteri.guncelleme.desc()).all()
    return jsonify({'musteriler': [_m(m) for m in kayitlar]})


# ── Mülkler ────────────────────────────────────────────────────────────────────
@bp.route('/mulkler', methods=['GET'])
@jwt_required()
def mulkler():
    kayitlar = Mulk.query.filter_by(emlakci_id=_eid(), aktif=True).order_by(Mulk.olusturma.desc()).all()
    return jsonify({'mulkler': [_mulk(m) for m in kayitlar]})


@bp.route('/mulkler', methods=['POST'])
@jwt_required()
def mulk_ekle():
    d = request.get_json() or {}
    _temel = ['baslik', 'adres', 'sehir', 'ilce', 'tip', 'islem_turu', 'fiyat', 'metrekare', 'oda_sayisi', 'ada', 'parsel', 'notlar']
    m = Mulk(emlakci_id=_eid(), **{k: d.get(k) for k in _temel if d.get(k) is not None})
    if d.get('detaylar'):
        m.detaylar = d['detaylar']
    db.session.add(m); db.session.commit()
    return jsonify({'mulk': _mulk(m)}), 201


@bp.route('/mulkler/<int:mid>', methods=['PUT'])
@jwt_required()
def mulk_guncelle(mid):
    m = Mulk.query.filter_by(id=mid, emlakci_id=_eid()).first_or_404()
    d = request.get_json() or {}
    for f in ['baslik', 'adres', 'sehir', 'ilce', 'tip', 'islem_turu', 'fiyat', 'metrekare', 'oda_sayisi', 'ada', 'parsel', 'notlar']:
        if f in d:
            setattr(m, f, d[f])
    if 'detaylar' in d:
        m.detaylar = d['detaylar']
    db.session.commit()
    return jsonify({'mulk': _mulk(m)})


@bp.route('/mulkler/<int:mid>', methods=['DELETE'])
@jwt_required()
def mulk_sil(mid):
    m = Mulk.query.filter_by(id=mid, emlakci_id=_eid()).first_or_404()
    m.aktif = False
    db.session.commit()
    return jsonify({'ok': True})


# ── Yer Göstermeler ────────────────────────────────────────────────────────────
@bp.route('/yer-gostermeler', methods=['GET'])
@jwt_required()
def yer_gostermeler():
    kayitlar = YerGosterme.query.filter_by(emlakci_id=_eid()).order_by(YerGosterme.tarih.desc()).limit(50).all()
    return jsonify({'kayitlar': [_yg(y) for y in kayitlar]})


# ── Notlar ─────────────────────────────────────────────────────────────────────
@bp.route('/notlar', methods=['GET'])
@jwt_required()
def notlar():
    kayitlar = Not.query.filter_by(emlakci_id=_eid(), tamamlandi=False).order_by(Not.olusturma.desc()).all()
    return jsonify({'notlar': [_not(n) for n in kayitlar]})


@bp.route('/notlar', methods=['POST'])
@jwt_required()
def not_ekle():
    d = request.get_json() or {}
    n = Not(emlakci_id=_eid(), icerik=d.get('icerik', ''), etiket=d.get('etiket', 'not'))
    db.session.add(n); db.session.commit()
    return jsonify({'not': _not(n)}), 201


# ── Serializer'lar ─────────────────────────────────────────────────────────────
def _m(m):
    return {
        'id': m.id, 'ad_soyad': m.ad_soyad, 'telefon': m.telefon,
        'islem_turu': m.islem_turu, 'butce_min': m.butce_min, 'butce_max': m.butce_max,
        'tercih_notlar': m.tercih_notlar, 'sicaklik': m.sicaklik,
        'detaylar': m.detaylar or {},
        'olusturma': m.olusturma.isoformat() if m.olusturma else None,
    }


def _mulk(m):
    return {
        'id': m.id, 'baslik': m.baslik, 'adres': m.adres, 'sehir': m.sehir,
        'ilce': m.ilce, 'tip': m.tip, 'islem_turu': m.islem_turu,
        'fiyat': m.fiyat, 'metrekare': m.metrekare, 'oda_sayisi': m.oda_sayisi,
        'ada': m.ada, 'parsel': m.parsel, 'notlar': m.notlar,
        'detaylar': m.detaylar or {},
        'olusturma': m.olusturma.isoformat() if m.olusturma else None,
    }


def _yg(y):
    return {
        'id': y.id, 'tarih': y.tarih.isoformat() if y.tarih else None,
        'pdf_url': y.pdf_url, 'musteri_onay': y.musteri_onay,
        'musteri_id': y.musteri_id, 'mulk_id': y.mulk_id,
    }


def _not(n):
    return {
        'id': n.id, 'icerik': n.icerik, 'etiket': n.etiket,
        'tamamlandi': n.tamamlandi,
        'olusturma': n.olusturma.isoformat() if n.olusturma else None,
    }
