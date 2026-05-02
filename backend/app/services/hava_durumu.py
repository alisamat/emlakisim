"""
HAVA DURUMU SERVİSİ — Open-Meteo (ücretsiz, key gerektirmez)
"""
import requests
import logging

logger = logging.getLogger(__name__)

# Türkiye şehir koordinatları
SEHIR_KOORDINAT = {
    'istanbul': (41.01, 28.98), 'ankara': (39.93, 32.86), 'izmir': (38.42, 27.14),
    'antalya': (36.89, 30.71), 'bursa': (40.19, 29.06), 'adana': (37.00, 35.32),
    'konya': (37.87, 32.49), 'gaziantep': (37.07, 37.38), 'mersin': (36.80, 34.64),
    'kayseri': (38.73, 35.49), 'eskisehir': (39.78, 30.52), 'trabzon': (41.00, 39.72),
    'samsun': (41.29, 36.33), 'denizli': (37.77, 29.09), 'sakarya': (40.69, 30.40),
    'mugla': (37.22, 28.36), 'bodrum': (37.04, 27.43), 'kadikoy': (40.98, 29.09),
    'besiktas': (41.04, 29.00), 'atasehir': (40.98, 29.13), 'bakirkoy': (40.98, 28.87),
}

HAVA_KODU = {
    0: '☀️ Açık', 1: '🌤 Az bulutlu', 2: '⛅ Parçalı bulutlu', 3: '☁️ Bulutlu',
    45: '🌫 Sisli', 48: '🌫 Kırağılı sis',
    51: '🌦 Hafif çisenti', 53: '🌦 Çisenti', 55: '🌧 Yoğun çisenti',
    61: '🌧 Hafif yağmur', 63: '🌧 Yağmur', 65: '🌧 Şiddetli yağmur',
    71: '🌨 Hafif kar', 73: '🌨 Kar', 75: '❄️ Yoğun kar',
    80: '🌦 Sağanak', 81: '🌧 Kuvvetli sağanak', 82: '⛈ Şiddetli sağanak',
    95: '⛈ Gök gürültülü fırtına', 96: '⛈ Dolu', 99: '⛈ Şiddetli dolu',
}


def hava_getir(sehir='istanbul', gun=3):
    """Hava durumu getir — bugün + sonraki günler."""
    sehir_lower = sehir.lower().replace('ı', 'i').replace('ş', 's').replace('ç', 'c').replace('ö', 'o').replace('ü', 'u').replace('ğ', 'g')

    # Koordinat bul
    lat, lon = SEHIR_KOORDINAT.get(sehir_lower, (41.01, 28.98))  # default İstanbul

    try:
        r = requests.get('https://api.open-meteo.com/v1/forecast', params={
            'latitude': lat, 'longitude': lon,
            'daily': 'temperature_2m_max,temperature_2m_min,precipitation_sum,weathercode,windspeed_10m_max',
            'timezone': 'Europe/Istanbul',
            'forecast_days': min(gun, 7),
        }, timeout=10)
        data = r.json()
        daily = data.get('daily', {})

        gunler = []
        for i in range(len(daily.get('time', []))):
            kod = daily['weathercode'][i]
            gunler.append({
                'tarih': daily['time'][i],
                'max_sicaklik': daily['temperature_2m_max'][i],
                'min_sicaklik': daily['temperature_2m_min'][i],
                'yagis_mm': daily['precipitation_sum'][i],
                'ruzgar_kmh': daily['windspeed_10m_max'][i],
                'durum': HAVA_KODU.get(kod, f'Kod {kod}'),
                'gosterim_uygun': kod < 61 and daily['precipitation_sum'][i] < 5,
            })

        return {'basarili': True, 'sehir': sehir, 'gunler': gunler}
    except Exception as e:
        logger.error(f'[HavaDurumu] Hata: {e}')
        return {'basarili': False, 'hata': str(e)}


def hava_formatla(sonuc):
    """Hava durumu sonucunu sohbet mesajına çevir."""
    if not sonuc.get('basarili'):
        return '⚠️ Hava durumu alınamadı.'

    satirlar = [f'🌤 *{sonuc["sehir"]} — Hava Durumu*\n']
    gun_adlari = ['Pazartesi', 'Salı', 'Çarşamba', 'Perşembe', 'Cuma', 'Cumartesi', 'Pazar']

    for i, g in enumerate(sonuc['gunler']):
        from datetime import datetime
        tarih = datetime.strptime(g['tarih'], '%Y-%m-%d')
        gun_adi = gun_adlari[tarih.weekday()]
        bugun = '_(bugün)_' if i == 0 else '_(yarın)_' if i == 1 else ''

        uygunluk = '✅ Gösterim uygun' if g['gosterim_uygun'] else '❌ Gösterim uygun değil'

        satirlar.append(
            f'*{gun_adi}* {bugun}\n'
            f'  {g["durum"]} · {g["min_sicaklik"]}°-{g["max_sicaklik"]}°C'
            + (f' · 🌧 {g["yagis_mm"]}mm' if g['yagis_mm'] > 0 else '')
            + (f' · 💨 {g["ruzgar_kmh"]}km/h' if g['ruzgar_kmh'] > 30 else '')
            + f'\n  {uygunluk}'
        )

    return '\n'.join(satirlar)
