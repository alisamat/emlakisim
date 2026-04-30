"""
GELİŞMİŞ — Web arama, metin analiz, sosyal medya içerik API
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models import Mulk
from app.services.gelismis import web_arama, metin_analiz, sosyal_medya_icerik
from app.services.pdf_okuyucu import pdf_metin_cikar, pdf_analiz
from app.services.sektorel import sektor_haberleri, piyasa_analizi
from app.services.ilan import ilan_metni_olustur
from app.services.reklam import reklam_metni_olustur, sunum_pdf
from app.models import Mulk
from app.models.iletisim_gecmisi import IletisimKayit

bp = Blueprint('gelismis', __name__, url_prefix='/api/panel/gelismis')


@bp.route('/web-ara', methods=['POST'])
@jwt_required()
def web_ara():
    d = request.get_json() or {}
    sorgu = d.get('sorgu', '').strip()
    if not sorgu:
        return jsonify({'message': 'Sorgu gerekli'}), 400
    sonuc = web_arama(sorgu)
    return jsonify(sonuc)


@bp.route('/metin-analiz', methods=['POST'])
@jwt_required()
def metin_analiz_endpoint():
    d = request.get_json() or {}
    metin = d.get('metin', '').strip()
    if not metin:
        return jsonify({'message': 'Metin gerekli'}), 400
    sonuc = metin_analiz(metin)
    return jsonify(sonuc)


@bp.route('/sosyal-medya', methods=['POST'])
@jwt_required()
def sosyal_medya():
    d = request.get_json() or {}
    mulk_id = d.get('mulk_id')
    platform = d.get('platform', 'instagram')
    if not mulk_id:
        return jsonify({'message': 'Mülk ID gerekli'}), 400
    mulk = Mulk.query.filter_by(id=mulk_id, emlakci_id=int(get_jwt_identity())).first()
    if not mulk:
        return jsonify({'message': 'Mülk bulunamadı'}), 404
    sonuc = sosyal_medya_icerik(mulk, platform)
    return jsonify(sonuc)


@bp.route('/pdf-oku', methods=['POST'])
@jwt_required()
def pdf_oku():
    """PDF dosyasını oku ve analiz et."""
    if 'file' not in request.files:
        return jsonify({'message': 'PDF dosyası gerekli'}), 400
    pdf_bytes = request.files['file'].read()
    soru = request.form.get('soru', '')
    sonuc = pdf_analiz(pdf_bytes, soru)
    return jsonify(sonuc)


@bp.route('/sektor-haberleri', methods=['POST'])
@jwt_required()
def sektor():
    d = request.get_json() or {}
    sonuc = sektor_haberleri(d.get('konu', 'emlak piyasası'))
    return jsonify(sonuc)


@bp.route('/piyasa-analizi', methods=['POST'])
@jwt_required()
def piyasa():
    d = request.get_json() or {}
    sonuc = piyasa_analizi(d.get('sehir', 'İstanbul'), d.get('tip', 'daire'))
    return jsonify(sonuc)


@bp.route('/ilan-metni', methods=['POST'])
@jwt_required()
def ilan_metni():
    """Mülk için ilan metni oluştur."""
    d = request.get_json() or {}
    mulk = Mulk.query.filter_by(id=d.get('mulk_id'), emlakci_id=int(get_jwt_identity())).first()
    if not mulk:
        return jsonify({'message': 'Mülk bulunamadı'}), 404
    platform = d.get('platform', 'sahibinden')
    metin = ilan_metni_olustur(mulk, platform)
    return jsonify({'ilan': metin, 'platform': platform})


@bp.route('/reklam-metni', methods=['POST'])
@jwt_required()
def reklam_metni():
    """Mülk için reklam metni oluştur."""
    d = request.get_json() or {}
    mulk = Mulk.query.filter_by(id=d.get('mulk_id'), emlakci_id=int(get_jwt_identity())).first()
    if not mulk:
        return jsonify({'message': 'Mülk bulunamadı'}), 404
    metin = reklam_metni_olustur(mulk, d.get('hedef', 'alici'), d.get('stil', 'profesyonel'))
    return jsonify({'reklam': metin})


@bp.route('/sunum-pdf', methods=['POST'])
@jwt_required()
def sunum_pdf_endpoint():
    """Mülk sunum PDF oluştur."""
    d = request.get_json() or {}
    mulk = Mulk.query.filter_by(id=d.get('mulk_id'), emlakci_id=int(get_jwt_identity())).first()
    if not mulk:
        return jsonify({'message': 'Mülk bulunamadı'}), 404
    from app.models import Emlakci
    emlakci = Emlakci.query.get(int(get_jwt_identity()))
    reklam = d.get('reklam_metin', '')
    import io
    from flask import send_file
    pdf_bytes = sunum_pdf(emlakci, mulk, reklam)
    return send_file(io.BytesIO(pdf_bytes), mimetype='application/pdf', as_attachment=True,
                     download_name=f'sunum_{mulk.id}.pdf')


# ── İletişim Geçmişi ─────────────────────────────────────
@bp.route('/iletisim-kayit', methods=['POST'])
@jwt_required()
def iletisim_kayit_ekle():
    d = request.get_json() or {}
    from app import db
    k = IletisimKayit(
        emlakci_id=int(get_jwt_identity()),
        musteri_id=d.get('musteri_id'),
        tip=d.get('tip', 'telefon'),
        yon=d.get('yon', 'giden'),
        ozet=d.get('ozet', ''),
        detaylar=d.get('detaylar', {}),
    )
    db.session.add(k); db.session.commit()
    return jsonify({'ok': True}), 201


@bp.route('/iletisim-gecmisi/<int:musteri_id>', methods=['GET'])
@jwt_required()
def iletisim_gecmisi(musteri_id):
    kayitlar = IletisimKayit.query.filter_by(
        emlakci_id=int(get_jwt_identity()), musteri_id=musteri_id
    ).order_by(IletisimKayit.olusturma.desc()).limit(30).all()
    return jsonify({'kayitlar': [{
        'id': k.id, 'tip': k.tip, 'yon': k.yon,
        'ozet': k.ozet, 'olusturma': k.olusturma.isoformat(),
    } for k in kayitlar]})
