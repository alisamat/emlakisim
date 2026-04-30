"""
EĞİTİM — Diyalog eğitim admin API'leri
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from app import db
from app.models.egitim import DiyalogKayit, OgrenilenPattern
from app.services.egitim import istatistik, cache_yenile
from app.models import IslemLog, Emlakci

bp = Blueprint('egitim', __name__, url_prefix='/api/panel/egitim')


@bp.route('/istatistik', methods=['GET'])
@jwt_required()
def egitim_istatistik():
    return jsonify(istatistik())


@bp.route('/anlasilamayan', methods=['GET'])
@jwt_required()
def anlasilamayan():
    """AI'ya giden mesajları listele — pattern'a dönüştürülebilir."""
    kayitlar = DiyalogKayit.query.filter_by(model='openai').order_by(
        DiyalogKayit.olusturma.desc()
    ).limit(50).all()
    return jsonify({'kayitlar': [{
        'id': k.id, 'mesaj': k.mesaj, 'mesaj_norm': k.mesaj_norm,
        'islem': k.islem, 'olusturma': k.olusturma.isoformat(),
    } for k in kayitlar]})


@bp.route('/patterns', methods=['GET'])
@jwt_required()
def pattern_listesi():
    patterns = OgrenilenPattern.query.filter_by(aktif=True).order_by(
        OgrenilenPattern.kullanim.desc()
    ).all()
    return jsonify({'patterns': [{
        'id': p.id, 'pattern': p.pattern, 'islem': p.islem,
        'kullanim': p.kullanim, 'kaynak': p.kaynak,
    } for p in patterns]})


@bp.route('/patterns', methods=['POST'])
@jwt_required()
def pattern_ekle():
    d = request.get_json() or {}
    p = OgrenilenPattern(
        pattern=d.get('pattern', ''),
        islem=d.get('islem', ''),
        kaynak=d.get('kaynak', 'manuel'),
    )
    db.session.add(p)
    db.session.commit()
    cache_yenile()
    return jsonify({'ok': True, 'id': p.id}), 201


@bp.route('/maliyet-rapor', methods=['GET'])
@jwt_required()
def maliyet_rapor():
    """Admin maliyet raporu — kredi kullanımı ve AI maliyeti."""
    from flask_jwt_extended import get_jwt_identity
    eid = int(get_jwt_identity())
    loglar = IslemLog.query.filter_by(emlakci_id=eid).order_by(IslemLog.olusturma.desc()).limit(200).all()

    toplam_kredi = sum(l.kredi_tutar or 0 for l in loglar)
    toplam_usd = sum(l.maliyet_usd or 0 for l in loglar)

    # İşlem tipi bazlı
    tip_bazli = {}
    for l in loglar:
        tip = l.islem_tipi or 'bilinmeyen'
        if tip not in tip_bazli:
            tip_bazli[tip] = {'sayi': 0, 'kredi': 0, 'usd': 0}
        tip_bazli[tip]['sayi'] += 1
        tip_bazli[tip]['kredi'] += l.kredi_tutar or 0
        tip_bazli[tip]['usd'] += l.maliyet_usd or 0

    return jsonify({
        'toplam_kredi': round(toplam_kredi, 2),
        'toplam_usd': round(toplam_usd, 6),
        'islem_sayisi': len(loglar),
        'tip_bazli': tip_bazli,
        'son_islemler': [{
            'tip': l.islem_tipi, 'kredi': l.kredi_tutar, 'usd': l.maliyet_usd,
            'aciklama': l.aciklama, 'tarih': l.olusturma.isoformat() if l.olusturma else None,
        } for l in loglar[:20]],
    })


@bp.route('/patterns/<int:pid>', methods=['DELETE'])
@jwt_required()
def pattern_sil(pid):
    p = OgrenilenPattern.query.get_or_404(pid)
    p.aktif = False
    db.session.commit()
    cache_yenile()
    return jsonify({'ok': True})
