"""
ADMIN — Platform yönetimi, fiyatlandırma, kullanıcı dashboard
"""
import os
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models import Emlakci, IslemLog
from app.services.kredi import KREDI_TABLOSU

bp = Blueprint('admin', __name__, url_prefix='/api/admin')


# ── Fiyatlandırma ────────────────────────────────────────
@bp.route('/fiyatlandirma', methods=['GET'])
@jwt_required()
def fiyatlandirma_getir():
    """Mevcut kredi fiyatlandırma tablosunu getir."""
    from app.services.kuveytturk import paketleri_getir
    pktler, kur = paketleri_getir()
    paketler = [{'id': k, 'ad': v['aciklama'], 'kredi': v['kredi'], 'usd': v['fiyat_usd'], 'tl': v['fiyat_tl']} for k, v in pktler.items()]
    return jsonify({
        'kredi_tablosu': KREDI_TABLOSU,
        'paketler': paketler,
        'kur': kur,
        'kdv_oran': 20,
    })


@bp.route('/fiyatlandirma', methods=['PUT'])
@jwt_required()
def fiyatlandirma_guncelle():
    """Kredi fiyatlandırma tablosunu güncelle (memory only — restart'ta sıfırlanır)."""
    d = request.get_json() or {}
    if 'kredi_tablosu' in d:
        for k, v in d['kredi_tablosu'].items():
            if k in KREDI_TABLOSU:
                KREDI_TABLOSU[k] = float(v)
    return jsonify({'ok': True, 'kredi_tablosu': KREDI_TABLOSU})


# ── Platform Dashboard ───────────────────────────────────
@bp.route('/dashboard', methods=['GET'])
@jwt_required()
def platform_dashboard():
    """Platform geneli istatistikler."""
    from app.models import Musteri, Mulk
    from app.models.lead import Lead
    from app.models.egitim import DiyalogKayit

    toplam_kullanici = Emlakci.query.filter_by(aktif=True).count()
    toplam_musteri = Musteri.query.count()
    toplam_mulk = Mulk.query.filter_by(aktif=True).count()
    toplam_lead = Lead.query.count()
    toplam_diyalog = DiyalogKayit.query.count()
    toplam_islem = IslemLog.query.count()

    # Toplam kredi kullanımı
    from sqlalchemy import func
    toplam_kredi = db.session.query(func.sum(IslemLog.kredi_tutar)).scalar() or 0
    toplam_usd = db.session.query(func.sum(IslemLog.maliyet_usd)).scalar() or 0

    return jsonify({
        'kullanicilar': toplam_kullanici,
        'musteriler': toplam_musteri,
        'mulkler': toplam_mulk,
        'leadler': toplam_lead,
        'diyaloglar': toplam_diyalog,
        'islemler': toplam_islem,
        'toplam_kredi_kullanim': round(toplam_kredi, 2),
        'toplam_ai_maliyet_usd': round(toplam_usd, 6),
    })


# ── Kullanıcı Yönetimi ──────────────────────────────────
@bp.route('/kullanicilar', methods=['GET'])
@jwt_required()
def kullanici_listesi():
    kullanicilar = Emlakci.query.order_by(Emlakci.olusturma.desc()).all()
    return jsonify({'kullanicilar': [{
        'id': e.id, 'ad_soyad': e.ad_soyad, 'email': e.email,
        'telefon': e.telefon, 'kredi': e.kredi, 'aktif': e.aktif,
        'olusturma': e.olusturma.isoformat() if e.olusturma else None,
    } for e in kullanicilar]})


@bp.route('/kullanicilar/<int:uid>/kredi', methods=['PUT'])
@jwt_required()
def kredi_ekle(uid):
    """Kullanıcıya kredi ekle (admin)."""
    e = Emlakci.query.get_or_404(uid)
    d = request.get_json() or {}
    miktar = float(d.get('miktar', 0))
    e.kredi = (e.kredi or 0) + miktar
    # Son kullanma tarihini 1 yıl uzat
    from datetime import datetime, timedelta
    e.kredi_son_kullanma = datetime.utcnow() + timedelta(days=366)
    db.session.commit()

    # İşlem log
    log = IslemLog(emlakci_id=uid, islem_tipi='kredi_yukleme',
                   kredi_tutar=miktar, aciklama=f'Admin kredi yükleme: {miktar}')
    db.session.add(log); db.session.commit()

    return jsonify({'ok': True, 'yeni_kredi': e.kredi, 'son_kullanma': e.kredi_son_kullanma.isoformat()})


# ── Platform Faturaları ──────────────────────────────────
@bp.route('/fatura-kes', methods=['POST'])
@jwt_required()
def fatura_kes():
    """Platform faturaları — kullanıcıya fatura kes."""
    d = request.get_json() or {}
    from app.models.fatura import Fatura
    from datetime import datetime

    f = Fatura(
        emlakci_id=d.get('kullanici_id'),
        fatura_no=f'PLT-{datetime.now().strftime("%Y%m%d%H%M")}',
        tip='platform',
        alici_ad=d.get('alici_ad', ''),
        alici_adres=d.get('alici_adres', ''),
        tutar=float(d.get('tutar', 0)),
        kdv_oran=20,
        kdv_tutar=round(float(d.get('tutar', 0)) * 0.2, 2),
        toplam=round(float(d.get('tutar', 0)) * 1.2, 2),
        kalemler=d.get('kalemler', [{'aciklama': d.get('paket', 'Kredi Paketi'), 'tutar': d.get('tutar', 0)}]),
        durum='odendi',
    )
    db.session.add(f); db.session.commit()
    return jsonify({'ok': True, 'fatura_no': f.fatura_no}), 201
