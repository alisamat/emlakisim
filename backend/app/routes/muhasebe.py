"""
MUHASEBE — Gelir/gider, cari hesap, OCR fiş okuma API'leri
"""
import base64
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models.muhasebe import GelirGider, Cari, CariHareket
from app.services.ocr import fis_oku
from app.services.banka import banka_excel_import
from datetime import datetime

bp = Blueprint('muhasebe', __name__, url_prefix='/api/panel/muhasebe')


def _eid():
    return int(get_jwt_identity())


# ── Gelir/Gider ──────────────────────────────────────────
@bp.route('/gelir-gider', methods=['GET'])
@jwt_required()
def gelir_gider_listesi():
    kayitlar = GelirGider.query.filter_by(emlakci_id=_eid()).order_by(GelirGider.tarih.desc()).limit(100).all()
    return jsonify({'kayitlar': [_gg(k) for k in kayitlar]})


@bp.route('/gelir-gider', methods=['POST'])
@jwt_required()
def gelir_gider_ekle():
    d = request.get_json() or {}
    k = GelirGider(
        emlakci_id=_eid(),
        tip=d.get('tip', 'gelir'),
        kategori=d.get('kategori'),
        tutar=float(d.get('tutar', 0)),
        aciklama=d.get('aciklama'),
        musteri_id=d.get('musteri_id'),
        mulk_id=d.get('mulk_id'),
        detaylar=d.get('detaylar', {}),
    )
    if d.get('tarih'):
        try: k.tarih = datetime.fromisoformat(d['tarih'])
        except: pass
    db.session.add(k); db.session.commit()
    return jsonify({'kayit': _gg(k)}), 201


@bp.route('/gelir-gider/<int:kid>', methods=['DELETE'])
@jwt_required()
def gelir_gider_sil(kid):
    k = GelirGider.query.filter_by(id=kid, emlakci_id=_eid()).first_or_404()
    db.session.delete(k); db.session.commit()
    return jsonify({'ok': True})


@bp.route('/ozet', methods=['GET'])
@jwt_required()
def ozet():
    kayitlar = GelirGider.query.filter_by(emlakci_id=_eid()).all()
    gelir = sum(k.tutar for k in kayitlar if k.tip == 'gelir')
    gider = sum(k.tutar for k in kayitlar if k.tip == 'gider')
    return jsonify({'gelir': gelir, 'gider': gider, 'net': gelir - gider, 'kayit_sayisi': len(kayitlar)})


# ── Cari ─────────────────────────────────────────────────
@bp.route('/cariler', methods=['GET'])
@jwt_required()
def cari_listesi():
    cariler = Cari.query.filter_by(emlakci_id=_eid()).order_by(Cari.olusturma.desc()).all()
    return jsonify({'cariler': [_cari(c) for c in cariler]})


@bp.route('/cariler', methods=['POST'])
@jwt_required()
def cari_ekle():
    d = request.get_json() or {}
    c = Cari(
        emlakci_id=_eid(),
        ad=d.get('ad', ''),
        tip=d.get('tip', 'musteri'),
        telefon=d.get('telefon'),
        detaylar=d.get('detaylar', {}),
    )
    db.session.add(c); db.session.commit()
    return jsonify({'cari': _cari(c)}), 201


@bp.route('/cariler/<int:cid>/hareket', methods=['POST'])
@jwt_required()
def cari_hareket_ekle(cid):
    c = Cari.query.filter_by(id=cid, emlakci_id=_eid()).first_or_404()
    d = request.get_json() or {}
    tutar = float(d.get('tutar', 0))
    tip = d.get('tip', 'borc')

    h = CariHareket(cari_id=cid, tip=tip, tutar=tutar, aciklama=d.get('aciklama'))
    if tip == 'alacak':
        c.bakiye += tutar
    else:
        c.bakiye -= tutar

    db.session.add(h); db.session.commit()
    return jsonify({'hareket': _ch(h), 'bakiye': c.bakiye}), 201


@bp.route('/cariler/<int:cid>', methods=['GET'])
@jwt_required()
def cari_detay(cid):
    c = Cari.query.filter_by(id=cid, emlakci_id=_eid()).first_or_404()
    hareketler = CariHareket.query.filter_by(cari_id=cid).order_by(CariHareket.tarih.desc()).all()
    return jsonify({'cari': _cari(c), 'hareketler': [_ch(h) for h in hareketler]})


# ── OCR Fiş Okuma ────────────────────────────────────────
@bp.route('/fis-oku', methods=['POST'])
@jwt_required()
def fis_oku_endpoint():
    """Fiş/fatura fotoğrafını OCR ile oku → gider kaydı öner."""
    if 'image' in request.files:
        img = request.files['image'].read()
        img_b64 = base64.b64encode(img).decode()
    elif request.is_json and request.json.get('image_base64'):
        img_b64 = request.json['image_base64']
    else:
        return jsonify({'message': 'Fotoğraf gerekli'}), 400

    sonuc = fis_oku(img_b64)

    if sonuc.get('hata'):
        return jsonify({'message': sonuc['hata']}), 500

    return jsonify({
        'ocr': sonuc,
        'oneri': {
            'tip': 'gider',
            'kategori': _kategori_esle(sonuc.get('kategori', '')),
            'tutar': sonuc.get('toplam', 0),
            'aciklama': f"{sonuc.get('firma', '')} - {sonuc.get('belge_tipi', 'fiş')}",
            'tarih': sonuc.get('tarih'),
        }
    })


@bp.route('/fis-kaydet', methods=['POST'])
@jwt_required()
def fis_kaydet():
    """OCR sonucunu onaylayıp gider olarak kaydet."""
    d = request.get_json() or {}
    k = GelirGider(
        emlakci_id=_eid(),
        tip='gider',
        kategori=d.get('kategori', 'Diğer Gider'),
        tutar=float(d.get('tutar', 0)),
        aciklama=d.get('aciklama', ''),
        detaylar={
            'ocr_model': d.get('ocr_model'),
            'firma': d.get('firma'),
            'kdv_tutar': d.get('kdv_tutar'),
            'kdv_oran': d.get('kdv_oran'),
            'kalemler': d.get('kalemler', []),
            'guven_skoru': d.get('guven_skoru'),
        },
    )
    if d.get('tarih'):
        try:
            k.tarih = datetime.strptime(d['tarih'], '%d.%m.%Y')
        except:
            pass
    db.session.add(k)
    db.session.commit()
    return jsonify({'kayit': _gg(k)}), 201


def _kategori_esle(ocr_kategori):
    eslesme = {
        'ofis': 'Ofis Kirası', 'ulaşım': 'Ulaşım', 'yemek': 'Yemek',
        'fatura': 'Fatura', 'reklam': 'Reklam', 'diğer': 'Diğer Gider',
    }
    return eslesme.get(ocr_kategori, 'Diğer Gider')


# ── Banka Excel Import ───────────────────────────────────
@bp.route('/banka-import', methods=['POST'])
@jwt_required()
def banka_import():
    """Banka hesap özeti Excel'den masraf çıkar."""
    if 'file' not in request.files:
        return jsonify({'message': 'Excel dosyası gerekli'}), 400
    data = request.files['file'].read()
    sonuc = banka_excel_import(_eid(), data)
    return jsonify(sonuc), 201 if not sonuc.get('hata') else 400


# ── Muhasebe Raporu ──────────────────────────────────────
@bp.route('/rapor', methods=['GET'])
@jwt_required()
def muhasebe_raporu():
    """Aylık/yıllık muhasebe raporu."""
    kayitlar = GelirGider.query.filter_by(emlakci_id=_eid()).order_by(GelirGider.tarih).all()

    aylik = {}
    for k in kayitlar:
        if not k.tarih:
            continue
        ay_key = k.tarih.strftime('%Y-%m')
        if ay_key not in aylik:
            aylik[ay_key] = {'gelir': 0, 'gider': 0}
        aylik[ay_key][k.tip] += k.tutar

    rapor = []
    for ay, veri in sorted(aylik.items()):
        rapor.append({
            'ay': ay,
            'gelir': round(veri['gelir'], 2),
            'gider': round(veri['gider'], 2),
            'kar': round(veri['gelir'] - veri['gider'], 2),
        })

    return jsonify({'rapor': rapor})


# ── Serializers ──────────────────────────────────────────
def _gg(k):
    return {
        'id': k.id, 'tip': k.tip, 'kategori': k.kategori,
        'tutar': k.tutar, 'aciklama': k.aciklama,
        'tarih': k.tarih.isoformat() if k.tarih else None,
        'detaylar': k.detaylar or {},
    }

def _cari(c):
    return {
        'id': c.id, 'ad': c.ad, 'tip': c.tip,
        'telefon': c.telefon, 'bakiye': c.bakiye,
        'detaylar': c.detaylar or {},
    }

def _ch(h):
    return {
        'id': h.id, 'tip': h.tip, 'tutar': h.tutar,
        'aciklama': h.aciklama,
        'tarih': h.tarih.isoformat() if h.tarih else None,
    }
