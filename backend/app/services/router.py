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
            # Ekleme
            'Ahmet Eker müşterimize ekle kiralık daire arıyor',
            'yeni müşteri kaydet Ali Veli satılık ev bakıyor',
            'müşteri ekle adı Fatma bütçesi 500 bin',
            'şu kişiyi müşterilere kaydet kiralık arıyor 2+1',
            'müşterimize ekle kiralık daire arayışı var 30000 civarı',
            # Listeleme
            'müşterilerimi göster',
            'müşteri listesi getir',
            'kaç müşterim var',
            'sıcak müşteriler kimler',
            'kiralık arayan müşteriler',
            # Arama
            'Ahmet diye bir müşterim var mı',
            'müşterilerde Ali ara',
            'A ile başlayan müşteriler',
            # Analiz
            'bu müşteri ciddi mi kaç gösterim yaptı',
            'Ahmet Beyin doğum günü ne zaman',
            'yaklaşan doğum günleri',
            # Eşleşme
            'Ahmet Beye uygun mülk var mı',
            # Silme / Güncelleme
            'müşteriyi sil',
            '2 numaralı müşteriyi sil',
            'Ahmetin telefonunu güncelle',
            'müşteriyi güncelle',
        ],
    },
    'mulk': {
        'ornekler': [
            # Ekleme
            'portföye yeni ilan ekle Kadıköy 3+1 daire kiralık 25000',
            'mülk ekle satılık villa Beşiktaş 5 milyon',
            'yeni ilan kaydet',
            # Listeleme
            'portföyü göster',
            'mülk listesi',
            'elimizde ne var',
            'kiralık neler var portföyde',
            'elimizdeki satılık daireler',
            'portföyümdeki ilanları göster',
            # Arama
            'Kadıköy de daire var mı portföyde',
            'portföyde 3+1 kiralık ara',
            '50 bin altı kiralık mülkler',
            # Silme / Güncelleme
            'mülkü sil',
            'ilanı sil portföyden kaldır',
            'fiyatı güncelle 30 bin yap',
            'mülkü güncelle',
        ],
    },
    'talep': {
        'ornekler': [
            'yeni talep ekle kiralık 2+1 daire arıyor',
            'talep oluştur satılık ev arıyor bütçe 500K',
            'talepleri göster listele',
            'kiralık arayanlar kimler',
            'satmak isteyenler',
            'kiraya vermek istiyor mülkünü',
            'mülkünü satmak istiyor',
            'talebi güncelle değiştir',
            'talebi sil kaldır',
            '1 numaralı talebi sil',
        ],
    },
    'eslestirme': {
        'ornekler': [
            'eşleştirme tablosunu göster',
            'hangi müşteri hangi mülke uygun',
            'eşleştirme yap',
            'uygun eşleşmeler var mı',
            'müşteri mülk eşleştirmesi',
        ],
    },
    'finans': {
        'ornekler': [
            'fatura kes Ahmet Bey 15000 TL komisyon',
            'faturaları göster',
            'gelir gider raporu',
            'bu ay ne kadar kazandım',
            'geçen ayki giderler',
            'cari hesap durumu',
            'ne kadar borcum var alacağım var',
            'komisyon hesapla 2 milyon satış',
            'tapu masrafı ne kadar olur',
            'kira vergisi hesapla yıllık 120 bin',
            'kira getirisi hesapla',
            'faturayı sil iptal et',
        ],
    },
    'planlama': {
        'ornekler': [
            'yarın öğleden sonra Ahmet Beyle toplantı koy',
            'yeni görev ekle',
            'görev ekle',
            'görev oluştur',
            'görev ekle pazartesi sabah gösterim var',
            'görevlerimi göster',
            'bugün ne var programım ne',
            'bu haftaki planım',
            'görevi tamamla iptal et sil',
            'görevi sil',
            '2 numaralı görevi sil',
            'randevu ayarla',
            'hatırlat bana akşam 6 da Mehmet i ara',
        ],
    },
    'not': {
        'ornekler': [
            'not ekle',
            'yeni not ekle',
            'not ekle Ahmet bey balkonu beğendi mutfağı küçük buldu',
            'not al bugün Kadıköy gösteriminde müşteri fiyatı yüksek buldu',
            'notlarımı göster',
            'notlarda Kadıköy ara',
            'gösterim notlarını göster',
            'bu notu göreve dönüştür',
            'unutma yarın Fatma hanımı ara',
            'hatırlatmalarım ne',
            # Silme / Güncelleme
            'notu sil',
            'notumu sil',
            '2 numaralı notu sil',
            'tek notum var onu da sil',
            'kalan notu sil',
            'tüm notları sil',
            'notu güncelle değiştir',
        ],
    },
    'iletisim': {
        'ornekler': [
            'Ahmet Beye WhatsApp tan yaz fiyat düştü',
            'müşteriye mesaj gönder',
            'tüm sıcak müşterilere mesaj at yeni ilan çıktı',
            'toplu mesaj gönder',
            'gösterimden sonra müşteriye anket gönder',
        ],
    },
    'teklif': {
        'ornekler': [
            'müşteri 2 milyon teklif etti',
            'teklif kaydet Kadıköy dairesi için 1.8 milyon',
            'teklif geçmişini göster',
            'satış kapandı 2.3 milyon',
            'karşı teklif geldi',
        ],
    },
    'analiz': {
        'ornekler': [
            'Kadıköy Moda mahallesi nasıl yatırım yapılır mı',
            'yarın hava nasıl gösterim yapabilir miyim',
            'hava durumu söyle',
            'emlak haberleri sektörde ne oldu',
            'piyasada son durum ne',
            'kimin satma ihtimali yüksek',
            'ısı haritası göster bölge analizi',
            'bu müşteri ciddi mi satıcı tahmin',
        ],
    },
    'islem_takip': {
        'ornekler': [
            'son işlemler ne yaptık bugün',
            'işlem geçmişi göster',
            'geri al son işlemi iptal et',
            'az önceki eklemeyi geri al',
            'ne değişiklik yaptım',
        ],
    },
    'arac': {
        'ornekler': [
            'QR kod oluştur',
            'kartvizit QR kodumu ver',
            'bu ilanı Arapçaya çevir',
            'İngilizce çeviri yap',
            'portföyü excel olarak indir',
            'müşteri listesini excel ver',
            'tüm veriyi zip indir',
            'web sayfamın linkini ver',
            'sayfam neydi',
            'ne zaman yedek aldım',
            'yedekleme durumu',
            'döviz kuru ne',
            'dolar kaç',
            'altın fiyatı',
        ],
    },
    'navigasyon': {
        'ornekler': [
            'müşteriler sayfasını aç',
            'portföye git',
            'muhasebe sayfasını göster',
            'takvimi aç',
            'ayarlara git',
            'notlar sayfasını aç',
        ],
    },
    'sohbet': {
        'ornekler': [
            'merhaba',
            'günaydın bugün nasılsın',
            'selam ne yapabilirsin',
            'teşekkürler çok yardımcı oldun',
            'uygulamayı anlat',
            'emlak piyasası hakkında ne düşünüyorsun',
            'tapu masrafı nasıl hesaplanır',
            'kira artış oranı ne kadar',
            'kendinden bahset',
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
