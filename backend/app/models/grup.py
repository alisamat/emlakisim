"""
EMLAKÇILAR & GRUP MODELLERİ
Emlakçılar dizini + İşbirliği grupları
"""
from app import db
from datetime import datetime


class EmlakciDizin(db.Model):
    """Dış emlakçılar dizini (uygulamayı kullanmayan da olabilir)"""
    __tablename__ = 'emlakci_dizin'

    id          = db.Column(db.Integer, primary_key=True)
    ekleyen_id  = db.Column(db.Integer, db.ForeignKey('emlakci.id'), nullable=False)
    ad_soyad    = db.Column(db.String(120), nullable=False)
    telefon     = db.Column(db.String(20))
    email       = db.Column(db.String(120))
    adres       = db.Column(db.Text)
    bolge       = db.Column(db.String(100))       # çalıştığı bölge
    uzmanlik    = db.Column(db.String(100))       # kiralık, satılık, ticari
    acente      = db.Column(db.String(120))
    notlar      = db.Column(db.Text)
    kullanici_id = db.Column(db.Integer, db.ForeignKey('emlakci.id'), nullable=True)  # uygulamayı kullananla eşleşme
    detaylar    = db.Column(db.JSON, default=dict)
    olusturma   = db.Column(db.DateTime, default=datetime.utcnow)


class Grup(db.Model):
    """Emlakçı işbirliği grubu"""
    __tablename__ = 'grup'

    id          = db.Column(db.Integer, primary_key=True)
    ad          = db.Column(db.String(120), nullable=False)
    slogan      = db.Column(db.String(200))
    aciklama    = db.Column(db.Text)
    kurucu_id   = db.Column(db.Integer, db.ForeignKey('emlakci.id'), nullable=False)
    aktif       = db.Column(db.Boolean, default=True)
    detaylar    = db.Column(db.JSON, default=dict)
    olusturma   = db.Column(db.DateTime, default=datetime.utcnow)

    uyeler      = db.relationship('GrupUyelik', backref='grup', lazy=True)


class GrupUyelik(db.Model):
    """Grup üyelik kaydı"""
    __tablename__ = 'grup_uyelik'

    id          = db.Column(db.Integer, primary_key=True)
    grup_id     = db.Column(db.Integer, db.ForeignKey('grup.id'), nullable=False)
    emlakci_id  = db.Column(db.Integer, db.ForeignKey('emlakci.id'), nullable=False)
    rol         = db.Column(db.String(15), default='uye')  # yonetici / uye
    durum       = db.Column(db.String(15), default='bekliyor')  # bekliyor / aktif / reddetti / cikti
    portfoy_acik = db.Column(db.Boolean, default=False)    # portföyü gruba açık mı
    talep_acik  = db.Column(db.Boolean, default=False)     # talepleri gruba açık mı
    olusturma   = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (db.UniqueConstraint('grup_id', 'emlakci_id', name='uq_grup_emlakci'),)


class GrupBildirim(db.Model):
    """Grup aktivite bildirimleri"""
    __tablename__ = 'grup_bildirim'

    id          = db.Column(db.Integer, primary_key=True)
    grup_id     = db.Column(db.Integer, db.ForeignKey('grup.id'), nullable=False)
    emlakci_id  = db.Column(db.Integer, db.ForeignKey('emlakci.id'), nullable=True)
    tip         = db.Column(db.String(20))       # uye_girdi, uye_cikti, yonetici_atandi
    mesaj       = db.Column(db.String(200))
    olusturma   = db.Column(db.DateTime, default=datetime.utcnow)
