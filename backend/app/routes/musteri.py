"""
MÜŞTERİ PORTAL — Belge onay, emlakçı profil, portföy görüntüleme
"""
from flask import Blueprint, request, jsonify
from datetime import datetime
from app import db
from app.models import MusteriOnayToken, YerGosterme, Emlakci, Mulk

bp = Blueprint('musteri', __name__, url_prefix='/api/musteri')


@bp.route('/onay/<token>', methods=['GET'])
def onay_bilgi(token):
    """Token ile yer gösterme detayını getir"""
    t = MusteriOnayToken.query.filter_by(token=token, kullanildi=False).first()
    if not t:
        return jsonify({'message': 'Geçersiz veya süresi dolmuş link'}), 404
    yg = YerGosterme.query.get(t.yer_gosterme_id)
    return jsonify({'yer_gosterme': {
        'id': yg.id, 'tarih': yg.tarih.isoformat() if yg.tarih else None,
        'pdf_url': yg.pdf_url, 'ham_veri': yg.ham_veri,
    }})


@bp.route('/onay/<token>', methods=['POST'])
def onay_kaydet(token):
    """Müşteri TC girerek onaylar"""
    t = MusteriOnayToken.query.filter_by(token=token, kullanildi=False).first()
    if not t:
        return jsonify({'message': 'Geçersiz veya süresi dolmuş link'}), 404

    d = request.get_json() or {}
    tc = d.get('tc_kimlik', '')
    yg = YerGosterme.query.get(t.yer_gosterme_id)

    # TC doğrulama
    if yg.ham_veri and yg.ham_veri.get('tc_kimlik') and yg.ham_veri['tc_kimlik'] != tc:
        return jsonify({'message': 'TC kimlik numarası eşleşmiyor'}), 400

    yg.musteri_onay  = True
    yg.onay_tarihi   = datetime.utcnow()
    yg.onay_ip       = request.remote_addr
    t.kullanildi     = True
    db.session.commit()

    return jsonify({'message': 'Onay alındı. Teşekkürler.'})


# ── Müşteri talep gönderme ───────────────────────────────
@bp.route('/talep', methods=['POST'])
def musteri_talep():
    """Alıcı/satıcı talep gönderir (kayıtsız)."""
    d = request.get_json() or {}
    emlakci_id = d.get('emlakci_id')
    if not emlakci_id:
        return jsonify({'message': 'Emlakçı belirtilmedi'}), 400

    e = Emlakci.query.filter_by(id=emlakci_id, aktif=True).first()
    if not e:
        return jsonify({'message': 'Emlakçı bulunamadı'}), 404

    # Lead olarak kaydet
    from app.models.lead import Lead
    lead = Lead(
        emlakci_id=emlakci_id,
        ad_soyad=d.get('ad_soyad', ''),
        telefon=d.get('telefon', ''),
        email=d.get('email', ''),
        kaynak='web',
        ilk_mesaj=d.get('mesaj', ''),
        detaylar=d.get('detaylar', {}),
    )
    db.session.add(lead)
    db.session.commit()
    return jsonify({'message': 'Talebiniz iletildi. En kısa sürede dönüş yapılacaktır.'})
