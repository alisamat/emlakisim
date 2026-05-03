"""
INTENT SERVİSİ — Embedding tabanlı komut eşleştirme
Pattern matching yerine semantik benzerlik ile doğru komutu bulur.

Akış:
1. Komut açıklamaları bir kez embedding'e çevrilir (cache'lenir)
2. Kullanıcı mesajı gelince embedding'i alınır
3. Cosine similarity ile en yakın komut bulunur
4. Threshold üstündeyse komut çalışır, altındaysa AI'a gider
"""
import os
import json
import logging
import numpy as np
import requests
from datetime import datetime

logger = logging.getLogger(__name__)

# Komut tanımları — her biri bir "intent"
# key: komut adı, value: açıklama (Türkçe, doğal dil)
INTENT_TANIMLARI = {
    # ═══ SADECE OKUMA / LİSTELEME / SORGULAMA ═══
    # Yazma komutları (ekle/sil/güncelle) → AI function calling çözsün

    # Müşteri
    'musteri_liste': 'müşteri listele göster müşterilerim kimler kaç müşterim var tüm müşteriler',
    'musteri_ara': 'müşterilerde ara bul isimle müşteri ara telefon ile ara müşteri var mı',
    # Portföy
    'mulk_liste': 'portföy listele mülkleri göster ilanlarım kaç mülk var portföyüm kiralık satılık mülkler',
    'mulk_ara': 'portföyde ara mülk bul daire ara lokasyon ile ara ilçede mülk',
    # Rapor
    'rapor': 'rapor özet genel durum nasıl gidiyor ne durumda genel bakış istatistik durum raporu',
    'bugun_ozet': 'bugün ne var günlük plan program bugünkü görevler bugünkü işler',
    # Görev
    'gorev_liste': 'görevleri listele görevlerim ne var yapılacaklar aktif görevler görev listesi',
    # Not
    'not_liste': 'notlar notları göster listele notlarım not listesi kayıtlı notlar',
    'hatirlatma_liste': 'hatırlatmalar ne var neyi unutmamam lazım hatırlatma listesi',
    # Muhasebe
    'muhasebe_rapor': 'gelir gider kar zarar muhasebe ne kadar kazandım harcadım muhasebe raporu mali durum',
    'cari_rapor': 'cari hesap alacak borç ne kadar borcum var cari durum',
    # Fatura
    'fatura_liste': 'fatura listele göster son faturalar fatura listesi',
    # Eşleştirme
    'eslestirme': 'eşleştir eşleştirme uygun mülk bul müşteriye uygun kim uygun portföy müşteri eşleşme',
    # Hava
    'hava_durumu_cmd': 'hava durumu hava nasıl yarın hava yağmur yağacak mı gösterim için hava uygun mu dışarısı nasıl',
    # Haber
    'haber_cmd': 'emlak haberleri sektör haberleri piyasa ne oldu son gelişmeler sektörde neler oluyor',
    # QR
    'qr_cmd': 'QR kod oluştur portföy QR barkod broşüre QR',
    'qr_kartvizit_cmd': 'kartvizit QR kodu vCard kartvizit barkod',
    # Web
    'web_sayfa_link': 'web sayfamın linki sayfam portföy linki müşteriye paylaşım linki web adresim',
    # Yedek
    'yedek_durum': 'yedekleme ne zaman yedek aldım son yedek yedekleme durumu backup',
    # Excel
    'portfoy_excel': 'portföy excel indir mülk listesi excel ver portföyü indir',
    'musteri_excel': 'müşteri excel indir müşteri listesi excel ver müşterileri indir',
    'tum_excel': 'tüm veriyi excel indir tüm veri export her şeyi indir tüm verileri indir',
    'tum_zip': 'zip indir tüm veri zip export zip olarak indir',
    # Tahmin
    'satici_tahmin': 'satıcı tahmin kimin satma ihtimali yüksek müşteri ciddi mi analiz tahmin',
    'isi_haritasi': 'ısı haritası ilçe analiz piyasa sıcak bölge pazar analizi bölge analizi',
    # Performans
    'performans': 'performans KPI verimlilik nasıl gidiyorum performans raporu',
    'strateji': 'strateji öneri tavsiye ne yapmalıyım yol haritası akıllı öneri',
    # Yasal
    'yasal_bilgi': 'yasal durum hukuki ipotek haciz iskan kontrol yasal risk',
    'piyasa_bilgi': 'piyasa değer analiz rapor karşılaştır m2 fiyat piyasa değeri metrekare fiyat',
    'surec_ozet_cmd': 'süreç durum ne durumda süreç takip süreç özeti',
    # Grup
    'grup_liste': 'gruplarım grup listele gruplar neler grup listesi',
    'grup_uyeleri': 'grup üyeleri kimler var üye listesi',
    # Emlakçı dizini
    'emlakci_liste': 'emlakçı listele dizin rehber göster emlakçı rehberi emlakçılar',
}

# Cache
_embedding_cache = {}  # {komut: embedding_vector}
_cache_zamani = None


def _embedding_al(metin):
    """OpenAI embedding API ile vektör al."""
    api_key = os.environ.get('OPENAI_API_KEY', '')
    if not api_key:
        return None

    try:
        r = requests.post('https://api.openai.com/v1/embeddings', headers={
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json',
        }, json={
            'model': 'text-embedding-3-small',
            'input': metin,
        }, timeout=5)
        data = r.json()
        return np.array(data['data'][0]['embedding'])
    except Exception as e:
        logger.error(f'[Intent] Embedding hata: {e}')
        return None


def _komut_embeddingler_yukle():
    """Komut açıklamalarının embedding'lerini hesapla ve cache'le."""
    global _embedding_cache, _cache_zamani

    # 6 saatte bir yenile (intent tanımları değişebilir)
    if _cache_zamani and (datetime.utcnow() - _cache_zamani).seconds < 21600 and _embedding_cache:
        return

    api_key = os.environ.get('OPENAI_API_KEY', '')
    if not api_key:
        return

    try:
        # Toplu embedding al (tek API çağrısı — çok ucuz)
        metinler = list(INTENT_TANIMLARI.values())
        komutlar = list(INTENT_TANIMLARI.keys())

        r = requests.post('https://api.openai.com/v1/embeddings', headers={
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json',
        }, json={
            'model': 'text-embedding-3-small',
            'input': metinler,
        }, timeout=15)
        data = r.json()

        for i, emb in enumerate(data['data']):
            _embedding_cache[komutlar[i]] = np.array(emb['embedding'])

        _cache_zamani = datetime.utcnow()
        logger.info(f'[Intent] {len(_embedding_cache)} komut embedding yüklendi')
    except Exception as e:
        logger.error(f'[Intent] Toplu embedding hata: {e}')


def _cosine_similarity(a, b):
    """İki vektör arası cosine benzerliği."""
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))


def intent_bul(metin, threshold=0.45):
    """
    Kullanıcı mesajından intent bul.

    Returns:
        (komut_adi, benzerlik_skoru) veya None
    """
    # Embedding cache yükle
    _komut_embeddingler_yukle()

    if not _embedding_cache:
        return None

    # Kullanıcı mesajının embedding'ini al
    kullanici_emb = _embedding_al(metin)
    if kullanici_emb is None:
        return None

    # En yakın komutu bul
    en_iyi_komut = None
    en_iyi_skor = 0

    for komut, komut_emb in _embedding_cache.items():
        skor = _cosine_similarity(kullanici_emb, komut_emb)
        if skor > en_iyi_skor:
            en_iyi_skor = skor
            en_iyi_komut = komut

    if en_iyi_skor >= threshold:
        logger.info(f'[Intent] "{metin[:50]}" → {en_iyi_komut} (skor: {en_iyi_skor:.3f})')
        return en_iyi_komut, en_iyi_skor

    logger.info(f'[Intent] "{metin[:50]}" → threshold altı (en iyi: {en_iyi_komut} {en_iyi_skor:.3f})')
    return None
