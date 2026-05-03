"""
PANEL SOHBET — Uygulama içi AI sohbet API + kredi sistemi
"""
import os
import logging
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models import db, Emlakci, PanelSohbet, PanelMesaj
from app.services.asistan import _ai_cevap, _sistem_prompt, _normalize, _pattern_isle, _komut_calistir, _openai_with_functions, _bekleyen_isle, _navigasyon_kontrol, _baglam_filtre
from app.services.kredi import kredi_kontrol, kredi_dus, KREDI_TABLOSU
from app.services.egitim import diyalog_kaydet, ogrenilen_pattern_esle

logger = logging.getLogger(__name__)
bp = Blueprint('sohbet', __name__, url_prefix='/api/panel')
_panel_sessions: dict[int, dict] = {}


@bp.route('/sohbet', methods=['POST'])
@jwt_required()
def mesaj_gonder():
    emlakci = Emlakci.query.get(get_jwt_identity())
    if not emlakci:
        return jsonify({'message': 'Kullanıcı bulunamadı'}), 404

    data = request.get_json() or {}
    metin = (data.get('mesaj') or '').strip()
    if not metin:
        return jsonify({'message': 'Mesaj boş olamaz'}), 400

    sohbet_id = data.get('sohbet_id')

    # Sohbeti bul veya oluştur
    if sohbet_id:
        sohbet = PanelSohbet.query.filter_by(id=sohbet_id, emlakci_id=emlakci.id).first()
        if not sohbet:
            return jsonify({'message': 'Sohbet bulunamadı'}), 404
    else:
        sohbet = PanelSohbet(emlakci_id=emlakci.id, baslik=metin[:50])
        db.session.add(sohbet)
        db.session.flush()

    # Kullanıcı mesajını kaydet
    db.session.add(PanelMesaj(sohbet_id=sohbet.id, rol='user', icerik=metin))

    # Geçmiş mesajları al
    gecmis = [{'role': m.rol, 'content': m.icerik}
              for m in PanelMesaj.query.filter_by(sohbet_id=sohbet.id).order_by(PanelMesaj.olusturma).all()]
    if len(gecmis) > 20:
        gecmis = gecmis[-20:]

    session = _panel_sessions.setdefault(emlakci.id, {})

    metin_norm = _normalize(metin)
    kullanilan_model = None
    nav_tab = None  # Sayfa navigasyonu

    # 0. Navigasyon kontrolü — "ayarlara git", "müşterileri aç" vb.
    nav = _navigasyon_kontrol(metin_norm)
    if nav:
        nav_tab, cevap = nav
        kullanilan_model = 'navigasyon'
        # Mesajı kaydet ve direkt dön
        db.session.add(PanelMesaj(sohbet_id=sohbet.id, rol='assistant', icerik=cevap))
        db.session.commit()
        return jsonify({
            'cevap': cevap,
            'kredi_kalan': emlakci.kredi,
            'sohbet_id': sohbet.id,
            'tab': nav_tab,
        })

    # 0.5. Bağlam filtresi — "bunlardan sıcak olanları", "1. numarayı göster"
    baglam = _baglam_filtre(metin_norm, emlakci, session)
    if baglam:
        cevap = baglam
        kullanilan_model = 'baglam_filtre'
        db.session.add(PanelMesaj(sohbet_id=sohbet.id, rol='assistant', icerik=cevap))
        db.session.commit()
        return jsonify({'cevap': cevap, 'kredi_kalan': emlakci.kredi, 'sohbet_id': sohbet.id})

    # 1. BAĞLAMSAL KARAR MOTORU
    from app.services.karar import baglam_karar
    try:
        karar = baglam_karar(emlakci.id, metin, metin_norm)
    except Exception:
        karar = None

    if karar:
        komut_adi, args = karar
        cevap = args.get('mesaj', 'İşlem tamamlandı.')
        if komut_adi == 'eslestirme_musteri':
            from app.services.eslestirme import eslesdir
            sonuclar = eslesdir(emlakci.id, musteri_id=args.get('musteri_id'), limit=5)
            if sonuclar:
                satirlar = [f'• {s["baslik"]} — {s["fiyat_str"]} (%{s["puan"]})' for s in sonuclar]
                cevap = f'🔗 *Uygun mülkler:*\n\n' + '\n'.join(satirlar)
            else:
                cevap = '📭 Uygun mülk bulunamadı.'
        kullanilan_model = 'baglam'
        kredi_dus(emlakci, komut_adi, aciklama=metin[:100], model='baglam')

    # 2. Minimal pattern (selamlama, döviz, kredi — bedava)
    elif _pattern_isle(metin_norm, emlakci, metin):
        komut = _pattern_isle(metin_norm, emlakci, metin)
        sonuc = _komut_calistir(komut, emlakci, metin, session)
        if isinstance(sonuc, tuple):
            cevap, nav_tab = sonuc
        else:
            cevap = sonuc
        if komut == 'kredi_panel':
            nav_tab = 'kredi'
        kredi_dus(emlakci, komut, aciklama=metin[:100], model='pattern')
        kullanilan_model = 'pattern'

    # 3. Embedding intent (neredeyse bedava, doğru eşleşme)
    else:
        from app.services.intent import intent_bul
        # Kısa mesajlarda bağlam ekle — "sayfayı aç" → önceki mesajdan ne sayfası?
        intent_metin = metin
        if len(metin.split()) <= 4 and len(gecmis) >= 2:
            onceki = gecmis[-2].get('content', '') if gecmis[-2].get('role') == 'user' else ''
            if onceki:
                intent_metin = f'{onceki} {metin}'
        intent_sonuc = intent_bul(intent_metin)
        if intent_sonuc:
            intent_komut, intent_skor = intent_sonuc
            if intent_komut == 'kredi_panel':
                nav_tab = 'kredi'
                cevap = '💎 Kredi paneli açılıyor...'
            else:
                sonuc = _komut_calistir(intent_komut, emlakci, metin, session)
                if isinstance(sonuc, tuple):
                    cevap, nav_tab = sonuc
                else:
                    cevap = sonuc
            kredi_dus(emlakci, intent_komut, aciklama=f'intent({intent_skor:.2f}): {metin[:80]}', model='intent')
            kullanilan_model = 'intent'

        # 4. AI function calling (son çare — her şeyi anlar)
        else:
            if not kredi_kontrol(emlakci, 1):
                cevap = '⚠️ *Krediniz yetersiz.*\n\nAI asistan kullanmak için kredi gereklidir.\nMevcut kredi: *0*'
                db.session.add(PanelMesaj(sohbet_id=sohbet.id, rol='assistant', icerik=cevap))
                db.session.commit()
                return jsonify({
                    'cevap': cevap,
                    'kredi_kalan': emlakci.kredi,
                    'sohbet_id': sohbet.id,
                    'kredi_yetersiz': True,
                }), 200

            sistem = _sistem_prompt(emlakci, metin)
            try:
                openai_key = os.environ.get('OPENAI_API_KEY', '')
                gemini_key = os.environ.get('GEMINI_API_KEY', '')
                if openai_key:
                    from app.services.asistan import _openai_with_functions as owf
                    ai_sonuc = owf(openai_key, sistem, gecmis, emlakci)
                    if isinstance(ai_sonuc, tuple):
                        cevap, nav_tab = ai_sonuc
                    else:
                        cevap = ai_sonuc
                    kullanilan_model = 'openai'
                elif gemini_key:
                    from app.services.asistan import _gemini_with_functions as gwf
                    try:
                        ai_sonuc = gwf(gemini_key, sistem, gecmis, emlakci)
                        if isinstance(ai_sonuc, tuple):
                            cevap, nav_tab = ai_sonuc
                        else:
                            cevap = ai_sonuc
                        kullanilan_model = 'gemini'
                    except Exception:
                        cevap = _ai_cevap(metin, gecmis, sistem)
                        kullanilan_model = 'gemini'
                else:
                    cevap = _ai_cevap(metin, gecmis, sistem)
                    kullanilan_model = 'claude'
            except Exception as e:
                logger.error(f'[Sohbet] AI hatası: {e}')
                cevap = 'Bir hata oluştu, lütfen tekrar deneyin.'
                kullanilan_model = 'hata'

            # AI kredi düş
            kredi_dus(emlakci, 'ai_sohbet', aciklama=metin[:100], model=kullanilan_model)

    # Zeka motoru — cevabı zenginleştir
    try:
        from app.services.zeka import mesaj_zenginlestir
        cevap = mesaj_zenginlestir(emlakci, metin, cevap)
    except Exception:
        pass

    # Diyaloğu kaydet (eğitim verisi)
    islem_adi = 'ai_sohbet'
    if kullanilan_model == 'pattern':
        islem_adi = 'pattern'
    elif kullanilan_model == 'ogrenilen':
        islem_adi = 'ogrenilen'
    diyalog_kaydet(emlakci.id, metin, metin_norm, islem_adi, model=kullanilan_model)

    # Konuşma özetini uzun dönem hafızaya kaydet
    try:
        from app.services.hafiza import konusma_ozeti_kaydet
        konusma_ozeti_kaydet(emlakci.id, gecmis)
    except Exception:
        pass

    # Asistan mesajını kaydet
    db.session.add(PanelMesaj(sohbet_id=sohbet.id, rol='assistant', icerik=cevap))
    db.session.commit()

    resp = {
        'cevap': cevap,
        'kredi_kalan': emlakci.kredi,
        'sohbet_id': sohbet.id,
    }
    if nav_tab:
        resp['tab'] = nav_tab
    return jsonify(resp)


@bp.route('/sohbetler', methods=['GET'])
@jwt_required()
def sohbet_listesi():
    emlakci_id = get_jwt_identity()
    sohbetler = PanelSohbet.query.filter_by(emlakci_id=emlakci_id)\
        .order_by(PanelSohbet.guncelleme.desc()).limit(50).all()
    return jsonify({
        'sohbetler': [{
            'id': s.id,
            'baslik': s.baslik,
            'olusturma': s.olusturma.isoformat(),
        } for s in sohbetler]
    })


@bp.route('/sohbetler/<int:sid>', methods=['GET'])
@jwt_required()
def sohbet_detay(sid):
    emlakci_id = get_jwt_identity()
    sohbet = PanelSohbet.query.filter_by(id=sid, emlakci_id=emlakci_id).first()
    if not sohbet:
        return jsonify({'message': 'Sohbet bulunamadı'}), 404
    return jsonify({
        'mesajlar': [{
            'rol': m.rol,
            'icerik': m.icerik,
            'olusturma': m.olusturma.isoformat(),
        } for m in sohbet.mesajlar]
    })


@bp.route('/sohbetler/export', methods=['GET'])
@jwt_required()
def sohbet_export():
    """Tüm sohbet geçmişini JSON olarak export et."""
    emlakci_id = get_jwt_identity()
    sohbetler = PanelSohbet.query.filter_by(emlakci_id=emlakci_id).order_by(PanelSohbet.olusturma).all()
    data = []
    for s in sohbetler:
        mesajlar = PanelMesaj.query.filter_by(sohbet_id=s.id).order_by(PanelMesaj.olusturma).all()
        data.append({
            'baslik': s.baslik,
            'tarih': s.olusturma.isoformat() if s.olusturma else None,
            'mesajlar': [{'rol': m.rol, 'icerik': m.icerik, 'tarih': m.olusturma.isoformat() if m.olusturma else None} for m in mesajlar],
        })
    return jsonify({'sohbetler': data, 'toplam': len(data)})


@bp.route('/sohbetler/<int:sid>', methods=['DELETE'])
@jwt_required()
def sohbet_sil(sid):
    emlakci_id = get_jwt_identity()
    sohbet = PanelSohbet.query.filter_by(id=sid, emlakci_id=emlakci_id).first()
    if not sohbet:
        return jsonify({'message': 'Sohbet bulunamadı'}), 404
    PanelMesaj.query.filter_by(sohbet_id=sid).delete()
    db.session.delete(sohbet)
    db.session.commit()
    return jsonify({'ok': True})
