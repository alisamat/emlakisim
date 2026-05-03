from app import db
from datetime import datetime
import secrets

# Muhasebe modelleri ayrı dosyada — buradan import et
from app.models.muhasebe import GelirGider, Cari, CariHareket
from app.models.planlama import Gorev
from app.models.egitim import DiyalogKayit, OgrenilenPattern
from app.models.lead import Lead, CagriKayit
from app.models.bildirim import Bildirim
from app.models.fatura import Fatura
from app.models.islem_takip import SurecTakip, Evrak
from app.models.ofis import Envanter, GeriBildirim
from app.models.ofis_ekip import Danisман, MusteriAtama
from app.models.iletisim_gecmisi import IletisimKayit
from app.models.grup import EmlakciDizin, Grup, GrupUyelik, GrupBildirim
from app.models.hafiza_model import MusteriHafiza, KonusmaState
from app.models.ayarlar import KullaniciAyar, SistemParametre
from app.models.talep import Talep


class Emlakci(db.Model):
    """Sisteme kayıtlı emlakçı/acente kullanıcılar"""
    __tablename__ = 'emlakci'

    id            = db.Column(db.Integer, primary_key=True)
    ad_soyad      = db.Column(db.String(120), nullable=False)
    email         = db.Column(db.String(120), unique=True, nullable=False)
    telefon       = db.Column(db.String(20), unique=True, nullable=False)
    sifre_hash    = db.Column(db.String(256), nullable=False)
    yetki_no      = db.Column(db.String(50))           # Taşınmaz Ticareti yetki belgesi
    acente_adi    = db.Column(db.String(120))
    slug          = db.Column(db.String(100), unique=True)  # web sayfası: emlakisim.com/sayfa/arif-kaya
    unvan         = db.Column(db.String(100))              # "Gayrimenkul Danışmanı", "Broker" vb.
    slogan        = db.Column(db.String(200))              # "Güvenilir emlak çözümleri"
    logo_url      = db.Column(db.Text)                     # logo base64 veya URL
    adres         = db.Column(db.Text)                     # işyeri adresi
    telefon2      = db.Column(db.String(20))               # ikinci telefon
    website       = db.Column(db.String(200))              # kişisel web sitesi
    sosyal_medya  = db.Column(db.JSON, default=dict)       # {"instagram": "...", "facebook": "...", "linkedin": "..."}
    ruhsat_no     = db.Column(db.String(50))               # emlakçılık ruhsat numarası
    vergi_no      = db.Column(db.String(20))               # vergi numarası
    profil_gorunum = db.Column(db.JSON, default=dict)      # hangi bilgiler public sayfada gösterilecek
    aktif         = db.Column(db.Boolean, default=True)
    kredi         = db.Column(db.Float, default=10.0)
    kredi_son_kullanma = db.Column(db.DateTime)    # kredi son kullanma tarihi
    olusturma     = db.Column(db.DateTime, default=datetime.utcnow)

    musteriler    = db.relationship('Musteri', backref='emlakci', lazy=True)
    mulkler       = db.relationship('Mulk', backref='emlakci', lazy=True)
    konusmalar    = db.relationship('Konusma', backref='emlakci', lazy=True)


class Musteri(db.Model):
    """Emlakçının müşterileri (alıcı/kiracı)"""
    __tablename__ = 'musteri'

    id            = db.Column(db.Integer, primary_key=True)
    emlakci_id    = db.Column(db.Integer, db.ForeignKey('emlakci.id'), nullable=False)
    ad_soyad      = db.Column(db.String(120), nullable=False)
    telefon       = db.Column(db.String(20))
    tc_kimlik     = db.Column(db.String(11))
    email         = db.Column(db.String(120))
    islem_turu    = db.Column(db.String(10))            # kira / satis
    butce_min     = db.Column(db.Float)
    butce_max     = db.Column(db.Float)
    tercih_notlar = db.Column(db.Text)                  # AI tarafından işlenen tercihler
    sicaklik      = db.Column(db.String(10), default='orta')  # soguk/orta/sicak
    grup          = db.Column(db.String(50))              # kullanıcı tanımlı grup
    kunye         = db.Column(db.String(100))             # ayırt edici: "Eyyüpteki", "Samilerin", "mimar"
    dogum_tarihi  = db.Column(db.Date)                   # doğum günü takibi için
    detaylar      = db.Column(db.JSON, default=dict)     # tip bazlı dinamik alanlar
    olusturma     = db.Column(db.DateTime, default=datetime.utcnow)
    guncelleme    = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    yer_gostermeler = db.relationship('YerGosterme', backref='musteri', lazy=True)


class Teklif(db.Model):
    """Mülk için gelen/verilen teklifler — pazarlık takibi"""
    __tablename__ = 'teklif'

    id          = db.Column(db.Integer, primary_key=True)
    emlakci_id  = db.Column(db.Integer, db.ForeignKey('emlakci.id'), nullable=False)
    mulk_id     = db.Column(db.Integer, db.ForeignKey('mulk.id'), nullable=True)
    musteri_id  = db.Column(db.Integer, db.ForeignKey('musteri.id'), nullable=True)
    teklif_tutar = db.Column(db.Float, nullable=False)
    istenen_tutar = db.Column(db.Float)                 # mal sahibinin istediği
    durum       = db.Column(db.String(20), default='bekliyor')  # bekliyor/kabul/red/karsi_teklif
    notlar      = db.Column(db.Text)
    olusturma   = db.Column(db.DateTime, default=datetime.utcnow)


class Mulk(db.Model):
    """Emlakçının portföyündeki mülkler"""
    __tablename__ = 'mulk'

    id            = db.Column(db.Integer, primary_key=True)
    emlakci_id    = db.Column(db.Integer, db.ForeignKey('emlakci.id'), nullable=False)
    baslik        = db.Column(db.String(200))
    adres         = db.Column(db.Text)
    sehir         = db.Column(db.String(50))
    ilce          = db.Column(db.String(50))
    tip           = db.Column(db.String(20))            # daire/villa/arsa/dukkan
    islem_turu    = db.Column(db.String(10))            # kira / satis
    fiyat         = db.Column(db.Float)
    metrekare     = db.Column(db.Float)
    oda_sayisi    = db.Column(db.String(10))            # 2+1, 3+1...
    ada           = db.Column(db.String(20))
    parsel        = db.Column(db.String(20))
    notlar        = db.Column(db.Text)
    detaylar      = db.Column(db.JSON, default=dict)     # tip bazlı dinamik alanlar
    grup          = db.Column(db.String(50))              # kullanıcı tanımlı grup
    yasal_durum   = db.Column(db.JSON, default=dict)     # iskan, ipotek, haciz, dask, imar
    resimler      = db.Column(db.JSON, default=list)     # [{"url": "...", "aciklama": "salon", "ana": true}]
    musteri_id    = db.Column(db.Integer, db.ForeignKey('musteri.id'), nullable=True)  # mülk sahibi
    aktif         = db.Column(db.Boolean, default=True)
    olusturma     = db.Column(db.DateTime, default=datetime.utcnow)

    yer_gostermeler = db.relationship('YerGosterme', backref='mulk', lazy=True)


class YerGosterme(db.Model):
    """Yer gösterme kayıtları ve belgeleri"""
    __tablename__ = 'yer_gosterme'

    id            = db.Column(db.Integer, primary_key=True)
    emlakci_id    = db.Column(db.Integer, db.ForeignKey('emlakci.id'), nullable=False)
    musteri_id    = db.Column(db.Integer, db.ForeignKey('musteri.id'))
    mulk_id       = db.Column(db.Integer, db.ForeignKey('mulk.id'))
    tarih         = db.Column(db.DateTime, default=datetime.utcnow)
    pdf_url       = db.Column(db.Text)
    musteri_onay  = db.Column(db.Boolean, default=False)
    onay_tarihi   = db.Column(db.DateTime)
    onay_ip       = db.Column(db.String(50))
    ham_veri      = db.Column(db.JSON)                  # WhatsApp'tan gelen raw data


class Konusma(db.Model):
    """WhatsApp konuşma geçmişi (AI hafızası için)"""
    __tablename__ = 'konusma'

    id            = db.Column(db.Integer, primary_key=True)
    emlakci_id    = db.Column(db.Integer, db.ForeignKey('emlakci.id'), nullable=False)
    wa_mesaj_id   = db.Column(db.String(100))
    yon           = db.Column(db.String(10))             # gelen / giden
    icerik        = db.Column(db.Text)
    tip           = db.Column(db.String(20))             # metin/foto/ses/konum
    ai_analiz     = db.Column(db.JSON)                   # AI tarafından çıkarılan yapısal veri
    olusturma     = db.Column(db.DateTime, default=datetime.utcnow)


class Not(db.Model):
    """Emlakçının notları ve planları"""
    __tablename__ = 'not'

    id            = db.Column(db.Integer, primary_key=True)
    emlakci_id    = db.Column(db.Integer, db.ForeignKey('emlakci.id'), nullable=False)
    musteri_id    = db.Column(db.Integer, db.ForeignKey('musteri.id'), nullable=True)
    mulk_id       = db.Column(db.Integer, db.ForeignKey('mulk.id'), nullable=True)
    icerik        = db.Column(db.Text, nullable=False)
    etiket        = db.Column(db.String(50))             # not/plan/hatirlatici
    tamamlandi    = db.Column(db.Boolean, default=False)
    hatirlatma    = db.Column(db.DateTime)
    olusturma     = db.Column(db.DateTime, default=datetime.utcnow)


class PanelSohbet(db.Model):
    """Uygulama içi AI sohbet konuşmaları"""
    __tablename__ = 'panel_sohbet'

    id          = db.Column(db.Integer, primary_key=True)
    emlakci_id  = db.Column(db.Integer, db.ForeignKey('emlakci.id'), nullable=False)
    baslik      = db.Column(db.String(200))
    olusturma   = db.Column(db.DateTime, default=datetime.utcnow)
    guncelleme  = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    mesajlar    = db.relationship('PanelMesaj', backref='sohbet', lazy=True, order_by='PanelMesaj.olusturma')


class PanelMesaj(db.Model):
    """Sohbet mesajları"""
    __tablename__ = 'panel_mesaj'

    id          = db.Column(db.Integer, primary_key=True)
    sohbet_id   = db.Column(db.Integer, db.ForeignKey('panel_sohbet.id'), nullable=False)
    rol         = db.Column(db.String(10), nullable=False)   # user / assistant
    icerik      = db.Column(db.Text, nullable=False)
    olusturma   = db.Column(db.DateTime, default=datetime.utcnow)


class IslemLog(db.Model):
    """Tüm işlemlerin kredi ve maliyet kaydı"""
    __tablename__ = 'islem_log'

    id           = db.Column(db.Integer, primary_key=True)
    emlakci_id   = db.Column(db.Integer, db.ForeignKey('emlakci.id'), nullable=False)
    islem_tipi   = db.Column(db.String(50))       # ai_sohbet, musteri_ekle, mulk_ekle, belge, rapor, pattern
    model        = db.Column(db.String(30))       # gemini-flash, gpt-4o-mini, claude-haiku, pattern, null
    token_input  = db.Column(db.Integer)
    token_output = db.Column(db.Integer)
    maliyet_usd  = db.Column(db.Float, default=0)
    kredi_tutar  = db.Column(db.Float, default=0)
    aciklama     = db.Column(db.String(200))
    olusturma    = db.Column(db.DateTime, default=datetime.utcnow)


class MusteriOnayToken(db.Model):
    """Müşteri belge onayı için tek kullanımlık token"""
    __tablename__ = 'musteri_onay_token'

    id              = db.Column(db.Integer, primary_key=True)
    yer_gosterme_id = db.Column(db.Integer, db.ForeignKey('yer_gosterme.id'), nullable=False)
    token           = db.Column(db.String(64), unique=True, default=lambda: secrets.token_hex(32))
    kullanildi      = db.Column(db.Boolean, default=False)
    olusturma       = db.Column(db.DateTime, default=datetime.utcnow)
