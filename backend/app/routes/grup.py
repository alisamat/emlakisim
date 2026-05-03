"""
EMLAKÇILAR & GRUP — Dizin + İşbirliği grubu API
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models import Emlakci, Musteri, Mulk
from app.models.grup import EmlakciDizin, Grup, GrupUyelik, GrupBildirim
from app.routes.bildirim import bildirim_olustur

bp = Blueprint('grup', __name__, url_prefix='/api/panel')


def _eid():
    return int(get_jwt_identity())


# ════════ EMLAKÇILAR DİZİNİ ════════

@bp.route('/emlakcilar', methods=['GET'])
@jwt_required()
def emlakci_listesi():
    kayitlar = EmlakciDizin.query.filter_by(ekleyen_id=_eid()).order_by(EmlakciDizin.ad_soyad).all()
    return jsonify({'emlakcilar': [_ed(e) for e in kayitlar]})


@bp.route('/emlakcilar', methods=['POST'])
@jwt_required()
def emlakci_ekle():
    d = request.get_json() or {}
    e = EmlakciDizin(
        ekleyen_id=_eid(), ad_soyad=d.get('ad_soyad', ''),
        telefon=d.get('telefon'), email=d.get('email'),
        adres=d.get('adres'), bolge=d.get('bolge'),
        uzmanlik=d.get('uzmanlik'), acente=d.get('acente'),
        notlar=d.get('notlar'), detaylar=d.get('detaylar', {}),
    )
    db.session.add(e); db.session.commit()
    return jsonify({'emlakci': _ed(e)}), 201


@bp.route('/emlakcilar/<int:eid_p>', methods=['PUT'])
@jwt_required()
def emlakci_guncelle(eid_p):
    e = EmlakciDizin.query.filter_by(id=eid_p, ekleyen_id=_eid()).first_or_404()
    d = request.get_json() or {}
    for f in ['ad_soyad', 'telefon', 'email', 'adres', 'bolge', 'uzmanlik', 'acente', 'notlar']:
        if f in d: setattr(e, f, d[f])
    db.session.commit()
    return jsonify({'emlakci': _ed(e)})


@bp.route('/emlakcilar/<int:eid_p>', methods=['DELETE'])
@jwt_required()
def emlakci_sil(eid_p):
    e = EmlakciDizin.query.filter_by(id=eid_p, ekleyen_id=_eid()).first_or_404()
    db.session.delete(e); db.session.commit()
    return jsonify({'ok': True})


# ════════ GRUP YÖNETİMİ ════════

@bp.route('/gruplar', methods=['GET'])
@jwt_required()
def grup_listesi():
    """Kullanıcının üye olduğu tüm gruplar."""
    eid = _eid()
    uyelikler = GrupUyelik.query.filter_by(emlakci_id=eid, durum='aktif').all()
    gruplar = []
    for u in uyelikler:
        g = Grup.query.get(u.grup_id)
        if g and g.aktif:
            uye_sayisi = GrupUyelik.query.filter_by(grup_id=g.id, durum='aktif').count()
            gruplar.append({
                **_g(g), 'rol': u.rol, 'uye_sayisi': uye_sayisi,
                'portfoy_acik': u.portfoy_acik, 'talep_acik': u.talep_acik,
            })
    return jsonify({'gruplar': gruplar})


@bp.route('/gruplar', methods=['POST'])
@jwt_required()
def grup_kur():
    """Yeni grup kur — kurucu otomatik yönetici+üye."""
    eid = _eid()

    # Max 2 grup kontrolü
    aktif_uyelik = GrupUyelik.query.filter_by(emlakci_id=eid, durum='aktif').count()
    if aktif_uyelik >= 2:
        return jsonify({'message': 'En fazla 2 gruba üye olabilirsiniz'}), 400

    d = request.get_json() or {}
    g = Grup(ad=d.get('ad', ''), slogan=d.get('slogan'), aciklama=d.get('aciklama'), kurucu_id=eid)
    db.session.add(g); db.session.flush()

    # Kurucu = yönetici + üye
    u = GrupUyelik(grup_id=g.id, emlakci_id=eid, rol='yonetici', durum='aktif')
    db.session.add(u)

    # Bildirim
    _grup_bildirim(g.id, eid, 'grup_kuruldu', f'Grup "{g.ad}" kuruldu')

    db.session.commit()
    return jsonify({'grup': _g(g)}), 201


@bp.route('/gruplar/<int:gid>/uye-ekle', methods=['POST'])
@jwt_required()
def gruba_uye_ekle(gid):
    """Gruba üye davet et — bildirim gider, onay bekler."""
    g = Grup.query.filter_by(id=gid, aktif=True).first_or_404()

    # Yönetici kontrolü
    yonetici = GrupUyelik.query.filter_by(grup_id=gid, emlakci_id=_eid(), rol='yonetici', durum='aktif').first()
    if not yonetici:
        return jsonify({'message': 'Bu işlem için yönetici yetkisi gerekli'}), 403

    d = request.get_json() or {}
    hedef_id = d.get('emlakci_id')
    if not hedef_id:
        return jsonify({'message': 'Emlakçı ID gerekli'}), 400

    # Hedef uygulamayı kullanan mı
    hedef = Emlakci.query.filter_by(id=hedef_id, aktif=True).first()
    if not hedef:
        return jsonify({'message': 'Emlakçı bulunamadı veya uygulamayı kullanmıyor'}), 404

    # Max 2 üyelik kontrolü
    aktif_uyelik = GrupUyelik.query.filter_by(emlakci_id=hedef_id, durum='aktif').count()
    if aktif_uyelik >= 2:
        return jsonify({'message': 'Bu emlakçı zaten 2 gruba üye'}), 400

    # Teklif kapalı mı
    from app.models.ayarlar import KullaniciAyar
    ayar = KullaniciAyar.query.filter_by(emlakci_id=hedef_id).first()
    if ayar and ayar.ayarlar and ayar.ayarlar.get('grup_teklif_kapali'):
        return jsonify({'message': 'Bu emlakçı grup tekliflerini kapatmış'}), 400

    # Zaten üye/bekliyor mu
    mevcut = GrupUyelik.query.filter_by(grup_id=gid, emlakci_id=hedef_id).first()
    if mevcut and mevcut.durum in ('aktif', 'bekliyor'):
        return jsonify({'message': 'Bu emlakçı zaten üye veya davet bekliyor'}), 400

    # Üyelik teklifi oluştur
    if mevcut:
        mevcut.durum = 'bekliyor'
    else:
        u = GrupUyelik(grup_id=gid, emlakci_id=hedef_id, rol='uye', durum='bekliyor')
        db.session.add(u)

    # Hedef emlakçıya bildirim
    bildirim_olustur(hedef_id, 'grup',
        f'📩 "{g.ad}" grubuna üyelik davetiniz var',
        f'Kabul etmek için Grup sayfasını ziyaret edin.', link='gruplar')

    db.session.commit()
    return jsonify({'ok': True, 'mesaj': 'Üyelik teklifi gönderildi'})


@bp.route('/gruplar/davet/<int:uyelik_id>', methods=['PUT'])
@jwt_required()
def davet_cevapla(uyelik_id):
    """Üyelik davetini kabul/red."""
    u = GrupUyelik.query.filter_by(id=uyelik_id, emlakci_id=_eid(), durum='bekliyor').first_or_404()
    d = request.get_json() or {}
    kabul = d.get('kabul', False)

    if kabul:
        # Max 2 kontrol
        aktif = GrupUyelik.query.filter_by(emlakci_id=_eid(), durum='aktif').count()
        if aktif >= 2:
            return jsonify({'message': 'En fazla 2 gruba üye olabilirsiniz'}), 400
        u.durum = 'aktif'
        _grup_bildirim(u.grup_id, _eid(), 'uye_girdi', f'{Emlakci.query.get(_eid()).ad_soyad} gruba katıldı')
        bildirim_olustur(_eid(), 'grup', f'✅ "{Grup.query.get(u.grup_id).ad}" grubuna katıldınız',
                        'İlanlarınızı gruba açmak ister misiniz? Grup ayarlarından yapabilirsiniz.', link='gruplar')
    else:
        u.durum = 'reddetti'
        # Red durumunda gruba bilgi gitmez

    db.session.commit()
    return jsonify({'ok': True})


@bp.route('/gruplar/<int:gid>/cik', methods=['POST'])
@jwt_required()
def gruptan_cik(gid):
    """Gruptan çık."""
    u = GrupUyelik.query.filter_by(grup_id=gid, emlakci_id=_eid(), durum='aktif').first_or_404()

    if u.rol == 'yonetici':
        # Başka yönetici var mı
        baska_yonetici = GrupUyelik.query.filter(
            GrupUyelik.grup_id == gid, GrupUyelik.emlakci_id != _eid(),
            GrupUyelik.rol == 'yonetici', GrupUyelik.durum == 'aktif'
        ).first()
        aktif_uye = GrupUyelik.query.filter(
            GrupUyelik.grup_id == gid, GrupUyelik.emlakci_id != _eid(),
            GrupUyelik.durum == 'aktif'
        ).count()
        if aktif_uye > 0 and not baska_yonetici:
            return jsonify({'message': 'Çıkmak için önce başka bir yönetici atayın'}), 400

    u.durum = 'cikti'
    _grup_bildirim(gid, _eid(), 'uye_cikti', f'{Emlakci.query.get(_eid()).ad_soyad} gruptan ayrıldı')

    # Grupta kimse kalmadıysa sil
    kalan = GrupUyelik.query.filter_by(grup_id=gid, durum='aktif').count()
    if kalan == 0:
        g = Grup.query.get(gid)
        if g: g.aktif = False

    db.session.commit()
    return jsonify({'ok': True})


@bp.route('/gruplar/<int:gid>/yonetici-ata', methods=['POST'])
@jwt_required()
def yonetici_ata(gid):
    """Gruba yönetici ata."""
    yonetici = GrupUyelik.query.filter_by(grup_id=gid, emlakci_id=_eid(), rol='yonetici', durum='aktif').first()
    if not yonetici:
        return jsonify({'message': 'Yönetici yetkisi gerekli'}), 403

    d = request.get_json() or {}
    hedef = GrupUyelik.query.filter_by(grup_id=gid, emlakci_id=d.get('emlakci_id'), durum='aktif').first()
    if not hedef:
        return jsonify({'message': 'Üye bulunamadı'}), 404

    hedef.rol = 'yonetici'
    _grup_bildirim(gid, hedef.emlakci_id, 'yonetici_atandi', f'{Emlakci.query.get(hedef.emlakci_id).ad_soyad} yönetici oldu')
    db.session.commit()
    return jsonify({'ok': True})


@bp.route('/gruplar/<int:gid>/uyeler', methods=['GET'])
@jwt_required()
def grup_uyeleri(gid):
    """Grup üye listesi."""
    uyeler = GrupUyelik.query.filter_by(grup_id=gid, durum='aktif').all()
    return jsonify({'uyeler': [{
        'id': u.id, 'emlakci_id': u.emlakci_id,
        'ad_soyad': Emlakci.query.get(u.emlakci_id).ad_soyad if Emlakci.query.get(u.emlakci_id) else '?',
        'rol': u.rol, 'portfoy_acik': u.portfoy_acik, 'talep_acik': u.talep_acik,
    } for u in uyeler]})


@bp.route('/gruplar/<int:gid>/ayarlar', methods=['PUT'])
@jwt_required()
def grup_ayarlar(gid):
    """Kendi portföy/talep paylaşım ayarını güncelle."""
    u = GrupUyelik.query.filter_by(grup_id=gid, emlakci_id=_eid(), durum='aktif').first_or_404()
    d = request.get_json() or {}
    if 'portfoy_acik' in d: u.portfoy_acik = bool(d['portfoy_acik'])
    if 'talep_acik' in d: u.talep_acik = bool(d['talep_acik'])
    db.session.commit()
    return jsonify({'ok': True})


@bp.route('/gruplar/<int:gid>/eslestirme', methods=['GET'])
@jwt_required()
def grup_eslestirme(gid):
    """Grup içi portföy-talep eşleştirme (sadece açık olanlar, kişisel bilgi gizli)."""
    # Üye mi kontrol
    uye = GrupUyelik.query.filter_by(grup_id=gid, emlakci_id=_eid(), durum='aktif').first()
    if not uye:
        return jsonify({'message': 'Üye değilsiniz'}), 403

    # Açık portföyler
    acik_portfoy_uyeler = GrupUyelik.query.filter_by(grup_id=gid, durum='aktif', portfoy_acik=True).all()
    portfoyler = []
    for u in acik_portfoy_uyeler:
        mulkler = Mulk.query.filter_by(emlakci_id=u.emlakci_id, aktif=True).all()
        for m in mulkler:
            # Kişisel bilgi gizle
            portfoyler.append({
                'tip': m.tip, 'islem_turu': m.islem_turu, 'fiyat': m.fiyat,
                'sehir': m.sehir, 'ilce': m.ilce, 'oda_sayisi': m.oda_sayisi,
                'uye_id': u.emlakci_id,  # sadece ID, isim değil
            })

    # Kendi taleplerim (Talep modeli — yeni sistem)
    talepler = []
    try:
        from app.models.talep import Talep
        kendi_talepler = Talep.query.filter_by(emlakci_id=_eid(), durum='aktif', yonu='arayan').all()
        for t in kendi_talepler:
            talepler.append({
                'islem_turu': t.islem_turu, 'butce_min': t.butce_min,
                'butce_max': t.butce_max, 'tercih_oda': t.tercih_oda,
                'tercih_ilce': t.tercih_ilce,
                'uye_id': _eid(),
            })
    except Exception:
        pass

    # Fallback: eski müşteri alanları (talep yoksa)
    if not talepler:
        acik_talep_uyeler = GrupUyelik.query.filter_by(grup_id=gid, emlakci_id=_eid(), durum='aktif', talep_acik=True).all()
        for u in acik_talep_uyeler:
            musteriler = Musteri.query.filter_by(emlakci_id=u.emlakci_id).all()
            for m in musteriler:
                if m.islem_turu:
                    talepler.append({
                        'islem_turu': m.islem_turu, 'butce_min': m.butce_min,
                        'butce_max': m.butce_max,
                        'uye_id': u.emlakci_id,
                    })

    # Eşleştirme: kendi taleplerim × gruptaki başkalarının mülkleri
    eslesimler = []
    for t in talepler:
        for p in portfoyler:
            if t['islem_turu'] == p['islem_turu'] and t['uye_id'] != p['uye_id']:
                if t['butce_max'] and p['fiyat'] and p['fiyat'] <= t['butce_max']:
                    eslesimler.append({
                        'talep_islem': t['islem_turu'],
                        'talep_butce': t['butce_max'],
                        'portfoy_fiyat': p['fiyat'],
                        'portfoy_ilce': p['ilce'],
                        'portfoy_tip': p['tip'],
                        'portfoy_oda': p['oda_sayisi'],
                    })

    return jsonify({
        'portfoy_sayisi': len(portfoyler),
        'talep_sayisi': len(talepler),
        'eslesim_sayisi': len(eslesimler),
        'eslesimler': eslesimler[:20],
    })


@bp.route('/gruplar/davetlerim', methods=['GET'])
@jwt_required()
def davetlerim():
    """Bekleyen grup davetleri."""
    bekleyenler = GrupUyelik.query.filter_by(emlakci_id=_eid(), durum='bekliyor').all()
    return jsonify({'davetler': [{
        'uyelik_id': u.id,
        'grup_id': u.grup_id,
        'grup_ad': Grup.query.get(u.grup_id).ad if Grup.query.get(u.grup_id) else '?',
    } for u in bekleyenler]})


# ── Helpers ──
def _ed(e):
    return {
        'id': e.id, 'ad_soyad': e.ad_soyad, 'telefon': e.telefon,
        'email': e.email, 'adres': e.adres, 'bolge': e.bolge,
        'uzmanlik': e.uzmanlik, 'acente': e.acente, 'notlar': e.notlar,
    }

def _g(g):
    return {
        'id': g.id, 'ad': g.ad, 'slogan': g.slogan,
        'aciklama': g.aciklama, 'kurucu_id': g.kurucu_id,
        'olusturma': g.olusturma.isoformat() if g.olusturma else None,
    }

def _grup_bildirim(grup_id, emlakci_id, tip, mesaj):
    b = GrupBildirim(grup_id=grup_id, emlakci_id=emlakci_id, tip=tip, mesaj=mesaj)
    db.session.add(b)
