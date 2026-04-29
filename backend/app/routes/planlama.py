"""
PLANLAMA — Görev, hatırlatma, takvim API
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models.planlama import Gorev
from datetime import datetime, timedelta

bp = Blueprint('planlama', __name__, url_prefix='/api/panel/planlama')


def _eid():
    return int(get_jwt_identity())


@bp.route('/gorevler', methods=['GET'])
@jwt_required()
def gorev_listesi():
    durum = request.args.get('durum')
    q = Gorev.query.filter_by(emlakci_id=_eid())
    if durum:
        q = q.filter_by(durum=durum)
    else:
        q = q.filter(Gorev.durum != 'iptal')
    kayitlar = q.order_by(Gorev.baslangic.asc().nullslast(), Gorev.olusturma.desc()).all()
    return jsonify({'gorevler': [_g(g) for g in kayitlar]})


@bp.route('/gorevler', methods=['POST'])
@jwt_required()
def gorev_ekle():
    d = request.get_json() or {}
    g = Gorev(
        emlakci_id=_eid(),
        baslik=d.get('baslik', ''),
        aciklama=d.get('aciklama'),
        tip=d.get('tip', 'gorev'),
        oncelik=d.get('oncelik', 'orta'),
        musteri_id=d.get('musteri_id'),
        mulk_id=d.get('mulk_id'),
        detaylar=d.get('detaylar', {}),
    )
    if d.get('baslangic'):
        try: g.baslangic = datetime.fromisoformat(d['baslangic'])
        except: pass
    if d.get('bitis'):
        try: g.bitis = datetime.fromisoformat(d['bitis'])
        except: pass
    db.session.add(g); db.session.commit()
    return jsonify({'gorev': _g(g)}), 201


@bp.route('/gorevler/<int:gid>', methods=['PUT'])
@jwt_required()
def gorev_guncelle(gid):
    g = Gorev.query.filter_by(id=gid, emlakci_id=_eid()).first_or_404()
    d = request.get_json() or {}
    for f in ['baslik', 'aciklama', 'tip', 'oncelik', 'durum']:
        if f in d:
            setattr(g, f, d[f])
    if 'baslangic' in d:
        try: g.baslangic = datetime.fromisoformat(d['baslangic']) if d['baslangic'] else None
        except: pass
    if 'bitis' in d:
        try: g.bitis = datetime.fromisoformat(d['bitis']) if d['bitis'] else None
        except: pass
    db.session.commit()
    return jsonify({'gorev': _g(g)})


@bp.route('/gorevler/<int:gid>', methods=['DELETE'])
@jwt_required()
def gorev_sil(gid):
    g = Gorev.query.filter_by(id=gid, emlakci_id=_eid()).first_or_404()
    db.session.delete(g); db.session.commit()
    return jsonify({'ok': True})


@bp.route('/takvim', methods=['GET'])
@jwt_required()
def takvim():
    """Belirli ay için görevleri getir."""
    yil = int(request.args.get('yil', datetime.now().year))
    ay = int(request.args.get('ay', datetime.now().month))
    baslangic = datetime(yil, ay, 1)
    if ay == 12:
        bitis = datetime(yil + 1, 1, 1)
    else:
        bitis = datetime(yil, ay + 1, 1)

    gorevler = Gorev.query.filter(
        Gorev.emlakci_id == _eid(),
        Gorev.baslangic >= baslangic,
        Gorev.baslangic < bitis,
        Gorev.durum != 'iptal',
    ).order_by(Gorev.baslangic).all()

    return jsonify({'gorevler': [_g(g) for g in gorevler], 'yil': yil, 'ay': ay})


@bp.route('/bugun', methods=['GET'])
@jwt_required()
def bugun():
    """Bugünkü görevler + yaklaşan hatırlatmalar."""
    simdi = datetime.utcnow()
    bugun_baslangic = simdi.replace(hour=0, minute=0, second=0)
    yarin = bugun_baslangic + timedelta(days=1)
    hafta = bugun_baslangic + timedelta(days=7)

    bugunkuler = Gorev.query.filter(
        Gorev.emlakci_id == _eid(),
        Gorev.baslangic >= bugun_baslangic,
        Gorev.baslangic < yarin,
        Gorev.durum != 'iptal',
    ).all()

    yaklasan = Gorev.query.filter(
        Gorev.emlakci_id == _eid(),
        Gorev.baslangic >= yarin,
        Gorev.baslangic < hafta,
        Gorev.durum == 'bekliyor',
    ).all()

    return jsonify({
        'bugun': [_g(g) for g in bugunkuler],
        'yaklasan': [_g(g) for g in yaklasan],
    })


def _g(g):
    return {
        'id': g.id, 'baslik': g.baslik, 'aciklama': g.aciklama,
        'tip': g.tip, 'oncelik': g.oncelik, 'durum': g.durum,
        'baslangic': g.baslangic.isoformat() if g.baslangic else None,
        'bitis': g.bitis.isoformat() if g.bitis else None,
        'musteri_id': g.musteri_id, 'mulk_id': g.mulk_id,
        'detaylar': g.detaylar or {},
    }
