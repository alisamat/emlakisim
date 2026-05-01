"""
HESAPLAMA — Emlak hesaplama API'leri
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from app.services.hesaplama import kira_vergisi, deger_artis_kazanci, kira_getirisi, aidat_analizi, tapu_masrafi, komisyon_hesapla

bp = Blueprint('hesaplama', __name__, url_prefix='/api/panel/hesaplama')


@bp.route('/kira-vergisi', methods=['POST'])
@jwt_required()
def kira_vergisi_endpoint():
    d = request.get_json() or {}
    sonuc = kira_vergisi(
        yillik_kira=float(d.get('yillik_kira', 0)),
        istisna_tutari=float(d.get('istisna', 33000)),
    )
    return jsonify(sonuc)


@bp.route('/deger-artis', methods=['POST'])
@jwt_required()
def deger_artis_endpoint():
    d = request.get_json() or {}
    sonuc = deger_artis_kazanci(
        alis_fiyati=float(d.get('alis_fiyati', 0)),
        satis_fiyati=float(d.get('satis_fiyati', 0)),
        alis_yili=int(d.get('alis_yili', 2024)),
        satis_yili=int(d.get('satis_yili', 2026)),
    )
    return jsonify(sonuc)


@bp.route('/kira-getirisi', methods=['POST'])
@jwt_required()
def kira_getirisi_endpoint():
    d = request.get_json() or {}
    sonuc = kira_getirisi(
        mulk_fiyati=float(d.get('mulk_fiyati', 0)),
        aylik_kira=float(d.get('aylik_kira', 0)),
        yillik_gider=float(d.get('yillik_gider', 0)),
    )
    return jsonify(sonuc)


@bp.route('/aidat-analizi', methods=['POST'])
@jwt_required()
def aidat_analizi_endpoint():
    d = request.get_json() or {}
    sonuc = aidat_analizi(
        aidat=float(d.get('aidat', 0)),
        kira=float(d.get('kira', 0)),
        mulk_fiyati=float(d.get('mulk_fiyati', 0)),
    )
    return jsonify(sonuc)


@bp.route('/tapu-masrafi', methods=['POST'])
@jwt_required()
def tapu_masrafi_endpoint():
    d = request.get_json() or {}
    sonuc = tapu_masrafi(float(d.get('satis_bedeli', 0)))
    return jsonify(sonuc)


@bp.route('/komisyon', methods=['POST'])
@jwt_required()
def komisyon_endpoint():
    d = request.get_json() or {}
    sonuc = komisyon_hesapla(d.get('islem_turu', 'satis'), float(d.get('bedel', 0)))
    return jsonify(sonuc)
