"""
FATURA — Fatura CRUD + PDF + durum takibi
"""
from flask import Blueprint, request, jsonify, send_file
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models.fatura import Fatura
from datetime import datetime
import io

bp = Blueprint('fatura', __name__, url_prefix='/api/panel/fatura')


def _eid():
    return int(get_jwt_identity())


@bp.route('/listele', methods=['GET'])
@jwt_required()
def listele():
    durum = request.args.get('durum')
    q = Fatura.query.filter_by(emlakci_id=_eid())
    if durum:
        q = q.filter_by(durum=durum)
    kayitlar = q.order_by(Fatura.olusturma.desc()).limit(100).all()
    return jsonify({'faturalar': [_f(f) for f in kayitlar]})


@bp.route('/ekle', methods=['POST'])
@jwt_required()
def ekle():
    d = request.get_json() or {}
    tutar = float(d.get('tutar', 0))
    kdv_oran = int(d.get('kdv_oran', 20))
    kdv_tutar = tutar * kdv_oran / 100
    toplam = tutar + kdv_tutar

    f = Fatura(
        emlakci_id=_eid(),
        fatura_no=d.get('fatura_no', f'F-{datetime.now().strftime("%Y%m%d%H%M")}'),
        tip=d.get('tip', 'hizmet'),
        musteri_id=d.get('musteri_id'),
        mulk_id=d.get('mulk_id'),
        alici_ad=d.get('alici_ad', ''),
        alici_adres=d.get('alici_adres', ''),
        tutar=tutar,
        kdv_oran=kdv_oran,
        kdv_tutar=round(kdv_tutar, 2),
        toplam=round(toplam, 2),
        kalemler=d.get('kalemler', []),
        detaylar=d.get('detaylar', {}),
    )
    if d.get('vade_tarihi'):
        try: f.vade_tarihi = datetime.fromisoformat(d['vade_tarihi'])
        except: pass
    db.session.add(f); db.session.commit()
    return jsonify({'fatura': _f(f)}), 201


@bp.route('/<int:fid>', methods=['PUT'])
@jwt_required()
def guncelle(fid):
    f = Fatura.query.filter_by(id=fid, emlakci_id=_eid()).first_or_404()
    d = request.get_json() or {}
    for k in ['durum', 'alici_ad', 'alici_adres', 'fatura_no']:
        if k in d:
            setattr(f, k, d[k])
    if d.get('durum') == 'odendi' and not f.odeme_tarihi:
        f.odeme_tarihi = datetime.utcnow()
    db.session.commit()
    return jsonify({'fatura': _f(f)})


@bp.route('/<int:fid>', methods=['DELETE'])
@jwt_required()
def sil(fid):
    f = Fatura.query.filter_by(id=fid, emlakci_id=_eid()).first_or_404()
    db.session.delete(f); db.session.commit()
    return jsonify({'ok': True})


@bp.route('/ozet', methods=['GET'])
@jwt_required()
def ozet():
    faturalar = Fatura.query.filter_by(emlakci_id=_eid()).all()
    toplam = sum(f.toplam for f in faturalar)
    odenen = sum(f.toplam for f in faturalar if f.durum == 'odendi')
    bekleyen = sum(f.toplam for f in faturalar if f.durum == 'bekliyor')
    geciken = sum(f.toplam for f in faturalar if f.durum == 'gecikti')
    return jsonify({'toplam': toplam, 'odenen': odenen, 'bekleyen': bekleyen, 'geciken': geciken, 'adet': len(faturalar)})


@bp.route('/<int:fid>/pdf', methods=['GET'])
@jwt_required()
def pdf(fid):
    f = Fatura.query.filter_by(id=fid, emlakci_id=_eid()).first_or_404()
    from app.models import Emlakci
    emlakci = Emlakci.query.get(_eid())

    from app.services.belge import TurkPDF
    p = TurkPDF()
    p.baslik('FATURA')
    p.set_font('Helvetica', '', 10)
    p.cell(0, 6, f'Fatura No: {f.fatura_no or "-"}', ln=True, align='R')
    p.cell(0, 6, f'Tarih: {f.olusturma.strftime("%d.%m.%Y") if f.olusturma else "-"}', ln=True, align='R')
    p.ln(6)
    p.alt_baslik('SATICI')
    p.satir('Ad', emlakci.ad_soyad)
    p.satir('Acente', emlakci.acente_adi or '-')
    p.satir('Telefon', emlakci.telefon)
    p.bos_satir()
    p.alt_baslik('ALICI')
    p.satir('Ad', f.alici_ad or '-')
    p.satir('Adres', f.alici_adres or '-')
    p.bos_satir()
    p.alt_baslik('KALEMLER')
    for k in (f.kalemler or []):
        p.satir(k.get('aciklama', '-'), f'{k.get("tutar", 0):,.2f} TL'.replace(',', '.'))
    p.bos_satir()
    p.satir('Ara Toplam', f'{f.tutar:,.2f} TL'.replace(',', '.'))
    p.satir(f'KDV (%{f.kdv_oran})', f'{f.kdv_tutar:,.2f} TL'.replace(',', '.'))
    p.set_font('Helvetica', 'B', 12)
    p.satir('GENEL TOPLAM', f'{f.toplam:,.2f} TL'.replace(',', '.'))

    pdf_bytes = p.output()
    return send_file(io.BytesIO(pdf_bytes), mimetype='application/pdf', as_attachment=True,
                     download_name=f'fatura_{f.fatura_no or f.id}.pdf')


def _f(f):
    return {
        'id': f.id, 'fatura_no': f.fatura_no, 'tip': f.tip,
        'alici_ad': f.alici_ad, 'tutar': f.tutar, 'kdv_oran': f.kdv_oran,
        'kdv_tutar': f.kdv_tutar, 'toplam': f.toplam, 'durum': f.durum,
        'kalemler': f.kalemler or [], 'detaylar': f.detaylar or {},
        'vade_tarihi': f.vade_tarihi.isoformat() if f.vade_tarihi else None,
        'odeme_tarihi': f.odeme_tarihi.isoformat() if f.odeme_tarihi else None,
        'olusturma': f.olusturma.isoformat() if f.olusturma else None,
    }
