"""
EMLAK DANIŞMANLIK — Sık sorulan sorular + mevzuat bilgi bankası
Pattern matching ile sıfır maliyet cevaplar.
"""

# Emlak danışmanlığı bilgi bankası — yeni soru eklemek = 1 satır
BILGI_BANKASI = {
    'tapu_masrafi': {
        'anahtar': ['tapu masraf', 'tapu harç', 'tapu ücreti', 'tapu maliyeti'],
        'cevap': (
            '*📋 Tapu Masrafları*\n\n'
            '• Tapu harcı: Satış bedelinin *%4*\'ü (alıcı %2 + satıcı %2)\n'
            '• Döner sermaye: ~₺700-1.500\n'
            '• Zorunlu deprem sigortası (DASK): ₺500-2.000\n'
            '• Ekspertiz: ₺3.000-5.000 (kredi kullanılıyorsa)\n\n'
            '_Not: Tapu harcı genellikle alıcı tarafından ödenir._'
        ),
    },
    'kira_artis': {
        'anahtar': ['kira artış', 'kira zam', 'kira artırım', 'tufe', 'tüfe'],
        'cevap': (
            '*📈 Kira Artış Oranı*\n\n'
            '• Konut kiraları: Yıllık *TÜFE* oranında artırılabilir\n'
            '• 12 aylık TÜFE ortalaması esas alınır\n'
            '• Taraflar anlaşırsa daha düşük oran uygulanabilir\n'
            '• 5 yıl sonunda hâkim yeniden belirleyebilir\n\n'
            '_TBK md. 344 — Konut ve çatılı işyeri kira artışı_'
        ),
    },
    'depozito': {
        'anahtar': ['depozito', 'güvence bedeli', 'kapora'],
        'cevap': (
            '*💰 Depozito (Güvence Bedeli)*\n\n'
            '• En fazla *3 aylık kira* tutarı alınabilir\n'
            '• Nakit olarak alınmamalı, bankaya yatırılmalı\n'
            '• Kira sözleşmesi bitiminde iade edilir\n'
            '• Hasar varsa hasar bedeli düşülebilir\n\n'
            '_TBK md. 342_'
        ),
    },
    'tahliye': {
        'anahtar': ['tahliye', 'kiracı çıkarma', 'kiracı tahliye', 'ev sahibi hakları'],
        'cevap': (
            '*🏠 Kiracı Tahliye Sebepleri*\n\n'
            '• İhtiyaç: Ev sahibi/yakınları için ihtiyaç (6 ay önce ihtar)\n'
            '• Yeni malik: Satın alan 6 ay içinde ihtar + 6 ay süre\n'
            '• Tadilat: Esaslı onarım/inşaat\n'
            '• 2 haklı ihtar: 1 yıl içinde 2 kez gecikme\n'
            '• 10 yıl uzama: 10 yılı dolduran sözleşme\n\n'
            '_Tahliye davası açmadan önce ihtar çekilmelidir._'
        ),
    },
    'emlakci_komisyon': {
        'anahtar': ['komisyon', 'emlakçı ücreti', 'hizmet bedeli', 'komisyon oranı'],
        'cevap': (
            '*💼 Emlakçı Komisyon Oranları*\n\n'
            '• Satış: Satış bedelinin *%2+KDV* (alıcı + satıcıdan ayrı ayrı)\n'
            '• Kiralama: *1 aylık kira* + KDV\n'
            '• Taşınmaz Ticareti Yönetmeliği\'ne göre belirlenir\n'
            '• Yetki belgesi olmadan komisyon alınamaz\n\n'
            '_Hizmet sözleşmesi zorunludur._'
        ),
    },
    'yetki_belgesi': {
        'anahtar': ['yetki belgesi', 'taşınmaz ticareti', 'emlakçı belgesi', 'mesleki yeterlilik'],
        'cevap': (
            '*📜 Taşınmaz Ticareti Yetki Belgesi*\n\n'
            '• Zorunlu: Tüm emlak danışmanları için\n'
            '• Seviye 5: Emlak danışmanı\n'
            '• Seviye 4: Sorumlu emlak danışmanı\n'
            '• MYK sınavı + Ticaret Bakanlığı onayı gerekli\n'
            '• Belgesiz faaliyet: Para cezası\n\n'
            '_Taşınmaz Ticareti Hakkında Yönetmelik_'
        ),
    },
    'dask': {
        'anahtar': ['dask', 'deprem sigortası', 'zorunlu sigorta'],
        'cevap': (
            '*🏗 DASK (Zorunlu Deprem Sigortası)*\n\n'
            '• Tapu işlemi için zorunlu\n'
            '• Belediye sınırları içindeki tüm binalar\n'
            '• Prim: yapı tarzı + m² + bölge risk grubuna göre\n'
            '• Teminat limiti: ~₺640.000 (2026)\n'
            '• Poliçe süresi: 1 yıl\n\n'
            '_6305 sayılı Afet Sigortaları Kanunu_'
        ),
    },
    'kat_mulkiyeti': {
        'anahtar': ['kat mülkiyeti', 'kat irtifakı', 'kat irtifaki', 'tapu türü', 'tapu turu'],
        'cevap': (
            '*📄 Kat Mülkiyeti vs Kat İrtifakı*\n\n'
            '• *Kat Mülkiyeti:* Bina tamamlanmış, iskan alınmış\n'
            '• *Kat İrtifakı:* İnşaat aşamasında veya iskan yok\n'
            '• Kat irtifakında kredi almak daha zor\n'
            '• Kat mülkiyeti fiyatı daha yüksek\n'
            '• İskan belgesi alındığında irtifak → mülkiyete dönüşür\n\n'
            '_Kat irtifakı riskli olabilir, iskan durumu mutlaka kontrol edilmeli._'
        ),
    },
    'kira_sozlesmesi': {
        'anahtar': ['kira sözleşme', 'kira sozlesme', 'kira kontrat', 'kontrat süresi', 'kontrat suresi'],
        'cevap': (
            '*📋 Kira Sözleşmesi Bilgileri*\n\n'
            '• Yazılı sözleşme zorunlu değil ama önerilir\n'
            '• Standart süre: 1 yıl (otomatik yenilenir)\n'
            '• Kiracı 15 gün önceden bildirimle çıkabilir\n'
            '• Ev sahibi 10 yıl sözleşmeyi feshedemez (ihtiyaç hariç)\n'
            '• Kontrat damga vergisi: %0,189 (genellikle paylaşılır)\n\n'
            '_TBK md. 339-356 — Konut ve çatılı işyeri kiraları_'
        ),
    },
    'emlak_vergisi': {
        'anahtar': ['emlak vergisi', 'bina vergisi', 'arsa vergisi', 'vergi oranı'],
        'cevap': (
            '*🏛 Emlak Vergisi Oranları*\n\n'
            '• Konut: *%0,1* (Büyükşehir %0,2)\n'
            '• İşyeri: *%0,2* (Büyükşehir %0,4)\n'
            '• Arsa: *%0,3* (Büyükşehir %0,6)\n'
            '• Arazi: *%0,1* (Büyükşehir %0,2)\n'
            '• Ödeme: Yılda 2 taksit (Mart-Mayıs / Kasım)\n'
            '• Muafiyet: Emekli, engelli, 200m² altı tek konut\n\n'
            '_1319 sayılı Emlak Vergisi Kanunu_'
        ),
    },
    'tapu_sureci': {
        'anahtar': ['tapu süreci', 'tapu sureci', 'tapu nasıl', 'tapu devir', 'tapu devri nasıl'],
        'cevap': (
            '*📋 Tapu Devir Süreci*\n\n'
            '1. Satış sözleşmesi imzalama\n'
            '2. Kapora/kaparo alımı\n'
            '3. DASK poliçesi\n'
            '4. Ekspertiz raporu (kredi varsa)\n'
            '5. Kredi onayı (varsa)\n'
            '6. Tapu müdürlüğü randevusu\n'
            '7. Tapu devri (her iki taraf hazır)\n'
            '8. Anahtar teslimi\n\n'
            '• Süre: Ortalama 2-4 hafta\n'
            '• Masraf: %4 tapu harcı + döner sermaye + DASK\n\n'
            '_"Tapu takibi oluştur" yazarak süreci takip edebilirsiniz._'
        ),
    },
    'kredi_sureci': {
        'anahtar': ['kredi süreci', 'kredi sureci', 'konut kredisi', 'mortgage', 'kredi nasıl'],
        'cevap': (
            '*🏦 Konut Kredisi Süreci*\n\n'
            '1. Banka başvurusu (gelir belgesi, kimlik)\n'
            '2. Gelir değerlendirme\n'
            '3. Ekspertiz (banka görevlisi gelir)\n'
            '4. Kredi onayı\n'
            '5. Sözleşme imzası\n'
            '6. Tapu devri ile eş zamanlı ödeme\n\n'
            '• Süre: 1-2 hafta\n'
            '• LTV: Genellikle %80 (konut değerinin)\n'
            '• Gerekli: Maaş bordrosu, SGK dökümü, kimlik\n\n'
            '_"Kredi takibi oluştur" yazarak süreci takip edebilirsiniz._'
        ),
    },
    'ekspertiz': {
        'anahtar': ['ekspertiz', 'değerleme', 'degerleme', 'ekspertiz raporu'],
        'cevap': (
            '*📊 Ekspertiz (Değerleme) Raporu*\n\n'
            '• Bankanın görevlendirdiği SPK lisanslı değerleme şirketi yapar\n'
            '• Süre: 2-5 iş günü\n'
            '• Ücret: ₺3.000-5.000 (alıcı öder)\n'
            '• İçerik: konum, m², yaş, emsal, imar, piyasa değeri\n'
            '• Kredi tutarı ekspertiz değerine göre belirlenir\n'
            '• Ekspertiz < satış fiyatı ise kredi düşük çıkar\n\n'
            '_Ekspertiz raporu 3 ay geçerlidir._'
        ),
    },
    'vergi_muafiyeti': {
        'anahtar': ['vergi muafiyet', 'kira vergi istisna', 'vergi istisnası'],
        'cevap': (
            '*🧾 Kira Geliri Vergi İstisnası*\n\n'
            '• Konut kira geliri istisnası: ~₺33.000/yıl (2026 tahmini)\n'
            '• İşyeri kiralarında istisna yoktur\n'
            '• Stopaj: İşyeri kiralarında %20 tevkifat\n'
            '• Beyanname: Mart ayında verilir\n'
            '• Götürü gider: %15 indirim hakkı\n\n'
            '_GVK md. 21 — Mesken kira geliri istisnası_'
        ),
    },
}


def danismanlik_cevapla(metin_norm):
    """Bilgi bankasından cevap bul. Bulursa cevap döndür, bulamazsa None."""
    for key, veri in BILGI_BANKASI.items():
        for anahtar in veri['anahtar']:
            if anahtar.replace('ı', 'i').replace('ö', 'o').replace('ü', 'u').replace('ş', 's').replace('ç', 'c').replace('ğ', 'g') in metin_norm:
                return veri['cevap']
    return None
