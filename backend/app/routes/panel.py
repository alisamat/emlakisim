"""
PANEL — Emlakçı dashboard API'leri
"""
from flask import Blueprint, request, jsonify, send_file
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models import Emlakci, Musteri, Mulk, YerGosterme, Not
from app.services.iletisim import email_gonder, musteri_email_sablonu, portfoy_email_sablonu
from app.services.yedekleme import excel_export, yedek_ozeti, yedek_durumu, yedek_logla, depolama_durumu
import io

bp = Blueprint('panel', __name__, url_prefix='/api/panel')


def _eid():
    return int(get_jwt_identity())


# ── İstatistikler ─────────────────────────────────────────────────────────────
@bp.route('/istatistik', methods=['GET'])
@jwt_required()
def istatistik():
    """Genel istatistik — müşteri + portföy + muhasebe dağılımları."""
    eid = _eid()
    musteriler = Musteri.query.filter_by(emlakci_id=eid).all()
    mulkler = Mulk.query.filter_by(emlakci_id=eid, aktif=True).all()

    from collections import Counter
    m_sicaklik = Counter(m.sicaklik or 'orta' for m in musteriler)
    m_islem = Counter(m.islem_turu or 'kira' for m in musteriler)
    m_grup = Counter(m.grup for m in musteriler if m.grup)

    p_tip = Counter(m.tip or 'daire' for m in mulkler)
    p_islem = Counter(m.islem_turu or 'kira' for m in mulkler)
    p_ilce = Counter(m.ilce for m in mulkler if m.ilce)
    p_grup = Counter(m.grup for m in mulkler if m.grup)

    fiyatlar = [m.fiyat for m in mulkler if m.fiyat]

    return jsonify({
        'musteri': {
            'toplam': len(musteriler),
            'sicaklik': dict(m_sicaklik),
            'islem': dict(m_islem),
            'gruplar': dict(m_grup),
        },
        'portfoy': {
            'toplam': len(mulkler),
            'tip': dict(p_tip),
            'islem': dict(p_islem),
            'ilce': dict(p_ilce.most_common(10)),
            'gruplar': dict(p_grup),
            'fiyat_ort': round(sum(fiyatlar) / len(fiyatlar)) if fiyatlar else 0,
            'fiyat_min': min(fiyatlar) if fiyatlar else 0,
            'fiyat_max': max(fiyatlar) if fiyatlar else 0,
        },
    })


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
    for f in ['baslik', 'adres', 'sehir', 'ilce', 'tip', 'islem_turu', 'fiyat', 'metrekare', 'oda_sayisi', 'ada', 'parsel', 'notlar', 'grup']:
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


@bp.route('/belge/yonlendirme', methods=['POST'])
@jwt_required()
def belge_yonlendirme():
    """Alıcı/satıcı yönlendirme belgesi PDF."""
    d = request.get_json() or {}
    emlakci = Emlakci.query.get(_eid())
    musteri = Musteri.query.filter_by(id=d.get('musteri_id'), emlakci_id=_eid()).first() if d.get('musteri_id') else None
    mulk = Mulk.query.filter_by(id=d.get('mulk_id'), emlakci_id=_eid()).first() if d.get('mulk_id') else None
    taraf = d.get('taraf', 'alici')

    from app.services.belge import yonlendirme_belgesi_pdf
    pdf_bytes = yonlendirme_belgesi_pdf(emlakci, musteri, mulk, taraf)
    return send_file(io.BytesIO(pdf_bytes), mimetype='application/pdf', as_attachment=True,
                     download_name=f'yonlendirme_{taraf}_{emlakci.id}.pdf')


# ── Müşteri Kartı Gönderme ────────────────────────────────────────────────────
@bp.route('/musteriler/<int:mid>/kart-gonder', methods=['POST'])
@jwt_required()
def musteri_kart_gonder(mid):
    """Müşteri kartını email ile gönder."""
    m = Musteri.query.filter_by(id=mid, emlakci_id=_eid()).first_or_404()
    d = request.get_json() or {}
    alici = d.get('email', '').strip()
    if not alici:
        return jsonify({'message': 'Email adresi gerekli'}), 400

    emlakci = Emlakci.query.get(_eid())
    html = f"""
    <div style="font-family:sans-serif;max-width:500px;margin:0 auto;border:1px solid #e2e8f0;border-radius:12px;overflow:hidden">
        <div style="background:#16a34a;color:#fff;padding:16px 20px"><strong>Müşteri Kartı</strong></div>
        <div style="padding:20px">
            <div style="font-size:18px;font-weight:700;margin-bottom:8px">{m.ad_soyad}</div>
            <div style="color:#64748b;font-size:14px">📞 {m.telefon or '-'}</div>
            <div style="color:#64748b;font-size:14px">🏷 {'Kiralık' if m.islem_turu == 'kira' else 'Satılık'}</div>
            {'<div style="color:#64748b;font-size:14px">💰 ' + str(m.butce_min or '') + ' - ' + str(m.butce_max or '') + ' TL</div>' if m.butce_min or m.butce_max else ''}
            {'<div style="color:#94a3b8;font-size:13px;margin-top:8px">' + m.tercih_notlar + '</div>' if m.tercih_notlar else ''}
            <hr style="border:none;border-top:1px solid #e2e8f0;margin:16px 0">
            <div style="font-size:12px;color:#94a3b8">{emlakci.ad_soyad} · {emlakci.acente_adi or ''}</div>
        </div>
    </div>"""

    basarili, sonuc = email_gonder(alici, f'Müşteri Kartı: {m.ad_soyad}', html, gonderen_ad=emlakci.ad_soyad)
    if basarili:
        return jsonify({'ok': True, 'mesaj': f'{m.ad_soyad} kartı {alici} adresine gönderildi'})
    return jsonify({'message': f'Gönderim hatası: {sonuc}'}), 500


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


@bp.route('/email/toplu', methods=['POST'])
@jwt_required()
def email_toplu():
    """Birden fazla müşteriye aynı anda email gönder."""
    d = request.get_json() or {}
    emlakci = Emlakci.query.get(_eid())
    musteri_idler = d.get('musteri_idler', [])
    mesaj = d.get('mesaj', '').strip()
    konu = d.get('konu', 'Emlakisim').strip()

    if not musteri_idler:
        return jsonify({'message': 'Müşteri listesi gerekli'}), 400

    gonderilen = 0
    hatali = 0
    for mid in musteri_idler:
        m = Musteri.query.filter_by(id=mid, emlakci_id=_eid()).first()
        if not m:
            continue
        det = m.detaylar or {}
        alici = det.get('email', '')
        if not alici:
            hatali += 1
            continue
        html = musteri_email_sablonu(emlakci, m, None, mesaj)
        ok, _ = email_gonder(alici, konu, html, gonderen_ad=emlakci.ad_soyad)
        if ok:
            gonderilen += 1
        else:
            hatali += 1

    return jsonify({'gonderilen': gonderilen, 'hatali': hatali, 'toplam': len(musteri_idler)})


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
    fmt = request.args.get('format', 'excel')  # excel veya json
    if fmt == 'json':
        from app.services.yedekleme import _json_export
        data = _json_export(emlakci)
        yedek_logla(emlakci)
        dosya_adi = f'emlakisim_yedek_{emlakci.id}_{__import__("datetime").datetime.now().strftime("%Y%m%d")}'
        return send_file(io.BytesIO(data), mimetype='application/json', as_attachment=True, download_name=f'{dosya_adi}.json')
    data = excel_export(emlakci)
    yedek_logla(emlakci)
    dosya_adi = f'emlakisim_yedek_{emlakci.id}_{__import__("datetime").datetime.now().strftime("%Y%m%d")}'
    if data[:2] == b'PK':  # xlsx
        return send_file(io.BytesIO(data), mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                         as_attachment=True, download_name=f'{dosya_adi}.xlsx')
    return send_file(io.BytesIO(data), mimetype='application/json',
                     as_attachment=True, download_name=f'{dosya_adi}.json')


@bp.route('/yedek/portfoy-excel', methods=['GET'])
@jwt_required()
def portfoy_excel():
    """Sadece portföy verisini Excel olarak indir."""
    emlakci = Emlakci.query.get(_eid())
    from app.services.yedekleme import portfoy_excel_export
    data = portfoy_excel_export(emlakci)
    dosya_adi = f'portfoy_{emlakci.id}_{__import__("datetime").datetime.now().strftime("%Y%m%d")}'
    if isinstance(data, bytes) and data[:2] == b'PK':
        return send_file(io.BytesIO(data), mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                         as_attachment=True, download_name=f'{dosya_adi}.xlsx')
    return send_file(io.BytesIO(data if isinstance(data, bytes) else data.encode()), mimetype='application/json',
                     as_attachment=True, download_name=f'{dosya_adi}.json')


@bp.route('/yedek/musteri-excel', methods=['GET'])
@jwt_required()
def musteri_excel():
    """Sadece müşteri verisini Excel olarak indir."""
    emlakci = Emlakci.query.get(_eid())
    from app.services.yedekleme import musteri_excel_export
    data = musteri_excel_export(emlakci)
    dosya_adi = f'musteriler_{emlakci.id}_{__import__("datetime").datetime.now().strftime("%Y%m%d")}'
    if isinstance(data, bytes) and data[:2] == b'PK':
        return send_file(io.BytesIO(data), mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                         as_attachment=True, download_name=f'{dosya_adi}.xlsx')
    return send_file(io.BytesIO(data if isinstance(data, bytes) else data.encode()), mimetype='application/json',
                     as_attachment=True, download_name=f'{dosya_adi}.json')


@bp.route('/yedek/ozet', methods=['GET'])
@jwt_required()
def yedek_ozet_endpoint():
    emlakci = Emlakci.query.get(_eid())
    ozet = yedek_ozeti(emlakci)
    ozet['yedek_durumu'] = yedek_durumu(emlakci)
    ozet['depolama'] = depolama_durumu(emlakci)
    return jsonify(ozet)


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


# ── SMS ───────────────────────────────────────────────────────────────────────
@bp.route('/sms/gonder', methods=['POST'])
@jwt_required()
def sms_gonder_endpoint():
    d = request.get_json() or {}
    telefon = d.get('telefon', '').strip()
    mesaj_text = d.get('mesaj', '').strip()
    if not telefon or not mesaj_text:
        return jsonify({'message': 'Telefon ve mesaj gerekli'}), 400
    from app.services.sms import sms_gonder
    ok, sonuc = sms_gonder(telefon, mesaj_text)
    if ok:
        return jsonify({'ok': True, 'mesaj': 'SMS gönderildi'})
    return jsonify({'message': f'SMS gönderilemedi: {sonuc}'}), 500


@bp.route('/sms/durum', methods=['GET'])
@jwt_required()
def sms_durum_endpoint():
    from app.services.sms import sms_durum
    return jsonify(sms_durum())


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
        'ada': m.ada, 'parsel': m.parsel, 'notlar': m.notlar, 'grup': m.grup,
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


# ════════ GÖRSEL ANALİZ & SANAL STAGING ════════

@bp.route('/gorsel-analiz', methods=['POST'])
@jwt_required()
def gorsel_analiz_endpoint():
    """Fotoğraftan konut analizi ve değerleme."""
    d = request.get_json() or {}
    images = d.get('images', [])  # base64 encoded images
    mulk_bilgi = d.get('mulk_bilgi')

    if not images:
        return jsonify({'message': 'En az 1 fotoğraf gerekli'}), 400

    from app.services.gorsel_analiz import konut_analiz, coklu_analiz

    if len(images) == 1:
        sonuc = konut_analiz(images[0], mulk_bilgi)
    else:
        sonuc = coklu_analiz(images[:5], mulk_bilgi)

    if sonuc.get('hata'):
        return jsonify({'message': sonuc['hata']}), 500

    return jsonify({'analiz': sonuc})


@bp.route('/sanal-staging', methods=['POST'])
@jwt_required()
def sanal_staging_endpoint():
    """Sanal ev düzenleme — boş odayı mobilyalı hale getir."""
    d = request.get_json() or {}
    image = d.get('image')  # base64
    stil = d.get('stil', 'modern')
    oda_tipi = d.get('oda_tipi')

    if not image:
        return jsonify({'message': 'Fotoğraf gerekli'}), 400

    from app.services.gorsel_analiz import sanal_staging
    sonuc = sanal_staging(image, stil, oda_tipi)

    if sonuc.get('hata'):
        return jsonify({'message': sonuc['hata']}), 500

    return jsonify({'staging': sonuc})


@bp.route('/mahalle-analiz', methods=['GET'])
@jwt_required()
def mahalle_analiz_endpoint():
    """Mahalle/ilçe analizi."""
    sehir = request.args.get('sehir', 'İstanbul')
    ilce = request.args.get('ilce', '')
    mahalle = request.args.get('mahalle', '')

    if not ilce:
        return jsonify({'message': 'İlçe gerekli'}), 400

    from app.services.asistan import _mahalle_analiz
    mesaj = _mahalle_analiz({'sehir': sehir, 'ilce': ilce, 'mahalle': mahalle})
    return jsonify({'analiz': mesaj})


# ════════ SATICI TAHMİN & ISI HARİTASI ════════

@bp.route('/tahmin/satici', methods=['GET'])
@jwt_required()
def satici_tahmin_endpoint():
    """Müşteri satış olasılığı tahmini."""
    from app.services.tahmin_motoru import satici_tahmin
    sonuclar = satici_tahmin(_eid())
    return jsonify({'tahminler': sonuclar})


@bp.route('/isi-haritasi', methods=['GET'])
@jwt_required()
def isi_haritasi_endpoint():
    """İlçe bazında portföy ısı haritası."""
    from app.services.tahmin_motoru import isi_haritasi
    sonuc = isi_haritasi(_eid())
    return jsonify({'harita': sonuc})
