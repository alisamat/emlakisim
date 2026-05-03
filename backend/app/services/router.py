"""
SEMANTIC ROUTER — LLM çağırmadan kategori belirleme
Embedding tabanlı yönlendirme: ~100ms, $0.0000004/mesaj

Akış:
1. Kullanıcı mesajı → embedding
2. Önceden hesaplanmış kategori embedding'leriyle karşılaştır
3. En yakın kategori(leri) döndür
4. Sadece o kategorinin tool'ları LLM'e gönderilir
"""
import os
import logging
import numpy as np
import requests
from datetime import datetime

logger = logging.getLogger(__name__)

# Kategori tanımları — her biri örnek cümleler içerir
KATEGORILER = {
    'musteri': {
        'ornekler': [
            'müşteri ekle kaydet yeni müşteri oluştur',
            'müşteri listele göster müşterilerim kimler',
            'müşterilerde ara bul isim telefon ile',
            'müşteri analiz ciddi mi doğum günü',
            'müşteriye uygun mülk eşleşme bul',
        ],
    },
    'mulk': {
        'ornekler': [
            'mülk ekle ilan portföye kaydet yeni daire villa',
            'portföy listele mülkler göster ilanlarım',
            'portföyde ara mülk bul kiralık satılık daire',
            'elimizde ne var portföydeki mülkler',
        ],
    },
    'eslestirme': {
        'ornekler': [
            'eşleştirme tablosu eşleştir müşteri mülk uygun',
            'kim hangi mülke uygun çapraz eşleşme',
        ],
    },
    'finans': {
        'ornekler': [
            'fatura kes oluştur fatura listele',
            'gelir gider kar zarar muhasebe rapor',
            'cari hesap alacak borç bakiye',
            'komisyon hesapla tapu masrafı vergi',
            'kira vergisi ROI getiri hesapla',
            'geçen ay bu ay gelir gider dönem',
        ],
    },
    'planlama': {
        'ornekler': [
            'görev ekle toplantı randevu hatırlatma planla',
            'görevleri listele bugün ne var program plan',
            'görev tamamla iptal güncelle',
            'yarın sabah öğleden sonra haftaya takvim',
        ],
    },
    'not': {
        'ornekler': [
            'not ekle kaydet yaz not al',
            'notları göster listele notlarım',
            'not ara bul gösterim notu sesli not',
            'notu göreve dönüştür',
            'unutma hatırla aklında tut',
        ],
    },
    'iletisim': {
        'ornekler': [
            'WhatsApp mesaj gönder yaz müşteriye haber ver',
            'toplu mesaj gönder tüm müşterilere',
            'gösterim geri bildirim anket gönder',
            'Ahmet beye yaz mesaj at',
        ],
    },
    'teklif': {
        'ornekler': [
            'teklif geldi teklif kaydet pazarlık',
            'teklif listele geçmişi göster',
            'satış kapandı komisyon fatura süreç başlat',
            'müşteri teklif etti kabul red karşı teklif',
        ],
    },
    'analiz': {
        'ornekler': [
            'mahalle analiz bölge puan güvenlik ulaşım',
            'satıcı tahmin kimin satma ihtimali',
            'ısı haritası ilçe piyasa analiz',
            'hava durumu yarın hava yağmur gösterim uygun',
            'emlak haberleri sektör piyasa gelişme',
        ],
    },
    'arac': {
        'ornekler': [
            'QR kod oluştur kartvizit barkod',
            'çeviri İngilizce Arapça Rusça çevir',
            'web sayfam linki portföy paylaşım',
            'excel indir zip export veri indir',
            'yedekleme ne zaman yedek aldım backup',
            'döviz kur dolar euro altın fiyat',
        ],
    },
    'navigasyon': {
        'ornekler': [
            'sayfayı aç git müşteriler portföy muhasebe takvim ayarlar',
            'sayfasını göster aç',
        ],
    },
    'sohbet': {
        'ornekler': [
            'merhaba selam günaydın iyi akşamlar',
            'teşekkür sağol eyvallah',
            'kendinden bahset ne yapabilirsin yardım',
            'nasılsın iyi misin',
            'emlak piyasası hakkında bilgi danışmanlık tavsiye',
        ],
    },
}

# Cache
_kategori_embeddings = {}  # {kategori: [embedding1, embedding2, ...]}
_cache_zamani = None


def _embedding_al(metin):
    """OpenAI embedding."""
    api_key = os.environ.get('OPENAI_API_KEY', '')
    if not api_key:
        return None
    try:
        r = requests.post('https://api.openai.com/v1/embeddings', headers={
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json',
        }, json={'model': 'text-embedding-3-small', 'input': metin}, timeout=5)
        return np.array(r.json()['data'][0]['embedding'])
    except Exception as e:
        logger.error(f'[Router] Embedding hata: {e}')
        return None


def _embeddings_yukle():
    """Kategori örnek cümlelerinin embedding'lerini hesapla."""
    global _kategori_embeddings, _cache_zamani
    if _cache_zamani and (datetime.utcnow() - _cache_zamani).seconds < 21600 and _kategori_embeddings:
        return

    api_key = os.environ.get('OPENAI_API_KEY', '')
    if not api_key:
        return

    try:
        tum_metinler = []
        meta = []  # (kategori, index)
        for kat, data in KATEGORILER.items():
            for ornek in data['ornekler']:
                tum_metinler.append(ornek)
                meta.append(kat)

        r = requests.post('https://api.openai.com/v1/embeddings', headers={
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json',
        }, json={'model': 'text-embedding-3-small', 'input': tum_metinler}, timeout=15)

        _kategori_embeddings = {}
        for i, emb in enumerate(r.json()['data']):
            kat = meta[i]
            if kat not in _kategori_embeddings:
                _kategori_embeddings[kat] = []
            _kategori_embeddings[kat].append(np.array(emb['embedding']))

        _cache_zamani = datetime.utcnow()
        logger.info(f'[Router] {len(tum_metinler)} örnek, {len(_kategori_embeddings)} kategori yüklendi')
    except Exception as e:
        logger.error(f'[Router] Embedding yükleme hata: {e}')


def _cosine(a, b):
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))


def route(metin, threshold=0.40):
    """
    Mesajı kategorize et.

    Returns:
        [('musteri', 0.85), ('planlama', 0.62)] — eşik üstü kategoriler, skorla sıralı
        veya [] — hiçbir kategori eşleşmezse
    """
    _embeddings_yukle()
    if not _kategori_embeddings:
        return []

    mesaj_emb = _embedding_al(metin)
    if mesaj_emb is None:
        return []

    skorlar = {}
    for kat, embeddings in _kategori_embeddings.items():
        max_skor = max(_cosine(mesaj_emb, e) for e in embeddings)
        if max_skor >= threshold:
            skorlar[kat] = max_skor

    # Skora göre sırala
    sirali = sorted(skorlar.items(), key=lambda x: x[1], reverse=True)
    logger.info(f'[Router] "{metin[:50]}" → {sirali[:3]}')
    return sirali


def multi_route(metin, threshold=0.40, min_fark=0.10):
    """
    Multi-intent: birden fazla kategori döndür.
    İkinci kategori birinciden min_fark kadar yakınsa dahil et.

    Returns:
        ['musteri', 'planlama'] veya ['musteri']
    """
    sonuclar = route(metin, threshold)
    if not sonuclar:
        return []

    kategoriler = [sonuclar[0][0]]
    birinci_skor = sonuclar[0][1]

    for kat, skor in sonuclar[1:]:
        if birinci_skor - skor <= min_fark:
            kategoriler.append(kat)

    return kategoriler
