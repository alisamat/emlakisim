"""
TOPLU İŞLEM — Excel/rehber/OCR import API'leri
"""
import base64
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.services.toplu import excel_musteri_import, excel_portfoy_import, ocr_portfoy_import, rehber_import

bp = Blueprint('toplu', __name__, url_prefix='/api/panel/toplu')


def _eid():
    return int(get_jwt_identity())


@bp.route('/musteri-excel', methods=['POST'])
@jwt_required()
def musteri_excel():
    if 'file' not in request.files:
        return jsonify({'message': 'Excel dosyası gerekli'}), 400
    data = request.files['file'].read()
    sonuc = excel_musteri_import(_eid(), data)
    return jsonify(sonuc), 201 if not sonuc.get('hata') else 400


@bp.route('/portfoy-excel', methods=['POST'])
@jwt_required()
def portfoy_excel():
    if 'file' not in request.files:
        return jsonify({'message': 'Excel dosyası gerekli'}), 400
    data = request.files['file'].read()
    sonuc = excel_portfoy_import(_eid(), data)
    return jsonify(sonuc), 201 if not sonuc.get('hata') else 400


@bp.route('/portfoy-ocr', methods=['POST'])
@jwt_required()
def portfoy_ocr():
    """Sahibinden ekran görüntüsünden portföy import."""
    if 'image' in request.files:
        img = request.files['image'].read()
        img_b64 = base64.b64encode(img).decode()
    elif request.is_json and request.json.get('image_base64'):
        img_b64 = request.json['image_base64']
    else:
        return jsonify({'message': 'Fotoğraf gerekli'}), 400

    sonuc = ocr_portfoy_import(_eid(), img_b64)
    return jsonify(sonuc), 201 if not sonuc.get('hata') else 400


@bp.route('/rehber', methods=['POST'])
@jwt_required()
def rehber():
    """Telefon rehberinden toplu müşteri ekleme."""
    d = request.get_json() or {}
    kisiler = d.get('kisiler', [])
    if not kisiler:
        return jsonify({'message': 'Kişi listesi gerekli'}), 400
    sonuc = rehber_import(_eid(), kisiler)
    return jsonify(sonuc), 201
