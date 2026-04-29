"""
PANEL — Emlakçı dashboard API'leri
"""
from flask import Blueprint, request, jsonify, send_file
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models import Emlakci, Musteri, Mulk, YerGosterme, Not
from app.services.iletisim import email_gonder, musteri_email_sablonu, portfoy_email_sablonu
from app.services.yedekleme import excel_export, yedek_ozeti
import io

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
    _temel = ['ad_soyad', 'telefon', 'tc_kimlik', 'email', 'islem_turu', 'butce_min', 'butce_max', 'tercih_notlar', 'sicaklik', 'grup']
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
    for f in ['ad_soyad', 'telefon', 'islem_turu', 'butce_min', 'butce_max', 'tercih_notlar', 'sicaklik', 'grup']:
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


@bp.route('/yer-gostermeler', methods=['POST'])
@jwt_required()
def yer_gosterme_olustur():
    d = request.get_json() or {}
    emlakci = Emlakci.query.get(_eid())
    musteri = Musteri.query.filter_by(id=d.get('musteri_id'), emlakci_id=_eid()).first() if d.get('musteri_id') else None
    mulk = Mulk.query.filter_by(id=d.get('mulk_id'), emlakci_id=_eid()).first() if d.get('mulk_id') else None

    yg = YerGosterme(emlakci_id=_eid(), musteri_id=d.get('musteri_id'), mulk_id=d.get('mulk_id'))
    db.session.add(yg)
    db.session.commit()
    return jsonify({'kayit': _yg(yg)}), 201


@bp.route('/belge/yer-gosterme', methods=['POST'])
@jwt_required()
def belge_yer_gosterme():
    """Yer gösterme belgesi PDF oluştur ve indir."""
    d = request.get_json() or {}
    emlakci = Emlakci.query.get(_eid())
    musteri = Musteri.query.filter_by(id=d.get('musteri_id'), emlakci_id=_eid()).first() if d.get('musteri_id') else None
    mulk = Mulk.query.filter_by(id=d.get('mulk_id'), emlakci_id=_eid()).first() if d.get('mulk_id') else None

    from app.services.belge import yer_gosterme_pdf
    pdf_bytes = yer_gosterme_pdf(emlakci, musteri, mulk)
    return send_file(
        io.BytesIO(pdf_bytes),
        mimetype='application/pdf',
        as_attachment=True,
        download_name=f'yer_gosterme_{emlakci.id}_{musteri.id if musteri else 0}.pdf',
    )


@bp.route('/belge/kira-kontrati', methods=['POST'])
@jwt_required()
def belge_kira_kontrati():
    """Kira kontratı PDF oluştur ve indir."""
    d = request.get_json() or {}
    emlakci = Emlakci.query.get(_eid())
    kiraci = Musteri.query.filter_by(id=d.get('musteri_id'), emlakci_id=_eid()).first() if d.get('musteri_id') else None
    mulk = Mulk.query.filter_by(id=d.get('mulk_id'), emlakci_id=_eid()).first() if d.get('mulk_id') else None

    from app.services.belge import kira_kontrati_pdf
    pdf_bytes = kira_kontrati_pdf(emlakci, kiraci, mulk, detaylar=d.get('detaylar'))
    return send_file(
        io.BytesIO(pdf_bytes),
        mimetype='application/pdf',
        as_attachment=True,
        download_name=f'kira_kontrati_{emlakci.id}.pdf',
    )


# ── Email ─────────────────────────────────────────────────────────────────────
@bp.route('/email/gonder', methods=['POST'])
@jwt_required()
def email_gonder_endpoint():
    d = request.get_json() or {}
    emlakci = Emlakci.query.get(_eid())
    alici = d.get('alici_email', '').strip()
    konu = d.get('konu', 'Emlakisim').strip()
    mesaj = d.get('mesaj', '').strip()

    if not alici:
        return jsonify({'message': 'Alıcı email gerekli'}), 400

    # Müşteri ve mülk bilgisi opsiyonel
    musteri = Musteri.query.filter_by(id=d.get('musteri_id'), emlakci_id=_eid()).first() if d.get('musteri_id') else None
    mulk = Mulk.query.filter_by(id=d.get('mulk_id'), emlakci_id=_eid()).first() if d.get('mulk_id') else None

    html = musteri_email_sablonu(emlakci, musteri, mulk, mesaj)
    basarili, sonuc = email_gonder(alici, konu, html, gonderen_ad=emlakci.acente_adi or emlakci.ad_soyad)

    if basarili:
        return jsonify({'ok': True, 'mesaj': 'Email gönderildi'})
    return jsonify({'message': f'Email gönderilemedi: {sonuc}'}), 500


@bp.route('/email/portfoy', methods=['POST'])
@jwt_required()
def email_portfoy():
    """Portföy listesini email ile gönder."""
    d = request.get_json() or {}
    emlakci = Emlakci.query.get(_eid())
    alici = d.get('alici_email', '').strip()

    if not alici:
        return jsonify({'message': 'Alıcı email gerekli'}), 400

    mulk_idler = d.get('mulk_idler', [])
    if mulk_idler:
        mulkler_q = Mulk.query.filter(Mulk.id.in_(mulk_idler), Mulk.emlakci_id == _eid(), Mulk.aktif == True).all()
    else:
        mulkler_q = Mulk.query.filter_by(emlakci_id=_eid(), aktif=True).limit(20).all()

    html = portfoy_email_sablonu(emlakci, mulkler_q)
    basarili, sonuc = email_gonder(alici, f'{emlakci.acente_adi or "Emlakisim"} — Portföy', html)

    if basarili:
        return jsonify({'ok': True, 'mesaj': f'{len(mulkler_q)} mülk email ile gönderildi'})
    return jsonify({'message': f'Email gönderilemedi: {sonuc}'}), 500


# ── Yedekleme ─────────────────────────────────────────────────────────────────
@bp.route('/yedek/indir', methods=['GET'])
@jwt_required()
def yedek_indir():
    """Tüm veriyi Excel olarak indir."""
    emlakci = Emlakci.query.get(_eid())
    data = excel_export(emlakci)
    dosya_adi = f'emlakisim_yedek_{emlakci.id}_{__import__("datetime").datetime.now().strftime("%Y%m%d")}'
    if data[:2] == b'PK':  # xlsx
        return send_file(io.BytesIO(data), mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                         as_attachment=True, download_name=f'{dosya_adi}.xlsx')
    return send_file(io.BytesIO(data), mimetype='application/json',
                     as_attachment=True, download_name=f'{dosya_adi}.json')


@bp.route('/yedek/ozet', methods=['GET'])
@jwt_required()
def yedek_ozet_endpoint():
    emlakci = Emlakci.query.get(_eid())
    return jsonify(yedek_ozeti(emlakci))


@bp.route('/yedek/email', methods=['POST'])
@jwt_required()
def yedek_email():
    """Yedek dosyasını email ile gönder."""
    emlakci = Emlakci.query.get(_eid())
    alici = (request.get_json() or {}).get('email', emlakci.email)
    if not alici:
        return jsonify({'message': 'Email adresi gerekli'}), 400

    data = excel_export(emlakci)
    # Email ile gönder
    import smtplib, os
    from email.mime.multipart import MIMEMultipart
    from email.mime.base import MIMEBase
    from email.mime.text import MIMEText
    from email import encoders

    smtp_user = os.environ.get('SMTP_USER', '')
    smtp_pass = os.environ.get('SMTP_PASS', '')
    if not smtp_user:
        return jsonify({'message': 'SMTP ayarları eksik'}), 500

    msg = MIMEMultipart()
    msg['Subject'] = f'Emlakisim Yedek — {__import__("datetime").datetime.now().strftime("%d.%m.%Y")}'
    msg['From'] = smtp_user
    msg['To'] = alici
    msg.attach(MIMEText('Emlakisim veri yedeğiniz ektedir.', 'plain', 'utf-8'))

    ext = 'xlsx' if data[:2] == b'PK' else 'json'
    part = MIMEBase('application', 'octet-stream')
    part.set_payload(data)
    encoders.encode_base64(part)
    part.add_header('Content-Disposition', f'attachment; filename="emlakisim_yedek.{ext}"')
    msg.attach(part)

    try:
        with smtplib.SMTP(os.environ.get('SMTP_HOST', 'smtp.gmail.com'), int(os.environ.get('SMTP_PORT', '587'))) as server:
            server.starttls()
            server.login(smtp_user, smtp_pass)
            server.send_message(msg)
        return jsonify({'ok': True, 'mesaj': f'Yedek {alici} adresine gönderildi'})
    except Exception as e:
        return jsonify({'message': f'Gönderim hatası: {e}'}), 500


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
        'tercih_notlar': m.tercih_notlar, 'sicaklik': m.sicaklik, 'grup': m.grup,
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
